# swiss-ai-hub-backup

Backup and restore orchestration for AI-Hub data services. Runs as an independent Dagster instance (3 containers: gRPC
code server, daemon, webserver) inside the Docker Compose project.

Requires the Docker socket (`/var/run/docker.sock`) to discover and manage platform containers via the
`com.docker.compose.project` label.

Dagster UI: <http://localhost:3004>

Currently a placeholder skeleton. The full backup implementation will be added in a follow-up issue.
