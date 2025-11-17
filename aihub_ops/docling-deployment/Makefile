.PHONY: sync help

# Default target
help:
	@echo "Available targets:"
	@echo "  make sync    - Sync deployment files to test-gpu-instance server"

# Sync files to remote server
sync:
	@echo "Syncing files to test-gpu-instance..."
	rsync -avz --progress \
		--include='docker-compose.yml' \
		--include='.env' \
		--include='README.md' \
		--include='traefik/' \
		--include='traefik/**' \
		--include='litellm/' \
		--include='litellm/**' \
		--exclude='*' \
		./ test-gpu-instance:~/docling-deployment/
	@echo "✅ Sync complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  ssh test-gpu-instance"
	@echo "  cd ~/docling-deployment"
	@echo "  docker compose up -d"
