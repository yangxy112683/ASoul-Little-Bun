#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vup_pet_launcher import append_notification, build_notification_event, log_hook_error, truncate_text

SUPPORTED_CODEBUDDY_TYPES = {'permission_prompt', 'idle_prompt'}


def read_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError as exc:
        log_hook_error(f'hook payload json decode failed: {exc}')
        return {}


def raw_payload_for_debug(payload):
    allowed_keys = ('hook_event_name', 'notification_type', 'message')
    return {
        key: truncate_text(payload.get(key), 240)
        for key in allowed_keys
        if key in payload
    }


def normalize_codex(event, payload):
    if event != 'Stop':
        return None
    message = payload.get('message') or 'Task finished'
    return build_notification_event(
        source='codex',
        event='Stop',
        level='success',
        message=message,
        ttl_seconds=120,
        raw=raw_payload_for_debug(payload),
    )


def normalize_codebuddy(event, payload):
    if event != 'Notification':
        return None

    notification_type = payload.get('notification_type')
    if notification_type not in SUPPORTED_CODEBUDDY_TYPES:
        return None

    if notification_type == 'permission_prompt':
        fallback_message = 'CodeBuddy needs permission'
        level = 'warning'
    else:
        fallback_message = 'CodeBuddy is waiting for input'
        level = 'info'

    return build_notification_event(
        source='codebuddy',
        event='Notification',
        level=level,
        message=payload.get('message') or fallback_message,
        ttl_seconds=120,
        raw=raw_payload_for_debug(payload),
    )


def normalize_event(source, event, payload):
    if source == 'codex':
        return normalize_codex(event, payload)
    if source == 'codebuddy':
        return normalize_codebuddy(event, payload)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Normalize hook notifications for VUP Pet.')
    parser.add_argument('--source', required=True, choices=('codex', 'codebuddy'))
    parser.add_argument('--event', required=True)
    args = parser.parse_args(argv)

    try:
        payload = read_payload()
        notification = normalize_event(args.source, args.event, payload)
        if notification is not None:
            append_notification(notification)
    except Exception as exc:  # fail-open：不能阻塞 hook 调用方
        log_hook_error(f'hook adapter failed open: {exc}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
