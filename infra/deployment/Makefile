.PHONY: mirror-image build-and-push-postgres-image build-and-push-presidio-analyzer-image build-and-push-playwright-image build-and-push-browser-proxy-image build-and-push-open-terminal-image build-and-push-openwebui-image build-and-push-rclone-image

# Build the project-managed postgres image (pgvector + pg_repack) and push to ghcr.
#
# Unlike `mirror-image`, the source isn't an upstream tag — we build it from
# `docker/postgres/Dockerfile` (FROM pgvector/pgvector:pg17 + apt install
# postgresql-17-repack). pg_repack is required by the maintenance subsystem in
# packages/backup. Re-run this whenever:
#   - the base pgvector tag in the Dockerfile changes (Postgres major bump)
#   - the postgresql-17-repack package needs an upgrade
# After running, non-build stages in compose-config.yml pick up the new image
# automatically via `docker compose pull`.
build-and-push-postgres-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/pgvector-repack:pg17..."
	@docker login ghcr.io
	@docker build \
		-t ghcr.io/bbvch-ai/aihub-core/pgvector-repack:pg17 \
		-f docker/postgres/Dockerfile \
		docker/postgres
	@docker push ghcr.io/bbvch-ai/aihub-core/pgvector-repack:pg17
	@echo "Successfully published pgvector-repack:pg17"

# Build the project-managed Open Terminal image (full sandbox + office/file libs)
# and push to ghcr.
#
# OpenWebUI's code-execution path routes to this sandbox; the upstream image lacks
# reportlab, fpdf2, pdfplumber and cryptography. The full variant (not `-slim`) is required for multi-user
# isolation. The Dockerfile lives at
# `infra/deployment/docker/open-terminal/Dockerfile`. Re-run this whenever the
# pinned base tag or the installed libraries change. After running, non-build
# stages pick up the new image automatically via `docker compose pull`.
build-and-push-open-terminal-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/open-terminal-office:0.11.34-3..."
	@docker login ghcr.io
	@docker build \
		-t ghcr.io/bbvch-ai/aihub-core/open-terminal-office:0.11.34-3 \
		-f docker/open-terminal/Dockerfile \
		docker/open-terminal
	@docker push ghcr.io/bbvch-ai/aihub-core/open-terminal-office:0.11.34-3
	@echo "Successfully published open-terminal-office:0.11.34-3"

# Build the project-managed Presidio analyzer image (Presidio 2.2.364 + GLiNER + spaCy German model, API-key check)
# and push to ghcr. The tag is the one pinned in compose-config.yml (image_tags.presidio_analyzer); bump it with every
# change to `docker/presidio-analyzer/`. The "Build Presidio analyzer image" workflow does the same from CI. The
# recognizer config is mounted, not baked in, so pattern changes need no rebuild.
PRESIDIO_ANALYZER_IMAGE = ghcr.io/bbvch-ai/aihub-core/$(shell awk '/^  presidio_analyzer:/{print $$2}' compose-config.yml)
build-and-push-presidio-analyzer-image:
	@echo "Building $(PRESIDIO_ANALYZER_IMAGE)..."
	@docker login ghcr.io
	@docker build -t $(PRESIDIO_ANALYZER_IMAGE) -f docker/presidio-analyzer/Dockerfile docker/presidio-analyzer
	@docker push $(PRESIDIO_ANALYZER_IMAGE)
	@echo "Successfully published $(PRESIDIO_ANALYZER_IMAGE)"

# Build the project-managed playwright image (Microsoft playwright base + npm
# package + server entrypoint) and push to ghcr.
#
# The Dockerfile lives at `infra/deployment/docker/playwright/Dockerfile`.
# Re-run this whenever the base playwright tag or the npm playwright version
# changes. After running, non-build stages pick up the new image automatically
# via `docker compose pull`.
build-and-push-playwright-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/playwright:v1.63.0-jammy-1..."
	@docker login ghcr.io
	@docker build --platform linux/amd64 \
		-t ghcr.io/bbvch-ai/aihub-core/playwright:v1.63.0-jammy-1 \
		-f docker/playwright/Dockerfile \
		docker/playwright
	@docker push ghcr.io/bbvch-ai/aihub-core/playwright:v1.63.0-jammy-1
	@echo "Successfully published playwright:v1.63.0-jammy-1"

