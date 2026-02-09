/**
 * UploaderAPI - Client for Google Drive Uploader API
 */
class UploaderAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  /**
   * Check if server is healthy and accessible
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseURL}/api/health`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  /**
   * Submit a new download request
   */
  async submitDownload(url, folder = '', format = '') {
    try {
      const response = await fetch(`${this.baseURL}/api/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          folder,
          format: format || undefined,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Submit failed: ${error.message}`);
    }
  }

  /**
   * Get current download queue
   */
  async getQueue() {
    try {
      const response = await fetch(`${this.baseURL}/api/queue`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Get queue failed: ${error.message}`);
    }
  }

  /**
   * Cancel a download by ID
   */
  async cancelDownload(id) {
    try {
      const response = await fetch(`${this.baseURL}/api/download/${id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Cancel failed: ${error.message}`);
    }
  }

  /**
   * Get list of available folders in Google Drive
   */
  async getFolders() {
    try {
      const response = await fetch(`${this.baseURL}/api/folders`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Get folders failed: ${error.message}`);
    }
  }

  /**
   * Create a new folder in Google Drive
   */
  async createFolder(name, parentId = null) {
    try {
      const response = await fetch(`${this.baseURL}/api/folders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          parent: parentId,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Create folder failed: ${error.message}`);
    }
  }

  /**
   * Get storage quota information
   */
  async getQuota() {
    try {
      const response = await fetch(`${this.baseURL}/api/quota`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Get quota failed: ${error.message}`);
    }
  }

  /**
   * Create a Server-Sent Events stream for real-time progress updates
   */
  createProgressStream(downloadId, onProgress, onComplete, onError) {
    const eventSource = new EventSource(
      `${this.baseURL}/api/progress/${downloadId}`
    );

    eventSource.addEventListener('progress', (event) => {
      try {
        const data = JSON.parse(event.data);
        onProgress(data);
      } catch (error) {
        onError(new Error(`Parse progress error: ${error.message}`));
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        onComplete(data);
        eventSource.close();
      } catch (error) {
        onError(new Error(`Parse complete error: ${error.message}`));
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (event) => {
      try {
        const data = event.data ? JSON.parse(event.data) : {};
        onError(new Error(data.error || 'Stream error'));
      } catch (error) {
        onError(new Error('Stream connection error'));
      }
      eventSource.close();
    });

    eventSource.onerror = () => {
      onError(new Error('Connection lost'));
      eventSource.close();
    };

    return eventSource;
  }
}
