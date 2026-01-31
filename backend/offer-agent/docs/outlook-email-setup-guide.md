# Outlook Email Integration Setup Guide

This guide walks through setting up Outlook/Office 365 email integration for the Automated Offer Creation System. The system needs to handle both incoming customer requests and outgoing offer notifications.

## Overview

The email integration consists of two main components:
1. **Incoming Email Processing**: Monitor a designated email address for customer requests
2. **Outgoing Email Notifications**: Send offer confirmations and notifications to sales team

## Prerequisites

- Office 365 business account or Outlook.com account
- Administrative access to configure email settings
- Access to Azure AD (for enterprise setups)

## Step 1: Create Dedicated Email Account

### 1.1 Set up the email account
Create a dedicated email address for the automation system:
- **Recommended**: `ai.tarjoukset@lvi-wabek.fi` (or similar)
- This account will receive customer requests and send automated responses

### 1.2 Configure mailbox permissions
If using Office 365 business:
1. Go to Microsoft 365 admin center
2. Navigate to **Users > Active users**
3. Find your automation email account
4. Ensure it has the necessary licenses and permissions

## Step 2: Configure Office 365 Business Authentication

### 2.0 Determine Which Method to Use

**Quick Test**: Try this command to check your O365 configuration:
```bash
# Test basic authentication
telnet smtp.office365.com 587
# If this connects, basic auth might be available
```

**Check with your IT admin**:
- Is basic authentication enabled for SMTP?
- Are app passwords supported?
- Do you have Azure AD admin permissions?

### 2.1 Option A: Modern Authentication with OAuth2 (Recommended)

For Office 365 business accounts, the recommended approach is to use OAuth2 with Microsoft Graph API:

1. **Register an App in Azure AD**:
   ```
   1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps
   2. Click "New registration"
   3. Name: "Offer Automation System"
   4. Supported account types: "Accounts in this organizational directory only"
   5. Redirect URI: https://localhost:8080/auth/callback (or your app URL)
   6. Click "Register"
   ```

2. **Configure API Permissions**:
   ```
   In your app registration:
   → API permissions → Add a permission → Microsoft Graph → Application permissions
   → Add these permissions:
     - Mail.Read (to read emails)
     - Mail.Send (to send emails)
     - User.Read.All (to read user info)
   → Grant admin consent for your organization
   ```

3. **Create Client Secret**:
   ```
   → Certificates & secrets → New client secret
   → Description: "Offer Automation"
   → Expires: 24 months (recommended)
   → Copy the secret value (you won't see it again!)
   ```

### 2.2 Option B: Basic Authentication (Fallback)

If your organization still allows basic authentication:

1. **Check if Basic Auth is enabled**:
   ```
   Microsoft 365 admin center → Settings → Org settings → Modern authentication
   Ensure "Enable modern authentication for Outlook" is ON
   BUT also check if "Allow basic authentication" is enabled for SMTP
   ```

2. **Use regular credentials** (if basic auth is allowed):
   ```
   Username: your-email@company.com
   Password: your-regular-password (not app password for O365 business)
   ```

### 2.3 Option C: App Passwords (Legacy/Hybrid)

Some O365 configurations may still support app passwords:

1. **Enable Security Defaults** (if not already):
   ```
   Azure AD → Properties → Manage Security defaults → Enable
   ```

2. **Generate App Password**:
   ```
   Go to: https://mysignins.microsoft.com/security-info
   → Add method → App password
   → Name: "Offer Automation System"
   → Copy the generated password
   ```

## Step 3: Configure SMTP Settings

### 3.1 SMTP Configuration for Office 365 Business

**Option A: OAuth2 SMTP (Recommended)**
```env
# OAuth2 SMTP Configuration
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_AUTH_METHOD=oauth2
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_CLIENT_ID=your-app-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
EMAIL_USERNAME=ai.tarjoukset@lvi-wabek.fi
```

**Option B: Basic Authentication SMTP (if enabled)**
```env
# Basic Auth SMTP Configuration
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_AUTH_METHOD=basic
SMTP_USERNAME=ai.tarjoukset@lvi-wabek.fi
SMTP_PASSWORD=your_regular_password  # Your O365 password
```

