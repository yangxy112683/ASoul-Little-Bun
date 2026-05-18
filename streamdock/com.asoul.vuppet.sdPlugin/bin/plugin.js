const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const WebSocket = require('ws');

const ACTION_UUID = 'com.asoul.vuppet.launch';
const PROJECT_ROOT = process.env.VUP_PET_PROJECT_ROOT
  || '/Users/dawn80s/work/personal/asoul_bongocat/ASoul-Little-Bun';
const LAUNCHER_PATH = path.join(PROJECT_ROOT, 'vup_pet_launcher.py');
const DEFAULT_PYTHON = fs.existsSync(path.join(PROJECT_ROOT, '.venv', 'bin', 'python3'))
  ? path.join(PROJECT_ROOT, '.venv', 'bin', 'python3')
  : 'python3';
const PYTHON = process.env.VUP_PET_PYTHON || DEFAULT_PYTHON;
const LOG_DIR = path.join(os.homedir(), 'Library', 'Application Support', 'HotSpot', 'StreamDock', 'logs');
const LOG_FILE = path.join(LOG_DIR, 'asoul-vup-pet-sdplugin.log');

let websocket = null;
let pluginUuid = null;
let registerEvent = null;
let port = null;

function log(message) {
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${message}\n`);
  } catch (_) {
    // Logging must not break the StreamDock action.
  }
}

function parseArgs(argv) {
  const result = {};
  for (let index = 2; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key || !key.startsWith('-')) {
      index -= 1;
      continue;
    }
    result[key.replace(/^-+/, '')] = value;
  }
  return result;
}

function send(event, context, payload = {}) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    return;
  }
  const message = { event, context, payload };
  websocket.send(JSON.stringify(message));
}

function setTitle(context, title) {
  send('setTitle', context, {
    title,
    target: 0
  });
}

function showOk(context) {
  send('showOk', context);
}

function showAlert(context) {
  send('showAlert', context);
}

function runLauncher(command, callback) {
  if (!fs.existsSync(LAUNCHER_PATH)) {
    callback(new Error(`launcher not found: ${LAUNCHER_PATH}`), '', '');
    return;
  }

  const child = spawn(PYTHON, [LAUNCHER_PATH, command], {
    cwd: PROJECT_ROOT,
    env: {
      ...process.env,
      VUP_PET_PROJECT_ROOT: PROJECT_ROOT,
      VUP_PET_PYTHON: PYTHON
    },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  let stdout = '';
  let stderr = '';
  child.stdout.on('data', data => {
    stdout += data.toString();
  });
  child.stderr.on('data', data => {
    stderr += data.toString();
  });
  child.on('error', error => {
    callback(error, stdout, stderr);
  });
  child.on('close', code => {
    if (code === 0) {
      callback(null, stdout, stderr);
      return;
    }
    callback(new Error(`launcher exited with code ${code}`), stdout, stderr);
  });
}

function handleLaunch(context) {
  setTitle(context, '启动中');
  runLauncher('start', (error, stdout, stderr) => {
    if (error) {
      log(`start failed: ${error.message}; stderr=${stderr.trim()}; stdout=${stdout.trim()}`);
      setTitle(context, '启动失败');
      showAlert(context);
      return;
    }

    log(`start ok: ${stdout.trim()}`);
    setTitle(context, '桌宠已开');
    showOk(context);
  });
}

function handleStatus(context) {
  runLauncher('status', (error, stdout, stderr) => {
    if (error) {
      log(`status failed: ${error.message}; stderr=${stderr.trim()}; stdout=${stdout.trim()}`);
      setTitle(context, '状态异常');
      return;
    }

    try {
      const payload = JSON.parse(stdout);
      setTitle(context, payload.running ? '桌宠已开' : '启动桌宠');
    } catch (_) {
      setTitle(context, '启动桌宠');
    }
  });
}

function handleMessage(raw) {
  let data;
  try {
    data = JSON.parse(raw);
  } catch (error) {
    log(`invalid websocket message: ${error.message}`);
    return;
  }

  if (data.action !== ACTION_UUID) {
    return;
  }

  if (data.event === 'keyUp') {
    handleLaunch(data.context);
    return;
  }

  if (data.event === 'willAppear') {
    setTitle(data.context, '启动桌宠');
    handleStatus(data.context);
  }
}

function connect() {
  const args = parseArgs(process.argv);
  port = args.port;
  pluginUuid = args.pluginUUID;
  registerEvent = args.registerEvent;

  if (!port || !pluginUuid || !registerEvent) {
    log(`missing StreamDock args: ${JSON.stringify(args)}`);
    process.exit(1);
  }

  websocket = new WebSocket(`ws://127.0.0.1:${port}`);
  websocket.on('open', () => {
    websocket.send(JSON.stringify({
      event: registerEvent,
      uuid: pluginUuid
    }));
    log('connected');
  });
  websocket.on('message', handleMessage);
  websocket.on('error', error => {
    log(`websocket error: ${error.message}`);
  });
  websocket.on('close', () => {
    log('websocket closed');
  });
}

connect();
