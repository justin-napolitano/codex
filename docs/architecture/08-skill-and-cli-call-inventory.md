# Skill and CLI call inventory

This page inventories what happens when Codex discovers, selects, reads, and
uses a skill during a turn. It also separates the host commands a skill script
can launch from Codex's internal skill APIs. A skill is instruction/data input;
it is not itself a privileged executor.

The inventory is evidence-linked. Every call has a stable ID, a source link,
claim links, and evidence IDs. The machine-readable version and the complete
adversarial review are in the
[skill-call research pass](audit/skill-call-inventory/README.md).
For human navigation, use the [clickable claim ledger](audit/skill-call-inventory/claim-ledger.md)
and [clickable source/evidence index](audit/skill-call-inventory/source-audit.md).

## Read the loop

```text
discover roots → load/validate → cache snapshot → expose catalog metadata
       │                                      │
       ├─ explicit user mention ─────────────┤
       ├─ implicit script/SKILL.md detection ─┤
       └─ model skills.list/read tools ───────┘
                         │
                         ▼
              read SKILL.md/resource
                         │
                         ▼
              inject selected instructions
                         │
                         ▼
             model proposes a tool/CLI call
                         │
                         ▼
          policy + sandbox + executor boundary
                         │
                         ▼
               correlated result + telemetry
```

The arrows describe a family of paths, not one mandatory sequence. An explicit
skill mention can read a skill directly; an implicit invocation can be emitted
after a command is already being considered; orchestrator skills can be listed
and read through model-visible `skills.list`/`skills.read` tools.

## Clickable call inventory

Each heading is an anchor used by the JSON inventory and the diagram. The
`source` link goes to the implementation or test; `claim` goes to the reviewed
claim; `evidence` goes to the exact evidence record.

### SKILL-DISC-001 — Resolve skill roots

**Phase:** discovery · **Kind:** internal function · **Model-visible:** no

`SkillsService::skill_roots_for_config`, `snapshot_for_config`, and the loader
derive roots from cwd, config layers, plugin roots, extra roots, bundled-skill
settings, and filesystem authority. The result is a set of candidate roots,
not yet model instructions.

