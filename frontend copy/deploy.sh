#!/bin/bash
set -e

echo "🚀 Starting ERP Agent deployment..."

echo "📦 Building application..."
npm run build

echo "☁️  Syncing to S3..."
aws s3 sync build/ s3://erp-agent.com --delete

echo "🔄 Creating CloudFront invalidation..."
DISTRIBUTION_ID="E53DMMKWU8AJU"
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "✅ Deployment complete!"
echo "🌐 Website: https://erp-agent.com"
echo "📊 CloudFront: https://d2sx9a6awls2t2.cloudfront.net"