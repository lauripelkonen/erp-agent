# Traffic Analytics for erp-agent.com

## Overview

CloudFront logging is enabled for erp-agent.com with the following configuration:

| Setting | Value |
|---------|-------|
| Distribution ID | `E53DMMKWU8AJU` |
| Log Bucket | `s3://erp-agent-cloudfront-logs/cf-logs/` |
| Region | eu-central-1 |
| Cookies Logged | Yes |
| CloudWatch Metrics | Enabled |

---

## Quick Commands (AWS CLI)

### View Recent Log Files

```bash
aws s3 ls s3://erp-agent-cloudfront-logs/cf-logs/ --recursive | tail -20
```

### Download Latest Log File

```bash
# List and get the most recent log
LATEST=$(aws s3 ls s3://erp-agent-cloudfront-logs/cf-logs/ --recursive | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://erp-agent-cloudfront-logs/$LATEST" /tmp/cf-log.gz
gunzip /tmp/cf-log.gz
cat /tmp/cf-log
```

### View Request Count (Last 7 Days)

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=E53DMMKWU8AJU Name=Region,Value=Global \
  --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Sum \
  --output table
```

### View Error Rate (4xx/5xx)

```bash
# 4xx errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 4xxErrorRate \
  --dimensions Name=DistributionId,Value=E53DMMKWU8AJU Name=Region,Value=Global \
  --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Average \
  --output table

# 5xx errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name 5xxErrorRate \
  --dimensions Name=DistributionId,Value=E53DMMKWU8AJU Name=Region,Value=Global \
  --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Average \
  --output table
```

### View Bytes Downloaded

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name BytesDownloaded \
  --dimensions Name=DistributionId,Value=E53DMMKWU8AJU Name=Region,Value=Global \
  --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Sum \
  --output table
```

---

## AWS Console Access

### CloudWatch Metrics Dashboard

1. Go to [CloudWatch Console](https://eu-central-1.console.aws.amazon.com/cloudwatch/)
2. Navigate to **Metrics** > **All metrics**
3. Select **CloudFront** > **Per-Distribution Metrics**
4. Filter by Distribution ID: `E53DMMKWU8AJU`

Available metrics:
- `Requests` - Total number of requests
- `BytesDownloaded` - Data transferred to viewers
- `BytesUploaded` - Data transferred from viewers
- `4xxErrorRate` - Percentage of 4xx errors
- `5xxErrorRate` - Percentage of 5xx errors
- `TotalErrorRate` - Combined error rate

### S3 Log Files

1. Go to [S3 Console](https://s3.console.aws.amazon.com/s3/buckets/erp-agent-cloudfront-logs)
2. Navigate to `cf-logs/` prefix
3. Download and decompress `.gz` files to view raw logs

---

## Log File Format

Each log file contains tab-separated fields:

| Field | Description |
|-------|-------------|
| date | Date of request (YYYY-MM-DD) |
| time | Time of request (HH:MM:SS) |
| x-edge-location | Edge location that served the request |
| sc-bytes | Bytes sent to viewer |
| c-ip | Client IP address |
| cs-method | HTTP method (GET, POST, etc.) |
| cs-uri-stem | URI path requested |
| sc-status | HTTP status code |
| cs(Referer) | Referrer URL |
| cs(User-Agent) | User agent string |
| cs-uri-query | Query string |
| cs(Cookie) | Cookie header |
| x-edge-result-type | Cache hit/miss status |
| time-taken | Request processing time |

---

## Analyzing Logs with Athena (Optional)

For advanced queries, you can set up Athena:

```sql
-- Create table (run once in Athena)
CREATE EXTERNAL TABLE cloudfront_logs (
  `date` DATE,
  time STRING,
  location STRING,
  bytes BIGINT,
  ip STRING,
  method STRING,
  host STRING,
  uri STRING,
  status INT,
  referrer STRING,
  useragent STRING,
  querystring STRING,
  cookie STRING,
  resulttype STRING,
  requestid STRING,
  hostheader STRING,
  protocol STRING,
  bytes_sent BIGINT,
  timetaken FLOAT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LOCATION 's3://erp-agent-cloudfront-logs/cf-logs/'
TBLPROPERTIES ('skip.header.line.count'='2');

-- Example: Top pages last 7 days
SELECT uri, COUNT(*) as hits
FROM cloudfront_logs
WHERE date >= current_date - interval '7' day
GROUP BY uri
ORDER BY hits DESC
LIMIT 20;

-- Example: Unique visitors by day
SELECT date, COUNT(DISTINCT ip) as unique_visitors
FROM cloudfront_logs
GROUP BY date
ORDER BY date DESC;
```

---

## Cost

- **S3 Standard Logging**: ~FREE (only S3 storage costs, ~$0.023/GB)
- **CloudWatch Metrics**: ~$0.02 per 10,000 requests
- **Estimated total**: < €2/month for typical traffic

---

## Troubleshooting

**No logs appearing?**
- Logs can take 5-15 minutes to appear after traffic
- Ensure there is actual traffic to the site

**Permission errors?**
- Verify AWS CLI is configured: `aws sts get-caller-identity`
- Check you have access to the S3 bucket and CloudWatch

**Date command not working on Linux?**
- Replace `-v-7d` with `-d '7 days ago'` for GNU date
