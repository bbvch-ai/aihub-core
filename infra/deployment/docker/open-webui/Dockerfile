# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM node:22-alpine3.20 AS frontend

RUN apk add --no-cache git
WORKDIR /upstream
COPY mods/compatibility.json /opt/aihub/compatibility.json
RUN git init . && \
    git remote add origin https://github.com/open-webui/open-webui.git && \
    git fetch --depth=1 origin "$(node -p "require('/opt/aihub/compatibility.json').source_commit")" && \
    git checkout --detach FETCH_HEAD && \
    test "$(git rev-parse HEAD)" = "$(node -p "require('/opt/aihub/compatibility.json').source_commit")"

ENV CYPRESS_INSTALL_BINARY=0 NODE_OPTIONS=--max-old-space-size=8192
RUN --mount=type=cache,target=/root/.npm npm ci --force --no-audit --no-fund
COPY mods /upstream/aihub-mods
COPY vite.aihub.config.ts /upstream/vite.aihub.config.ts
RUN node --conditions=browser --test aihub-mods/tests/*.test.mjs
RUN node aihub-mods/build_compiler.mjs /opt/aihub/compiler-cli.mjs
RUN node aihub-mods/install_client_hook.mjs /upstream
RUN npm run pyodide:fetch && \
    APP_BUILD_HASH="$(git rev-parse --short HEAD)-aihub-$(find aihub-mods -type f -exec sha256sum {} \; | sort | sha256sum | cut -c1-12)" \
    ./node_modules/.bin/vite build --config vite.aihub.config.ts

# Keep the deployed backend release and align its client with the browser server.
FROM ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.4

# The release predates the eMudhra intermediate CA compromise (2026-10): its system bundle and certifi still trust
# emSign ECC Root CA - G3, and gRPC ships its own root list. Refresh both bundles and point gRPC at the system one.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright==1.63.0 certifi==2026.10.23

ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt

RUN rm -rf /app/build
COPY --from=frontend /upstream/build /app/build
COPY --from=frontend /opt/aihub/compiler-cli.mjs /opt/aihub/compiler-cli.mjs
COPY mods/backend /app/backend/aihub_mods
COPY mods/compatibility.json /app/backend/aihub_mods/compatibility.json
RUN python -c 'import json, sys; from pathlib import Path; expected = json.loads(Path("/app/backend/aihub_mods/compatibility.json").read_text()); assert json.loads(Path("/app/package.json").read_text())["version"] == expected["openwebui"], "Backend image does not match compatibility.json"; assert sys.version_info[:2] == tuple(map(int, expected["python"].split("."))), "Python does not match compatibility.json"'
RUN python -m aihub_mods.patch_startup /app/backend/start.sh

COPY mods/tests /opt/aihub-mod-tests
RUN WEBUI_AUTH=false OFFLINE_MODE=true HF_HUB_OFFLINE=1 DATA_DIR=/tmp/aihub-mod-tests \
    python -m unittest discover -s /opt/aihub-mod-tests -p 'test_*.py'
RUN PYTHONPATH=/app/backend OFFLINE_MODE=true HF_HUB_OFFLINE=1 DATA_DIR=/tmp/aihub-native-acceptance \
    WEBUI_SECRET_KEY=disposable-native-acceptance-secret-at-least-32 \
    AIHUB_BASE_URL=http://hub AIHUB_SUPERUSER_API_KEY=disposable-service-token \
    OPEN_WEBUI_SIGNING_SECRET=disposable-signing-secret \
    python /opt/aihub-mod-tests/native_backend_acceptance.py && \
    rm -rf /tmp/aihub-mod-tests /tmp/aihub-native-acceptance /opt/aihub-mod-tests
