package daifend.gateway

# API gateway authorization. POST /v1/data/daifend/gateway/allow
# input: { tenantId, method, path[], sub, permissions[] }

default allow = false

allow {
  count(input.permissions) > 0
}

allow {
  input.sub == "internal"
}
