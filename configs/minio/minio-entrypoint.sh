#!/bin/sh
set -e

# Start MinIO in background
minio server /minio-data --console-address ":9001" &
MINIO_PID=$!

# Wait for MinIO to be ready
echo "Waiting for MinIO to start..."
until curl -f http://localhost:9000/minio/health/live 2>/dev/null; do
  sleep 1
done

# Create buckets
if [ -n "$MINIO_DEFAULT_BUCKETS" ]; then
  mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

  IFS=',' read -ra BUCKETS <<< "$MINIO_DEFAULT_BUCKETS"
  for bucket in "${BUCKETS[@]}"; do
    echo "Creating bucket: $bucket"
    mc mb local/$bucket --ignore-existing
    # Optionally set bucket policy
    mc policy set public local/$bucket
  done
  echo "Bucket creation completed"
fi

# Bring MinIO to foreground
echo "MinIO setup complete, running in foreground..."
wait $MINIO_PID