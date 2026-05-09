#!/bin/sh
set -e
export PYTHONPATH="${PYTHONPATH:-}:/app/daifend_grpc"
uvicorn app.main:app --host 0.0.0.0 --port 8003 &
exec python -m app.grpc_server
