# Codex Desktop Pet Adaptation Plan

## Objective

Adapt the current `ASoul-Little-Bun` project into a VUP Pet: an independent ASoul/BongoCat-style desktop pet that keeps realtime keyboard and mouse interaction while optionally reflecting Codex activity state.

This document is the implementation specification for the first landing pass. The MVP runtime is the existing PyQt6 application, adapted for macOS-first local use and controlled from Codex through a `vup-pet` skill.

## Summary

`ASoul-Little-Bun` should not be embedded into the official Codex `/pet` system as-is. The project is currently an independent PyQt6 desktop pet application. The selected adaptation path is:

1. Reuse character assets and interaction rules.
2. Preserve realtime keyboard and mouse interaction in an independent desktop pet.
3. Add a Codex skill launcher named `vup-pet`.
4. Add an optional Codex state bridge so the pet can reflect Codex activity.
5. Keep the first implementation local-first. Redistribution, packaging, and any direct reuse outside this repository must be reviewed against GPL-2.0 and character asset rights.

## Selected Direction

Use the independent VUP Pet route.

The stable invocation should be:

```text
$vup-pet start
```

Do not rely on `/vup-pet` as the primary command. Codex slash commands are built-in commands; a true `/vup-pet` command would require unsupported custom slash command support or patching Codex itself. The skill can still present itself to the user as "VUP Pet" and provide a short command surface through `$vup-pet`.

The skill should support at least:

```text
$vup-pet start
$vup-pet stop
$vup-pet status
```

Optional later commands:

```text
$vup-pet switch-character 嘉然
$vup-pet enable-codex-state
$vup-pet disable-codex-state
```

## Rejected Direction: Official Codex Pet Package

The official Codex Pet system remains useful for static state-display pets, but it cannot satisfy the realtime keyboard/mouse requirement.

Reasons:

1. Official custom pets are loaded as `pet.json + spritesheet.webp`.
2. Codex owns the overlay, animation playback, and state routing.
3. The public contract exposes a fixed 8-column by 9-row sprite atlas.
4. It does not expose arbitrary keyboard, mouse movement, or mouse click events to the pet.
5. It cannot run the existing PyQt/Python interaction logic.

Use this route only if the goal changes to "make an ASoul-themed Codex status pet" rather than "preserve BongoCat-style realtime input animation."

## Target Runtime

The target runtime is the existing PyQt6 desktop application, running as an independent process launched or controlled by a Codex skill.

Implications:

- The VUP Pet owns the transparent window, rendering, keyboard/mouse listeners, role switching, and local settings.
- The `vup-pet` skill owns launching, stopping, and reporting status from Codex.
- Codex state should be bridged through a local file or localhost API, not through the official `/pet` spritesheet runtime.
- The VUP Pet may run as a separate process.
- macOS Accessibility/Input Monitoring permissions are expected for global input capture.

MVP runtime decision:

- Keep `main.py`, `input_handler.py`, `window_manager.py`, `character_manager.py`, and the existing `img/<character>/` asset model.
- Do not port to Tauri, Electron, or the official Codex Pet runtime in the MVP.
- Do not patch the Codex app bundle.
- Treat macOS as the first supported target. Windows behavior can remain only when guarded behind platform checks.

## Official Codex Pet Contract

