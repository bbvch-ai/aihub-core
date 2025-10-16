#!/bin/sh
set -e

# SeaweedFS S3 credentials
SEAWEEDFS_S3_USER=${SEAWEEDFS_S3_USER}
SEAWEEDFS_S3_PASSWORD=${SEAWEEDFS_S3_PASSWORD}

S3_PORT=${S3_PORT:-9000}
S3_FILER=${S3_FILER:-seaweedfs-filer:8888}
S3_BIND_IP=${S3_BIND_IP:-0.0.0.0}
S3_ALLOW_EMPTY_FOLDER=${S3_ALLOW_EMPTY_FOLDER:-true}

# Generate s3.json dynamically from environment variables
cat > /tmp/s3.json <<EOF
{
  "identities": [
    {
      "name": "admin",
      "credentials": [
        {
          "accessKey": "${SEAWEEDFS_S3_USER}",
          "secretKey": "${SEAWEEDFS_S3_PASSWORD}"
        }
      ],
      "actions": [
        "Admin",
        "Read",
        "ReadAcp",
        "Write",
        "WriteAcp",
        "List",
        "Tagging"
      ]
    },
    {
      "name": "anonymous",
      "actions": [
        "Read"
      ]
    }
  ]
}
EOF

echo "Starting SeaweedFS S3 Gateway"
echo "  - Port: ${S3_PORT}"
echo "  - Filer: ${S3_FILER}"
echo "  - User: ${SEAWEEDFS_S3_USER}"

S3_CMD="weed s3 \
  -filer=${S3_FILER} \
  -port=${S3_PORT} \
  -ip.bind=${S3_BIND_IP} \
  -config=/tmp/s3.json \
  -allowEmptyFolder=${S3_ALLOW_EMPTY_FOLDER}"

exec ${S3_CMD} "$@"