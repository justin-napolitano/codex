# Interfaces and process boundaries

## Codex has more than one protocol

The repository contains both an internal agent protocol and external client
protocols. Do not assume the terminal UI’s in-process messages are a stable
public API.

| Boundary | Contract | Use |
| --- | --- | --- |
| Core ↔ Rust surface | `codex-rs/protocol/src/protocol.rs` | Internal `Op` submissions and `EventMsg` events. |
| IDE/app ↔ app-server | `app-server-protocol/src/protocol/v2/` | Current JSON-RPC API for rich local clients. |
| MCP client ↔ Codex MCP server | MCP over stdio | Experimental interface to control/use a local Codex engine. |
| Core ↔ model provider | Responses/model-client types | Streaming model input/output, including function/custom tool calls. |
| Core ↔ execution host | exec/exec-server protocol | Allows tool execution to live in a separate environment/OS. |

## App-server: the integration boundary

See the complete client/server exchange:
[app-server RPC flow diagram](diagrams/05-app-server-rpc-flow.mmd).

`codex app-server` is a local JSON-RPC 2.0 server used by richer clients such
as IDE integrations. Its detailed contract is in
`codex-rs/app-server/README.md`.

Supported transports include JSON lines over standard I/O, websocket in an
experimental mode, and Unix-domain-socket control paths. A client must perform
an initialization handshake before using thread/turn methods.

The normal control flow is:

```text
client                         app-server                    core session
  │ initialize                    │                              │
  ├──────────────────────────────►│ validate/initialize           │
  │ initialized notification      │                              │
  ├──────────────────────────────►│                              │
  │ thread/start or resume        │                              │
  ├──────────────────────────────►│ create/load                   │
  │ turn/start                    │                              │
  ├──────────────────────────────►│ submit user turn ────────────►│
  │                                │◄────── stream core events ───┤
  │◄── item and turn notifications─┤                              │
  │                                │── approval request ─────────►│
  │ approval response              │                              │
  ├──────────────────────────────►│ ─────────────────────────────►│
```

The app-server translates rather than duplicates the agent. Its request
processors cover thread lifecycle, turns, approvals, configuration, model
catalogs, MCP refresh, file/process operations, and other client needs.

The connection-level `initialize` handshake is intentional. It lets the server
know client metadata/capabilities before it accepts work, and prevents an
otherwise valid thread or turn request from arriving on an uninitialized
connection.

## The v2 API is the forward path

The contributor rules state that active app-server API development belongs in
v2. It uses resource-style method names such as `thread/start` and
`turn/start`, with typed parameter/response/notification objects. Wire fields
are ordinarily camelCase; config payloads intentionally mirror `config.toml`
with snake_case.

For a new integration, work from the v2 definitions in:

```text
codex-rs/app-server-protocol/src/protocol/v2/thread.rs
codex-rs/app-server-protocol/src/protocol/v2/turn.rs
codex-rs/app-server-protocol/src/protocol/v2/item.rs
codex-rs/app-server-protocol/src/protocol/v2/notification.rs
```

The old protocol documentation is still useful for concepts, but it explicitly
warns that code may differ from the v1 description. Treat v1 as historical
mental-model material, not a contract for a new client.

## Approvals cross the boundary in the opposite direction

Most calls travel client → server. Approvals are different: the runtime needs
the client to ask the user. The server therefore issues a JSON-RPC request to
the client—for example, command or patch approval—and waits for the client’s
allow/deny response.

That requires a bidirectional protocol and durable correlation IDs. A client
that only fires `turn/start` requests and ignores server-initiated requests is
not a complete Codex client.

## MCP: two related but different ideas

MCP appears in two roles.

1. **Codex as an MCP client.** Codex can connect to configured MCP servers and
   expose their tools/resources to the model. Those tool calls still flow
   through Codex’s local tool lifecycle and policy boundary.
2. **Codex as an MCP server.** `codex mcp-server` exposes a local Codex engine
   to an MCP client. This interface is documented in
   `codex-rs/docs/codex_mcp_interface.md` and is explicitly experimental.

The direction matters. “Use MCP” does not automatically mean that an external
tool has the same permissions as Codex or that Codex itself is being remotely
controlled. Ask which side is the MCP client, which is the server, and where
the trust/policy boundary is.

## What is stable enough to build against?

For a new rich client, use app-server v2 types and generated schemas. The core
`Op`/`EventMsg` protocol is a Rust implementation interface and evolves with
the engine. The MCP server is useful for experimentation and interoperability,
but its own documentation marks it experimental. This distinction prevents a
common integration error: binding a product client to the convenient internal
event shapes instead of the versioned external contract.

## Separate execution hosts

Codex supports architectures in which the UI/app-server and command-execution
server run on different operating systems or hosts. That is why execution has
its own `exec-server` and protocol crates. A durable agent system should not
assume that the machine rendering the UI is necessarily the machine with the
repository, credentials, sandbox, or shell.

## Designing an interface for your own agent

- Make your model loop an internal service with typed input/events.
- Put stable external APIs at an explicit adapter boundary.
- Stream granular events; don’t make clients scrape logs or infer state from
  text.
- Support server-to-client approval/question requests, not only HTTP-style
  request/response.
- Generate schemas from shared types where possible.
- Version public protocols separately from internal data structures.
