#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

SUPPORTED_STATES = {'idle', 'running', 'waiting', 'review', 'failed'}
SUPPORTED_NOTIFICATION_SOURCES = {'codex', 'codebuddy', 'launcher'}
SUPPORTED_NOTIFICATION_LEVELS = {'info', 'success', 'warning', 'error'}
MAX_NOTIFICATION_QUEUE_SIZE = 1024 * 1024
NOTIFICATION_LOCK_TIMEOUT_SECONDS = 2.0


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def get_codex_home():
    return Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser()


def get_data_dir():
    return get_codex_home() / 'vup-pet'


def get_pid_file():
    return get_data_dir() / 'pid.json'


def get_state_file():
    return get_data_dir() / 'state.json'


def get_log_file():
    return get_data_dir() / 'launcher.log'


def get_notification_file():
    return get_data_dir() / 'notifications.jsonl'


def get_rotated_notification_file():
    return get_data_dir() / 'notifications.jsonl.1'


def get_notification_cursor_file():
    return get_data_dir() / 'notification_cursor.json'


def get_notification_lock_file():
    return get_data_dir() / 'notifications.lock'


def get_hook_log_file():
    return Path('/tmp/vup-pet-hook-notify.log')


def get_project_root():
    override = os.environ.get('VUP_PET_PROJECT_ROOT')
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent


def atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f'.{path.name}.tmp')
    with temp_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(temp_path, path)


def read_json(path):
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def is_process_running(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def read_pid_info():
    data = read_json(get_pid_file())
    return data if isinstance(data, dict) else {}


def get_recorded_pid():
    pid = read_pid_info().get('pid')
    return pid if isinstance(pid, int) else None


def remove_pid_file():
    try:
        get_pid_file().unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def write_state(state, message):
    if state not in SUPPORTED_STATES:
        raise ValueError(f'unsupported state: {state}')
    atomic_write_json(get_state_file(), {
        'source': 'vup-pet-launcher',
        'state': state,
        'message': message,
        'updatedAt': utc_now(),
    })


def log_hook_error(message):
    try:
        with get_hook_log_file().open('a', encoding='utf-8') as f:
            f.write(f'[{utc_now()}] {message}\n')
    except OSError:
        pass


def truncate_text(text, limit=120):
    text = str(text or '').replace('\n', ' ').strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1] + '…'


def notification_title(source):
    return {
        'codex': 'Codex',
        'codebuddy': 'CodeBuddy',
        'launcher': 'VUP Pet',
    }.get(source, source)


def build_notification_event(source, event, message, level='info', ttl_seconds=120, raw=None):
    if source not in SUPPORTED_NOTIFICATION_SOURCES:
        raise ValueError(f'unsupported notification source: {source}')
    if level not in SUPPORTED_NOTIFICATION_LEVELS:
        raise ValueError(f'unsupported notification level: {level}')

    created_at = utc_now()
    title = notification_title(source)
    message = truncate_text(message or 'Notification')
    display_text = truncate_text(f'{title}: {message}')
    digest = hashlib.sha1(f'{created_at}:{source}:{event}:{message}'.encode('utf-8')).hexdigest()[:8]
    event_id = f'{created_at}-{source}-{event.lower()}-{digest}'
    payload = {
        'id': event_id,
        'source': source,
        'event': event,
        'level': level,
        'title': title,
        'message': message,
        'displayText': display_text,
        'createdAt': created_at,
        'ttlSeconds': int(ttl_seconds),
    }
    if raw is not None:
        payload['raw'] = raw
    return payload


def rotate_notifications_if_needed():
    queue_file = get_notification_file()
    if not queue_file.exists() or queue_file.stat().st_size <= MAX_NOTIFICATION_QUEUE_SIZE:
        return

    rotated_file = get_rotated_notification_file()
    try:
        rotated_file.unlink()
    except FileNotFoundError:
        pass
    queue_file.replace(rotated_file)


def append_notification(notification, timeout_seconds=NOTIFICATION_LOCK_TIMEOUT_SECONDS):
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_file = get_notification_lock_file()
    queue_file = get_notification_file()

    if fcntl is None:
        message = 'fcntl is unavailable; notification queue append skipped'
        log_hook_error(message)
        return False, message

    deadline = time.monotonic() + timeout_seconds
    locked = False
    try:
        with lock_file.open('a+', encoding='utf-8') as lock:
            while True:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        message = 'notification lock timeout'
                        log_hook_error(message)
                        return False, message
                    time.sleep(0.05)

            rotate_notifications_if_needed()
            with queue_file.open('a', encoding='utf-8') as queue:
                queue.write(json.dumps(notification, ensure_ascii=False, separators=(',', ':')))
                queue.write('\n')
                queue.flush()
                os.fsync(queue.fileno())
        return True, None
    except OSError as exc:
        message = f'notification append failed: {exc}'
        log_hook_error(message)
        return False, message
    finally:
        if locked:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            except (NameError, OSError, ValueError):
                pass


def file_size(path):
    try:
        return path.stat().st_size
    except OSError:
        return 0


