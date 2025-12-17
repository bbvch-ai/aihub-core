.PHONY: sync help cleanup download-models

# Default target
help:
	@echo "Available targets:"
	@echo "  make cleanup         - Stop and remove existing containers on server"
	@echo "  make sync            - Sync deployment files to test-gpu-instance server"
	@echo "  make download-models - Download Docling models to the volume on server"

# Sync files to remote server
sync:
	@echo "Syncing files to test-gpu-instance..."
	rsync -avz --progress \
		--include='docker-compose.yml' \
		--include='.env' \
		--include='traefik/' \
		--include='traefik/**' \
		--exclude='*' \
		./ test-gpu-instance:~/docling-deployment/
	@echo "✅ Sync complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  ssh test-gpu-instance"
	@echo "  cd ~/docling-deployment"
	@echo "  docker compose up -d"

# Stop and remove existing containers on server
cleanup:
	@echo "Cleaning up existing containers on test-gpu-instance..."
	ssh test-gpu-instance 'sudo docker ps -a --format "{{.Names}}" | xargs -r sudo docker stop'
	ssh test-gpu-instance 'sudo docker ps -a --format "{{.Names}}" | xargs -r sudo docker rm'
	@echo "✅ Cleanup complete!"
	@echo ""
	@echo "All containers stopped and removed. Auto-restart disabled."

# Download Docling models to the volume on server
# This runs a one-off container to download all models into the docling-models volume
download-models:
	@echo "Downloading Docling models on test-gpu-instance..."
	ssh test-gpu-instance 'cd ~/docling-deployment && sudo docker run --rm \
		-v docling-deployment_docling-models:/models \
		quay.io/docling-project/docling-serve-cu128:v1.9.0 \
		docling-tools models download --all -o /models'
	@echo "✅ Models downloaded successfully!"
	@echo ""
	@echo "Restart docling-serve to use the new models:"
	@echo "  ssh test-gpu-instance 'cd ~/docling-deployment && sudo docker compose restart docling-serve'"
