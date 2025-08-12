from werkzeug.wrappers import Response

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_with_phone_number
from .twilio_handler import Twilio, IncomingCall, TwilioCallDetails
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import incoming_message_callback
from twilio.twiml.messaging_response import MessagingResponse

@frappe.whitelist()
def get_twilio_phone_numbers():
	twilio = Twilio.connect()
	return (twilio and twilio.get_phone_numbers()) or []

@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK.
	"""
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value('Voice Call Settings', frappe.session.user, 'twilio_number')
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller"
		}

	token=twilio.generate_voice_access_token(from_number=from_number, identity=frappe.session.user)
	return {
		'token': frappe.safe_decode(token)
	}

@frappe.whitelist(allow_guest=True)
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server.
	"""
	def _get_caller_number(caller):
		identity = caller.replace('client:', '').strip()
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value('Voice Call Settings', user, 'twilio_number')

	args = frappe._dict(kwargs)
	twilio = Twilio.connect()
	if not twilio:
		return

	assert args.AccountSid == twilio.account_sid
	assert args.ApplicationSid == twilio.application_sid

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)
	resp = twilio.generate_twilio_dial_response(from_number, args.To)

	call_details = TwilioCallDetails(args, call_from=from_number)
	create_call_log(call_details)
	return Response(resp.to_xml(), mimetype='text/xml')

@frappe.whitelist(allow_guest=True)
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	call_details = TwilioCallDetails(args)
	create_call_log(call_details)

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype='text/xml')

@frappe.whitelist()
def create_call_log(call_details: TwilioCallDetails):
	call_log = frappe.get_doc({**call_details.to_dict(),
		'doctype': 'Call Log',
		'medium': 'Twilio'
	})

	call_log.flags.ignore_permissions = True
	call_log.save()
	frappe.db.commit()

@frappe.whitelist()
def update_call_log(call_sid, status=None):
	"""Update call log status.
	"""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("Call Log", call_sid)): return

	call_details = twilio.get_call_info(call_sid)
	call_log = frappe.get_doc("Call Log", call_sid)
	call_log.status = status or TwilioCallDetails.get_call_status(call_details.status)
	call_log.duration = call_details.duration
	call_log.flags.ignore_permissions = True
	call_log.save()
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	try:
		args = frappe._dict(kwargs)
		recording_url = args.RecordingUrl
		call_sid = args.CallSid
		update_call_log(call_sid)
		frappe.db.set_value("Call Log", call_sid, "recording_url", recording_url)
	except:
		frappe.log_error(title=_("Failed to capture Twilio recording"))

@frappe.whitelist()
def get_contact_details(phone):
	"""Get information about existing contact in the system.
	"""
	contact = get_contact_with_phone_number(phone.strip())
	if not contact: return
	contact_doc = frappe.get_doc('Contact', contact)
	return contact_doc and {
		'first_name': contact_doc.first_name.title(),
		'email_id': contact_doc.email_id,
		'phone_number': contact_doc.phone
	}

@frappe.whitelist(allow_guest=True)
def incoming_whatsapp_message_handler(**kwargs):
	"""This is a webhook called by Twilio when a WhatsApp message is received.
	"""
	args = frappe._dict(kwargs)
	incoming_message_callback(args)
	resp = MessagingResponse()

	# Add a message
	resp.message(frappe.db.get_single_value('Twilio Settings', 'reply_message'))
	return Response(resp.to_xml(), mimetype='text/xml')

@frappe.whitelist(allow_guest=True)
def whatsapp_message_status_callback(**kwargs):
	"""This is a webhook called by Twilio whenever sent WhatsApp message status is changed.
	"""
	args = frappe._dict(kwargs)
	try:
		if frappe.db.exists({'doctype': 'WhatsApp Message', 'id': args.MessageSid, 'from_': args.From, 'to': args.To}):
			message = frappe.get_doc('WhatsApp Message', {'id': args.MessageSid, 'from_': args.From, 'to': args.To})
			
			# Update status with enhanced error handling
			new_status = args.MessageStatus.title()
			message.db_set('status', new_status)
			
			# Log template-related errors specifically
			if new_status == 'Failed' and hasattr(args, 'ErrorCode'):
				error_details = f"Error Code: {args.ErrorCode}"
				if hasattr(args, 'ErrorMessage'):
					error_details += f", Message: {args.ErrorMessage}"
				
				# Check for template-specific errors
				if args.ErrorCode == '63016':
					error_details += " - This error occurs when sending freeform messages outside the 24-hour window. Use WhatsApp Template mode instead."
				
				frappe.log_error(
					title=f"WhatsApp Message Failed - {args.MessageSid}",
					message=error_details
				)
			
			frappe.db.commit()
	except Exception as e:
		frappe.log_error(
			title="WhatsApp Status Callback Error",
			message=f"Failed to process status callback: {str(e)}\nArgs: {args}"
		)

@frappe.whitelist()
def get_approved_whatsapp_templates():
	"""Get list of approved WhatsApp templates for notifications"""
	return frappe.get_all(
		'WhatsApp Message Template',
		filters={'template_status': 'Approved'},
		fields=['name', 'template_name', 'content_sid', 'message']
	)

@frappe.whitelist()
def test_whatsapp_template(template_name, test_variables=None):
	"""Test WhatsApp template with sample variables"""
	if not template_name:
		return {"success": False, "message": "Template name is required"}
	
	try:
		template_doc = frappe.get_doc('WhatsApp Message Template', template_name)
		
		if template_doc.template_status != 'Approved':
			return {"success": False, "message": "Template is not approved"}
		
		if not template_doc.content_sid:
			return {"success": False, "message": "Template does not have Content SID"}
		
		# Prepare test variables
		if test_variables:
			import json
			if isinstance(test_variables, str):
				test_variables = json.loads(test_variables)
		else:
			test_variables = {}
		
		# Get content variables for template
		content_vars = template_doc.get_content_variables(test_variables)
		
		return {
			"success": True,
			"template_name": template_doc.template_name,
			"content_sid": template_doc.content_sid,
			"content_variables": content_vars,
			"message": template_doc.message
		}
	
	except Exception as e:
		return {"success": False, "message": str(e)}

@frappe.whitelist()
def check_session_window(phone_number):
	"""Check if phone number is within 24-hour session window"""
	from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage
	
	if not phone_number:
		return {"in_session": False, "message": "Phone number is required"}
	
	# Ensure proper WhatsApp format
	if not phone_number.startswith('whatsapp:'):
		phone_number = f'whatsapp:{phone_number}'
	
	in_session = WhatsAppMessage.is_in_session_window(phone_number)
	
	return {
		"in_session": in_session,
		"phone_number": phone_number,
		"message": "Within 24-hour window" if in_session else "Outside 24-hour window - template required"
	}