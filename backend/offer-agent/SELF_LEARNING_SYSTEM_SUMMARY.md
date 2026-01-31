# Self-Learning Offer Automation System - Implementation Summary

## Overview

The self-learning system has been successfully implemented to enable the AI offer automation agent to learn from user corrections. The system automatically detects when users modify AI-generated offers and extracts learnings to improve future product matching.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OFFER GENERATION FLOW                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Email → AI Analysis → Product Matching → Offer Creation    │
│                                                                 │
│  2. Save Context to S3 (offer-requests/)                       │
│     - Original email                                            │
│     - AI matched products                                       │
│     - Customer info                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            USER REVIEWS AND MODIFIES OFFER IN ERP               │
│  - Changes product codes                                        │
│  - Adjusts quantities                                           │
│  - Adds/removes rows                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           NIGHTLY LEARNING AGENT (Lambda @ 2 AM)                │
│                                                                 │
│  1. List offers from past 3 days (from S3)                     │
│  2. For each offer:                                             │
│     - Fetch current state from Lemonsoft API                   │
│     - Calculate hash of offer rows                             │
│     - Compare with last processed hash                         │
│     - Skip if unchanged                                         │
│  3. If changed:                                                 │
│     - Compare original AI vs final user version                │
│     - Detect product swaps, additions, deletions               │
│     - Use Gemini AI to analyze each change                     │
│     - Extract learnings (product swaps or general rules)       │
│  4. Save learnings to S3                                        │
│  5. Update processing state                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│         LEARNINGS APPLIED IN FUTURE OFFERS                      │
│                                                                 │
│  ProductMatcher loads S3 learnings at startup:                 │
│  - Merges product_swaps.csv with training_dataset.csv          │
│  - Loads general_rules.txt                                     │
│  - Adds rules to Gemini system prompt                          │
└─────────────────────────────────────────────────────────────────┘
```

## Components Implemented

### 1. S3 Request Logger (`src/learning/request_logger.py`)

**Purpose**: Saves complete offer context to S3 when offers are created.

**Key Features**:
- Stores original email data
- Stores AI-matched products with confidence scores
- Stores customer information
- Generates unique S3 keys with timestamps
- Handles S3 errors gracefully (doesn't fail offer creation)

**Integration**: Called from `main.py` after successful offer creation (line ~1295).

### 2. Nightly Learning Agent (`src/learning/nightly_learning_agent.py`)

**Purpose**: Lambda function that runs nightly to analyze offer corrections.

**Key Features**:
- Lists offers from past 3 days
- Compares AI-generated vs user-edited offers
- Uses MD5 hashing to detect changes (avoids reprocessing)
- Gemini AI analysis for each change
- Stores learnings in S3 (CSV and TXT)
- Tracks processing state to prevent duplicates

**Configuration**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 15 minutes
- Schedule: Daily at 2 AM UTC via CloudWatch Events

### 3. ProductMatcher Updates (`src/emails/product_matcher.py`)

**Purpose**: Loads S3 learnings at startup for improved matching.

**Key Features**:
- `_merge_s3_learnings()`: Downloads and merges S3 learnings with local training data
- `_build_learning_rules_section()`: Adds learned rules to Gemini system prompt
- Deduplicates learnings (S3 learnings take precedence)
- Graceful fallback if S3 unavailable

**Integration**: Called automatically during ProductMatcher initialization.

### 4. AWS Infrastructure Documentation (`AWS_LEARNING_INFRASTRUCTURE.md`)

Complete guide covering:
- S3 bucket structure and lifecycle policies
- Lambda function configuration
- IAM roles and permissions
- CloudWatch Events schedule
- Cost estimates (~$2/month)
- Deployment checklist
- Troubleshooting guide

## Data Flow

### Learning Storage Format

#### Product Swaps CSV
```csv
customer_term,matched_product_code,matched_product_name,confidence_score,reasoning,match_type,timestamp,source_files
"KUPARIPUTKI 3M 15mm","1234567","KUPARIPUTKI TIGRIS 5M 15MM",0.95,"User prefers 5m Tigris pipes",learned_from_correction,2025-11-06T22:00:00,offer_700123
```

#### General Rules TXT
```
2025-11-06: Prefer TIGRIS brand composite pipes over ONEPIPE
2025-11-07: For projects >10m length, prefer 5m sections over 3m
```

## Gemini AI Analysis

The learning agent uses the same Gemini configuration as ProductMatcher:
- **Model**: `gemini-2.5-flash`
- **Temperature**: 0.1 (deterministic)
- **Output Format**: Structured JSON

### Analysis Prompt Structure

For each detected change, Gemini analyzes:
1. **Original AI Selection**: Product code + name
2. **User Correction**: New product code + name
3. **Context**: Customer email, company name, project details
4. **Decision**: Is this a learning opportunity?
   - Product swap: Specific brand/variant preference
   - General rule: Broader matching principle
   - Not a learning: One-off correction

## Deduplication Strategy

The system prevents duplicate learnings through:

1. **Hash-based Change Detection**
   - MD5 hash of offer rows (product code + quantity + discount)
   - Stored in `learning-state/{offer_number}.json`
   - Only process if hash changed since last check

2. **CSV Deduplication**
   - Merges local and S3 training data
   - Removes duplicates by `customer_term + matched_product_code`
   - Keeps most recent entry (S3 learnings take precedence)

3. **3-Day Window**
   - Only processes offers from past 3 days
   - Assumes users complete edits within 3 days
   - Older offers archived via S3 lifecycle policies

## Configuration

### Environment Variables (added to `example.env`)

```bash
# AWS Configuration for Learning System
AWS_S3_BUCKET_LEARNING=offer-learning-data
AWS_REGION=eu-north-1
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