**Option C: App Password SMTP (legacy)**
```env
# App Password SMTP Configuration
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_AUTH_METHOD=basic
SMTP_USERNAME=ai.tarjoukset@lvi-wabek.fi
SMTP_PASSWORD=your_16_character_app_password
```

### 3.2 Alternative SMTP Settings

Some organizations may use different settings:
```env
# Alternative configurations
SMTP_HOST=smtp-mail.outlook.com  # Sometimes used for hybrid setups
SMTP_PORT=25    # Internal SMTP relay (if configured)
SMTP_PORT=465   # SSL (less common for O365)
```

## Step 4: Configure Environment Variables

### 4.1 Update .env file

Create or update your `.env` file with the following email settings:

```env
# =================================
# EMAIL CONFIGURATION - OFFICE 365 BUSINESS
# =================================

# Choose ONE of the following authentication methods:

# METHOD 1: OAuth2 (Recommended for O365 Business)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_AUTH_METHOD=oauth2
MICROSOFT_TENANT_ID=your-tenant-id-here
MICROSOFT_CLIENT_ID=your-app-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
EMAIL_USERNAME=ai.tarjoukset@lvi-wabek.fi

# METHOD 2: Basic Authentication (if enabled by admin)
# SMTP_HOST=smtp.office365.com
# SMTP_PORT=587
# SMTP_USE_TLS=true
# SMTP_AUTH_METHOD=basic
# SMTP_USERNAME=ai.tarjoukset@lvi-wabek.fi
# SMTP_PASSWORD=your_regular_o365_password

# METHOD 3: App Password (legacy, uncomment if using)
# SMTP_HOST=smtp.office365.com
# SMTP_PORT=587
# SMTP_USE_TLS=true
# SMTP_AUTH_METHOD=basic
# SMTP_USERNAME=ai.tarjoukset@lvi-wabek.fi
# SMTP_PASSWORD=your_16_character_app_password

# Email Addresses
EMAIL_FROM_ADDRESS=ai.tarjoukset@lvi-wabek.fi
EMAIL_FROM_NAME=Offer Automation System
EMAIL_REPLY_TO=ai.tarjoukset@lvi-wabek.fi

# Microsoft Graph API Settings (for incoming email monitoring)
MICROSOFT_GRAPH_API_VERSION=v1.0
MICROSOFT_SCOPES=https://graph.microsoft.com/Mail.Read,https://graph.microsoft.com/Mail.Send

# Alternative: Gmail forwarding (if forwarding O365 to Gmail)
# GMAIL_CREDENTIALS_FILE=path/to/gmail-credentials.json
# GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify

# Email Processing Settings
EMAIL_CHECK_INTERVAL=60  # seconds
EMAIL_MAX_ATTACHMENT_SIZE=10485760  # 10MB
EMAIL_ALLOWED_SENDERS=@lvi-wabek.fi,@metec.fi  # comma-separated domains

# Notification Settings
NOTIFICATION_RECIPIENTS=sales@lvi-wabek.fi,manager@lvi-wabek.fi
ERROR_NOTIFICATION_RECIPIENTS=admin@lvi-wabek.fi
```

### 4.2 Required Settings Explained

| Setting | Description | Example |
|---------|-------------|---------|
| `SMTP_HOST` | Outlook SMTP server | `smtp-mail.outlook.com` |
| `SMTP_PORT` | SMTP port (587 for TLS) | `587` |
| `SMTP_USE_TLS` | Enable TLS encryption | `true` |
| `SMTP_USERNAME` | Email account username | `ai.tarjoukset@lvi-wabek.fi` |
| `SMTP_PASSWORD` | App password (not regular password) | `abcd efgh ijkl mnop` |
| `EMAIL_FROM_ADDRESS` | Sender email address | `ai.tarjoukset@lvi-wabek.fi` |
| `EMAIL_FROM_NAME` | Sender display name | `Offer Automation System` |

## Step 5: Set up Gmail API (for Incoming Email)

Since Outlook doesn't have push notifications like Gmail, we'll use Gmail API with forwarding.

### 5.1 Option A: Forward Outlook to Gmail

1. **Set up email forwarding**:
   ```
   Outlook → Settings → Mail → Forwarding
   → Enable forwarding to a Gmail account
   → Keep a copy in Outlook inbox
   ```

