# AWS Learning Infrastructure Setup

This document describes all AWS resources required for the self-learning offer automation system.

## Overview

The learning system analyzes user corrections to AI-generated offers and extracts learnings that improve future product matching. The system uses:
- **S3** for storing offer contexts, learnings, and processing state
- **Lambda** for nightly learning agent execution
- **CloudWatch Events** for scheduled execution
- **IAM** for permissions management

## S3 Bucket Structure

### Bucket Name
- Primary: `offer-learning-data`
- Region: `eu-north-1` (Stockholm)

### Directory Structure

```
offer-learning-data/
├── offer-requests/           # Original AI offer contexts
│   ├── {offer_number}_{timestamp}.json
│   └── ...
├── learning-state/           # Processing state tracking
│   ├── {offer_number}.json
│   └── ...
└── learnings/               # Extracted learnings
    ├── product_swaps.csv    # Product code swap learnings
    └── general_rules.txt    # General matching rules
```

### File Formats

#### Offer Requests (`offer-requests/{offer_number}_{timestamp}.json`)
```json
{
  "offer_number": "700123",
  "timestamp": "2025-11-06T22:00:00Z",
  "email": {
    "subject": "Tarjouspyyntö - Vesimittarit",
    "sender": "myyjä@lvi-wabek.fi",
    "body": "...",
    "date": "2025-11-06",
    "message_id": "..."
  },
  "customer": {
    "id": "12345",
    "number": "218772",
    "name": "Asiakasyritys Oy",
    "street": "Teollisuustie 1",
    "city": "Helsinki",
    "postal_code": "00100"
  },
  "ai_matched_products": [
    {
      "product_code": "1234567",
      "product_name": "VESIMITTARI DN15",
      "description": "...",
      "quantity": 10,
      "unit": "KPL",
      "price": 25.50,
      "confidence_score": 0.85,
      "match_method": "ai_analyzer",
      "product_group": "101600",
      "match_details": {
        "original_customer_term": "vesimittari 15mm",
        "ai_confidence": 85,
        "ai_reasoning": "Koko ja tyyppi täsmäävät täydellisesti"
      }
    }
  ],
  "pricing": {
    "net_total": 255.00,
    "vat_amount": 61.20,
    "total_amount": 316.20,
    "total_discount_percent": 10.0,
    "currency": "EUR",
    "line_items": [...]
  }
}
```

#### Learning State (`learning-state/{offer_number}.json`)
```json
{
  "offer_number": "700123",
  "last_processed_hash": "a3f5c9e1b2d4...",
  "last_check_timestamp": "2025-11-07T02:00:00Z"
}
```

#### Product Swaps CSV (`learnings/product_swaps.csv`)
```csv
customer_term,matched_product_code,matched_product_name,confidence_score,reasoning,match_type,timestamp,source_files
"KUPARIPUTKI 3M 15mm","1234567","KUPARIPUTKI TIGRIS 5M 15MM",0.95,"User prefers 5m Tigris pipes over 3m generic pipes for project efficiency",learned_from_correction,2025-11-06T22:00:00,offer_700123
```

#### General Rules (`learnings/general_rules.txt`)
```
2025-11-06: Prefer TIGRIS brand composite pipes over ONEPIPE when both match customer requirements
2025-11-07: For projects requiring total pipe length >10m, prefer 5m sections over 3m sections to reduce joints
```

## S3 Bucket Configuration

### Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "ArchiveOfferRequests",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "offer-requests/"
      },
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "DeleteOldProcessingState",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "learning-state/"
      },
      "Expiration": {
        "Days": 180
      }
    }
  ]
}
```

### CORS Configuration
Not required for this use case (Lambda and backend only).

### Versioning
Recommended: Enabled for `learnings/` directory to track learning evolution.

### Encryption
Recommended: Server-side encryption (SSE-S3) enabled.

## Lambda Function

### Function Name
`offer-learning-agent`

### Configuration
- **Runtime**: Python 3.11
- **Memory**: 512 MB (sufficient for AI analysis)
- **Timeout**: 15 minutes (900 seconds)
- **Architecture**: x86_64
- **Handler**: `nightly_learning_agent.lambda_handler`

### Deployment Package
The Lambda function requires these files:
```
deployment-package/
├── nightly_learning_agent.py
├── requirements.txt          # boto3, google-generativeai, httpx
└── ... (dependencies)
```

### Environment Variables

```bash
# AWS
AWS_S3_BUCKET_LEARNING=offer-learning-data
AWS_REGION=eu-north-1

# Lemonsoft API
ERP_API_URL=https://api.lemonsoft.fi
ERP_API_KEY=<your-api-key>
ERP_USERNAME=<username>
ERP_PASSWORD=<password>
ERP_DATABASE=<database-name>

