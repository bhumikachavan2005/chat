/**
 * Authenticated Local API Client
 * - Attaches X-Archive-Token header
 * - Auto-triggers lock screen on 401 Unauthorized
 * - Zero external dependencies
 */

const API = {
  tokenKey: "vinu_bhumi_archive_token",

  getToken() {
    return sessionStorage.getItem(this.tokenKey);
  },

  setToken(token) {
    if (token) {
      sessionStorage.setItem(this.tokenKey, token);
    } else {
      sessionStorage.removeItem(this.tokenKey);
    }
  },

  clearToken() {
    sessionStorage.removeItem(this.tokenKey);
  },

  getBaseUrl() {
    if (window.location.protocol === "file:" || !window.location.port) {
      return "http://127.0.0.1:8765";
    }
    return "";
  },

  async request(endpoint, options = {}) {
    const base = this.getBaseUrl();
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = endpoint.startsWith("http") ? endpoint : `${base}${cleanEndpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token) {
      headers["X-Archive-Token"] = token;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"] && options.method && options.method !== "GET") {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401 && !endpoint.includes("/api/auth/login") && !endpoint.includes("/api/auth/setup") && !endpoint.includes("/api/wrapped/verify-pin")) {
        // Session expired or unauthorized for data endpoints
        this.clearToken();
        if (window.App && typeof window.App.showLockScreen === "function") {
          window.App.showLockScreen();
        }
        throw new Error("Session expired or unauthorized. Please unlock.");
      }

      // Check if binary download response (like encrypted backup)
      const disposition = response.headers.get("Content-Disposition");
      if (disposition && disposition.includes("attachment")) {
        const blob = await response.blob();
        return { blob, filename: disposition.split("filename=")[1]?.replace(/"/g, "") || "backup.enc" };
      }

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Request failed");
      }

      return data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      if (err.name === "TypeError" && (err.message.includes("fetch") || err.message.includes("NetworkError"))) {
        throw new Error("Cannot connect to server. Please ensure start.bat is running, or visit http://127.0.0.1:8765");
      }
      throw err;
    }
  },

  // Auth Endpoints
  auth: {
    status() { return API.request("/api/auth/status"); },
    setup(password) { return API.request("/api/auth/setup", { method: "POST", body: JSON.stringify({ password }) }); },
    login(password) { return API.request("/api/auth/login", { method: "POST", body: JSON.stringify({ password }) }); },
    logout() { return API.request("/api/auth/logout", { method: "POST" }); },
    changePassword(current_password, new_password) {
      return API.request("/api/auth/change-password", { method: "POST", body: JSON.stringify({ current_password, new_password }) });
    },
    lockSettings(timeout_minutes) {
      return API.request("/api/auth/lock-settings", { method: "POST", body: JSON.stringify({ timeout_minutes }) });
    }
  },

  // Chat Endpoints
  chat: {
    getBounds() { return API.request("/api/chat/bounds"); },
    getMessages(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/chat/messages?${query}`);
    },
    getAround(messageId, contextSize = 15) {
      return API.request(`/api/chat/around/${messageId}?context_size=${contextSize}`);
    },
    getMessage(messageId) {
      return API.request(`/api/chat/message/${messageId}`);
    },
    jumpDate(dateStr) {
      return API.request(`/api/chat/jump-date?date=${encodeURIComponent(dateStr)}`);
    },
    getOffset(messageId, params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/chat/offset/${messageId}?${query}`);
    },
    getRandom() {
      return API.request("/api/chat/random");
    }
  },

  // Search Endpoints
  search: {
    query(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/search?${query}`);
    }
  },

  // Memory Endpoints
  memories: {
    list(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/memories?${query}`);
    },
    stats() { return API.request("/api/memories/stats"); },
    create(data) { return API.request("/api/memories", { method: "POST", body: JSON.stringify(data) }); },
    update(id, data) { return API.request(`/api/memories/${id}`, { method: "PUT", body: JSON.stringify(data) }); },
    delete(id) { return API.request(`/api/memories/${id}`, { method: "DELETE" }); }
  },

  // Stats Endpoints
  stats: {
    overview() { return API.request("/api/stats/overview"); },
    timeline() { return API.request("/api/stats/timeline"); },
    evolution(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/stats/evolution?${query}`);
    }
  },

  // Insights & Funny Moments
  insights: {
    prebuilt() { return API.request("/api/insights/prebuilt"); },
    query(id) { return API.request(`/api/insights/query/${id}`); },
    ask(query) { return API.request("/api/insights/ask", { method: "POST", body: JSON.stringify({ query }) }); },
    funnyMoments(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/funny/moments?${query}`);
    },
    setFunnyStatus(message_id, status) {
      return API.request("/api/funny/status", { method: "POST", body: JSON.stringify({ message_id, status }) });
    }
  },

  // System & Backup
  system: {
    exportBackup(passphrase) {
      return API.request("/api/system/export-backup", { method: "POST", body: JSON.stringify({ passphrase }) });
    },
    async restoreBackup(file, passphrase) {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("passphrase", passphrase);
      return API.request("/api/system/restore-backup", { method: "POST", body: fd });
    },
    async importTxt(file) {
      const fd = new FormData();
      fd.append("file", file);
      return API.request("/api/system/import-txt", { method: "POST", body: fd });
    },
    wipe() { return API.request("/api/system/wipe", { method: "POST" }); },
    wipeAll(password) {
      return API.request("/api/system/wipe-all", { method: "POST", body: JSON.stringify({ password }) });
    }
  },

  // Media Endpoints
  media: {
    getItems(params = {}) {
      const query = new URLSearchParams(params).toString();
      return API.request(`/api/media/items?${query}`);
    }
  },

  // Wrapped Endpoints
  wrapped: {
    getStory() { return API.request("/api/wrapped/story"); },
    getPinStatus() { return API.request("/api/wrapped/pin-status"); },
    verifyPin(pin) { return API.request("/api/wrapped/verify-pin", { method: "POST", body: JSON.stringify({ pin }) }); },
    setPin(pin) { return API.request("/api/wrapped/set-pin", { method: "POST", body: JSON.stringify({ pin }) }); },
    getPhotos() { return API.request("/api/wrapped/photos"); },
    uploadPhoto(formData) { return API.request("/api/wrapped/photos/upload", { method: "POST", body: formData }); },
    deletePhoto(id) { return API.request(`/api/wrapped/photos/${id}`, { method: "DELETE" }); }
  },

  // Quiz Endpoints
  quiz: {
    getQuestions() { return API.request("/api/quiz/questions"); }
  }
};