2. **Configure Gmail API** (follow existing Gmail setup documentation)

### 5.2 Option B: Use Microsoft Graph API (Advanced)

For enterprise setups, use Microsoft Graph API:

```env
# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID=your_app_client_id
MICROSOFT_CLIENT_SECRET=your_app_client_secret
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_REDIRECT_URI=https://your-app.com/auth/callback
```

## Step 5.5: Quick Setup for Most O365 Business Users

### 5.5.1 Try This First (Simplest Method)

Most O365 business accounts can use basic authentication if enabled by the admin:

1. **Create a simple .env file**:
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_AUTH_METHOD=basic
SMTP_USERNAME=ai.tarjoukset@lvi-wabek.fi
SMTP_PASSWORD=your_regular_o365_password
EMAIL_FROM_ADDRESS=ai.tarjoukset@lvi-wabek.fi
EMAIL_FROM_NAME=Offer Automation System
```

2. **Run the test script**:
```bash
python test_email_config.py
```

3. **If it fails with authentication error**:
   - Your admin has disabled basic auth → Use OAuth2 method
   - Try generating an app password → Use app password method
   - Contact your IT admin for guidance

### 5.5.2 Common Error Solutions

**Error**: "Authentication failed"
```
Solution 1: Ask IT admin to enable basic auth for SMTP
Solution 2: Use OAuth2 method (requires app registration)
Solution 3: Enable app passwords (if supported)
```

**Error**: "Connection refused"
```
Solution: Check firewall settings for port 587
Alternative: Try port 25 (if internal relay is configured)
```

## Step 6: Test Email Configuration

### 6.1 Create Test Script

Create a test script to verify email settings:

```python
# test_email_config.py
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

