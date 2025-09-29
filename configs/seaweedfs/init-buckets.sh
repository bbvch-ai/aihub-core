#!/bin/sh
set -e

echo "Waiting for S3 to be ready..."
sleep 5

ENDPOINT=${S3_ENDPOINT:-"http://seaweedfs-s3:9000"}
BUCKETS=${DEFAULT_BUCKETS:-"open-webui milvus playground"}

echo "Creating buckets..."
for bucket in $BUCKETS; do
  if aws --endpoint-url $ENDPOINT s3 ls s3://$bucket 2>/dev/null; then
    echo "Bucket $bucket already exists"
  else
    aws --endpoint-url $ENDPOINT s3 mb s3://$bucket
    echo "Created bucket: $bucket"
  fi
done

# Set CORS for each bucket
echo "Setting CORS configuration..."
cat > /tmp/cors.json <<EOF
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "POST", "DELETE", "GET", "HEAD"],
    "MaxAgeSeconds": 3000,
    "ExposeHeaders": ["ETag", "x-amz-request-id", "x-amz-version-id"]
  }]
}
EOF

for bucket in $BUCKETS; do
  aws --endpoint-url $ENDPOINT s3api put-bucket-cors \
    --bucket $bucket --cors-configuration file:///tmp/cors.json || true
  echo "CORS configured for bucket: $bucket"
done

echo "Bucket initialization complete!"