Official custom pets are loaded from local Codex home:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/
├── pet.json
└── spritesheet.webp
```

`pet.json` shape:

```json
{
  "id": "pet-name",
  "displayName": "Pet Name",
  "description": "One short sentence.",
  "spritesheetPath": "spritesheet.webp"
}
```

The app loads custom pets from the folder name under `${CODEX_HOME:-$HOME/.codex}/pets/`.

The spritesheet is a fixed sprite atlas:

- Format: PNG or WebP; packaged output should use `spritesheet.webp`.
- Dimensions: `1536x1872`.
- Grid: 8 columns x 9 rows.
- Cell: `192x208`.
- Background: transparent.
- Unused cells: fully transparent.

Codex uses fixed CSS background positions for the row and column counts. Do not add labels, gutters, borders, grid lines, shadows outside the cell, or extra frames.

This contract is documented here because it explains why the official Codex Pet route is not the selected implementation path.

## Official Animation States

| Row | State | Used columns | Purpose |
| --- | --- | ---: | --- |
| 0 | `idle` | 0-5 | calm low-distraction breathing/blinking loop |
| 1 | `running-right` | 0-7 | directional right movement for overlay movement |
| 2 | `running-left` | 0-7 | directional left movement for overlay movement |
| 3 | `waving` | 0-3 | greeting or attention gesture |
| 4 | `jumping` | 0-4 | anticipation, lift, peak, descent, settle |
| 5 | `failed` | 0-7 | error/sad/deflated reaction |
| 6 | `waiting` | 0-5 | blocked on user input, approval, or help |
| 7 | `running` | 0-5 | active task work, processing, or focused effort |
| 8 | `review` | 0-5 | review or inspection state |

## Current Project Shape

The current project is a Python desktop application:

- Entry point: `main.py`
- UI runtime: PyQt6, `QOpenGLWidget`, `QLabel` layers
- Input listener: `pynput`
- Windows-specific logic: `pywin32`, `ctypes.windll.user32`, `.bat` packaging scripts
- Character assets: `img/<character>/`
- Configuration: per-character `config.json` and `custom_layers.json`

## Reusable Parts

The following parts are suitable for migration:

- Character image assets under `img/<character>/`
- `bgImage.png`
- `keyboardImage.png`
- `mouseImage.png`
- `leftClickImage.png`
- `rightClickImage.png`
- Per-character positioning and sizing concepts
- Layer-ordering concepts
- Keyboard press animation behavior
- Mouse-follow behavior
- Left-click and right-click visual states
- Character switching behavior

## Parts Not Recommended For Direct Reuse

The following parts should not be migrated into the official Codex Pet runtime:

- PyQt6 window code
- `QLabel`-based layer rendering
- `pynput` global keyboard and mouse listeners
- Windows taskbar hiding behavior
- Windows startup-folder integration
- PyInstaller packaging scripts
- Built-in updater scripts
- System tray menu implementation

For the PyQt6 MVP, these are the concrete code targets:

| Area | Current file | MVP action |
| --- | --- | --- |
| Entry point | `main.py` | Keep as app entry point; allow launcher-safe startup from skill helper. |
| Input capture | `input_handler.py` | Keep `pynput`; document macOS Accessibility/Input Monitoring requirement. |
| Mouse passthrough | `window_manager.py` | Keep Qt passthrough behavior if it works on macOS; guard platform-specific branches. |
| Windows taskbar API | `window_manager.py` `_hide_from_taskbar`, `_show_in_taskbar` | Guard with `sys.platform == "win32"` or no-op on macOS. |
| Windows startup folder | `settings.py` `get_startup_folder`, `open_startup_folder` | Guard with `sys.platform == "win32"`; do not expose as MVP macOS feature. |
| Dependencies | `requirements.txt` | Split or conditionally mark `pywin32` so macOS install does not require it. |
| Packaging | `build.bat`, `build.spec`, updater scripts | Exclude from MVP unless a separate packaging task is opened. |

## Target Architecture

The adapted VUP Pet should be split into four layers.

### 1. Asset Layer

The `img` folder remains the runtime asset source for the VUP Pet.

Each character should expose the same core asset set:

```json
{
  "id": "asoul-little-bun",
  "characters": [
    {
      "id": "jiaran",
      "name": "嘉然",
      "assets": {
        "background": "img/嘉然/bgImage.png",
        "keyboard": "img/嘉然/keyboardImage.png",
        "mouse": "img/嘉然/mouseImage.png",
        "leftClick": "img/嘉然/leftClickImage.png",
        "rightClick": "img/嘉然/rightClickImage.png"
      }
    }
  ]
}
```

This inventory should become a local runtime manifest for the VUP Pet, not an official Codex Pet manifest.

### 2. Realtime Interaction Layer

The VUP Pet keeps the original BongoCat-style interaction model:

- keyboard press and release animation
- mouse movement follow animation
- left-click and right-click state layers
- optional key display
- role/character switching

This layer cannot be implemented with the official Codex Pet spritesheet contract.

### 3. Codex State Bridge

Add an optional bridge so the pet can reflect Codex activity. Start with a file-based bridge because it is simple, inspectable, and avoids keeping a localhost server alive unless needed.

Recommended file:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/state.json
```