async def test_smtp_connection():
    """Test SMTP connection and send test email."""
    
    # Load settings from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp-mail.outlook.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        print("❌ Missing SMTP_USERNAME or SMTP_PASSWORD in environment")
        return False
    
    try:
        print(f"🔗 Connecting to {smtp_host}:{smtp_port}")
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()  # Enable TLS
        
        print("🔐 Authenticating...")
        server.login(smtp_username, smtp_password)
        
        print("✅ SMTP connection successful!")
        
        # Send test email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = smtp_username  # Send to self
        msg['Subject'] = "Test: Offer Automation Email Setup"
        
        body = """
        This is a test email from the Offer Automation System.
        
        If you receive this email, your SMTP configuration is working correctly!
        
        Next steps:
        1. Verify incoming email monitoring
        2. Test end-to-end offer creation
        3. Configure error notifications
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        print("📧 Sending test email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {smtp_username}")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_smtp_connection())
```

### 6.2 Run Email Test

```bash
# Load environment variables
source .env  # Linux/Mac
# OR
# Load .env in Windows PowerShell

# Run test
python test_email_config.py
```

Expected output:
```
🔗 Connecting to smtp-mail.outlook.com:587
🔐 Authenticating...
✅ SMTP connection successful!
📧 Sending test email...
✅ Test email sent successfully!
📬 Check your inbox: ai.tarjoukset@lvi-wabek.fi
```

## Step 7: Configure Email Templates

### 7.1 Create Email Templates Directory

```bash
mkdir -p templates/email
```

### 7.2 Offer Notification Template

Create `templates/email/offer_created.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Automated Offer Created</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #0066cc; color: white; padding: 15px; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .offer-details { background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #0066cc; }
        .footer { padding: 15px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🤖 Automated Offer Created</h2>
    </div>
    
    <div class="content">
        <p>A new offer has been automatically created from a customer request.</p>
        
        <div class="offer-details">
            <h3>Offer Details</h3>
            <ul>
                <li><strong>Offer Number:</strong> {{ offer_number }}</li>
                <li><strong>Customer:</strong> {{ customer_name }}</li>
                <li><strong>Total Amount:</strong> €{{ total_amount }}</li>
                <li><strong>Line Items:</strong> {{ line_count }}</li>
                <li><strong>Created:</strong> {{ created_at }}</li>
            </ul>
        </div>
        
        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Review the offer in Lemonsoft</li>
            <li>Download PDF: <a href="{{ pdf_url }}">Offer PDF</a></li>
            <li>Contact customer if needed</li>
        </ul>
    </div>
    
    <div class="footer">
        <p>This is an automated message from the Offer Automation System.</p>
        <p>Please do not reply to this email.</p>
    </div>
</body>
</html>
```

## Step 8: Troubleshooting Common Issues

### 8.1 Authentication Errors

**Error**: "Username and Password not accepted"
```
Solutions:
1. Verify app password is correct (not regular password)
2. Check if 2FA is enabled on the account
3. Ensure "Less secure app access" is enabled
4. Try generating a new app password
```

**Error**: "SMTP connection timeout"
```
Solutions:
1. Check firewall settings
2. Verify SMTP host and port
3. Ensure TLS is enabled
4. Test from different network
```

### 8.2 Email Delivery Issues

**Problem**: Emails go to spam
```
Solutions:
1. Add SPF record to DNS: "v=spf1 include:spf.protection.outlook.com ~all"
2. Configure DKIM in Office 365
3. Add sender to recipient's safe senders list
4. Use consistent from address
```

**Problem**: Large attachments rejected
```
Solutions:
1. Check EMAIL_MAX_ATTACHMENT_SIZE setting
2. Outlook limit is typically 25MB
3. Use file sharing links for large files
4. Compress attachments when possible
```

### 8.3 API Rate Limiting

**Problem**: Too many API calls
```
Solutions:
1. Implement exponential backoff
2. Cache email data locally
3. Use batch operations where possible
4. Monitor API usage quotas
```

## Step 9: Security Best Practices

### 9.1 Credential Security

1. **Never commit credentials to version control**
2. **Use environment variables only**
3. **Rotate app passwords regularly** (every 90 days)
4. **Monitor failed login attempts**
5. **Use dedicated service account** (not personal email)

### 9.2 Email Security

1. **Validate sender domains** before processing
2. **Scan attachments** for malware
3. **Limit attachment types** (Excel, PDF only)
4. **Log all email activities** for audit
5. **Encrypt sensitive data** in emails

### 9.3 Access Control

```env
# Restrict allowed senders
EMAIL_ALLOWED_SENDERS=@lvi-wabek.fi,@metec.fi,@approved-domain.com

# Monitor specific folders only
EMAIL_FOLDERS=INBOX,Offers

# Set processing limits
EMAIL_MAX_EMAILS_PER_HOUR=50
EMAIL_MAX_ATTACHMENT_SIZE=10485760
```

## Step 10: Monitoring and Maintenance

### 10.1 Email Health Checks

Create automated health checks:

```python
async def email_health_check():
    """Check email system health."""
    checks = {
        'smtp_connection': await test_smtp_connection(),
        'inbox_access': await test_inbox_access(),
        'template_loading': test_template_loading(),
        'credential_validity': test_credentials()
    }
    
    return all(checks.values()), checks
```

### 10.2 Log Monitoring

Monitor these log patterns:
- Email processing failures
- Authentication errors
- High email volumes
- Attachment processing errors
- Template rendering issues

### 10.3 Regular Maintenance

- **Weekly**: Check email processing logs
- **Monthly**: Verify email templates
- **Quarterly**: Rotate app passwords
- **Annually**: Review email security settings

## Step 11: Integration Testing

### 11.1 End-to-End Test

1. **Send test customer request** to automation email
2. **Verify email is processed** and parsed correctly
3. **Check offer creation** in Lemonsoft
4. **Confirm notification sent** to sales team
5. **Validate all attachments** downloaded and processed

### 11.2 Load Testing

Test email system under load:
- Multiple simultaneous emails
- Large attachments
- High email volume periods
- Error recovery scenarios

## Conclusion

Once configured, the email system will:

1. **Monitor** the designated inbox for customer requests
2. **Process** emails and attachments automatically
3. **Create** offers in Lemonsoft based on parsed content
4. **Send** notifications to sales team with offer details
5. **Handle** errors gracefully with proper logging

The system is designed to be robust, secure, and scalable for enterprise use.

---

**Next Steps:**
1. Complete email setup using this guide
2. Test email integration thoroughly
3. Configure email templates for your organization
4. Set up monitoring and alerting
5. Train sales team on the new automated process 