# Google Gemini
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL_ITERATION=gemini-2.5-flash
```

### Lambda Layer (Optional)
Consider using a Lambda Layer for large dependencies like `google-generativeai` to reduce deployment package size.

## IAM Roles and Permissions

### Lambda Execution Role
Name: `offer-learning-agent-execution-role`

#### Trust Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### Permissions Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-north-1:*:log-group:/aws/lambda/offer-learning-agent:*"
    },
    {
      "Sid": "S3ReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::offer-learning-data",
        "arn:aws:s3:::offer-learning-data/*"
      ]
    }
  ]
}
```

### Application Role (for main.py)
The main offer automation application needs S3 write permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3WriteOfferRequests",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::offer-learning-data/offer-requests/*"
    }
  ]
}
```

## CloudWatch Events Schedule

### Event Rule
Name: `offer-learning-agent-schedule`

#### Schedule Expression
```
cron(0 2 * * ? *)
```
This runs daily at 2:00 AM UTC (4:00 AM Helsinki time in winter, 5:00 AM in summer).

#### Target
- **Target**: Lambda function `offer-learning-agent`
- **Input**: Empty JSON `{}`

### Alternative Schedule Options
- Every 12 hours: `cron(0 */12 * * ? *)`
- Every night at 3 AM: `cron(0 3 * * ? *)`
- Weekly on Monday: `cron(0 2 ? * MON *)`

## CloudWatch Logs

### Log Group
- **Name**: `/aws/lambda/offer-learning-agent`
- **Retention**: 30 days (configurable)
- **Log Format**: JSON structured logs

### Sample Log Entry
```json
{
  "timestamp": "2025-11-06T02:00:15.123Z",
  "level": "INFO",
  "message": "Learning agent run complete: 12 offers processed, 8 learnings extracted",
  "context": {
    "offers_processed": 12,
    "successful": 12,
    "skipped": 4,
    "with_learnings": 8,
    "total_learnings": 8
  }
}
```

## Monitoring and Alerts

### CloudWatch Metrics
- Lambda invocations
- Lambda duration
- Lambda errors
- Lambda throttles

### Recommended Alarms
1. **Lambda Errors**: Alert if error count > 0 in 24 hours
2. **Lambda Duration**: Alert if duration > 13 minutes (near timeout)
3. **S3 Bucket Size**: Monitor growth rate

## Cost Estimates

### S3 Storage
- **Offer requests**: ~10 KB per offer × 100 offers/day × 90 days = ~90 MB
- **Learning state**: ~1 KB per offer × 100 offers = ~100 KB
- **Learnings**: ~100 KB (grows slowly)
- **Total**: < 100 MB = **< $0.01/month**

### Lambda Execution
- **Invocations**: 30/month (daily)
- **Duration**: ~5 minutes average
- **Memory**: 512 MB
- **Cost**: **< $1/month**

### Data Transfer
- Minimal (all within AWS)
- **Cost**: **< $0.10/month**

### Total Monthly Cost: **< $2/month**

## Deployment Checklist

- [ ] Create S3 bucket `offer-learning-data` in `eu-north-1`
- [ ] Configure S3 lifecycle policies
- [ ] Enable S3 versioning for `learnings/` directory
- [ ] Enable S3 server-side encryption
- [ ] Create IAM execution role for Lambda
- [ ] Create Lambda function with correct configuration
- [ ] Set all environment variables in Lambda
- [ ] Deploy Lambda code (upload .zip or use container)
- [ ] Create CloudWatch Events rule for scheduling
- [ ] Test Lambda function manually
- [ ] Verify S3 write permissions from main application
- [ ] Set up CloudWatch alarms
- [ ] Document any custom configurations

## Testing

### Manual Lambda Test
```json
{
  "test": true,
  "debug": true
}
```

### Verify S3 Structure
```bash
aws s3 ls s3://offer-learning-data/ --recursive
```

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/offer-learning-agent --follow
```

## Troubleshooting

### Common Issues

1. **Lambda timeout**
   - Increase timeout to 15 minutes
   - Reduce number of offers processed per run
   - Add pagination for large offer lists

2. **S3 permissions error**
   - Verify IAM role has correct permissions
   - Check bucket policy
   - Verify bucket name matches environment variable

3. **Lemonsoft API errors**
   - Check API credentials in environment variables
   - Verify API endpoint is accessible from Lambda
   - Check rate limits

4. **Gemini API errors**
   - Verify API key is valid
   - Check quota and rate limits
   - Add retry logic for transient errors

## Security Considerations

1. **Secrets Management**
   - Use AWS Secrets Manager for Lemonsoft credentials
   - Rotate API keys regularly
   - Use environment variable encryption

2. **S3 Bucket Security**
   - Block public access
   - Enable access logging
   - Use bucket policies to restrict access

3. **Lambda Security**
   - Use VPC if accessing internal resources
   - Enable function URL only if needed
   - Monitor invocation patterns for anomalies

## Future Enhancements

1. **Dead Letter Queue (DLQ)**: For failed Lambda invocations
2. **Step Functions**: For complex workflows
3. **EventBridge**: For more sophisticated event routing
4. **X-Ray**: For distributed tracing
5. **CloudWatch Insights**: For advanced log analytics