Process metadata file:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/pid.json
```

Suggested shape:

```json
{
  "source": "codex",
  "state": "running",
  "threadTitle": "ASoul pet adaptation",
  "message": "Codex is running a task",
  "updatedAt": "2026-05-15T16:00:00Z"
}
```

Supported `state` values:

| State | Meaning |
| --- | --- |
| `idle` | Codex is idle or no state is available |
| `running` | Codex is actively working |
| `waiting` | Codex is blocked on user input or approval |
| `review` | Codex is reviewing or asking for inspection |
| `failed` | last Codex action failed |

The VUP Pet should treat Codex state as secondary. Realtime keyboard/mouse animation remains primary.

Bridge semantics:

- The MVP does not assume access to Codex internal runtime state.
- The skill may write explicit bridge states when it performs commands, for example `running` after `start`, `idle` after `stop`, and `failed` when launch fails.
- The pet should poll `state.json` no faster than once per second.
- Writes should be atomic: write a temporary file in the same directory, then rename it to `state.json`.
- `updatedAt` must be ISO-8601 UTC.
- If `updatedAt` is older than 5 minutes, the pet should treat the bridge state as stale and fall back to `idle`.
- If `state.json` is missing, invalid JSON, or contains an unknown state, the pet should ignore it and continue realtime input animation.
- Codex state visuals are secondary overlays or expression changes; they must not block keyboard/mouse animation.

### 4. Hook Notification Bridge

Add a lightweight notification bridge so Codex App hooks and CodeBuddy Code hooks can show short text prompts inside the VUP Pet window.

This bridge is separate from `state.json`:

- `state.json` represents durable activity state such as `running`, `waiting`, or `failed`.
- Hook notifications represent short-lived messages that should appear in a text box and then disappear.

Recommended queue file:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl
```

Recommended cursor file:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notification_cursor.json
```

Recommended write lock:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.lock
```

Suggested queue event shape:

```json
{
  "id": "2026-05-18T16:00:00.123Z-codex-stop-7f3a",
  "source": "codex",
  "event": "Stop",
  "level": "success",
  "title": "Codex",
  "message": "Task finished",
  "displayText": "Codex: Task finished",
  "createdAt": "2026-05-18T16:00:00.123Z",
  "ttlSeconds": 120,
  "raw": {
    "hook_event_name": "Stop"
  }
}
```

Suggested cursor shape:

```json
{
  "lastConsumedId": "2026-05-18T16:00:00.123Z-codex-stop-7f3a",
  "updatedAt": "2026-05-18T16:00:05Z"
}
```

Supported `source` values:

| Source | Meaning |
| --- | --- |
| `codex` | Notification came from Codex App hooks |
| `codebuddy` | Notification came from CodeBuddy Code hooks |
| `launcher` | Notification came from the VUP Pet launcher itself |

Initial supported event scope:

| Source | Event | Matcher | Meaning |
| --- | --- | --- | --- |
| `codex` | `Stop` | none | Codex turn or task ended |
| `codebuddy` | `Notification` | `permission_prompt|idle_prompt` | CodeBuddy needs user attention |

Supported `level` values:

| Level | Display rule |
| --- | --- |
| `info` | normal short prompt, hide after about 3 seconds |
| `success` | completion prompt, hide after about 3 seconds |
| `warning` | visible longer, hide after about 5 seconds |
| `error` | visible longest, hide after about 6-8 seconds |

Hook notification semantics:

- Hooks must not talk directly to the PyQt process.
- Hooks should call a hook adapter script that normalizes Codex and CodeBuddy payloads before writing the bridge queue.
- Hooks append one JSON object per line to `notifications.jsonl`.
- The pet tracks consumption in `notification_cursor.json`; it should not delete queue lines after displaying them.
- The pet should ignore queue events older than their `ttlSeconds`.
- The pet should only show messages after the `lastConsumedId`.
- If `notifications.jsonl` is missing, invalid, stale, or contains an unknown source/level/event, the pet should ignore the invalid entry and continue.
- Display text should be capped to a practical length, for example 80-120 characters.
- The notification text box must be independent from the existing keypress display label so hook prompts do not overwrite keyboard input feedback.
- Notification display is secondary UI. It must not block keyboard animation, mouse tracking, click state layers, or custom layer updates.

