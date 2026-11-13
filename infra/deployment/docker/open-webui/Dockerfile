# Keep the deployed OpenWebUI release and align its client with the browser server.
FROM ghcr.io/bbvch-ai/aihub-core/open-webui:v0.12.5

# After the eMudhra intermediate CA compromise (2026-10), gRPC's own root list still trusts emSign ECC Root CA - G3, so
# gRPC is pointed at the system bundle. v0.12.5 already ships the fixed system bundle and certifi; refreshing both keeps
# a later base from bringing back an older one.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright==1.63.0 certifi==2026.10.23

ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt
