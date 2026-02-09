/**
 * UploaderUI - User interface controller
 */
class UploaderUI {
  constructor() {
    this.activeDownloads = new Map();
    this.completedDownloads = [];
  }

  /**
   * Update connection status indicator
   */
  updateConnectionStatus(connected, url = '') {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    const addBtn = document.getElementById('add-queue-btn');

    if (connected) {
      dot.className = 'w-3 h-3 rounded-full bg-green-500';
      text.textContent = `Connected: ${url}`;
      text.className = 'text-sm text-green-400';
      addBtn.disabled = false;
    } else {
      dot.className = 'w-3 h-3 rounded-full bg-red-500';
      text.textContent = 'Disconnected';
      text.className = 'text-sm text-slate-400';
      addBtn.disabled = true;
    }
  }

  /**
   * Add a new download card to active section
   */
  addDownloadCard(id, url, filename = 'Downloading...') {
    const container = document.getElementById('active-downloads');

    if (this.activeDownloads.size === 0) {
      container.innerHTML = '';
    }

    const card = document.createElement('div');
    card.id = `download-${id}`;
    card.className =
      'bg-slate-700 rounded-lg p-4 border border-slate-600 transition-all';
    card.innerHTML = `
      <div class="flex items-start justify-between mb-2">
        <div class="flex-1 min-w-0">
          <div class="font-medium truncate" id="filename-${id}">${filename}</div>
          <div class="text-xs text-slate-400 truncate mt-1">${url}</div>
        </div>
        <button
          onclick="window.cancelDownload('${id}')"
          class="ml-3 p-1.5 text-red-400 hover:text-red-300 hover:bg-slate-600 rounded transition-colors"
          title="Cancel download"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="space-y-2">
        <div class="w-full bg-slate-600 rounded-full h-2">
          <div id="progress-bar-${id}" class="bg-blue-500 h-2 rounded-full transition-all" style="width: 0%"></div>
        </div>

        <div class="flex justify-between text-xs text-slate-400">
          <span id="progress-text-${id}">0%</span>
          <span id="size-text-${id}">-- / --</span>
        </div>

        <div class="flex justify-between text-xs text-slate-500">
          <span id="speed-text-${id}">--</span>
          <span id="eta-text-${id}">ETA: --</span>
        </div>
      </div>
    `;

    container.appendChild(card);
    this.activeDownloads.set(id, { url, filename });
    this.updateActiveCount();
  }

  /**
   * Update progress for a download
   */
  updateProgress(id, percent, speed, eta, downloaded, total) {
    const progressBar = document.getElementById(`progress-bar-${id}`);
    const progressText = document.getElementById(`progress-text-${id}`);
    const sizeText = document.getElementById(`size-text-${id}`);
    const speedText = document.getElementById(`speed-text-${id}`);
    const etaText = document.getElementById(`eta-text-${id}`);

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }
    if (progressText) {
      progressText.textContent = `${percent.toFixed(1)}%`;
    }
    if (sizeText) {
      sizeText.textContent = `${this.formatBytes(downloaded)} / ${this.formatBytes(total)}`;
    }
    if (speedText) {
      speedText.textContent = speed ? `${this.formatBytes(speed)}/s` : '--';
    }
    if (etaText) {
      etaText.textContent = eta ? `ETA: ${this.formatTime(eta)}` : 'ETA: --';
    }
  }

  /**
   * Move download from active to completed
   */
  moveToCompleted(id, filename, size, folder) {
    const card = document.getElementById(`download-${id}`);
    if (card) {
      card.remove();
    }

    this.activeDownloads.delete(id);
    this.completedDownloads.push({ id, filename, size, folder });

    if (this.activeDownloads.size === 0) {
      const container = document.getElementById('active-downloads');
      container.innerHTML =
        '<div class="text-center py-8 text-slate-400">No active downloads</div>';
    }

    this.updateActiveCount();
    this.updateCompletedList();
  }

  /**
   * Update completed downloads list
   */
  updateCompletedList() {
    const container = document.getElementById('completed-downloads');
    const count = document.getElementById('completed-count');

    count.textContent = this.completedDownloads.length;

    if (this.completedDownloads.length === 0) {
      container.innerHTML =
        '<div class="text-center py-4 text-slate-400">No completed downloads</div>';
      return;
    }

    container.innerHTML = this.completedDownloads
      .map(
        (item) => `
      <div class="flex items-center justify-between p-3 bg-slate-700 rounded-lg border border-slate-600">
        <div class="flex-1 min-w-0">
          <div class="font-medium truncate">${item.filename}</div>
          <div class="text-xs text-slate-400 mt-1">
            ${this.formatBytes(item.size)} ${item.folder ? `• ${item.folder}` : ''}
          </div>
        </div>
        <svg class="w-5 h-5 text-green-500 ml-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
    `
      )
      .join('');
  }

  /**
   * Update active downloads count
   */
  updateActiveCount() {
    const count = document.getElementById('active-count');
    count.textContent = this.activeDownloads.size;
  }

  /**
   * Show error toast notification
   */
  showError(message) {
    this.showToast(message, 'error');
  }

  /**
   * Show success toast notification
   */
  showSuccess(message) {
    this.showToast(message, 'success');
  }

  /**
   * Show toast notification
   */
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const id = `toast-${Date.now()}`;

    const colors = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      info: 'bg-blue-500',
    };

    toast.id = id;
    toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg max-w-sm toast-enter`;
    toast.innerHTML = `
      <div class="flex items-center justify-between gap-3">
        <span class="flex-1">${message}</span>
        <button onclick="document.getElementById('${id}').remove()" class="hover:opacity-75">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-exit');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  /**
   * Populate folder dropdown
   */
  populateFolderDropdown(folders) {
    const select = document.getElementById('folder-select');
    select.innerHTML = '<option value="">Root</option>';

    folders.forEach((folder) => {
      const option = document.createElement('option');
      option.value = folder.id;
      option.textContent = folder.name;
      select.appendChild(option);
    });
  }

  /**
   * Update storage quota display
   */
  updateQuota(used, total, percent) {
    const quotaText = document.getElementById('quota-text');
    const quotaBar = document.getElementById('quota-bar');

    quotaText.textContent = `${this.formatBytes(used)} / ${this.formatBytes(total)}`;
    quotaBar.style.width = `${percent}%`;

    if (percent > 90) {
      quotaBar.className = 'bg-red-500 h-2 rounded-full transition-all';
    } else if (percent > 75) {
      quotaBar.className = 'bg-yellow-500 h-2 rounded-full transition-all';
    } else {
      quotaBar.className = 'bg-blue-500 h-2 rounded-full transition-all';
    }
  }

  /**
   * Toggle theme between dark and light
   */
  toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('bg-slate-900');

    if (isDark) {
      body.className = 'bg-white text-slate-900 min-h-screen';
    } else {
      body.className = 'bg-slate-900 text-slate-100 min-h-screen';
    }

    localStorage.setItem('theme', isDark ? 'light' : 'dark');
  }

  /**
   * Format bytes to human readable format
   */
  formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }

  /**
   * Format seconds to human readable time
   */
  formatTime(seconds) {
    if (!seconds || seconds < 0) return '--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }
}