Queue write semantics:

- `notifications.lock` is the only lock used for queue appends.
- The write lock must never be held while invoking external commands, reading cursor state, updating UI, or writing other bridge files.
- The locked section should only open `notifications.jsonl`, append one JSON line, flush/fsync, and close.
- Lock acquisition must time out quickly, for example after 1-2 seconds.
- Lock timeout or write failure must fail open: log to `/tmp/vup-pet-hook-notify.log` and return success to the hook caller.
- Cursor writes should use atomic replacement: write a temporary file in the same directory, then `os.replace()`.

Queue rotation semantics:

- Before appending, if `notifications.jsonl` is larger than 1 MB, rotate it to `notifications.jsonl.1`.
- Keep at most one rotated file.
- Rotation happens while holding `notifications.lock`.
- The pet reads only the current `notifications.jsonl`; it should not replay `notifications.jsonl.1`.
- If the cursor points to an event not present in the current file, resume from the first unexpired event in the current file.

Display trigger semantics:

- The primary trigger should be `QFileSystemWatcher`, not 0.5-1 second polling.
- Watch both `${CODEX_HOME:-$HOME/.codex}/vup-pet/` and `notifications.jsonl`.
- Directory watching handles file creation and queue rotation.
- File watching handles ordinary append events.
- Watcher events may be merged; each trigger must drain all newly readable events after the cursor.
- After queue rotation or file recreation, re-register the file watcher if needed.
- A low-frequency safety check, for example once per 60 seconds, may be used only to recover from missed watcher events.

Hook adapter command contract:

```text
python3 hooks/vup_pet_notify.py --source codex --event Stop
python3 hooks/vup_pet_notify.py --source codebuddy --event Notification
python3 vup_pet_launcher.py notify --source codex --event Stop --message "Task finished"
```

Recommended hook mapping:

| Hook producer | Adapter source | Event | Display prefix |
| --- | --- | --- | --- |
| Codex App hooks | `codex` | `Stop` | `Codex:` |
| CodeBuddy Code hooks | `codebuddy` | `Notification` | `CodeBuddy:` |

Hook adapter responsibilities:

- Live at `hooks/vup_pet_notify.py`.
- Read hook payload JSON from stdin.
- Normalize Codex and CodeBuddy payloads into queue event fields.
- Store display-ready fields: `source`, `event`, `level`, `title`, `message`, `displayText`, `createdAt`, and `ttlSeconds`.
- Optionally store a truncated `raw` payload for debugging.
- Write `/tmp/vup-pet-hook-notify.log` on adapter errors.
- Always fail open and exit 0 so notification failures never block Codex or CodeBuddy.

Global hook configuration policy:

- Repository implementation must not directly modify `~/.codex/hooks.json`.
- Repository implementation must not directly modify `~/.codebuddy/settings.json`.
- Provide setup documentation and optional dry-run installer guidance instead.
- Any future installer must merge settings rather than overwrite them, and must require an explicit apply step before writing global config files.

First implementation should keep placement and styling conservative:

- A dedicated `QLabel` in `main.py`.
- `wordWrap` enabled.
- Semi-transparent dark background.
- White text.
- Default placement near the pet body but away from the existing keypress display.
- Auto-hide timer reset whenever a new message arrives.

Configuration can be added later after the bridge works:

- enable/disable hook notifications
- text box position
- max width
- display duration
- background visibility

### 5. Skill Launcher Layer

Create a Codex skill named `vup-pet`. Its responsibility is orchestration, not rendering.

The skill should:

- locate the VUP Pet app/script
- start it if it is not already running
- stop it on request
- report process and bridge status
- optionally write Codex state into the bridge file
- optionally write hook notification events into the notification bridge file
- never patch the Codex app bundle

Skill installation target:

```text
${CODEX_HOME:-$HOME/.codex}/skills/vup-pet/
├── SKILL.md
└── scripts/
    └── vup_pet_launcher.py
```

Launcher command contract:

```text
python3 ${CODEX_HOME:-$HOME/.codex}/skills/vup-pet/scripts/vup_pet_launcher.py start
python3 ${CODEX_HOME:-$HOME/.codex}/skills/vup-pet/scripts/vup_pet_launcher.py stop
python3 ${CODEX_HOME:-$HOME/.codex}/skills/vup-pet/scripts/vup_pet_launcher.py status
python3 ${CODEX_HOME:-$HOME/.codex}/skills/vup-pet/scripts/vup_pet_launcher.py notify --source codex --event Stop --message "Task finished"
```

