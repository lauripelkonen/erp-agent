# Gmail Authentication Setup for Offer Automation

This guide explains how to set up Gmail authentication for the offer automation system to send confirmation emails.

## Overview

The system uses Google Service Account authentication to send emails via Gmail API. This requires:
1. A Google Cloud Project
2. A Gmail service account with domain-wide delegation
3. Proper environment configuration

## Setup Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note the project ID for later use

### 2. Enable Gmail API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on Gmail API and enable it

### 3. Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the service account details:
   - Name: `offer-automation-gmail`
   - Description: `Service account for automated offer emails`
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

### 4. Generate Service Account Key

1. In the service accounts list, click on your new service account
2. Go to the "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Select "JSON" format
5. Download the JSON file
6. Store it securely (e.g., `config/gmail-service-account.json`)

### 5. Configure Environment Variables (Simple Setup)

Set these environment variables in your `.env` file:

```bash
# Gmail Configuration (Simple Setup)
GMAIL_SERVICE_ACCOUNT_FILE=/path/to/your/gmail-service-account.json
MONITORED_EMAIL=ai.tarjous.wcom@gmail.com

# Alternative: Set the path relative to project root
GMAIL_SERVICE_ACCOUNT_FILE=config/gmail-service-account.json
```

**Note**: We're using the simple setup without domain-wide delegation, so no `GMAIL_DELEGATED_EMAIL` is needed.

### 7. Test Configuration

The system will automatically test Gmail connectivity during startup. Check logs for:

```
INFO | Gmail sender initialized with email: ai.tarjous.wcom@gmail.com
```

## Troubleshooting

### Error: "Gmail service account file not found"

**Solution**: 
- Verify the `GMAIL_SERVICE_ACCOUNT_FILE` path is correct
- Ensure the JSON file exists and is readable
- Use absolute path or relative to project root

### Error: "Insufficient authentication scopes"

**Solution**:
- Verify domain-wide delegation is enabled
- Check the scopes in Google Admin Console
- Ensure the service account has the correct scopes

### Error: "User rate limit exceeded"

**Solution**:
- Implement rate limiting in email sending
- Consider using batch API calls
- Check Gmail API quotas in Google Cloud Console

### Error: "Invalid JWT"

**Solution**:
- Verify the service account JSON file is valid
- Check system clock is synchronized
- Regenerate service account key if needed

## Alternative: Skip Email Notifications

If you don't need email notifications, the system will automatically skip them when Gmail is not configured:

```bash
# Don't set GMAIL_SERVICE_ACCOUNT_FILE, and the system will log:
# "Gmail service account not configured - skipping email notifications"
```

## Security Best Practices

1. **Secure Storage**: Store service account JSON files outside the codebase
2. **Environment Variables**: Use environment variables for paths, not hardcoded values
3. **Access Control**: Limit service account permissions to minimum required
4. **Key Rotation**: Regularly rotate service account keys
5. **Monitoring**: Monitor Gmail API usage and quotas

## Example Configuration

Complete `.env` example:

```bash
# Gmail Configuration (Simple Setup)
GMAIL_SERVICE_ACCOUNT_FILE=/opt/offer-automation/config/gmail-service-account.json
MONITORED_EMAIL=ai.tarjous.wcom@gmail.com

# SMTP Fallback (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=ai.tarjous.wcom@gmail.com
SMTP_PASSWORD=your_app_specific_password
```

## FAQ

**Q: Do I need domain-wide delegation?**
A: No, we're using the simple setup without delegation. Emails will come from the service account email.

**Q: Can I use personal Gmail?**
A: Yes, this setup works with personal Gmail accounts or Google Workspace.

**Q: What if I don't want email notifications?**
A: Simply don't set `GMAIL_SERVICE_ACCOUNT_FILE`. The system will skip email notifications gracefully.

**Q: How do I test email sending?**
A: The system automatically sends confirmation emails when offers are created. Check the logs for success/failure messages. 