[source](../../codex-rs/core-skills/src/service.rs#L150) · [claim SK-CLAIM-001](audit/skill-call-inventory/claim-ledger.json#sk-claim-001) · [evidence E-SK-001](audit/skill-call-inventory/source-audit.json#e-sk-001)

### SKILL-DISC-002 — Load and cache a skill snapshot

**Phase:** discovery · **Kind:** internal function · **Model-visible:** no

`snapshot_for_config`/`snapshot_for_cwd` load roots into a `HostSkillsSnapshot`.
The cache is keyed by cwd or skill-relevant configuration; a snapshot contains
metadata, errors, filesystem authority, and indexes used later for invocation.

[source](../../codex-rs/core-skills/src/service.rs#L126) · [claim SK-CLAIM-002](audit/skill-call-inventory/claim-ledger.json#sk-claim-002) · [evidence E-SK-002](audit/skill-call-inventory/source-audit.json#e-sk-002)

### SKILL-DISC-003 — Discover and validate `SKILL.md`

**Phase:** discovery · **Kind:** internal loader · **Model-visible:** metadata only

`load_skills_from_roots` and `load_skill_root` scan skill roots, parse YAML
frontmatter/metadata, enforce name and description limits, and produce either
`SkillMetadata` or a recorded `SkillError`. The body is not automatically sent
to the model merely because discovery succeeded.

[source](../../codex-rs/core-skills/src/loader.rs#L195) · [claim SK-CLAIM-003](audit/skill-call-inventory/claim-ledger.json#sk-claim-003) · [evidence E-SK-003](audit/skill-call-inventory/source-audit.json#e-sk-003)

### SKILL-DISC-004 — Invalidate snapshots when skills change

**Phase:** lifecycle · **Kind:** watcher/cache call · **Model-visible:** no

The app-server `SkillsWatcher` listens for skill changes and clears the
`SkillsService` cache. Cache invalidation makes a later turn re-discover skill
metadata instead of silently reusing an old snapshot.

[source](../../codex-rs/app-server/src/skills_watcher.rs#L29) · [claim SK-CLAIM-004](audit/skill-call-inventory/claim-ledger.json#sk-claim-004) · [evidence E-SK-004](audit/skill-call-inventory/source-audit.json#e-sk-004)

### SKILL-CAT-005 — Build a source-aware catalog

**Phase:** catalog · **Kind:** provider call · **Model-visible:** derived

The skills extension asks source-specific providers to list skills. Host,
executor, bundled, plugin, and orchestrator sources can have different
authority and resource semantics; the provider returns catalog entries rather
than ambient filesystem paths.

[source](../../codex-rs/ext/skills/src/provider.rs#L60) · [claim SK-CLAIM-005](audit/skill-call-inventory/claim-ledger.json#sk-claim-005) · [evidence E-SK-005](audit/skill-call-inventory/source-audit.json#e-sk-005)

### SKILL-CAT-006 — Serve `skills/list`

**Phase:** client API · **Kind:** app-server/TUI request · **Model-visible:** no

App-server catalog processors and the TUI background request expose a list of
enabled skills for clients. This is a management/read API, distinct from the
model-facing `skills.list` tool.

[source](../../codex-rs/app-server/src/request_processors/catalog_processor.rs#L120) · [claim SK-CLAIM-006](audit/skill-call-inventory/claim-ledger.json#sk-claim-006) · [evidence E-SK-006](audit/skill-call-inventory/source-audit.json#e-sk-006)

### SKILL-SEL-007 — Select structured skill input

**Phase:** selection · **Kind:** user-input resolution · **Model-visible:** not yet

`UserInput::Skill` selections resolve an explicit path against enabled catalog
entries. Disabled or duplicate paths are skipped. This is stronger than a
plain-name match because it preserves the selected resource identity.

[source](../../codex-rs/ext/skills/src/selection.rs#L14) · [claim SK-CLAIM-007](audit/skill-call-inventory/claim-ledger.json#sk-claim-007) · [evidence E-SK-007](audit/skill-call-inventory/source-audit.json#e-sk-007)

### SKILL-SEL-008 — Select `$skill` text mentions

**Phase:** selection · **Kind:** mention parser · **Model-visible:** not yet

Text inputs are scanned for `$skill-name` and explicit resource links. Exact
paths win; plain names are selected only when the match is enabled and
unambiguous. The selected entries are then read by the appropriate provider.

[source](../../codex-rs/core-skills/src/injection.rs#L149) · [claim SK-CLAIM-008](audit/skill-call-inventory/claim-ledger.json#sk-claim-008) · [evidence E-SK-008](audit/skill-call-inventory/source-audit.json#e-sk-008)

### SKILL-READ-009 — Read and inject a host `SKILL.md`

**Phase:** injection · **Kind:** filesystem/provider read · **Model-visible:** yes, after injection

`build_skill_injections` reads selected skill bodies through the skill's
filesystem authority, records a success/error metric, and creates a
`SkillInjection` fragment. Read failures become warnings rather than silently
invented instructions.

[source](../../codex-rs/core-skills/src/injection.rs#L63) · [claim SK-CLAIM-009](audit/skill-call-inventory/claim-ledger.json#sk-claim-009) · [evidence E-SK-009](audit/skill-call-inventory/source-audit.json#e-sk-009)

### SKILL-CTX-010 — Render available skill metadata under budget

**Phase:** context construction · **Kind:** prompt renderer · **Model-visible:** yes

`build_available_skills` renders names, descriptions, and locators into the
skills instruction block. It applies a character/token budget, truncates
descriptions, and emits warnings when entries or descriptions cannot fit.

[source](../../codex-rs/core-skills/src/render.rs#L155) · [claim SK-CLAIM-010](audit/skill-call-inventory/claim-ledger.json#sk-claim-010) · [evidence E-SK-010](audit/skill-call-inventory/source-audit.json#e-sk-010)

### SKILL-CTX-011 — Contribute thread/world-state skill context

**Phase:** context construction · **Kind:** extension contributor · **Model-visible:** yes

The skills extension contributes catalog instructions at thread/context time,
selects skills for a turn, reads main prompts, truncates oversized bodies, and
stores turn-local catalog/selection state. Host prompts already injected are
tracked to avoid duplicate injection.

[source](../../codex-rs/ext/skills/src/extension.rs#L110) · [claim SK-CLAIM-011](audit/skill-call-inventory/claim-ledger.json#sk-claim-011) · [evidence E-SK-011](audit/skill-call-inventory/source-audit.json#e-sk-011)

### SKILL-IMPL-012 — Detect an implicit script or document invocation

**Phase:** attribution · **Kind:** command inspection · **Model-visible:** no direct output

`detect_implicit_skill_invocation_for_command` recognizes supported interpreter
families (`python`, `bash`, `zsh`, `sh`, `node`, `deno`, `ruby`, `perl`, and
`pwsh`) and script extensions, or a command that reads a matching `SKILL.md`.
This call attributes a command to a skill; it does not execute it.

[source](../../codex-rs/core-skills/src/invocation_utils.rs#L31) · [claim SK-CLAIM-012](audit/skill-call-inventory/claim-ledger.json#sk-claim-012) · [evidence E-SK-012](audit/skill-call-inventory/source-audit.json#e-sk-012)

### SKILL-IMPL-013 — Emit implicit invocation telemetry once per turn

**Phase:** attribution · **Kind:** analytics/extension callback · **Model-visible:** no

`maybe_emit_implicit_skill_invocation` deduplicates a skill/path/name key per
turn, notifies extension contributors, increments `codex.skill.injected`, and
sends an analytics invocation with `InvocationType::Implicit`.

[source](../../codex-rs/core/src/skills.rs#L50) · [claim SK-CLAIM-013](audit/skill-call-inventory/claim-ledger.json#sk-claim-013) · [evidence E-SK-013](audit/skill-call-inventory/source-audit.json#e-sk-013)

### SKILL-TOOL-014 — Model calls `skills.list`

**Phase:** model tool loop · **Kind:** model-visible tool · **Model-visible:** yes

The extension registers a namespaced `skills.list` tool for the supported
orchestrator authority. The tool returns bounded package/name/description/main
resource handles and warnings; it does not return arbitrary host paths.

[source](../../codex-rs/ext/skills/src/tools/list.rs#L51) · [claim SK-CLAIM-014](audit/skill-call-inventory/claim-ledger.json#sk-claim-014) · [evidence E-SK-014](audit/skill-call-inventory/source-audit.json#e-sk-014)

### SKILL-TOOL-015 — Model calls `skills.read`

**Phase:** model tool loop · **Kind:** model-visible tool · **Model-visible:** yes

`skills.read` accepts the exact authority/package/resource handles returned by
`skills.list`, validates bounded handles, rechecks availability, reads through
the same provider authority, and returns structured external JSON content.

[source](../../codex-rs/ext/skills/src/tools/read.rs#L42) · [claim SK-CLAIM-015](audit/skill-call-inventory/claim-ledger.json#sk-claim-015) · [evidence E-SK-015](audit/skill-call-inventory/source-audit.json#e-sk-015)

### SKILL-TOOL-016 — Route list/read through a provider boundary

**Phase:** model tool loop · **Kind:** provider dispatch · **Model-visible:** indirect

The `SkillProvider` trait separates `list`, `read`, and `search`. A provider
owns the authority for a resource; a listed opaque handle must not be converted
into an ambient local path by the caller.

[source](../../codex-rs/ext/skills/src/provider.rs#L60) · [claim SK-CLAIM-016](audit/skill-call-inventory/claim-ledger.json#sk-claim-016) · [evidence E-SK-016](audit/skill-call-inventory/source-audit.json#e-sk-016)

### SKILL-CLI-017 — Hand a skill script to a host executor

**Phase:** execution · **Kind:** shell/unified-exec process · **Model-visible:** result only

When the model or user causes a command such as `python skill/scripts/check.py`
to run, the skill detector can attribute it to the skill, but the shell or
unified-exec runtime owns process creation, output streaming, cancellation,
approval, and sandboxing. The inventory must not imply that skill metadata
grants process authority.

[source](../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L156) · [claim SK-CLAIM-017](audit/skill-call-inventory/claim-ledger.json#sk-claim-017) · [evidence E-SK-017](audit/skill-call-inventory/source-audit.json#e-sk-017)

### SKILL-CLI-018 — Apply approval and sandbox controls

**Phase:** execution · **Kind:** policy/sandbox gate · **Model-visible:** status/result

The executor applies the concrete command/patch approval policy and sandbox
permissions. A skill's instructions can recommend a command; they cannot
self-authorize it. Remote or connector tools have separate boundaries.

[source](../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L146) · [claim SK-CLAIM-018](audit/skill-call-inventory/claim-ledger.json#sk-claim-018) · [evidence E-SK-018](audit/skill-call-inventory/source-audit.json#e-sk-018)

### SKILL-OUT-019 — Return correlated output and record attribution

**Phase:** completion · **Kind:** result/telemetry · **Model-visible:** yes, when returned

The normal tool loop returns a result correlated to the originating call. Skill
injection and implicit invocation paths additionally emit metrics/analytics;
these are observability records, not the skill body itself.

[source](../../codex-rs/core/src/skills.rs#L105) · [claim SK-CLAIM-019](audit/skill-call-inventory/claim-ledger.json#sk-claim-019) · [evidence E-SK-019](audit/skill-call-inventory/source-audit.json#e-sk-019)

### SKILL-FAIL-020 — Handle disabled, oversized, missing, or failed skills

**Phase:** failure/recovery · **Kind:** warning/filter/cache path · **Model-visible:** warnings and surviving metadata

Disabled skills are filtered, oversized metadata/body content is truncated or
omitted with warnings, failed reads become warnings, and watcher/config changes
clear caches. A failed or omitted skill must not be represented as successfully
injected instructions.

[source](../../codex-rs/core-skills/src/render.rs#L190) · [claim SK-CLAIM-020](audit/skill-call-inventory/claim-ledger.json#sk-claim-020) · [evidence E-SK-020](audit/skill-call-inventory/source-audit.json#e-sk-020)

## What this inventory does not claim

This is a static, pinned source inventory. It is not a production trace, does
not prove that every possible skill script command is safe, and does not claim
that every emitted metric corresponds to a durable rollout item. The audit's
open gaps identify where a runtime trace or broader authority matrix is still
needed.
