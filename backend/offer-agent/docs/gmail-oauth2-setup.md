# Gmail OAuth2 Setup Guide

This guide explains how to set up OAuth2 Gmail authentication for **personal Gmail accounts**. This is the correct method for accessing Gmail when you can't use service accounts with domain-wide delegation.

## 🎯 When to Use OAuth2 vs Service Account

| Authentication Type | Use Case | Gmail Account Type |
|---|---|---|
| **OAuth2 (This Guide)** | Personal Gmail, No admin access | `@gmail.com` |
| **Service Account** | Google Workspace, Admin access | `@yourdomain.com` |

## 📋 Prerequisites

- Google Cloud Console access
- Gmail API enabled (you already have this ✅)
- Personal Gmail account (`ai.tarjous.wcom@gmail.com`)

## 🚀 Setup Steps

### Step 1: Create OAuth2 Client Credentials

1. **Go to Google Cloud Console**
   - Navigate to: https://console.cloud.google.com/apis/credentials
   - Select your project: `calcium-verbena-463208-e5`

2. **Create OAuth2 Client ID**
   - Click **"+ CREATE CREDENTIALS"**
   - Select **"OAuth client ID"**

3. **Configure OAuth Consent Screen** (if not done)
   - Click **"Configure Consent Screen"**
   - Choose **"External"** (for personal Gmail)
   - Fill required fields:
     - **App name**: `Offer Automation`
     - **User support email**: `ai.tarjous.wcom@gmail.com`
     - **Developer contact**: `ai.tarjous.wcom@gmail.com`
   - Save and continue through steps

4. **Create Desktop Application Credentials**
   - **Application type**: Desktop application
   - **Name**: `Gmail OAuth Client`
   - Click **"Create"**

5. **Download Credentials**
   - Click **"Download JSON"** 
   - Save as: `config/gmail_oauth_credentials.json`

### Step 2: Configure OAuth2 Scopes

The application will request these scopes automatically:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Mark as read

### Step 3: Environment Configuration

Update your environment variables (no changes needed for OAuth2):

```bash
# Keep existing settings
MONITORED_EMAIL=ai.tarjous.wcom@gmail.com

# OAuth2 doesn't use service account file
# GMAIL_SERVICE_ACCOUNT_FILE=  # Not needed for OAuth2
```

### Step 4: Test OAuth2 Setup

```bash
# Test OAuth2 authentication
python test_gmail_oauth.py
```

**What happens during first run:**
1. Browser opens automatically
2. Google asks you to sign in (`ai.tarjous.wcom@gmail.com`)
3. Google asks permission to access Gmail
4. Click **"Allow"**
5. Credentials saved automatically for future use

## 🔐 OAuth2 Flow Details

### First Time Setup
1. **Browser Authorization**: Opens browser for user consent
2. **Token Storage**: Saves `config/gmail_token.pickle` 
3. **Automatic Refresh**: Tokens refresh automatically when expired

### Subsequent Runs
- Uses saved tokens automatically
- No browser interaction needed
- Tokens refresh automatically

## 📁 File Structure After Setup

```
config/
├── gmail_oauth_credentials.json    # OAuth2 client credentials (from Google)
├── gmail_token.pickle             # Saved user tokens (auto-generated)
└── environment.template           # Environment config
```

## 🧪 Testing Your Setup

### Complete Test
```bash
python test_gmail_oauth.py
# Choose option 1 (complete test)
```

### Individual Tests
```bash
# Test just email reading
python test_gmail_oauth.py  # Option 4

# Test just email sending
python test_gmail_oauth.py  # Option 3
```

## ✅ Expected Results

After successful setup, you should see:
```
✅ OAuth2 credentials file found
✅ Gmail OAuth reader initialized successfully
✅ Health check passed - Connected to: ai.tarjous.wcom@gmail.com
✅ Gmail OAuth sender initialized successfully
✅ Successfully read latest email
✅ Test email sent successfully
```

## 🔧 Troubleshooting

### "OAuth2 credentials file not found"
- Download OAuth2 client credentials from Google Cloud Console
- Save as `config/gmail_oauth_credentials.json`

### "Access blocked: This app's request is invalid"
- Configure OAuth consent screen properly
- Add your Gmail address as a test user if needed

### "invalid_grant" error
- Delete `config/gmail_token.pickle`
- Run test again to re-authorize

### Browser doesn't open
```python
# Manual authorization URL will be printed
# Copy URL to browser manually
```

## 🚀 Integration with Main System

Once OAuth2 is working, update `src/main.py` to use OAuth2:

```python
# Replace service account imports
from src.email_processing.gmail_oauth_processor import GmailOAuthProcessor
from src.notifications.gmail_oauth_sender import GmailOAuthSender

# In OfferAutomationOrchestrator.__init__():
self.gmail_processor = GmailOAuthProcessor()
self.gmail_sender = GmailOAuthSender()
```

## 🔒 Security Notes

- **OAuth2 tokens** are stored locally in `config/gmail_token.pickle`
- **Credentials file** contains client secrets (keep secure)
- **Tokens refresh** automatically (no re-authorization needed)
- **Scope limited** to Gmail read/send only

## 📖 Additional Resources

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth2 Scopes Reference](https://developers.google.com/identity/protocols/oauth2/scopes#gmail)

## ❓ FAQ

**Q: Do I need a Google Workspace account?**
A: No, OAuth2 works with personal Gmail accounts.

**Q: Will users need to authorize every time?**
A: No, authorization is saved and tokens refresh automatically.

**Q: Can I use both OAuth2 and service accounts?**
A: You should choose one method. OAuth2 is recommended for personal Gmail.

**Q: Is this secure for production?**
A: Yes, OAuth2 is the recommended method for accessing Gmail APIs.

---

✅ **Ready to test?** Run `python test_gmail_oauth.py` to get started! 