The skill should expose these as:

```text
$vup-pet start
$vup-pet stop
$vup-pet status
```

`vup_pet_launcher.py` responsibilities:

- Resolve the project root. Default to `/Users/dawn80s/work/personal/asoul_bongocat/ASoul-Little-Bun`, with an override through `VUP_PET_PROJECT_ROOT`.
- Start the pet with the selected Python interpreter and `main.py`.
- Create `${CODEX_HOME:-$HOME/.codex}/vup-pet/` if missing.
- Write `pid.json` after a successful launch.
- Refuse duplicate starts when the recorded PID is still alive.
- `stop` should first send a graceful terminate signal, wait briefly, then report if manual cleanup is required.
- `status` should report at least `running`, `pid`, `projectRoot`, `stateFile`, `notificationsFile`, `notificationCursorFile`, `pidFile`, and whether each bridge file is present.
- `notify` should append a normalized hook notification event without requiring the pet process to be running.
- Do not use shell-specific command strings for process execution; pass argv arrays.
- Do not require modifying the Codex app bundle.

## Interaction Mapping

The selected VUP Pet route is arbitrary input-event-driven.

That means the original ASoul BongoCat interaction model can be preserved:

- Keyboard press drives the keyboard layer.
- Mouse movement drives the mouse layer.
- Left/right click drives the click layers.
- Codex activity state can add secondary badges, expressions, or small overlay changes.

The official Codex Pet route remains state-driven and is not used for the MVP.

## Feature Migration Table

| Feature | Current implementation | Codex adaptation |
| --- | --- | --- |
| Transparent always-on-top window | PyQt window flags | VUP Pet app responsibility |
| Background image | `QLabel` | keep in PyQt6 MVP |
| Keyboard press animation | `QPropertyAnimation` | preserve |
| Mouse follow | `QCursor` plus `QTimer` | preserve |
| Left/right click state | `pynput` mouse listener | preserve |
| Character switching | scan `img` subfolders | preserve, manifest-backed if refactored |
| Settings panel | PyQt dialog | preserve initially, refine later |
| Tray menu | `QSystemTrayIcon` | do not migrate initially |
| Auto update | updater scripts | do not migrate |
| Hide taskbar | Windows API | omit on macOS-first MVP |
| Codex launch | none | `$vup-pet start` skill command |
| Codex state | none | optional bridge file |
| Hook notifications | none | optional `notifications.jsonl` queue plus pet text box |

## Recommended Implementation Order

1. Guard Windows-only behavior for macOS in `window_manager.py` and `settings.py`.
2. Make dependency installation macOS-safe by removing or platform-marking `pywin32`.
3. Verify the existing PyQt6 app still preserves keyboard, mouse movement, and click animations.
4. Add a process-safe launcher helper for `start`, `stop`, and `status`.
5. Add the `vup-pet` Codex skill wrapper that calls the launcher helper.
6. Add `${CODEX_HOME:-$HOME/.codex}/vup-pet/pid.json` process tracking.
7. Add optional `${CODEX_HOME:-$HOME/.codex}/vup-pet/state.json` bridge writes from the launcher.
8. Teach the VUP Pet to watch the bridge file and apply secondary visual state if feasible.
9. Add `${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl` queue appends from `notify`.
10. Add `hooks/vup_pet_notify.py` to normalize Codex and CodeBuddy hook payloads.
11. Teach the VUP Pet to watch `notifications.jsonl` through `QFileSystemWatcher` and show a short-lived text box for Codex App and CodeBuddy hook messages.
12. Add `docs/hooks-notification-setup.md` with hook configuration snippets and validation commands.
13. Add local install and permission notes for macOS.

## Initial MVP Scope

The first usable version should include:

- One selected ASoul character
- Transparent always-on-top VUP Pet window
- Keyboard press animation
- Mouse-follow animation
- Left-click and right-click state images
- `$vup-pet start`
- `$vup-pet stop`
- `$vup-pet status`

The MVP should exclude:

