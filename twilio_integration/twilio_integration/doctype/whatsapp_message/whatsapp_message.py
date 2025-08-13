# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from six import string_types
import json
import re
from frappe.utils.password import get_decrypted_password
from frappe.utils import get_site_url, now_datetime, get_datetime
from frappe import _
from ...twilio_handler import Twilio

class WhatsAppMessage(Document):
	def send(self):
		client = Twilio.get_twilio_client()
		message_dict = self.get_message_dict()
		response = frappe._dict()

		try:
			response = client.messages.create(**message_dict)
			self.sent_received = 'Sent'
			self.status = response.status.title()
			self.id = response.sid
			self.send_on = response.date_sent
			self.save(ignore_permissions=True)
		
		except Exception as e:
			self.db_set('status', "Error")
			error_msg = str(e)
			
			# Handle specific WhatsApp template errors
			if "63016" in error_msg or "freeform message" in error_msg.lower():
				error_msg = "Failed to send freeform message outside 24-hour window. Please use WhatsApp Template mode."
				
			frappe.log_error(title=_('Twilio WhatsApp Message Error'), message=error_msg)
			frappe.msgprint(_("WhatsApp Message Error: {0}").format(error_msg), indicator="red")
	
	def get_message_dict(self):
		"""Build message parameters for Twilio API based on template mode"""
		# Get the correct base URL for current environment
		site_url = get_site_url(frappe.local.site)
		
		# Handle different environments
		if 'localhost' in site_url or '127.0.0.1' in site_url:
			# Local development - use localhost with port
			base_url = 'http://localhost:8002'
		elif site_url.startswith('http://'):
			# Already has http protocol
			base_url = site_url
		elif site_url.startswith('https://'):
			# Already has https protocol  
			base_url = site_url
		else:
			# Add https for production/cloud deployments
			base_url = f'https://{site_url}'
			
		args = {
			'from_': self.from_,
			'to': self.to,
			'status_callback': f'{base_url}/api/method/twilio_integration.twilio_integration.api.whatsapp_message_status_callback'
		}
		
		if self.template_mode and self.content_sid:
			# Template mode - use Twilio's WhatsApp template parameters
			# Note: content_sid might not be the correct parameter name for Twilio API
			# Let's use the body with template syntax for now
			args['body'] = self.message
			
			# Alternative approach: Use template name if available
			if hasattr(self, 'whatsapp_template') and self.whatsapp_template:
				# For now, send the rendered message as body
				# This works for approved templates in session window
				pass
		else:
			# Session mode - use body parameter
			args['body'] = self.message
			
		if self.media_link:
			args['media_url'] = [self.media_link]

		return args

	@classmethod
	def send_whatsapp_message(cls, receiver_list, message, doctype, docname, media=None, template_info=None):
		"""Send WhatsApp message with template support"""
		if isinstance(receiver_list, string_types):
			from json import loads
			receiver_list = loads(receiver_list)
			if not isinstance(receiver_list, list):
				receiver_list = [receiver_list]

		for rec in receiver_list:
			wa_message = cls.store_whatsapp_message(rec, message, doctype, docname, media, template_info)
			wa_message.send()

	@staticmethod
	def store_whatsapp_message(to, message, doctype=None, docname=None, media=None, template_info=None):
		"""Store WhatsApp message with template support"""
		sender = frappe.db.get_single_value('Twilio Settings', 'whatsapp_no')
		
		message_doc = {
			'doctype': 'WhatsApp Message',
			'type': 'Outgoing',
			'from_': 'whatsapp:{}'.format(sender),
			'to': 'whatsapp:{}'.format(to),
			'message': message,
			'reference_doctype': doctype,
			'reference_document_name': docname,
			'reference_name': docname,  # CRM app expects this field
			'media_link': media,
			'content_type': 'text',
			'message_type': 'Text'
		}
		
		# Add template information if provided
		if template_info:
			message_doc.update({
				'template_mode': 1,
				'whatsapp_template': template_info.get('template_name'),
				'content_sid': template_info.get('content_sid'),
				'content_variables': template_info.get('content_variables')
			})
		
		wa_msg = frappe.get_doc(message_doc).insert(ignore_permissions=True)
		return wa_msg

	@staticmethod
	def is_in_session_window(to_number):
		"""Check if recipient is within 24-hour session window"""
		# Get last received message from this number
		last_received = frappe.db.sql("""
			SELECT send_on FROM `tabWhatsApp Message`
			WHERE from_ = %s AND sent_received = 'Received'
			ORDER BY send_on DESC LIMIT 1
		""", (to_number,), as_dict=True)
		
		if not last_received:
			return False
			
		# Check if within 24 hours
		last_message_time = get_datetime(last_received[0].send_on)
		current_time = now_datetime()
		time_diff = current_time - last_message_time
		
		# Return True if within 24 hours (86400 seconds)
		return time_diff.total_seconds() <= 86400
	
	@staticmethod
	def extract_variables_from_message(message_text):
		"""Extract variables from message with {{variable_name}} format"""
		if not message_text:
			return {}
			
		# Find all {{variable}} patterns
		variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
		variables = re.findall(variable_pattern, message_text)
		
		return {var.strip(): f"[{var.strip()}]" for var in variables}

def incoming_message_callback(args):
	wa_msg = frappe.get_doc({
			'doctype': 'WhatsApp Message',
			'type': 'Incoming',
			'from_': args.From,
			'to': args.To,
			'message': args.Body,
			'profile_name': args.ProfileName,
			'sent_received': args.SmsStatus.title(),
			'id': args.MessageSid,
			'send_on': frappe.utils.now(),
			'status': 'Received',
			'content_type': 'text',
			'message_type': 'Text',
			'message_id': args.MessageSid
		}).insert(ignore_permissions=True)