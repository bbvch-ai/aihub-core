# Keep the deployed OpenWebUI release and align its client with the browser server.
FROM ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.4

# The release predates the eMudhra intermediate CA compromise (2026-10): its system bundle and certifi still trust
# emSign ECC Root CA - G3, and gRPC ships its own root list. Refresh both bundles and point gRPC at the system one.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright==1.63.0 certifi==2026.10.23

ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt

# OpenWebUI serves its HTML without Cache-Control, so browsers keep booting the previous frontend after an upgrade.
# The patch fails the build when a new release moves the code it edits.
COPY patch_spa_cache_control.py /tmp/patch_spa_cache_control.py
RUN python /tmp/patch_spa_cache_control.py && rm /tmp/patch_spa_cache_control.py