- Official Codex Pet spritesheet packaging
- Auto updater
- Windows-specific taskbar behavior
- Startup-folder integration
- Custom layer editor
- True `/vup-pet` slash command support
- Patching the Codex app bundle

## MVP Acceptance Criteria

The first landing pass is complete only when all required checks pass:

1. `python3 -m pip install -r requirements.txt` does not require `pywin32` on macOS.
2. Starting the app directly with `python3 main.py` opens the transparent always-on-top pet window on macOS.
3. Keyboard press/release changes the keyboard layer.
4. Mouse movement changes the mouse layer.
5. Left-click and right-click visual states work.
6. `$vup-pet start` starts the pet when it is not running.
7. `$vup-pet start` does not create duplicate pet processes when it is already running.
8. `$vup-pet status` reports running state, PID, project root, `pid.json`, and `state.json` presence.
9. `$vup-pet stop` exits the pet process or reports that manual cleanup is required.
10. The implementation does not patch the Codex app bundle and does not depend on `/vup-pet`.
11. Missing macOS Accessibility/Input Monitoring permission is documented as an expected host permission issue, not treated as a code failure.

Optional bridge acceptance:

1. Launcher writes `state.json` atomically.
2. Pet ignores missing, stale, invalid, or unknown bridge state.
3. Bridge visuals never block realtime keyboard/mouse animation.

Optional hook notification acceptance:

1. Launcher appends valid JSONL events to `notifications.jsonl` through the `notify` command.
2. Hook adapter writes Codex `Stop` events without modifying global Codex config.
3. Hook adapter writes CodeBuddy `Notification` events for `permission_prompt|idle_prompt` without modifying global CodeBuddy config.
4. The pet uses `QFileSystemWatcher` as the primary trigger for new queue events.
5. Codex App hooks can trigger a visible `Codex:` text prompt in the pet window after the user applies the documented hook config.
6. CodeBuddy Code hooks can trigger a visible `CodeBuddy:` text prompt in the pet window after the user applies the documented hook config.
7. Notification prompts auto-hide and do not overwrite the keypress display label.
8. Missing, stale, invalid, unknown, or expired notification payloads are ignored without affecting realtime animation.

## Configuration Model

Source asset inventory can use a normalized config:

```json
{
  "window": {
    "width": 240,
    "height": 135
  },
  "layers": {
    "background": {
      "x": 0,
      "y": 0,
      "width": 240,
      "height": 135
    },
    "keyboard": {
      "x": 94,
      "y": 84,
      "width": 25,
      "height": 25,
      "pressOffset": 5,
      "horizontalTravel": 50
    },
    "mouse": {
      "x": 190,
      "y": 90,
      "width": 25,
      "height": 25,
      "maxOffset": 20,
      "sensitivity": 0.3,
      "returnSpeed": 0.05
    }
  }
}
```

This keeps the existing configuration meaning as VUP Pet runtime metadata. It is not consumed by official Codex Pet directly.

## Licensing And Distribution Risk

The source repository is GPL-2.0 licensed.

Recommended approach:

- Reimplement the Codex runtime code independently.
- Use the existing implementation as behavioral reference only.
- Treat direct code copying as GPL-2.0-derived work unless reviewed otherwise.
- Check whether character assets can be redistributed in the intended context.

If the final result is only for local personal use, the practical risk is lower. If it will be redistributed, licensing and character/IP rights should be reviewed first.

## Main Risks

- Global keyboard and mouse capture may require host-level permissions.
- The existing Windows-only behaviors do not transfer cleanly to macOS.
- Asset licensing and character rights may constrain redistribution.
- A direct PyQt-to-official-Codex-Pet embedding path is not supported by the official pet contract.
- The custom layer editor is larger than the initial pet MVP and should be delayed.
- `$vup-pet` is the stable skill invocation; `/vup-pet` is not a supported custom slash command unless Codex adds that capability or the app is patched.

## Recommended Decision

Proceed with the independent VUP Pet plus `vup-pet` skill launcher.

Do not try to force realtime keyboard and mouse behavior into the official Codex Pet spritesheet package. Keep the VUP Pet as a separate desktop process and let the Codex skill launch/control it. Use an optional local state bridge for Codex activity, and reserve official `pet.json + spritesheet.webp` support as a separate, lower-capability export path.
