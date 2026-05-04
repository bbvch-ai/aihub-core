.PHONY: mirror-image build-and-push-postgres-image build-and-push-playwright-image

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

# Build the project-managed playwright image (Microsoft playwright base + npm
# package + server entrypoint) and push to ghcr.
#
# The Dockerfile lives at `infra/deployment/docker/playwright/Dockerfile`.
# Re-run this whenever the base playwright tag or the npm playwright version
# changes. After running, non-build stages pick up the new image automatically
# via `docker compose pull`.
build-and-push-playwright-image:
	@echo "Building ghcr.io/bbvch-ai/aihub-core/playwright:v1.58.0-jammy..."
	@docker login ghcr.io
	@docker build \
		-t ghcr.io/bbvch-ai/aihub-core/playwright:v1.58.0-jammy \
		-f docker/playwright/Dockerfile \
		docker/playwright
	@docker push ghcr.io/bbvch-ai/aihub-core/playwright:v1.58.0-jammy
	@echo "Successfully published playwright:v1.58.0-jammy"

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