# Learning System Settings
LEARNING_RETENTION_DAYS=90
```

### Lambda Environment Variables

```bash
# AWS
AWS_S3_BUCKET_LEARNING=offer-learning-data
AWS_REGION=eu-north-1

# Lemonsoft API
LEMONSOFT_API_URL=https://api.lemonsoft.fi
LEMONSOFT_API_KEY=<your-api-key>
LEMONSOFT_USERNAME=<username>
LEMONSOFT_PASSWORD=<password>
LEMONSOFT_DATABASE=<database-name>

# Google Gemini
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL_ITERATION=gemini-2.5-flash
```

## Testing & Validation

### Manual Testing Steps

1. **Test S3 Logger**
   ```python
   # Create a test offer and verify S3 upload
   # Check S3 console for file in offer-requests/
   ```

2. **Test Lambda Function**
   ```bash
   # Invoke manually with test event
   aws lambda invoke --function-name offer-learning-agent output.json
   ```

3. **Verify Learning Merge**
   ```python
   # Check ProductMatcher logs for:
   # "✅ Merged S3 learnings with local training data"
   ```

### Monitoring

- **CloudWatch Logs**: `/aws/lambda/offer-learning-agent`
- **S3 Bucket**: Monitor file count and size
- **ProductMatcher Logs**: Check for S3 merge success

## Deployment Steps

### 1. Create S3 Bucket
```bash
aws s3 mb s3://offer-learning-data --region eu-north-1
```

### 2. Deploy Lambda Function
```bash
cd src/learning
pip install -r requirements.txt -t .
zip -r learning-agent.zip .
aws lambda create-function \
  --function-name offer-learning-agent \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --handler nightly_learning_agent.lambda_handler \
  --zip-file fileb://learning-agent.zip
```

### 3. Create CloudWatch Schedule
```bash
aws events put-rule \
  --name offer-learning-agent-schedule \
  --schedule-expression "cron(0 2 * * ? *)"
```

### 4. Set Environment Variables
Update Lambda function with all required environment variables.

## Benefits

1. **Continuous Improvement**: Agent learns from every correction
2. **No Manual Training**: Learnings extracted automatically
3. **Brand Preferences**: Captures user preferences for specific brands
4. **Pattern Recognition**: Identifies general matching rules
5. **Cost Effective**: ~$2/month AWS costs
6. **Non-Disruptive**: Doesn't affect offer creation if S3 unavailable

## Future Enhancements

1. **Machine Learning Model**: Train custom models from learnings
2. **Confidence Scoring**: Dynamic confidence based on learning patterns
3. **A/B Testing**: Compare performance with/without learnings
4. **Learning Dashboard**: Visualize learning accumulation over time
5. **Manual Review Interface**: Allow admins to approve/reject learnings

## Files Modified/Created

### Created Files
- `src/learning/__init__.py`
- `src/learning/request_logger.py`
- `src/learning/nightly_learning_agent.py`
- `AWS_LEARNING_INFRASTRUCTURE.md`
- `SELF_LEARNING_SYSTEM_SUMMARY.md`

### Modified Files
- `src/main.py`: Added request logger integration
- `src/emails/product_matcher.py`: Added S3 learning merge and rules section
- `example.env`: Added AWS and learning configuration

## Support & Troubleshooting

See `AWS_LEARNING_INFRASTRUCTURE.md` for:
- Common issues and solutions
- CloudWatch log examples
- IAM permission troubleshooting
- Cost monitoring

## Success Metrics

Track these metrics to measure system effectiveness:
1. **Learning Accumulation Rate**: Learnings/week
2. **Match Confidence Improvement**: Average confidence over time
3. **Manual Corrections Reduction**: % of offers needing user edits
4. **Product Code 9000 Usage**: Frequency of fallback code
5. **Processing Time**: Nightly agent execution time

---

**Status**: ✅ All components implemented and ready for AWS deployment
**Next Step**: Create AWS resources as documented in `AWS_LEARNING_INFRASTRUCTURE.md`

