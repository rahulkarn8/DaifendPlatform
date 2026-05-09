package daifend.agent

# Central policy for agent tool calls. Fed by agent-runtime-engine after local checks.
# POST /v1/data/daifend/agent/allow  body: {"input": {...}}

default allow = false

dangerous_tools = {"run_shell", "execute_code", "http_request"}

allow {
  count(input.local_violations) == 0
  not dangerous_tools[input.tool_name]
}
