# ASoul Little Bun Codex Pet Context

This context defines the project language for adapting `ASoul-Little-Bun` into a pet experience launched from the Codex desktop app.

## Language

**Codex Pet**:
An optional animated companion loaded by the Codex desktop app from the local Codex home and toggled with the official `/pet` command.
_Avoid_: standalone PyQt app, generic web demo, StreamDock plugin, `/宠物` as an implementation name

**VUP Pet**:
The independent ASoul/BongoCat-style desktop pet that keeps realtime keyboard and mouse interaction while optionally reflecting Codex activity state.
_Avoid_: official Codex Pet, static spritesheet package

**VUP Pet Skill**:
A Codex skill named `vup-pet` that launches or controls the independent VUP Pet from Codex, using `$vup-pet` invocation rather than an official slash command.
_Avoid_: `/pet`, `/vup-pet`, built-in slash command

**VUP Pet Bridge**:
An optional local mechanism that lets a VUP Pet reflect secondary Codex activity state.
_Avoid_: required Codex internal event feed, replacement for realtime keyboard/mouse animation

**Custom Pet Package**:
A folder under `${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/` containing `pet.json` and `spritesheet.webp`.
_Avoid_: plugin, skill, app bundle, PyQt executable

**Asset Pack**:
The reusable source character images and metadata used to produce the final Codex pet spritesheet.
_Avoid_: PyQt resource folder

**Sprite Atlas**:
The fixed `1536x1872` transparent animation spritesheet consumed by the Codex app, arranged as 8 columns by 9 rows of `192x208` cells.
_Avoid_: arbitrary image folder, live DOM renderer, per-state PNG set

## Relationships

- A **Codex Pet** is toggled by the Codex desktop app through `/pet`.
- A **Custom Pet Package** defines one **Codex Pet**.
- A **Custom Pet Package** contains one **Sprite Atlas**.
- An **Asset Pack** is source material for producing a **Sprite Atlas**.
- A **VUP Pet Skill** launches or controls one **VUP Pet**.
- A **VUP Pet** may reuse the same **Asset Pack** without becoming a **Codex Pet**.
- A **VUP Pet** may read a **VUP Pet Bridge** without becoming a **Codex Pet**.

## Example Dialogue

> **Dev:** "Should we run the PyQt app when the user types `/pet`?"
> **Domain expert:** "No. Codex should load a Custom Pet Package from local Codex home, while the existing images become source material for the Sprite Atlas."

> **Dev:** "Can we keep realtime keyboard and mouse interaction?"
> **Domain expert:** "Yes, but that is a VUP Pet launched by a VUP Pet Skill, not an official Codex Pet package."

## Flagged Ambiguities

- "Codex 桌面应用的宠物" is resolved as **Codex Pet**, meaning the official Codex app pet overlay toggled by `/pet`, not an external desktop application.
- `/宠物` was used as a Chinese description of the pet command, but the official documented command is `/pet`.
- `/vup-pet` was proposed as the launcher command, but stable Codex skill invocation should be `$vup-pet`; a true slash command would require unsupported custom slash command support or patching Codex itself.
