.PHONY: mirror-image

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