# Build the project-managed browser-proxy image (Squid with our squid.conf and empty
# error pages) and push to ghcr. It is the Playwright browser's only way out of the
# platform and refuses every address that is not public. Re-run whenever the
# Dockerfile, squid.conf or the alpine base changes, bumping the -N suffix here and
# in compose-config.yml.
build-and-push-browser-proxy-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/browser-proxy:7.6-1..."
	@docker login ghcr.io
	@docker build --platform linux/amd64 \
		-t ghcr.io/bbvch-ai/aihub-core/browser-proxy:7.6-1 \
		-f docker/browser-proxy/Dockerfile \
		docker/browser-proxy
	@docker push ghcr.io/bbvch-ai/aihub-core/browser-proxy:7.6-1
	@echo "Successfully published browser-proxy:7.6-1"

# Keep OpenWebUI's Python client compatible with the project-managed browser server.
# Publish both images before deploying their matching tags from compose-config.yml.
build-and-push-openwebui-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.4-playwright1.63.0-1..."
	@docker login ghcr.io
	@docker build --platform linux/amd64 \
		-t ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.4-playwright1.63.0-1 \
		-f docker/open-webui/Dockerfile \
		docker/open-webui
	@docker push ghcr.io/bbvch-ai/aihub-core/open-webui:v0.11.4-playwright1.63.0-1
	@echo "Successfully published open-webui:v0.11.4-playwright1.63.0-1"

# Build the project-managed rclone image (upstream rclone + a refreshed CA bundle) and push to ghcr.
# The Dockerfile lives at `infra/deployment/docker/rclone/Dockerfile`. Re-run this whenever the base rclone tag changes.
build-and-push-rclone-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/rclone:1.71.2-1..."
	@docker login ghcr.io
	@docker build --platform linux/amd64 \
		-t ghcr.io/bbvch-ai/aihub-core/rclone:1.71.2-1 \
		-f docker/rclone/Dockerfile \
		docker/rclone
	@docker push ghcr.io/bbvch-ai/aihub-core/rclone:1.71.2-1
	@echo "Successfully published rclone:1.71.2-1"

# Mirror an image from source to target
# Usage: make mirror-image SOURCE=source/image:tag TARGET=target/image:tag
# Example: make mirror-image SOURCE=ghcr.io/open-webui/open-webui:v0.6.10 TARGET=ghcr.io/bbvch-ai/aihub-core/open-webui:v0.6.10
mirror-image:
	@if [ -z "$(SOURCE)" ] || [ -z "$(TARGET)" ]; then \
		echo "Error: SOURCE and TARGET parameters are required"; \
		echo "Usage: make mirror-image SOURCE=source/image:tag TARGET=target/image:tag"; \
		exit 1; \
	fi
	@echo "Mirroring $(SOURCE) to $(TARGET)..."
	@docker login ghcr.io
	@docker pull $(SOURCE)
	@docker tag $(SOURCE) $(TARGET)
	@docker push $(TARGET)
	@echo "Successfully mirrored $(SOURCE) to $(TARGET)"

mirror-image-win:
	@powershell -Command "if (-not '$(SOURCE)' -or -not '$(TARGET)') { Write-Host 'Error: SOURCE and TARGET parameters are required' -ForegroundColor Red; Write-Host 'Usage: make mirror-image SOURCE=source/image:tag TARGET=target/image:tag' -ForegroundColor Yellow; exit 1 }"
	@echo Mirroring $(SOURCE) to $(TARGET)...
	@docker login ghcr.io
	@docker pull $(SOURCE)
	@docker tag $(SOURCE) $(TARGET)
	@docker push $(TARGET)
	@echo Successfully mirrored $(SOURCE) to $(TARGET)
