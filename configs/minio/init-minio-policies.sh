#!/bin/sh
set -e

# Wait until MinIO is healthy
until curl -sf http://minio:9000/minio/health/live; do
  echo "Waiting for MinIO..."
  sleep 2
done

# Setup alias for MinIO
mc alias set minio http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"

# Add policy from JSON file
mc admin policy add minio datalakeadmin /policies/oicd-policy.json

# Assign policy to group (OIDC role)
mc admin policy set minio datalakeadmin group=DataLakeAdmin

echo "MinIO policy initialized."