#!/bin/sh
set -e

# Copy workspace.yaml into DAGSTER_HOME so both daemon and webserver find it.
# The volume mount for /dagster_home (used for SQLite run storage) replaces the
# directory contents, so the file baked into the image at build time is lost.
cp -f /etc/dagster/workspace.yaml "$DAGSTER_HOME/workspace.yaml"

# Start both Dagster processes
dagster-daemon run -w "$DAGSTER_HOME/workspace.yaml" &
DAEMON_PID=$!

dagster-webserver -h 0.0.0.0 -p 3000 -w "$DAGSTER_HOME/workspace.yaml" &
WEBSERVER_PID=$!

trap 'kill "$DAEMON_PID" "$WEBSERVER_PID" 2>/dev/null; wait; exit 0' TERM INT

# Monitor both processes — exit if either dies (Docker restart policy will recover)
while kill -0 "$DAEMON_PID" 2>/dev/null && kill -0 "$WEBSERVER_PID" 2>/dev/null; do
    sleep 5
done

echo "Process exited unexpectedly, shutting down"
kill "$DAEMON_PID" "$WEBSERVER_PID" 2>/dev/null || true
wait
exit 1
