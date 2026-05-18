# Hook Notification Setup

This document describes how Codex App hooks and CodeBuddy Code hooks can send short text notifications to the independent ASoul Little Bun VUP Pet.

This repository should not directly modify global hook config files. Treat the snippets below as setup examples until they are explicitly applied.

## Architecture

Hook notifications use an append-only queue:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl
```

The pet records consumption separately:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notification_cursor.json
```

Queue writes use a short-held lock:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.lock
```

The hook adapter is:

```text
hooks/vup_pet_notify.py
```

The adapter reads hook JSON from stdin, normalizes it into a queue event, and appends one JSON object per line. It must fail open: notification failures are logged but must not block Codex or CodeBuddy.

Fallback log:

```text
/tmp/vup-pet-hook-notify.log
```

## Initial Event Scope

First version only wires events that need user attention:

| Producer | Event | Matcher | Display |
| --- | --- | --- | --- |
| Codex App | `Stop` | none | `Codex: ...` |
| CodeBuddy Code | `Notification` | `permission_prompt|idle_prompt` | `CodeBuddy: ...` |

Do not wire `PreToolUse`, `PostToolUse`, or `UserPromptSubmit` in the first pass. Those events are higher frequency and should be added only after filtering and display throttling are proven.

## Queue Event Shape

Each line in `notifications.jsonl` should look like:

```json
{"id":"2026-05-18T16:00:00.123Z-codex-stop-7f3a","source":"codex","event":"Stop","level":"success","title":"Codex","message":"Task finished","displayText":"Codex: Task finished","createdAt":"2026-05-18T16:00:00.123Z","ttlSeconds":120,"raw":{"hook_event_name":"Stop"}}
```

Required fields:

| Field | Purpose |
| --- | --- |
| `id` | unique sortable event id |
| `source` | `codex`, `codebuddy`, or `launcher` |
| `event` | hook event name |
| `level` | `info`, `success`, `warning`, or `error` |
| `title` | short producer label |
| `message` | normalized message |
| `displayText` | final text for the pet label |
| `createdAt` | ISO-8601 UTC timestamp |
| `ttlSeconds` | expiry window |

`raw` is optional and should be truncated. Do not store large payloads or sensitive command output in full.

## Write Rules

`notifications.lock` is only for queue appends.

Rules:

- Use one lock only.
- Hold the lock only while rotating and appending the queue file.
- Do not call subprocesses, update UI, read cursor state, or write other bridge files while holding the lock.
- Lock acquisition must time out quickly, for example after 1-2 seconds.
- On lock timeout or write failure, write `/tmp/vup-pet-hook-notify.log` and exit 0.
- Rotate `notifications.jsonl` to `notifications.jsonl.1` when it exceeds 1 MB.
- Keep only one rotated file.

## Pet Read Rules

The PyQt pet should use `QFileSystemWatcher` instead of frequent polling.

Watch both:

```text
${CODEX_HOME:-$HOME/.codex}/vup-pet/
${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl
```

Rules:

- Directory watching handles file creation and queue rotation.
- File watching handles ordinary appends.
- Watcher events may be merged, so each trigger should drain all readable events after the cursor.
- If the file is recreated or rotated, re-register the file watcher.
- Read only the current `notifications.jsonl`; do not replay `notifications.jsonl.1`.
- If the cursor points to an event no longer in the current file, resume from the first unexpired event.
- A low-frequency safety check, such as once per 60 seconds, may be used only to recover missed watcher events.

## Manual Validation

After `hooks/vup_pet_notify.py` exists, test Codex normalization with:

```bash
echo '{"hook_event_name":"Stop"}' | python3 hooks/vup_pet_notify.py --source codex --event Stop
```

Test CodeBuddy normalization with:

```bash
echo '{"hook_event_name":"Notification","notification_type":"idle_prompt","message":"CodeBuddy is waiting for input"}' | python3 hooks/vup_pet_notify.py --source codebuddy --event Notification
```

Check the queue:

```bash
tail -n 5 "${CODEX_HOME:-$HOME/.codex}/vup-pet/notifications.jsonl"
```

Check adapter errors:

```bash
tail -n 20 /tmp/vup-pet-hook-notify.log
```

## Codex Config Snippet

Do not write this automatically. Merge it into `~/.codex/hooks.json` only after review.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/dawn80s/work/personal/asoul_bongocat/ASoul-Little-Bun/hooks/vup_pet_notify.py --source codex --event Stop",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

If `~/.codex/hooks.json` already has a `Stop` hook, merge this as an additional command hook rather than replacing the existing hook.

## CodeBuddy Config Snippet

Project-level option for `ASoul-Little-Bun/.codebuddy/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt|idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/dawn80s/work/personal/asoul_bongocat/ASoul-Little-Bun/hooks/vup_pet_notify.py --source codebuddy --event Notification",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

User-level option is `~/.codebuddy/settings.json`. If using the user-level file, merge with existing hooks and enabled plugins. Do not overwrite the file.

## Future Events

After the MVP is stable, additional events can use the same queue shape:

- Codex `Notification` or future attention events.
- CodeBuddy `SessionStart`.
- CodeBuddy `Stop`.
- CodeBuddy filtered `PostToolUse`.

Before enabling high-frequency events, add filtering rules so the pet does not become a message stream.
