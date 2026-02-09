/**
 * Main application logic
 */

let api;
let ui;
let pollInterval;

document.addEventListener('DOMContentLoaded', () => {
  const savedURL = localStorage.getItem('serverURL') || '';
  const serverInput = document.getElementById('server-url');

  if (savedURL) {
    serverInput.value = savedURL;
  }

  api = new UploaderAPI(savedURL);
  ui = new UploaderUI();

  initializeEventListeners();
  loadTheme();

  if (savedURL) {
    tryConnect(savedURL);
  }
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
  document
    .getElementById('connect-btn')
    .addEventListener('click', handleConnect);
  document
    .getElementById('add-queue-btn')
    .addEventListener('click', handleSubmitDownload);
  document
    .getElementById('theme-toggle')
    .addEventListener('click', () => ui.toggleTheme());
  document
    .getElementById('toggle-completed')
    .addEventListener('click', toggleCompleted);
  document
    .getElementById('clear-completed')
    .addEventListener('click', clearCompleted);
  document
    .getElementById('new-folder-btn')
    .addEventListener('click', showNewFolderModal);
  document
    .getElementById('cancel-folder-btn')
    .addEventListener('click', hideNewFolderModal);
  document
    .getElementById('create-folder-btn')
    .addEventListener('click', handleCreateFolder);

  document.getElementById('server-url').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleConnect();
    }
  });
}

/**
 * Handle server connection
 */
async function handleConnect() {
  const serverInput = document.getElementById('server-url');
  const url = serverInput.value.trim();

  if (!url) {
    ui.showError('Please enter a server URL');
    return;
  }

  await tryConnect(url);
}

/**
 * Attempt to connect to server
 */
async function tryConnect(url) {
  const connectBtn = document.getElementById('connect-btn');
  connectBtn.disabled = true;
  connectBtn.textContent = 'Connecting...';

  try {
    api = new UploaderAPI(url);
    const health = await api.checkHealth();

    if (health.status === 'ok') {
      localStorage.setItem('serverURL', url);
      ui.updateConnectionStatus(true, url);
      ui.showSuccess('Connected to server');

      await loadFolders();
      await loadQuota();
      startPolling();
    } else {
      throw new Error('Server returned unhealthy status');
    }
  } catch (error) {
    ui.showError(`Connection failed: ${error.message}`);
    ui.updateConnectionStatus(false);
  } finally {
    connectBtn.disabled = false;
    connectBtn.textContent = 'Connect';
  }
}

/**
 * Handle download submission
 */
async function handleSubmitDownload() {
  const urlInput = document.getElementById('url-input');
  const folderSelect = document.getElementById('folder-select');
  const formatSelect = document.getElementById('format-select');

  const urls = urlInput.value
    .split('\n')
    .map((u) => u.trim())
    .filter((u) => u.length > 0);

  if (urls.length === 0) {
    ui.showError('Please enter at least one URL');
    return;
  }

  const folder = folderSelect.value;
  const format = formatSelect.value;

  for (const url of urls) {
    try {
      const result = await api.submitDownload(url, folder, format);
      ui.addDownloadCard(result.id, url, result.filename || 'Processing...');
      ui.showSuccess(`Added: ${url.substring(0, 50)}...`);

      startProgressStream(result.id);
    } catch (error) {
      ui.showError(`Failed to add ${url}: ${error.message}`);
    }
  }

  urlInput.value = '';
}

/**
 * Start progress stream for a download
 */
function startProgressStream(downloadId) {
  api.createProgressStream(
    downloadId,
    (data) => {
      const filenameEl = document.getElementById(`filename-${downloadId}`);
      if (filenameEl && data.filename) {
        filenameEl.textContent = data.filename;
      }

      ui.updateProgress(
        downloadId,
        data.percent || 0,
        data.speed || 0,
        data.eta || 0,
        data.downloaded || 0,
        data.total || 0
      );
    },
    (data) => {
      ui.moveToCompleted(
        downloadId,
        data.filename,
        data.size || 0,
        data.folder || ''
      );
      ui.showSuccess(`Completed: ${data.filename}`);
      loadQuota();
    },
    (error) => {
      ui.showError(`Download failed: ${error.message}`);
      const card = document.getElementById(`download-${downloadId}`);
      if (card) {
        card.classList.add('border-red-500');
      }
    }
  );
}

/**
 * Cancel a download
 */
window.cancelDownload = async function (id) {
  try {
    await api.cancelDownload(id);
    const card = document.getElementById(`download-${id}`);
    if (card) {
      card.remove();
    }
    ui.showSuccess('Download cancelled');
  } catch (error) {
    ui.showError(`Cancel failed: ${error.message}`);
  }
};

/**
 * Load folders from server
 */
async function loadFolders() {
  try {
    const folders = await api.getFolders();
    ui.populateFolderDropdown(folders.folders || []);
  } catch (error) {
    ui.showError(`Failed to load folders: ${error.message}`);
  }
}

/**
 * Load storage quota
 */
async function loadQuota() {
  try {
    const quota = await api.getQuota();
    const used = quota.used || 0;
    const total = quota.total || 1;
    const percent = (used / total) * 100;
    ui.updateQuota(used, total, percent);
  } catch (error) {
    ui.showError(`Failed to load quota: ${error.message}`);
  }
}

/**
 * Start polling queue
 */
function startPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
  }

  pollInterval = setInterval(async () => {
    try {
      await api.checkHealth();
    } catch (error) {
      ui.updateConnectionStatus(false);
      clearInterval(pollInterval);
      ui.showError('Connection lost');
    }
  }, 5000);
}

/**
 * Toggle completed section visibility
 */
function toggleCompleted() {
  const section = document.getElementById('completed-downloads');
  const button = document.getElementById('toggle-completed');

  if (section.classList.contains('hidden')) {
    section.classList.remove('hidden');
    button.textContent = 'Hide';
  } else {
    section.classList.add('hidden');
    button.textContent = 'Show';
  }
}

/**
 * Clear completed downloads
 */
function clearCompleted() {
  ui.completedDownloads = [];
  ui.updateCompletedList();
  ui.showSuccess('Cleared completed downloads');
}

/**
 * Show new folder modal
 */
function showNewFolderModal() {
  const modal = document.getElementById('new-folder-modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  document.getElementById('new-folder-name').focus();
}

/**
 * Hide new folder modal
 */
function hideNewFolderModal() {
  const modal = document.getElementById('new-folder-modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.getElementById('new-folder-name').value = '';
}

/**
 * Handle folder creation
 */
async function handleCreateFolder() {
  const nameInput = document.getElementById('new-folder-name');
  const name = nameInput.value.trim();

  if (!name) {
    ui.showError('Please enter a folder name');
    return;
  }

  try {
    await api.createFolder(name);
    ui.showSuccess(`Created folder: ${name}`);
    hideNewFolderModal();
    await loadFolders();
  } catch (error) {
    ui.showError(`Failed to create folder: ${error.message}`);
  }
}

/**
 * Load theme from localStorage
 */
function loadTheme() {
  const theme = localStorage.getItem('theme') || 'dark';
  if (theme === 'light') {
    document.body.className = 'bg-white text-slate-900 min-h-screen';
  }
}
