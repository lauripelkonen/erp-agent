# OAuth2 Integration in Main System

The main offer automation system has been updated to use OAuth2 for Gmail integration, providing a complete workflow from email receipt to offer creation and notification.

## 🔄 **Complete Workflow**

### 1. Email Flow
```
Customer → Salesperson → AI Agent (ai.tarjous.wcom@gmail.com) → Salesperson
   ↑                                    ↓
   └─────── Offer Review ←──── Offer Created in Lemonsoft
```

**Detailed Steps:**
1. **Customer** sends offer request to **Salesperson**
2. **Salesperson** forwards email to `ai.tarjous.wcom@gmail.com`
3. **AI Agent** processes the email automatically:
   - Extracts company information
   - Looks up customer in Lemonsoft
   - Matches products using AI
   - Creates offer in Lemonsoft
   - Sends confirmation back to **Salesperson**
4. **Salesperson** reviews the offer and sends to customer if approved

## 🚀 **System Components**

### OAuth2 Gmail Integration
- **Reader**: `GmailOAuthProcessor` - reads incoming emails
- **Sender**: `GmailOAuthSender` - sends confirmation emails
- **Authentication**: Personal Gmail account with OAuth2 user consent

### Core Processing
- **AI Analysis**: Company extraction, product matching
- **Customer Lookup**: Enhanced Lemonsoft customer search
- **Pricing**: Sophisticated pricing rules and discounts
- **Offer Creation**: Complete Lemonsoft offer with verification

## 📧 **Email Processing Features**

### Automatic Email Monitoring
```python
# Main.py runs continuously and checks for new emails every 30 seconds
while True:
    await asyncio.sleep(30)
    results = await orchestrator.process_incoming_email_requests(max_emails=3)
```

### Email Analysis
- **Company Detection**: AI extracts customer company name
- **Contact Information**: Identifies delivery contact person
- **Customer Reference**: Generates or extracts project references
- **Attachment Processing**: Handles Excel/PDF product lists

### Offer Creation
- **Customer Lookup**: Multiple search strategies in Lemonsoft
- **Product Matching**: AI-powered product identification
- **Pricing Calculation**: Sophisticated discount rules
- **Credit Check**: Automatic handling of credit-denied customers

## ✅ **Updated Configuration**

### Required OAuth2 Setup
1. **OAuth2 Credentials**: `config/gmail_oauth_credentials.json`
2. **User Authorization**: One-time browser consent
3. **Token Storage**: `config/gmail_token.pickle` (auto-refreshed)

### Environment Variables
```bash
MONITORED_EMAIL=ai.tarjous.wcom@gmail.com
# No longer needed: GMAIL_SERVICE_ACCOUNT_FILE
```

## 🔧 **Testing & Usage**

### 1. Test OAuth2 Setup
```bash
python test_gmail_oauth.py
```

### 2. Test Main System
```bash
python test_main_oauth.py
```

### 3. Run Production System
```bash
python src/main.py
```

## 📊 **System Monitoring**

### Health Check
- **Gmail OAuth**: Connection status and email access
- **Lemonsoft API**: Backend system connectivity
- **AI Components**: AI analyzer and product matcher
- **Pricing Calculator**: Discount rules engine

### Logging & Audit
- **Processing Logs**: Detailed workflow tracking
- **Audit Trail**: Offer creation history
- **Error Handling**: Graceful failure recovery

## 🔍 **Email Processing Logic**

### Unread Email Detection
```python
# Checks for unread emails
emails = await gmail_processor.get_recent_emails(query="is:unread", max_results=5)
```

### Processing Pipeline
1. **Extract Company Info**: AI analyzes email content
2. **Customer Lookup**: Multiple Lemonsoft search strategies
3. **Product Analysis**: AI matches products from text/attachments
4. **Pricing Calculation**: Apply sophisticated discount rules
5. **Offer Creation**: Create complete offer in Lemonsoft
6. **Verification**: Validate created offer data
7. **Notification**: Send confirmation to salesperson

### Email Status Management
- **Mark as Read**: Successfully processed emails
- **Leave Unread**: Failed processing for manual review
- **Error Logging**: Detailed failure information

## 💼 **Business Workflow Benefits**

### For Salespersons
- **Quick Processing**: Forward email → receive offer confirmation
- **Quality Control**: Review offer before sending to customer
- **Credit Warnings**: Automatic alerts for credit-denied customers
- **Detailed Reports**: Complete product matching and pricing analysis

### For Management
- **Audit Trail**: Complete processing history
- **Performance Metrics**: Processing success rates
- **Cost Analysis**: Automated discount application tracking
- **Customer Intelligence**: Enhanced customer data utilization

## 🛡️ **Security & Reliability**

### OAuth2 Security
- **Limited Scopes**: Only Gmail read/send permissions
- **Token Refresh**: Automatic credential renewal
- **Personal Account**: No domain-wide delegation needed

### Error Handling
- **Graceful Failures**: System continues running on errors
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Processing**: Manual intervention triggers for unclear cases

### Data Protection
- **Local Tokens**: Credentials stored locally only
- **Encrypted Transit**: All API communications secured
- **Access Logging**: Complete audit trail

## 📖 **Usage Examples**

### Manual Email Processing
```python
orchestrator = OfferAutomationOrchestrator()

# Process specific email
email_data = {...}  # Email from Gmail API
result = await orchestrator.process_email_offer_request(email_data)

if result['success']:
    print(f"Offer created: {result['offer_details']['offer_number']}")
```

### Batch Processing
```python
# Process all unread emails
results = await orchestrator.process_incoming_email_requests(max_emails=10)
successful = sum(1 for r in results if r['success'])
print(f"Processed {successful}/{len(results)} emails successfully")
```

## 🔄 **Migration from Service Account**

### Changes Made
1. **Import Updates**: OAuth2 components instead of service account
2. **Initialization**: OAuth2 flow instead of service account file
3. **Error Handling**: OAuth2-specific error handling
4. **Health Checks**: OAuth2 service validation

### No Changes Needed
- **Lemonsoft Integration**: Unchanged
- **AI Processing**: Unchanged  
- **Pricing Logic**: Unchanged
- **Business Workflow**: Unchanged

## 🎯 **Production Deployment**

### Requirements
- OAuth2 credentials configured
- Gmail access authorized
- Lemonsoft API credentials
- AI service (Gemini) configured

### Monitoring
- Health check endpoint available
- Structured logging for analysis
- Email processing metrics
- Offer creation success rates

---

✅ **The system is now ready for production use with OAuth2 Gmail integration!**

The workflow maintains the same business logic while using proper OAuth2 authentication for Gmail access. 