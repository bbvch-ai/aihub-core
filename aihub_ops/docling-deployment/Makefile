.PHONY: sync help cleanup

# Default target
help:
	@echo "Available targets:"
	@echo "  make cleanup - Stop and remove existing containers on server"
	@echo "  make sync    - Sync deployment files to test-gpu-instance server"

# Sync files to remote server
sync:
	@echo "Syncing files to test-gpu-instance..."
	rsync -avz --progress \
		--include='docker-compose.yml' \
		--include='.env' \
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

# Stop and remove existing containers on server
cleanup:
	@echo "Cleaning up existing containers on test-gpu-instance..."
	ssh test-gpu-instance 'sudo docker ps -a --format "{{.Names}}" | xargs -r sudo docker stop'
	ssh test-gpu-instance 'sudo docker ps -a --format "{{.Names}}" | xargs -r sudo docker rm'
	@echo "✅ Cleanup complete!"
	@echo ""
	@echo "All containers stopped and removed. Auto-restart disabled."
