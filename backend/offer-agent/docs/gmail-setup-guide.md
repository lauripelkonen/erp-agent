# Gmail Setup Guide for Offer Automation System

This guide walks you through setting up Gmail for automated email sending and receiving in the LVI-Wabek Offer Automation System.

## Why Gmail?

✅ **Easy App Password Setup** - No complex PowerShell commands  
✅ **Reliable SMTP/IMAP** - Well-established email protocols  
✅ **Familiar Interface** - Most IT administrators know Gmail  
✅ **Good Documentation** - Clear setup instructions from Google  

## Prerequisites

- Gmail account: `ai.tarjous.wcom@gmail.com` (already created)
- Admin access to this Gmail account
- 2-Factor Authentication must be enabled

## Step 1: Enable 2-Factor Authentication

1. **Go to Google Account Settings**:
   - Visit: https://myaccount.google.com/
   - Sign in with `ai.tarjous.wcom@gmail.com`

2. **Enable 2-Step Verification**:
   - Click **"Security"** in the left panel
   - Under **"Signing in to Google"**, click **"2-Step Verification"**
   - Follow the setup wizard (use phone number or authenticator app)

## Step 2: Generate App Password

1. **Access App Passwords**:
   - Still in **"Security"** section
   - Scroll down to **"App passwords"** (only appears after 2FA is enabled)
   - Click **"App passwords"**

2. **Create New App Password**:
   - Select app: **"Mail"**
   - Select device: **"Other (custom name)"**
   - Enter name: **"LVI Wabek Offer Automation"**
   - Click **"Generate"**

3. **Save the Password**:
   - Google will show a 16-character password like: `abcd efgh ijkl mnop`
   - **IMPORTANT**: Copy this password immediately - you won't see it again!

## Step 3: Configure Environment

1. **Copy Configuration Template**:
   ```bash
   cp email_config_example.env .env
   ```

2. **Update .env File**:
   ```bash
   # Gmail Configuration
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=true
   SMTP_USERNAME=ai.tarjous.wcom@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop    # Your 16-character app password

   # IMAP for incoming emails
   IMAP_HOST=imap.gmail.com
   IMAP_PORT=993
   IMAP_USE_SSL=true

   # Email settings
   EMAIL_FROM_ADDRESS=ai.tarjous.wcom@gmail.com
   EMAIL_FROM_NAME=LVI-Wabek Offer Automation
   ```

## Step 4: Test Configuration

1. **Run Test Script**:
   ```bash
   python test_email_config.py
   ```

2. **Expected Output**:
   ```
   🧪 Testing Email Configuration
   ==================================================
   📧 SMTP Host: smtp.gmail.com
   🔌 SMTP Port: 587
   👤 Username: ai.tarjous.wcom@gmail.com
   🏷️  From Name: LVI-Wabek Offer Automation
   ==================================================
   🔗 Connecting to smtp.gmail.com:587...
   🔐 Starting TLS encryption...
   🔓 Authenticating...
   ✅ SMTP connection successful!
   📧 Sending test email...
   ✅ Test email sent successfully!
   📬 Check your inbox: ai.tarjous.wcom@gmail.com
   ```

3. **Check Gmail Inbox**:
   - Open Gmail for `ai.tarjous.wcom@gmail.com`
   - Look for test email with subject: "✅ Test: Offer Automation Email Setup"
   - If not in inbox, check spam folder

## Step 5: Configure Gmail Settings

### Allow Automation Access

1. **Enable IMAP** (for reading emails):
   - Gmail Settings → **"Forwarding and POP/IMAP"**
   - **"IMAP Access"** → Select **"Enable IMAP"**
   - Click **"Save Changes"**

2. **Configure Filters** (optional):
   - Create filter for offer emails: `from:(*@lvi-wabek.fi OR *@metec.fi)`
   - Actions: Never send to spam, apply label "Offers"

### Set Up Forwarding (Optional)

If you want copies sent to your regular email:
1. Gmail Settings → **"Forwarding and POP/IMAP"**
2. **"Add a forwarding address"** → Enter your regular email
3. Verify the forwarding address

## Step 6: Test Full Integration

1. **Send Test Offer Email**:
   ```bash
   python -c "
   from src.email.sender import EmailSender
   sender = EmailSender()
   sender.send_offer_created('test@example.com', 'TEST-001', {'customer': 'Test'})
   "
   ```

2. **Check Results**:
   - Verify email was sent from Gmail
   - Check email formatting and content
   - Confirm delivery to recipient

## Troubleshooting

### Common Issues

**❌ Authentication Failed (535 Error)**
```
Solution: Double-check your 16-character app password
```

**❌ Connection Timeout**
```
Solution: Check firewall settings for outbound SMTP (port 587)
```

**❌ "Less Secure Apps" Error**
```
Solution: Use app password instead of regular password (this guide already covers this)
```

**❌ 2FA Not Enabled Error**
```
Solution: Complete Step 1 first - 2FA is required for app passwords
```

### Debug Mode

For detailed troubleshooting, edit `test_email_config.py`:
```python
server.set_debuglevel(1)  # Change from 0 to 1
```

This will show detailed SMTP conversation.

## Security Considerations

### Best Practices
- ✅ Use dedicated Gmail account for automation (not personal email)
- ✅ Use app passwords, never regular password
- ✅ Enable 2-Factor Authentication
- ✅ Monitor sent emails regularly
- ✅ Rotate app password quarterly

### App Password Management
- Store app password securely in `.env` file
- Never commit `.env` to version control
- Generate new app password if compromised
- Use descriptive names for app passwords

## Next Steps

Once Gmail is working:

1. **Configure Email Templates** → `templates/email/`
2. **Set Up Monitoring** → Dashboard for sent emails
3. **Train Users** → How to send offers via email
4. **Configure Alerts** → Error notifications

## Support

**For Gmail Issues**:
- Google Workspace Admin Help: https://support.google.com/a/
- Gmail Help Center: https://support.google.com/gmail/

**For Integration Issues**:
- Developer: lauri.pelkonen@metec.fi
- System Documentation: `docs/`

---

**✅ Gmail setup complete! Your offer automation system can now send emails.** 