def status_payload():
    pid_info = read_pid_info()
    pid = pid_info.get('pid') if isinstance(pid_info.get('pid'), int) else None
    state_file = get_state_file()
    pid_file = get_pid_file()
    notification_file = get_notification_file()
    rotated_notification_file = get_rotated_notification_file()
    notification_cursor_file = get_notification_cursor_file()
    notification_lock_file = get_notification_lock_file()
    return {
        'running': is_process_running(pid),
        'pid': pid,
        'projectRoot': str(get_project_root()),
        'pidFile': str(pid_file),
        'pidFilePresent': pid_file.exists(),
        'stateFile': str(state_file),
        'stateFilePresent': state_file.exists(),
        'logFile': str(get_log_file()),
        'logFilePresent': get_log_file().exists(),
        'notificationQueueFile': str(notification_file),
        'notificationQueueFilePresent': notification_file.exists(),
        'notificationQueueFileSize': file_size(notification_file),
        'notificationRotatedFile': str(rotated_notification_file),
        'notificationRotatedFilePresent': rotated_notification_file.exists(),
        'notificationCursorFile': str(notification_cursor_file),
        'notificationCursorFilePresent': notification_cursor_file.exists(),
        'notificationLockFile': str(notification_lock_file),
        'notificationLockFilePresent': notification_lock_file.exists(),
        'state': read_json(state_file),
    }


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def start_pet():
    existing_pid = get_recorded_pid()
    if is_process_running(existing_pid):
        payload = status_payload()
        payload['message'] = 'VUP Pet is already running.'
        print_json(payload)
        return 0

    project_root = get_project_root()
    main_py = project_root / 'main.py'
    if not main_py.exists():
        write_state('failed', f'main.py not found: {main_py}')
        print_json({'running': False, 'error': f'main.py not found: {main_py}'})
        return 1

    python = os.environ.get('VUP_PET_PYTHON') or sys.executable
    command = [python, str(main_py)]

    get_data_dir().mkdir(parents=True, exist_ok=True)
    log_file = get_log_file()
    popen_kwargs = {
        'cwd': str(project_root),
        'stdin': subprocess.DEVNULL,
    }
    if sys.platform == 'win32':
        popen_kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs['start_new_session'] = True

    try:
        with log_file.open('ab') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, **popen_kwargs)
    except OSError as exc:
        write_state('failed', f'failed to start VUP Pet: {exc}')
        print_json({'running': False, 'error': str(exc), 'logFile': str(log_file)})
        return 1

    try:
        exit_code = process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        exit_code = None

    if exit_code is not None:
        write_state('failed', f'VUP Pet exited during startup with code {exit_code}.')
        print_json({
            'running': False,
            'pid': process.pid,
            'exitCode': exit_code,
            'error': 'VUP Pet exited during startup.',
            'logFile': str(log_file),
        })
        return 1

    atomic_write_json(get_pid_file(), {
        'pid': process.pid,
        'projectRoot': str(project_root),
        'command': command,
        'startedAt': utc_now(),
    })
    write_state('running', 'VUP Pet started.')

    payload = status_payload()
    payload['message'] = 'VUP Pet started.'
    print_json(payload)
    return 0


def stop_pet():
    pid = get_recorded_pid()
    if not is_process_running(pid):
        remove_pid_file()
        write_state('idle', 'VUP Pet is not running.')
        payload = status_payload()
        payload['message'] = 'VUP Pet is not running.'
        print_json(payload)
        return 0

    try:
        if sys.platform == 'win32':
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        write_state('failed', f'failed to stop VUP Pet: {exc}')
        print_json({'running': True, 'pid': pid, 'error': str(exc)})
        return 1

    deadline = time.time() + 5
    while time.time() < deadline:
        if not is_process_running(pid):
            remove_pid_file()
            write_state('idle', 'VUP Pet stopped.')
            payload = status_payload()
            payload['message'] = 'VUP Pet stopped.'
            print_json(payload)
            return 0
        time.sleep(0.2)

    write_state('failed', 'VUP Pet did not stop after terminate signal.')
    print_json({
        'running': True,
        'pid': pid,
        'message': 'Terminate signal sent, but the process is still running. Manual cleanup may be required.',
    })
    return 1


def notify_pet(source, event, message, level='info', ttl_seconds=120):
    try:
        notification = build_notification_event(
            source=source,
            event=event,
            message=message,
            level=level,
            ttl_seconds=ttl_seconds,
            raw={'source': 'vup_pet_launcher'},
        )
    except ValueError as exc:
        print_json({'ok': False, 'error': str(exc)})
        return 1

    ok, error = append_notification(notification)
    print_json({
        'ok': ok,
        'error': error,
        'notification': notification,
        'notificationQueueFile': str(get_notification_file()),
    })
    return 0


def show_status():
    print_json(status_payload())
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Launch and control the ASoul Little Bun VUP Pet.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('start', help='start the VUP Pet')
    subparsers.add_parser('stop', help='stop the VUP Pet')
    subparsers.add_parser('status', help='show process and bridge status')
    notify_parser = subparsers.add_parser('notify', help='append a hook notification event')
    notify_parser.add_argument('--source', required=True, choices=sorted(SUPPORTED_NOTIFICATION_SOURCES))
    notify_parser.add_argument('--event', required=True)
    notify_parser.add_argument('--message', required=True)
    notify_parser.add_argument('--level', default='info', choices=sorted(SUPPORTED_NOTIFICATION_LEVELS))
    notify_parser.add_argument('--ttl-seconds', type=int, default=120)

    args = parser.parse_args(argv)
    if args.command == 'start':
        return start_pet()
    if args.command == 'stop':
        return stop_pet()
    if args.command == 'status':
        return show_status()
    if args.command == 'notify':
        return notify_pet(args.source, args.event, args.message, args.level, args.ttl_seconds)
    return 1


if __name__ == '__main__':
    sys.exit(main())
