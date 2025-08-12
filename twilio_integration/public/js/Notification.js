frappe.ui.form.on('Notification', {
	onload: function(frm) {
		frm.set_query('twilio_number', function() {
			return {
				filters: {
					communication_channel: "Twilio",
					communication_medium_type: "WhatsApp"
				}
			};
		});
		
		frm.set_query('whatsapp_template', function() {
			return {
				filters: {
					template_status: "Approved"
				}
			};
		});
	},

	refresh: function(frm) {
		frm.events.setup_whatsapp_template(frm);
		frm.events.setup_template_mode_warnings(frm);
	},

	channel: function(frm) {
		frm.events.setup_whatsapp_template(frm);
		frm.events.setup_template_mode_warnings(frm);
	},

	use_whatsapp_template: function(frm) {
		frm.events.setup_template_mode_warnings(frm);
		
		if (frm.doc.use_whatsapp_template) {
			frappe.msgprint({
				title: __('Template Mode Enabled'),
				message: __('You are now using WhatsApp Business Template mode. This allows sending messages outside the 24-hour window but requires pre-approved templates.'),
				indicator: 'blue'
			});
		}
	},

	whatsapp_template: function(frm) {
		if (frm.doc.whatsapp_template) {
			frappe.db.get_doc('WhatsApp Message Template', frm.doc.whatsapp_template)
				.then(template_doc => {
					let message_help = `<div class="alert alert-info">
						<strong>Template Variables:</strong><br>
						Template Message: ${template_doc.message}<br><br>
						<strong>Available Variables:</strong><ul>`;
					
					if (template_doc.template_variables) {
						template_doc.template_variables.forEach(variable => {
							message_help += `<li>{{${variable.variable_position}}} - ${variable.variable_name} (${variable.variable_type})</li>`;
						});
					}
					
					message_help += `</ul>
						<strong>Note:</strong> Your notification message should contain variables that match these template positions.
					</div>`;
					
					frm.set_df_property('message', 'description', message_help);
				});
		}
	},

	setup_whatsapp_template: function(frm) {
		let template = '';
		if (frm.doc.channel === 'WhatsApp') {
			template = `<div class="alert alert-warning">
				<h5 style='display: inline-block'>WhatsApp Business API Requirements (2025):</h5>
				<ul>
					<li>Messages outside 24-hour window require pre-approved templates</li>
					<li>Templates must use Content SID and Content Variables</li>
					<li>Freeform messages only work within active conversation window</li>
				</ul>
			</div>
			
			<h5>Template Mode Example</h5>
			<pre>Your appointment is scheduled for {{1}} at {{2}}</pre>
			
			<h5>Session Mode Example</h5>
			<pre>Your appointment is coming up on {{ doc.date }} at {{ doc.time }}</pre>`;
		}
		if (template) {
			frm.set_df_property('message_examples', 'options', template);
		}
	},

	setup_template_mode_warnings: function(frm) {
		if (frm.doc.channel === 'WhatsApp' && !frm.doc.use_whatsapp_template) {
			frm.dashboard.add_comment(
				__('Warning: Freeform messages only work within 24-hour conversation window. Enable template mode for messages outside this window.'),
				'orange', true
			);
		} else {
			frm.dashboard.clear_comment();
		}
	}
});