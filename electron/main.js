const { app, BrowserWindow, session, Menu, shell } = require('electron');
const path = require('path');
const fs   = require('fs');

// ── Load target URL from config.json ────────────────────────────────────────
let TARGET_URL  = 'https://meet.google.com';
let APP_TITLE   = 'Google Meet';
let APP_WIDTH   = 1280;
let APP_HEIGHT  = 800;

const cfgPath = path.join(__dirname, 'config.json');
if (fs.existsSync(cfgPath)) {
  try {
    const cfg  = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
    TARGET_URL = cfg.url        || TARGET_URL;
    APP_TITLE  = cfg.title      || APP_TITLE;
    APP_WIDTH  = cfg.width      || APP_WIDTH;
    APP_HEIGHT = cfg.height     || APP_HEIGHT;
  } catch(_) {}
}

// ── Permission bypass — called BEFORE window loads ───────────────────────────
function patchPermissions() {
  const ses = session.defaultSession;

  // Auto-approve every permission request (camera, mic, geolocation, etc.)
  ses.setPermissionRequestHandler((_wc, _perm, callback) => {
    callback(true);
  });

  // Also bypass the synchronous permission check
  ses.setPermissionCheckHandler((_wc, _perm) => true);

  // Chromium device-access handler (getUserMedia at lower level)
  ses.setDevicePermissionHandler(() => true);
}

// ── Main window ──────────────────────────────────────────────────────────────
function createWindow() {
  patchPermissions();

  const win = new BrowserWindow({
    width:  APP_WIDTH,
    height: APP_HEIGHT,
    title:  APP_TITLE,
    icon:   path.join(__dirname, 'build', 'icon.png'),
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration:              false,
      contextIsolation:             true,
      allowRunningInsecureContent:  false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Remove native menu bar entirely
  Menu.setApplicationMenu(null);

  win.loadURL(TARGET_URL);

  // Keep navigation inside the same window (no popups)
  win.webContents.setWindowOpenHandler(({ url }) => {
    win.loadURL(url);
    return { action: 'deny' };
  });

  // Spoof User-Agent — strip Electron + app name, keep pure Chrome UA
  const realUA = win.webContents.getUserAgent()
    .replace(/Electron\/\S+\s?/, '')
    .replace(/SecureMeet\/\S+\s?/, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
  win.webContents.setUserAgent(realUA);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => { app.quit(); });
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
