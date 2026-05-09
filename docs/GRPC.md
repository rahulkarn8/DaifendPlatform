# gRPC (internal engines)

REST remains the **edge contract** via the API gateway. gRPC is the recommended **service-to-service** transport for high-throughput analyze calls and streaming audits.

## Proto

Definitions live under `proto/daifend/v1/`. Example: `memory.proto` for the Memory Integrity engine.

## Generate Python stubs

```bash
python3 -m pip install grpcio-tools
python3 -m grpc_tools.protoc \
  -I proto \
  --python_out=packages/daifend-grpc/gen \
  --grpc_python_out=packages/daifend-grpc/gen \
  proto/daifend/v1/memory.proto
```

Then implement `MemoryIntegrityServicer` in `apps/memory-integrity-engine` and run a second listener (e.g. `:50051`) or use a sidecar.

## Generate Go stubs

Use `buf` or `protoc` with `protoc-gen-go` and `protoc-gen-go-grpc` — align `go_package` in protos with your module path.

## Response shape

`AnalyzeResponse` includes `prompt_injection_signals` (sample index, score, reasons) alongside trust metrics — keep protos in sync with REST.

## mTLS

In production, terminate mTLS at the mesh (Linkerd/Istio) or use **SPIFFE** identities between engine pods; keep JWT/OIDC at the gateway only. The Python server listens on **`:50051` insecure** unless you wrap it with a sidecar or add `grpc.ssl_server_credentials` in `grpc_server.py`.
