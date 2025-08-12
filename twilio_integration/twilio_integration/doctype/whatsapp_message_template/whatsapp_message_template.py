# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document
from frappe import _

class WhatsAppMessageTemplate(Document):
	def validate(self):
		self.validate_content_sid()
		self.extract_variables_from_message()
	
	def validate_content_sid(self):
		"""Validate that Content SID is provided for approved templates"""
		if self.template_status == "Approved" and not self.content_sid:
			frappe.throw(_("Content SID is required for approved templates"))
	
	def extract_variables_from_message(self):
		"""Extract variables from message template and update template_variables table"""
		if not self.message:
			return
		
		# Find all {{number}} patterns in message
		variable_pattern = r'\{\{(\d+)\}\}'
		variables = re.findall(variable_pattern, self.message)
		
		if variables:
			# Clear existing variables
			self.template_variables = []
			
			# Add found variables
			for var in sorted(set(variables), key=int):
				self.append('template_variables', {
					'variable_name': f'Variable {var}',
					'variable_position': int(var),
					'variable_type': 'TEXT'
				})
	
	def get_content_variables(self, variable_values):
		"""
		Convert variable values to Twilio ContentVariables format
		
		Args:
			variable_values: Dict with variable names as keys and values as values
			
		Returns:
			Dict formatted for Twilio ContentVariables parameter
		"""
		content_variables = {}
		
		for variable in self.template_variables:
			var_key = str(variable.variable_position)
			
			# Try to get value from variable_values dict
			if variable.variable_name in variable_values:
				content_variables[var_key] = variable_values[variable.variable_name]
			elif f'Variable {var_key}' in variable_values:
				content_variables[var_key] = variable_values[f'Variable {var_key}']
			elif variable.default_value:
				content_variables[var_key] = variable.default_value
			else:
				# Use placeholder if no value provided
				content_variables[var_key] = f"[{variable.variable_name}]"
		
		return content_variables
