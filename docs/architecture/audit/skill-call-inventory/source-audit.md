# Clickable source and evidence index

This is the human-readable companion to
[`source-audit.json`](source-audit.json). Each evidence ID is a stable link
used by the claim ledger and inventory.

## Evidence points

<a id="e-sk-001"></a>
### E-SK-001 — Root resolution

[service.rs](../../../../codex-rs/core-skills/src/service.rs#L150) shows
`skill_roots_for_config` deriving roots from configuration, cwd, plugin roots,
and extra roots.

<a id="e-sk-002"></a>
### E-SK-002 — Snapshot caches

[service.rs](../../../../codex-rs/core-skills/src/service.rs#L126) shows
configuration/cwd snapshot methods and cache-backed `HostSkillsSnapshot` output.

<a id="e-sk-003"></a>
### E-SK-003 — Metadata loading

[loader.rs](../../../../codex-rs/core-skills/src/loader.rs#L195) shows root
loading and metadata parsing/validation.

<a id="e-sk-004"></a>
### E-SK-004 — Watcher invalidation

[skills_watcher.rs](../../../../codex-rs/app-server/src/skills_watcher.rs#L29)
shows the watcher and cache-clear path.

<a id="e-sk-005"></a>
### E-SK-005 — Provider catalog authority

[provider.rs](../../../../codex-rs/ext/skills/src/provider.rs#L60) defines
provider-owned list/read/search operations and authority-preserving requests.

<a id="e-sk-006"></a>
### E-SK-006 — Client catalog calls

[catalog_processor.rs](../../../../codex-rs/app-server/src/request_processors/catalog_processor.rs#L120)
and the [TUI background request](../../../../codex-rs/tui/src/app/background_requests.rs#L844)
show client-facing skill listing.

<a id="e-sk-007"></a>
### E-SK-007 — Structured selection

[selection.rs](../../../../codex-rs/ext/skills/src/selection.rs#L14) handles
explicit skill input and enabled path matching.

<a id="e-sk-008"></a>
### E-SK-008 — Text mentions

[injection.rs](../../../../codex-rs/core-skills/src/injection.rs#L149) handles
text mention extraction and explicit selection.

<a id="e-sk-009"></a>
### E-SK-009 — Explicit body read

[injection.rs](../../../../codex-rs/core-skills/src/injection.rs#L63) reads
selected skill content through the selected filesystem authority.

<a id="e-sk-010"></a>
### E-SK-010 — Metadata budget

[render.rs](../../../../codex-rs/core-skills/src/render.rs#L155) implements
available-skill rendering, budgets, truncation, and warnings.

<a id="e-sk-011"></a>
### E-SK-011 — Extension context

[extension.rs](../../../../codex-rs/ext/skills/src/extension.rs#L110) contributes
thread/world-state fragments and stores turn-local skill state.

<a id="e-sk-012"></a>
### E-SK-012 — Implicit detection

[invocation_utils.rs](../../../../codex-rs/core-skills/src/invocation_utils.rs#L31)
recognizes bounded runner/script and `SKILL.md` read patterns.

<a id="e-sk-013"></a>
### E-SK-013 — Implicit telemetry

[core skills bridge](../../../../codex-rs/core/src/skills.rs#L50) deduplicates
implicit invocation and emits contributor/metric/analytics records.

<a id="e-sk-014"></a>
### E-SK-014 — `skills.list`

[list.rs](../../../../codex-rs/ext/skills/src/tools/list.rs#L51) defines the
namespaced model-facing list tool and bounded handle response.

<a id="e-sk-015"></a>
### E-SK-015 — `skills.read`

[read.rs](../../../../codex-rs/ext/skills/src/tools/read.rs#L42) defines handle
validation, authority recheck, provider read, and structured output.

<a id="e-sk-016"></a>
### E-SK-016 — Provider routing

[provider.rs](../../../../codex-rs/ext/skills/src/provider.rs#L60) is the source
of the provider boundary used by list/read/search.

<a id="e-sk-017"></a>
### E-SK-017 — Process execution

[unified_exec.rs](../../../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L258)
owns the local process execution runtime.

<a id="e-sk-018"></a>
### E-SK-018 — Approval and sandbox

[unified_exec.rs](../../../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L146)
shows the approval/sandbox traits used before local execution.

<a id="e-sk-019"></a>
### E-SK-019 — Observability

[skills.rs](../../../../codex-rs/core/src/skills.rs#L105) and
[injection.rs](../../../../codex-rs/core-skills/src/injection.rs#L113) show
implicit/explicit invocation analytics and metrics.

<a id="e-sk-020"></a>
### E-SK-020 — Failure and budget handling

[render.rs](../../../../codex-rs/core-skills/src/render.rs#L190) and the
[extension tests](../../../../codex-rs/ext/skills/tests/skills_extension.rs#L131)
show omission/truncation warnings and selected injection/failure cases.
