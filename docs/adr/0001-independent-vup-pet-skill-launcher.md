# ADR 0001: Use Independent VUP Pet With Codex Skill Launcher

## Status

Accepted

## Context

The goal is to adapt `ASoul-Little-Bun` into a pet experience usable from the Codex desktop app while preserving realtime keyboard and mouse interaction.

The official Codex Pet system is toggled through `/pet` and loads a local custom pet package from:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/
├── pet.json
└── spritesheet.webp
```

That official path is suitable for state-driven sprite animation. It is not suitable for arbitrary global keyboard events, mouse movement following, left/right click state layers, or running the existing PyQt6 logic.

The existing project is already a desktop pet application with:

- PyQt6 rendering and transparent window behavior.
- `pynput` keyboard and mouse listeners.
- ASoul/BongoCat-style image layers under `img/<character>/`.
- Windows-specific behavior that must be guarded for macOS.

## Decision

Use an independent VUP Pet process controlled by a Codex skill named `vup-pet`.

The stable user-facing invocation is:

```text
$vup-pet start
$vup-pet stop
$vup-pet status
```

The MVP keeps the existing PyQt6 runtime and adapts it for macOS-first local use. The skill launches, stops, and reports status for the process. Optional Codex activity state is passed through a local bridge file under:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/state.json
```

Short-lived hook messages from Codex App hooks and CodeBuddy Code hooks use an append-only notification queue under:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl
```

The launcher owns bridge writes. Hook adapter scripts normalize Codex and CodeBuddy hook payloads and append queue events. The PyQt pet process watches the queue with `QFileSystemWatcher`, records consumption in `notification_cursor.json`, and displays a temporary text box.

The first hook integration scope is intentionally narrow:

- Codex App: `Stop`.
- CodeBuddy Code: `Notification` with `permission_prompt|idle_prompt`.

Repository implementation should not directly modify global `~/.codex/hooks.json` or `~/.codebuddy/settings.json`. Configuration snippets and dry-run install guidance belong in repository documentation until the user explicitly applies them.

Do not implement the MVP by patching the Codex app bundle, adding a true `/vup-pet` slash command, or forcing the realtime interaction model into the official `pet.json + spritesheet.webp` contract.

## Consequences

Positive:

- Realtime keyboard and mouse interaction can be preserved.
- The project can reuse existing PyQt6 app structure and assets.
- Codex integration remains local, inspectable, and reversible.
- The implementation avoids depending on unsupported Codex app patching.

Negative:

- The VUP Pet is not the official Codex `/pet` overlay.
- It runs as a separate process and needs its own lifecycle management.
- macOS global input capture may require Accessibility/Input Monitoring permissions.
- The skill cannot automatically observe all Codex internal states unless Codex exposes or writes that state.

## Alternatives Considered

### Official Codex Pet Package

Rejected for MVP.

This would produce a `pet.json` and fixed `1536x1872` spritesheet. It can create an ASoul-themed Codex status pet, but it cannot preserve realtime BongoCat keyboard/mouse interaction.

### Patch Codex App Pet Runtime

Rejected for MVP.

Patching could theoretically add richer animation or interaction support, but it depends on unsupported app internals, creates upgrade risk, and is unnecessary for a local independent desktop pet.

### Port To Tauri Or Electron First

Deferred.

A new runtime may be useful later, but it would increase first-pass scope and delay the core goal. The current PyQt6 app already owns the main behaviors needed for MVP.

## Follow-Up Work

- Guard Windows-only code paths for macOS.
- Make dependencies installable on macOS without `pywin32`.
- Add the `vup-pet` skill and launcher helper.
- Add process tracking through `pid.json`.
- Add optional file-based bridge state.
- Add optional hook notification bridge through `notifications.jsonl`.
- Add `hooks/vup_pet_notify.py` as the hook adapter.
- Add a dedicated pet text box for Codex App and CodeBuddy hook messages.
- Add setup documentation for Codex and CodeBuddy hook configuration without writing global config by default.
- Document macOS permission requirements.
