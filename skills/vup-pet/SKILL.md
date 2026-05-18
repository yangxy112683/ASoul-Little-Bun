---
name: vup-pet
description: Launch and control the independent ASoul Little Bun VUP Pet from Codex.
---

# vup-pet

Use this skill to launch or control the independent ASoul Little Bun VUP Pet. This is not the official Codex `/pet` custom pet package; it runs the PyQt6 desktop pet as a separate local process.

## Commands

- `$vup-pet start` — start the VUP Pet if it is not already running.
- `$vup-pet stop` — stop the recorded VUP Pet process.
- `$vup-pet status` — show process and bridge status.

## Implementation

Run the repository launcher:

```bash
python3 skills/vup-pet/scripts/vup_pet_launcher.py start
python3 skills/vup-pet/scripts/vup_pet_launcher.py stop
python3 skills/vup-pet/scripts/vup_pet_launcher.py status
```

The launcher records process metadata under `${CODEX_HOME:-$HOME/.codex}/vup-pet/pid.json` and bridge state under `${CODEX_HOME:-$HOME/.codex}/vup-pet/state.json`.

## Boundaries

Do not implement or depend on custom slash commands or Chinese aliases. Do not patch the Codex app bundle. The official `/pet` command is reserved for Codex custom pet packages that contain `pet.json` and `spritesheet.webp`.
