# Fix OAuth Access Blocked Error

The error "Pääsy estetty: AI offers ei ole suorittanut Googlen todennusmenettelyä loppuun" (Access blocked: AI offers has not completed Google's verification process) occurs because your OAuth consent screen needs proper configuration.

## 🚨 Error: 403: access_denied

This happens when:
- OAuth consent screen is not properly configured
- App is in testing mode but user is not added as test user
- Missing required OAuth consent screen information

## 🔧 **Step-by-Step Fix**

### Step 1: Configure OAuth Consent Screen

1. **Go to OAuth Consent Screen**
   - Navigate to: https://console.cloud.google.com/apis/credentials/consent
   - Select your project: `calcium-verbena-463208-e5`

2. **Configure App Information**
   - **App name**: `Offer Automation Gmail`
   - **User support email**: `ai.tarjous.wcom@gmail.com`
   - **App domain** (optional): Leave empty for testing
   - **Developer contact**: `ai.tarjous.wcom@gmail.com`
   - Click **Save and Continue**

3. **Configure Scopes**
   - Click **Add or Remove Scopes**
   - Add these scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.send
     https://www.googleapis.com/auth/gmail.modify
     ```
   - Click **Update** then **Save and Continue**

4. **Add Test Users**
   - Click **Add Users**
   - Add your Gmail address: `ai.tarjous.wcom@gmail.com`
   - Click **Save and Continue**

5. **Review and Submit**
   - Review all settings
   - Click **Back to Dashboard**

### Step 2: Verify OAuth Client Configuration

1. **Go to Credentials**
   - Navigate to: https://console.cloud.google.com/apis/credentials
   - Click on your OAuth client ID

2. **Check Application Type**
   - Should be: **Desktop application**
   - If not, delete and recreate as desktop application

3. **Download New Credentials**
   - Click **Download JSON**
   - Save as `config/gmail_oauth_credentials.json`
   - Replace the old file

### Step 3: Clear Existing Tokens

```bash
# Remove old authorization tokens
rm config/gmail_token.pickle
```

### Step 4: Test Again

```bash
python test_gmail_oauth.py
```

## 🎯 **Alternative: Use Internal App Type**

If you continue having issues, you can set the app to "Internal" (if using Google Workspace):

1. **OAuth Consent Screen**
2. **User Type**: Select **Internal** instead of **External**
3. This limits access to your organization only

## ✅ **Expected Result After Fix**

When you run the test again, you should see:
- Browser opens to Google authorization
- You can sign in with `ai.tarjous.wcom@gmail.com`
- Google shows permission request for Gmail access
- You can click "Allow" 
- Authorization completes successfully

## 🔍 **Troubleshooting**

### Still getting access_denied?
1. **Wait 5-10 minutes** after configuring consent screen
2. **Try incognito/private browser** mode
3. **Clear browser cache** for google.com
4. **Verify test user email** matches exactly

### App still showing as unverified?
This is normal for testing. Google will show:
- "Google hasn't verified this app"
- "This app wants access to your Google Account"
- Click **Advanced** → **Go to Offer Automation Gmail (unsafe)**

### Need immediate access?
For development/testing purposes:
1. Use **Internal** user type (Google Workspace only)
2. Or add your email as test user in External app
3. Google allows up to 100 test users

## 📖 **Why This Happens**

- **External apps** in testing mode can only be used by added test users
- **Unverified apps** show security warnings (this is normal for development)
- **Test users** must be explicitly added to the OAuth consent screen

---

🔧 **Quick Fix Summary:**
1. Add yourself as test user in OAuth consent screen
2. Download new OAuth credentials
3. Delete old token file
4. Test again

The app will work perfectly for testing once you're added as a test user! 