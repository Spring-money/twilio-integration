# WhatsApp Business API Setup and Configuration Guide

## Overview

This guide covers the setup and configuration of WhatsApp Business messaging using Twilio's API with template support for 2025 compliance requirements.

## Table of Contents

1. [WhatsApp Business API Changes (2025)](#whatsapp-business-api-changes-2025)
2. [Initial Setup](#initial-setup)
3. [Template Configuration](#template-configuration)
4. [Notification Setup](#notification-setup)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## WhatsApp Business API Changes (2025)

### Important Changes Effective April 1, 2025

- **Template Requirement**: Messages sent outside the 24-hour conversation window **must** use pre-approved WhatsApp Business templates
- **Content SID Required**: Templates must be sent using `contentSid` and `contentVariables` parameters
- **No More Body Parameter**: The `body` parameter is deprecated for template messages outside conversation windows
- **Error 63016**: Freeform messages outside the 24-hour window will fail with error code 63016

### Message Types

1. **Session Messages**: Messages within 24-hour window from customer's last message - can be freeform
2. **Template Messages**: Messages outside 24-hour window - must use approved templates

## Initial Setup

### 1. Twilio Settings Configuration

Navigate to **Twilio Settings** and configure:

```
Account SID: Your Twilio Account SID
Auth Token: Your Twilio Auth Token (encrypted)
Enabled: ✓ Check this box
WhatsApp Number: Your Twilio WhatsApp Business number (e.g., +14155238886)
Reply Message: Auto-reply message for incoming messages
```

### 2. Webhook Configuration

Configure these webhooks in your Twilio Console:

- **Incoming Messages**: `https://yoursite.com/api/method/twilio_integration.twilio_integration.api.incoming_whatsapp_message_handler`
- **Status Callbacks**: `https://yoursite.com/api/method/twilio_integration.twilio_integration.api.whatsapp_message_status_callback`

## Template Configuration

### 1. Create WhatsApp Message Template

1. Go to **WhatsApp Message Template** DocType
2. Click **New**
3. Configure the template:

```
Template Name: appointment_reminder
Content SID: HX1234567890abcdef1234567890abcdef  (from Twilio Console)
Template Status: Approved
Language Code: en
Template Message: Your appointment is scheduled for {{1}} at {{2}}. Please confirm by replying YES.
```

### 2. Template Variables

The system automatically extracts variables from your template message:
- `{{1}}` becomes Variable 1 (position 1)
- `{{2}}` becomes Variable 2 (position 2)
- etc.

Variables support these types:
- **TEXT**: Plain text values
- **NUMBER**: Numeric values
- **DATE**: Date values
- **CURRENCY**: Currency amounts

### 3. Getting Content SID from Twilio

1. Log into [Twilio Console](https://console.twilio.com)
2. Go to **Messaging** → **Content** → **Content Builder**
3. Find your approved WhatsApp template
4. Copy the **Content SID** (starts with 'HX')

## Notification Setup

### 1. Create Notification

1. Go to **Notification** DocType
2. Create new notification with these settings:

```
Document Type: [Your DocType]
Channel: WhatsApp
Twilio Number: [Select your configured number]
```

### 2. Template Mode (Recommended)

For messages that may be sent outside 24-hour window:

```
✓ Use WhatsApp Template: Enabled
WhatsApp Template: [Select approved template]
```

Message format for template mode:
```
Your appointment for {{doc.subject}} is scheduled for {{doc.date}} at {{doc.time}}.
```

### 3. Session Mode (Legacy)

For messages within 24-hour conversation window only:

```
☐ Use WhatsApp Template: Disabled
```

Message format for session mode:
```
Your appointment for {{ doc.subject }} is scheduled for {{ doc.date }} at {{ doc.time }}.
```

## Testing

### 1. Test Template

Use the API to test your template:

```python
# In console
import frappe
result = frappe.call(
    'twilio_integration.twilio_integration.api.test_whatsapp_template',
    template_name='appointment_reminder',
    test_variables='{"Variable 1": "Tomorrow", "Variable 2": "2:00 PM"}'
)
print(result)
```

### 2. Check Session Window

```python
# Check if phone number is within 24-hour window
result = frappe.call(
    'twilio_integration.twilio_integration.api.check_session_window',
    phone_number='+1234567890'
)
print(result)
```

### 3. Send Test Message

1. Create a test document
2. Trigger the notification
3. Check **WhatsApp Message** DocType for delivery status

## Troubleshooting

### Common Errors

#### Error 63016: "Failed to send freeform message because you are outside the allowed window"

**Solution**: Enable template mode in your notification:
1. Check "Use WhatsApp Template"
2. Select an approved template
3. Ensure template has valid Content SID

#### "Template is not approved"

**Solution**: 
1. Submit template to WhatsApp for approval through Twilio Console
2. Update template status to "Approved" once approved
3. Add Content SID from Twilio

#### "Content SID is required for approved templates"

**Solution**: 
1. Go to Twilio Console → Content Builder
2. Find your approved template
3. Copy Content SID to template configuration

#### Variables not replacing correctly

**Solution**: 
1. Ensure template message uses `{{1}}`, `{{2}}` format
2. Check variable mapping in template configuration
3. Verify notification message provides values for all variables

### Debug Tips

1. **Check Error Log**: Go to Error Log DocType for detailed error messages
2. **Monitor WhatsApp Messages**: Check delivery status in WhatsApp Message DocType
3. **Webhook Logs**: Enable webhook logging in Twilio Console
4. **Template Testing**: Use the test API functions before sending to customers

## API Reference

### Template Testing
```
GET/POST /api/method/twilio_integration.twilio_integration.api.test_whatsapp_template
Parameters:
- template_name: Name of template to test
- test_variables: JSON object with variable values
```

### Session Window Check
```
GET/POST /api/method/twilio_integration.twilio_integration.api.check_session_window
Parameters:
- phone_number: Phone number to check (with or without whatsapp: prefix)
```

### Get Approved Templates
```
GET/POST /api/method/twilio_integration.twilio_integration.api.get_approved_whatsapp_templates
Returns: List of approved templates
```

## Best Practices

1. **Always Use Templates** for notifications that may be sent outside business hours
2. **Test Templates** thoroughly before production use
3. **Monitor Delivery Status** through webhooks and status callbacks
4. **Keep Variables Simple** - avoid complex formatting in template variables
5. **Handle Errors Gracefully** - implement fallback mechanisms for failed template messages
6. **Stay Updated** on WhatsApp Business API policy changes

## Support

For issues or questions:
1. Check Twilio's WhatsApp documentation
2. Review error logs in the system
3. Test with Twilio's WhatsApp Sandbox first
4. Contact your Twilio support representative for template approval issues

---

Last Updated: January 12, 2025
Version: 2.0 (WhatsApp Business API 2025 Compliance)