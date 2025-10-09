#!/bin/sh
set -e

echo "Waiting for S3 to be ready..."
sleep 5

ENDPOINT=${S3_ENDPOINT:-"http://seaweedfs-s3:9000"}
BUCKETS=${DEFAULT_BUCKETS:-"open-webui milvus"}

echo "Creating buckets..."
for bucket in $BUCKETS; do
  if aws --endpoint-url $ENDPOINT s3 ls s3://$bucket 2>/dev/null; then
    echo "Bucket $bucket already exists"
  else
    aws --endpoint-url $ENDPOINT s3 mb s3://$bucket
    echo "Created bucket: $bucket"
  fi
done

echo "Bucket initialization complete!"