# OpenWebUI with a current CA bundle.
FROM ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.3

# The release predates the eMudhra intermediate CA compromise (2026-10): its system bundle and certifi still trust
# emSign ECC Root CA - G3, and gRPC ships its own root list. Refresh both bundles and point gRPC at the system one.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir certifi==2026.10.23

ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt
