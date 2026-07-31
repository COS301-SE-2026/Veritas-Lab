#!/bin/sh
set -e

if ! python /app/init_db.py; then
	echo "Warning: init_db.py failed; starting backend anyway"
fi
exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000