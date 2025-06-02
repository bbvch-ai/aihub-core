DAGSTER_HOME_DIR := $(HOME)/.dagster_home

dagster-home:
	@echo "Ensure dagster home exists..."
	mkdir -p "$(DAGSTER_HOME_DIR)" && cp -r . "$(DAGSTER_HOME_DIR)"

clear-dagster-home:
	@echo "Clearing dagster home"
	rm -f "$(DAGSTER_HOME_DIR)"

dagster-code-server: dagster-home
	@echo "Running code server for rag pipeline..."
	poetry run dagster api grpc -m default_rag_pipeline -h 0.0.0.0 -p 4000 --log-level INFO

dagster-daemon: dagster-home
	@echo "Running dagster daemon..."
	poetry run dagster-daemon run -w workspace.yaml --log-level INFO

dagster-webserver: dagster-home
	@echo "Running dagster webserver..."
	poetry run dagster-webserver -w workspace.yaml -h 0.0.0.0 -p 3000 --log-level INFO

dagster-worker-1: dagster-home
	@echo "Running dagster worker..."
	export DAGSTER_HOME="$(DAGSTER_HOME_DIR)" && poetry run -- dagster-celery worker start --app dagster_celery.app -y celery.yaml --loglevel INFO -- --concurrency 2

dagster-worker-2: dagster-home
	@echo "Running dagster worker..."
	export DAGSTER_HOME="$(DAGSTER_HOME_DIR)" && poetry run -- dagster-celery worker start --app dagster_celery.app -y celery.yaml --loglevel INFO -- --concurrency 2
