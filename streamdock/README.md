# ASoul VUP Pet StreamDock Plugin

This folder contains a local StreamDock sdPlugin that adds a keypad action for starting the ASoul Little Bun desktop pet.

The installed plugin folder is:

```text
/Users/dawn80s/Library/Application Support/HotSpot/StreamDock/plugins/com.asoul.vuppet.sdPlugin
```

The action launches:

```text
/Users/dawn80s/work/personal/asoul_bongocat/ASoul-Little-Bun/vup_pet_launcher.py start
```

It prefers the project virtualenv at `.venv/bin/python3` when present, otherwise it falls back to `python3`.

Logs are written to:

```text
/Users/dawn80s/Library/Application Support/HotSpot/StreamDock/logs/asoul-vup-pet-sdplugin.log
```
