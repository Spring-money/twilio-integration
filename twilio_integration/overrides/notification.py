import frappe
import re
from frappe import _
from frappe.email.doctype.notification.notification import Notification, get_context, json
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage

class SendNotification(Notification):
	def validate(self):
		self.validate_twilio_settings()

	def validate_twilio_settings(self):
		if self.enabled and self.channel == "WhatsApp" \
			and not frappe.db.get_single_value("Twilio Settings", "enabled"):
			frappe.throw(_("Please enable Twilio settings to send WhatsApp messages"))
		
		# Validate template settings
		if self.enabled and self.channel == "WhatsApp" and self.use_whatsapp_template:
			if not self.whatsapp_template:
				frappe.throw(_("Please select a WhatsApp template when template mode is enabled"))
			
			# Check if template is approved
			template_doc = frappe.get_doc("WhatsApp Message Template", self.whatsapp_template)
			if template_doc.template_status != "Approved":
				frappe.throw(_("Selected WhatsApp template must be approved before use"))

	def send(self, doc):
		context = get_context(doc)
		context = {"doc": doc, "alert": self, "comments": None}
		if doc.get("_comments"):
			context["comments"] = json.loads(doc.get("_comments"))

		if self.is_standard:
			self.load_standard_properties(context)

		try:
			if self.channel == 'WhatsApp':
				self.send_whatsapp_msg(doc, context)
		except:
			frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())

		super(SendNotification, self).send(doc)

	def send_whatsapp_msg(self, doc, context):
		receiver_list = self.get_receiver_list(doc, context)
		rendered_message = frappe.render_template(self.message, context)
		
		template_info = None
		
		if self.use_whatsapp_template and self.whatsapp_template:
			# Template mode - extract variables and prepare template info
			template_doc = frappe.get_doc("WhatsApp Message Template", self.whatsapp_template)
			
			if template_doc.content_sid:
				# Extract variables from rendered message
				variable_values = self.extract_template_variables(rendered_message, template_doc)
				
				template_info = {
					'template_name': self.whatsapp_template,
					'content_sid': template_doc.content_sid,
					'content_variables': template_doc.get_content_variables(variable_values)
				}
			else:
				frappe.throw(_("Template {0} does not have a Content SID").format(self.whatsapp_template))
		else:
			# Check if recipients are within session window for freeform messages
			for receiver in receiver_list:
				if not WhatsAppMessage.is_in_session_window(f"whatsapp:{receiver}"):
					frappe.msgprint(
						_("Recipient {0} is outside 24-hour window. Consider using WhatsApp Template mode.").format(receiver),
						indicator="orange"
					)

		WhatsAppMessage.send_whatsapp_message(
			receiver_list=receiver_list,
			message=rendered_message,
			doctype=self.doctype,
			docname=self.name,
			template_info=template_info
		)
	
	def extract_template_variables(self, rendered_message, template_doc):
		"""Extract variable values from rendered message for template"""
		variable_values = {}
		
		# Simple pattern matching approach
		# Look for names (capitalized words) and phone numbers
		words = re.findall(r'\b[A-Z][a-zA-Z\s]+\b', rendered_message)
		phone_numbers = re.findall(r'[\+]?[1-9]\d{1,14}', rendered_message)
		
		# Clean up words (remove common words, keep likely names)
		likely_names = []
		common_words = {'Hi', 'Thank', 'You', 'For', 'Choosing', 'SpringMoney', 'Your', 'Personal', 'Financial', 'Advisor', 'Account', 'Setup', 'Complete', 'Next', 'Steps', 'Document', 'Verification', 'Goal', 'Maximize', 'Growth', 'Need', 'Assistance', 'Reply', 'This', 'Message', 'Or', 'Call', 'Growing', 'Wealth', 'Securing', 'Future'}
		
		for word in words:
			cleaned_word = word.strip()
			if cleaned_word and cleaned_word not in common_words and len(cleaned_word) > 1:
				likely_names.append(cleaned_word)
		
		# Map to template variables
		# Based on your message: Hi {{1}}, I'm {{2}}, call {{3}}
		if likely_names:
			variable_values["Variable 1"] = likely_names[0]  # First name for greeting
			if len(likely_names) > 1:
				variable_values["Variable 2"] = likely_names[1]  # Second name for advisor
			else:
				variable_values["Variable 2"] = likely_names[0]  # Same name if only one
		
		if phone_numbers:
			variable_values["Variable 3"] = phone_numbers[0]  # Phone number
		
		# Fallback values if extraction fails
		if not variable_values.get("Variable 1"):
			variable_values["Variable 1"] = "Customer"
		if not variable_values.get("Variable 2"):
			variable_values["Variable 2"] = "Advisor"
		if not variable_values.get("Variable 3"):
			variable_values["Variable 3"] = "+1234567890"
			
		return variable_values