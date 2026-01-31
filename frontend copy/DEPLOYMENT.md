# ERP Agent Website Deployment Guide

## Overview
This guide covers deploying the ERP Agent React website to AWS S3 with CloudFront CDN and custom domain setup.

## Architecture
- **S3 Bucket**: Static website hosting (`erp-agent.com`)
- **CloudFront**: CDN distribution with SSL certificate
- **Route 53**: DNS management for custom domain
- **ACM**: SSL/TLS certificate management

## Prerequisites
- AWS CLI installed and configured
- Node.js and npm installed
- Domain registered and Route 53 hosted zone configured

## Initial Setup (One-time)

### 1. Build the Application
```bash
cd /path/to/website-project
npm run build
```

### 2. Create S3 Bucket
```bash
# Create bucket
aws s3 mb s3://erp-agent.com --region eu-central-1

# Enable static website hosting
aws s3 website s3://erp-agent.com --index-document index.html --error-document index.html

# Disable block public access
aws s3api put-public-access-block --bucket erp-agent.com \
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

### 3. Set Bucket Policy
Create `bucket-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::erp-agent.com/*"
        }
    ]
}
```

Apply the policy:
```bash
aws s3api put-bucket-policy --bucket erp-agent.com --policy file://bucket-policy.json
```

### 4. Request SSL Certificate
```bash
# Request certificate (must be in us-east-1 for CloudFront)
aws acm request-certificate \
  --domain-name erp-agent.com \
  --subject-alternative-names www.erp-agent.com \
  --validation-method DNS \
  --region us-east-1
```

### 5. Add DNS Validation Records
Get validation records:
```bash
aws acm describe-certificate --certificate-arn YOUR_CERT_ARN --region us-east-1
```

Add CNAME records to Route 53 for validation.

### 6. Create CloudFront Distribution
Create `cloudfront-config.json`:
```json
{
    "CallerReference": "erp-agent-YYYY-MM-DD",
    "Aliases": {
        "Quantity": 2,
        "Items": ["erp-agent.com", "www.erp-agent.com"]
    },
    "DefaultRootObject": "index.html",
    "Comment": "ERP Agent website CloudFront distribution",
    "Enabled": true,
    "Origins": {
        "Quantity": 1,
        "Items": [{
            "Id": "S3-erp-agent.com",
            "DomainName": "erp-agent.com.s3-website.eu-central-1.amazonaws.com",
            "CustomOriginConfig": {
                "HTTPPort": 80,
                "HTTPSPort": 443,
                "OriginProtocolPolicy": "http-only"
            }
        }]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-erp-agent.com",
        "ViewerProtocolPolicy": "redirect-to-https",
        "MinTTL": 0,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {"Forward": "none"}
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        }
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 403,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": "YOUR_CERT_ARN",
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "PriceClass": "PriceClass_100"
}
```

Create distribution:
```bash
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

### 7. Point Domain to CloudFront
Create `domain-records.json`:
```json
{
    "Comment": "Point domain to CloudFront distribution",
    "Changes": [
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "erp-agent.com",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "YOUR_CLOUDFRONT_DOMAIN.cloudfront.net",
                    "EvaluateTargetHealth": false,
                    "HostedZoneId": "Z2FDTNDATAQYW2"
                }
            }
        },
        {
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "www.erp-agent.com",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "YOUR_CLOUDFRONT_DOMAIN.cloudfront.net",
                    "EvaluateTargetHealth": false,
                    "HostedZoneId": "Z2FDTNDATAQYW2"
                }
            }
        }
    ]
}
```

Apply DNS records:
```bash
aws route53 change-resource-record-sets --hosted-zone-id YOUR_ZONE_ID --change-batch file://domain-records.json
```

## Regular Deployment Updates

### Quick Deploy Script
Create `deploy.sh`:
```bash
#!/bin/bash
set -e

echo "Building application..."
npm run build

echo "Syncing to S3..."
aws s3 sync build/ s3://erp-agent.com --delete

echo "Creating CloudFront invalidation..."
DISTRIBUTION_ID="E53DMMKWU8AJU"
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "Deployment complete!"
echo "Website: https://erp-agent.com"
```

Make it executable:
```bash
chmod +x deploy.sh
```

### Manual Deployment Steps
1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Upload to S3**:
   ```bash
   aws s3 sync build/ s3://erp-agent.com --delete
   ```

3. **Invalidate CloudFront cache** (optional, for immediate updates):
   ```bash
   aws cloudfront create-invalidation --distribution-id E53DMMKWU8AJU --paths "/*"
   ```

## Current Configuration

### AWS Resources
- **S3 Bucket**: `erp-agent.com` (eu-central-1)
- **CloudFront Distribution**: `E53DMMKWU8AJU`
- **Domain**: `d2sx9a6awls2t2.cloudfront.net`
- **SSL Certificate**: `arn:aws:acm:us-east-1:039612872461:certificate/108cba20-b6e2-451d-9815-347e3a120ce2`
- **Route 53 Zone**: `Z053476613B6ZMCZ53590`

### DNS Records (Route 53)
- **A Records**: erp-agent.com & www.erp-agent.com → CloudFront distribution
- **MX Record**: erp-agent.com → 1 SMTP.GOOGLE.COM (for Gmail)
- **TXT Record**: google-site-verification=nR3azBOFak9xM-NU_uoOfpcLQ4qC9egL3L_u2YR-eGg
- **SSL Validation**: CNAME records for certificate validation

### URLs
- **Production**: https://erp-agent.com
- **WWW**: https://www.erp-agent.com
- **S3 Direct**: http://erp-agent.com.s3-website.eu-central-1.amazonaws.com
- **CloudFront**: https://d2sx9a6awls2t2.cloudfront.net
- **Custom Email**: lauri@erp-agent.com (configured with Gmail)

## Troubleshooting

### Common Issues
1. **Certificate validation fails**: Ensure DNS validation records are added to Route 53
2. **CloudFront shows CloudFront error**: Check S3 bucket policy and public access settings
3. **React routing issues**: Verify custom error responses are configured (403/404 → index.html)
4. **Changes not visible**: Create CloudFront invalidation or wait for cache expiration

### Cache Management
- **CloudFront cache duration**: 24 hours (86400 seconds)
- **Force cache refresh**: Create invalidation for `/*`
- **S3 website endpoint**: No caching, immediate updates

### Monitoring
- Check CloudFront metrics in AWS Console
- Monitor S3 access logs if enabled
- Use browser dev tools to verify HTTPS and proper routing

## Security Notes
- S3 bucket has public read access for static hosting
- SSL/TLS certificate auto-renews through ACM
- CloudFront enforces HTTPS redirects
- No server-side processing, static files only

## Cost Optimization
- Using PriceClass_100 (lowest cost tier)
- S3 Standard storage class
- CloudFront configured for optimal caching
- Route 53 charges apply for DNS queries

---

**Last Updated**: September 16, 2025
**Distribution ID**: E53DMMKWU8AJU
**Certificate ARN**: arn:aws:acm:us-east-1:039612872461:certificate/108cba20-b6e2-451d-9815-347e3a120ce2

## Recent Updates
- **Sept 16, 2025**: Added Gmail custom email setup (lauri@erp-agent.com)
- **Sept 16, 2025**: Updated favicon to use e-logo.png
- **Sept 14, 2025**: Added comprehensive SEO optimization with meta tags and structured data
- **Sept 14, 2025**: Fixed missing integration icons by moving assets to public folder
- **Sept 14, 2025**: Initial deployment with CloudFront, SSL, and custom domain