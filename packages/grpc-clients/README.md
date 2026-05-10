# Daifend gRPC client contracts

Canonical Protobuf definitions live in `proto/daifend/v1/`. Generated Python stubs for services ship beside each service (for example `apps/memory-integrity-engine/daifend_grpc/`).

## Generating stubs

```bash
python -m venv .venv-protoc && source .venv-protoc/bin/activate
pip install grpcio-tools 'protobuf>=5.26'
cd /path/to/Daifendplatform
python -m grpc_tools.protoc -I proto \
  --python_out=apps/memory-integrity-engine/daifend_grpc \
  --grpc_python_out=apps/memory-integrity-engine/daifend_grpc \
  proto/daifend/v1/memory.proto
```

## Other languages

Point `protoc` or Buf at `proto/` and publish generated clients from your internal artifact registry. This repository does not vendor Java/Go/TS stubs to avoid drift; CI should fail if `proto/` changes without regenerated Python where required.
