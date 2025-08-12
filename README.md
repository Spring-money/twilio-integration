# Twilio Integration App

A comprehensive Frappe/ERPNext application for integrating Twilio services including Voice Calls and WhatsApp Business messaging with 2025 API compliance.

## Features

### 📞 Voice Calls
- **Browser-based Calling**: Make calls directly from ERPNext interface
- **Incoming Call Handling**: Automatic call routing and logging
- **Call Recording**: Optional call recording with webhook support
- **Call Logs**: Complete call history and management

### 💬 WhatsApp Business Messaging
- **Template Support**: Full support for WhatsApp Business templates (2025 compliant)
- **Session Messaging**: Freeform messages within 24-hour conversation windows
- **Notification Integration**: Send WhatsApp messages via ERPNext notifications
- **Status Tracking**: Real-time delivery status updates
- **Error Handling**: Comprehensive error handling with specific guidance

## WhatsApp Business API 2025 Compliance

This app is fully updated for the **April 1, 2025** WhatsApp Business API changes:

- ✅ **Template Messages**: Support for contentSid and contentVariables
- ✅ **Session Window Detection**: Automatic 24-hour window checking  
- ✅ **Error 63016 Handling**: Specific guidance for freeform message failures
- ✅ **Enhanced Notifications**: Template mode integration with Frappe notifications

## Installation

```bash
# Get the app
cd frappe-bench
bench get-app https://github.com/frappe/twilio-integration.git

# Install on site
bench --site sitename install-app twilio_integration

# Migrate
bench --site sitename migrate
```

## Quick Setup

### 1. Configure Twilio Settings
- Go to **Twilio Settings**
- Add your Account SID and Auth Token
- Set your WhatsApp Business number
- Enable the integration

### 2. Setup WhatsApp Templates (Recommended)
- Create templates in **WhatsApp Message Template**
- Get Content SID from Twilio Console
- Set template status to "Approved"

### 3. Configure Notifications
- Go to **Notification** DocType
- Set Channel to "WhatsApp"
- Enable "Use WhatsApp Template" for reliable delivery
- Select your approved template

## Documentation

- 📖 **[Complete Setup Guide](WHATSAPP_SETUP.md)** - Detailed configuration instructions
- 🔧 **[API Reference](WHATSAPP_SETUP.md#api-reference)** - Available API methods
- 🐛 **[Troubleshooting](WHATSAPP_SETUP.md#troubleshooting)** - Common issues and solutions

## Original Features (Still Supported)

### Voice Call Setup
Every user(Agent) needs to have voice call settings to make or receive calls:

1. Choose the `Call Receiving Device` as `Computer` to receive calls in the browser or `Phone` to receive calls in your phone
2. Choose your twilio number from `Twilio Number` dropdown field

### Outgoing Calls
Click the phone icon next to phone numbers to make outgoing calls. Ensure area code is included (ex: +91).

### Incoming Calls
Calls are redirected to phone or browser depending on user voice call settings.

## DocTypes

### Core DocTypes
- **Twilio Settings**: Main configuration
- **WhatsApp Message**: Message records and status tracking
- **WhatsApp Message Template**: Template management with variable support
- **WhatsApp Template Variable**: Template variable definitions

### Campaign Management
- **WhatsApp Campaign**: Bulk messaging campaigns
- **WhatsApp Campaign Recipient**: Campaign recipient management

## API Methods

### WhatsApp Template Testing
```python
frappe.call(
    'twilio_integration.twilio_integration.api.test_whatsapp_template',
    template_name='your_template',
    test_variables='{"1": "test value"}'
)
```

### Session Window Checking
```python
frappe.call(
    'twilio_integration.twilio_integration.api.check_session_window',
    phone_number='+1234567890'
)
```

## Error Handling

The app provides comprehensive error handling for common WhatsApp issues:

- **Error 63016**: Automatic detection with template mode suggestions
- **Template Errors**: Validation and helpful error messages
- **Session Window**: Proactive warnings for recipients outside 24-hour window
- **Status Webhooks**: Real-time delivery status updates

## Development

### Pre-requisites
- [ERPNext](https://docs.erpnext.com/docs/user/manual/en/introduction/getting-started-with-erpnext)
- Twilio account with WhatsApp Business API access

### Configure Twilio
1. Create a [new project](https://www.twilio.com/console/projects/create) in your Twilio account
2. For voice calls: Get a voice-capable Twilio number and create a TwiML App
3. For WhatsApp: Get WhatsApp Business API access and approved templates

### Running Tests
```bash
bench --site sitename run-tests --app twilio_integration
```

### Building Assets
```bash
bench build --app twilio_integration
```

## Changelog

### Version 2.0 (January 2025)
- ✅ WhatsApp Business API 2025 compliance
- ✅ Template support with Content SID
- ✅ Enhanced error handling for error 63016
- ✅ Session window detection
- ✅ Improved notification integration
- ✅ Comprehensive documentation

### Version 1.0 (Original)
- ✅ Basic WhatsApp messaging
- ✅ Voice call integration
- ✅ Call logging and recording

## License

MIT

## Support

- 📚 Documentation: See [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)
- 🐛 Issues: Report bugs via GitHub issues
- 💬 Community: Frappe Community Forums

---

**Note**: This app requires a Twilio account with WhatsApp Business API access. WhatsApp Business templates must be approved by WhatsApp before use in production.