/**
 * Central Application Controller
 * - Master password setup & login flow
 * - Inactivity detector & auto-lock lifecycle
 * - SPA Tab Router
 * - Memory Modal Controller
 * - Dark / Light Theme Manager
 */

window.App = {
  currentTab: "chat",
  inactivityTimeoutMinutes: 15,
  inactivityTimer: null,
  theme: "dark",

  async init() {
    this.initTheme();
    this.bindGlobalEvents();
    this.bindAuthEvents();
    this.bindMemoryModalEvents();

    // Initialize Components
    ChatComponent.init();
    SearchComponent.init();
    SettingsComponent.init();

    await this.checkAuthStatus();
  },

  // ---------------- Theme Management ----------------
  initTheme() {
    const savedTheme = localStorage.getItem("archive_theme") || "dark";
    this.setTheme(savedTheme);

    const toggleBtn = document.getElementById("themeToggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const nextTheme = this.theme === "dark" ? "light" : "dark";
        this.setTheme(nextTheme);
      });
    }
  },

  setTheme(themeName) {
    this.theme = themeName;
    document.documentElement.setAttribute("data-theme", themeName);
    localStorage.setItem("archive_theme", themeName);
    const icon = document.getElementById("themeIcon");
    if (icon) {
      icon.textContent = themeName === "dark" ? "🌙" : "☀️";
    }
  },

  // ---------------- Authentication & Lock Lifecycle ----------------
  async checkAuthStatus() {
    const offlineBanner = document.getElementById("serverOfflineBanner");
    try {
      const status = await API.auth.status();
      if (offlineBanner) offlineBanner.classList.add("hidden");
      this.inactivityTimeoutMinutes = status.auto_lock_minutes || 15;

      const timeoutSelect = document.getElementById("selectLockTimeout");
      if (timeoutSelect) timeoutSelect.value = String(this.inactivityTimeoutMinutes);

      const setupForm = document.getElementById("setupForm");
      const loginForm = document.getElementById("loginForm");

      if (!status.has_password) {
        // First-time initialization
        if (setupForm) setupForm.classList.remove("hidden");
        if (loginForm) loginForm.classList.add("hidden");
        this.showLockScreen();
      } else if (status.is_authenticated) {
        // Valid existing session
        this.unlockApp();
      } else {
        // Master password exists, prompt login
        if (setupForm) setupForm.classList.add("hidden");
        if (loginForm) loginForm.classList.remove("hidden");
        this.showLockScreen();
      }
    } catch (err) {
      console.error("Auth check failed:", err);
      if (offlineBanner) offlineBanner.classList.remove("hidden");
      this.showLockScreen();
    }
  },

  bindAuthEvents() {
    // Setup form
    const setupForm = document.getElementById("setupForm");
    const setupErr = document.getElementById("setupError");
    if (setupForm) {
      setupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const p1 = document.getElementById("setupPassword")?.value;
        const p2 = document.getElementById("setupPasswordConfirm")?.value;

        if (p1 !== p2) {
          if (setupErr) {
            setupErr.textContent = "Passwords do not match!";
            setupErr.classList.remove("hidden");
          }
          return;
        }

        try {
          const res = await API.auth.setup(p1);
          API.setToken(res.token);
          this.unlockApp();
        } catch (err) {
          if (setupErr) {
            setupErr.textContent = err.message;
            setupErr.classList.remove("hidden");
          }
        }
      });
    }

    // Login form
    const loginForm = document.getElementById("loginForm");
    const loginErr = document.getElementById("loginError");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pass = document.getElementById("loginPassword")?.value;
        if (!pass) return;

        try {
          const res = await API.auth.login(pass);
          API.setToken(res.token);
          this.unlockApp();
        } catch (err) {
          if (loginErr) {
            loginErr.textContent = err.message || "Incorrect password.";
            loginErr.classList.remove("hidden");
          }
        }
      });
    }

    // Password Reveal Eye Toggles
    document.querySelectorAll(".btn-toggle-pwd").forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const input = document.getElementById(targetId);
        if (input) {
          if (input.type === "password") {
            input.type = "text";
            btn.textContent = "🙈";
          } else {
            input.type = "password";
            btn.textContent = "👁️";
          }
        }
      });
    });

    // Instant Lock Button
    const btnLock = document.getElementById("btnLockNow");
    if (btnLock) {
      btnLock.addEventListener("click", async () => {
        await API.auth.logout();
        API.clearToken();
        this.showLockScreen();
      });
    }
  },

  showLockScreen() {
    this.stopInactivityTimer();
    const lock = document.getElementById("lockScreen");
    const app = document.getElementById("appContainer");
    if (lock) {
      lock.classList.add("active");
      lock.classList.remove("hidden");
    }
    if (app) {
      app.classList.add("hidden");
    }

    // Clear password fields
    const loginPass = document.getElementById("loginPassword");
    if (loginPass) loginPass.value = "";
  },

  unlockApp() {
    const lock = document.getElementById("lockScreen");
    const app = document.getElementById("appContainer");
    if (lock) {
      lock.classList.remove("active");
      lock.classList.add("hidden");
    }
    if (app) {
      app.classList.remove("hidden");
    }

    this.startInactivityTimer();
    this.switchTab(this.currentTab);
    this.updateHeaderStatus();
  },

  // ---------------- Inactivity Auto-Lock Timer ----------------
  startInactivityTimer() {
    this.resetInactivityTimer();
    const events = ["mousemove", "keydown", "scroll", "touchstart", "click"];
    const handler = () => this.resetInactivityTimer();

    events.forEach(e => window.addEventListener(e, handler, { passive: true }));
  },

  resetInactivityTimer() {
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    const ms = (this.inactivityTimeoutMinutes || 15) * 60 * 1000;
    this.inactivityTimer = setTimeout(() => {
      API.auth.logout();
      API.clearToken();
      this.showLockScreen();
      this.showToast("Archive locked due to inactivity.");
    }, ms);
  },

  stopInactivityTimer() {
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
  },

  bindGlobalEvents() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.tab;
        this.switchTab(target);
      });
    });

    // Sub-category Navigation in Statistics & Story
    const statsSubBtns = document.querySelectorAll("[data-stats-sub]");
    statsSubBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const sub = btn.dataset.statsSub;
        statsSubBtns.forEach(b => b.classList.toggle("active", b === btn));
        document.querySelectorAll(".stats-sub-view").forEach(v => {
          v.classList.toggle("active", v.id === `stats-sub-${sub}`);
        });
      });
    });

    // Sub-category Navigation in Insights & Moments
    const insightsSubBtns = document.querySelectorAll("[data-insights-sub]");
    insightsSubBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const sub = btn.dataset.insightsSub;
        insightsSubBtns.forEach(b => b.classList.toggle("active", b === btn));
        document.querySelectorAll(".insights-sub-view").forEach(v => {
          v.classList.toggle("active", v.id === `insights-sub-${sub}`);
        });
      });
    });

    const btnWrapped = document.getElementById("btnOpenWrapped");
    if (btnWrapped) {
      btnWrapped.onclick = (e) => {
        if (e) e.preventDefault();
        console.log("[App] btnOpenWrapped clicked");
        const comp = window.WrappedComponent || (typeof WrappedComponent !== "undefined" ? WrappedComponent : null);
        if (comp && typeof comp.open === "function") {
          comp.open();
        } else {
          console.error("[App] WrappedComponent not found!");
          alert("Wrapped component is loading or not found. Please refresh the page (Ctrl+F5).");
        }
      };
    }
  },

  switchTab(tabName) {
    this.currentTab = tabName;

    // Update nav tab active class
    document.querySelectorAll(".nav-tab").forEach(t => {
      if (t.dataset.tab === tabName) t.classList.add("active");
      else t.classList.remove("active");
    });

    // Update views
    document.querySelectorAll(".tab-view").forEach(v => {
      if (v.id === `view-${tabName}`) v.classList.add("active");
      else v.classList.remove("active");
    });

    // Lazy load tab data
    if (tabName === "chat") {
      ChatComponent.loadInitial();
    } else if (tabName === "timeline") {
      TimelineComponent.load();
    } else if (tabName === "memories") {
      MemoriesComponent.load();
    } else if (tabName === "stats") {
      StatsComponent.load();
      if (window.EvolutionComponent) EvolutionComponent.load();
    } else if (tabName === "insights") {
      InsightsComponent.load();
      if (window.FunnyComponent) FunnyComponent.load();
    }
  },

  switchToTabAndJump(tabName, messageId) {
    this.switchTab(tabName);
    if (tabName === "chat") {
      ChatComponent.jumpToMessage(messageId);
    }
  },

  async refreshAllViews() {
    await ChatComponent.reloadChat();
    if (window.WrappedComponent) WrappedComponent.storyData = null;
    
    // Refresh all components
    if (window.StatsComponent) StatsComponent.load();
    if (window.EvolutionComponent) EvolutionComponent.load();
    if (window.MemoriesComponent) MemoriesComponent.load();
    if (window.TimelineComponent) TimelineComponent.load();
    if (window.InsightsComponent) {
      InsightsComponent.load();
      if (window.FunnyComponent) FunnyComponent.load();
    }

    await this.updateHeaderStatus();
  },

  async updateHeaderStatus() {
    try {
      const bounds = await API.chat.getBounds();
      const badge = document.getElementById("headerStatusBadge");
      if (badge && bounds && bounds.total_count) {
        badge.textContent = `${bounds.total_count.toLocaleString()} Messages • ${bounds.start_date || ''} – ${bounds.end_date || ''}`;
      }
    } catch (err) {
      console.error(err);
    }
  },

  // ---------------- Memory Modal ----------------
  bindMemoryModalEvents() {
    const modal = document.getElementById("memoryModal");
    const btnClose = document.getElementById("btnCloseMemoryModal");
    const btnCancel = document.getElementById("btnCancelMemoryModal");
    const form = document.getElementById("memoryModalForm");
    const btnDelete = document.getElementById("btnDeleteMemoryInModal");

    const hideModal = () => {
      if (modal) modal.classList.add("hidden");
    };

    if (btnClose) btnClose.addEventListener("click", hideModal);
    if (btnCancel) btnCancel.addEventListener("click", hideModal);

    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const msgId = parseInt(document.getElementById("modalMessageId")?.value);
        const memId = document.getElementById("modalMemoryId")?.value;
        const cat = document.querySelector("input[name='modalCategory']:checked")?.value || "special";
        const note = document.getElementById("modalMemoryNote")?.value || "";
        const tags = document.getElementById("modalMemoryTags")?.value || "";

        try {
          if (memId && parseInt(memId) > 0) {
            await API.memories.update(parseInt(memId), { category: cat, note, tags });
            this.showToast("✨ Memory updated!");
          } else {
            await API.memories.create({ message_id: msgId, category: cat, note, tags });
            this.showToast("❤️ Saved to Memories!");
          }

          hideModal();
          // Update memory count in navbar
          const stats = await API.memories.stats();
          const badge = document.getElementById("navMemoryBadge");
          if (badge) badge.textContent = stats.total || 0;

          // Refresh active views
          if (this.currentTab === "memories" && window.MemoriesComponent) MemoriesComponent.load();
          if (this.currentTab === "chat" && window.ChatComponent) ChatComponent.reloadChat();
        } catch (err) {
          alert(`Error saving memory: ${err.message}`);
        }
      });
    }

    if (btnDelete) {
      btnDelete.addEventListener("click", async () => {
        const memId = document.getElementById("modalMemoryId")?.value;
        if (!memId) return;
        if (!confirm("Are you sure you want to delete this memory?")) return;

        try {
          await API.memories.delete(parseInt(memId));
          this.showToast("🗑️ Memory removed.");
          hideModal();
          // Update memory count in navbar
          const stats = await API.memories.stats();
          const badge = document.getElementById("navMemoryBadge");
          if (badge) badge.textContent = stats.total || 0;

          if (this.currentTab === "memories" && window.MemoriesComponent) MemoriesComponent.load();
          if (this.currentTab === "chat" && window.ChatComponent) ChatComponent.reloadChat();
        } catch (err) {
          alert(`Error: ${err.message}`);
        }
      });
    }
  },

  async openMemoryModalForMessage(messageId, defaultCategory = "special", existingMemory = null) {
    const modal = document.getElementById("memoryModal");
    const preview = document.getElementById("modalMessagePreview");
    const modalTitle = document.getElementById("memoryModalTitle");
    const msgIdInput = document.getElementById("modalMessageId");
    const memIdInput = document.getElementById("modalMemoryId");
    const noteInput = document.getElementById("modalMemoryNote");
    const tagsInput = document.getElementById("modalMemoryTags");
    const btnDelete = document.getElementById("btnDeleteMemoryInModal");

    if (msgIdInput) msgIdInput.value = messageId;
    if (memIdInput) memIdInput.value = "";
    if (noteInput) noteInput.value = "";
    if (tagsInput) tagsInput.value = "";
    if (btnDelete) btnDelete.classList.add("hidden");
    if (modalTitle) modalTitle.textContent = "❤️ Add to Memories";

    // If pre-filled memory data is supplied (e.g. from Memories view Edit Note button)
    if (existingMemory && existingMemory.id) {
      if (memIdInput) memIdInput.value = existingMemory.id;
      if (noteInput) noteInput.value = existingMemory.note || "";
      if (tagsInput) tagsInput.value = existingMemory.tags || "";
      if (btnDelete) btnDelete.classList.remove("hidden");
      if (modalTitle) modalTitle.textContent = "✏️ Edit Memory";
      const catVal = existingMemory.category || defaultCategory;
      const catRadio = document.querySelector(`input[name='modalCategory'][value='${catVal}']`);
      if (catRadio) catRadio.checked = true;
    } else {
      const catRadio = document.querySelector(`input[name='modalCategory'][value='${defaultCategory}']`);
      if (catRadio) catRadio.checked = true;
    }

    if (modal) modal.classList.remove("hidden");
    if (preview) preview.innerHTML = `<div style="text-align:center;padding:0.75rem;color:var(--text-muted);"><div class="spinner"></div> Loading details...</div>`;

    // Fetch message details & verify if a memory exists in DB
    try {
      const targetMsg = await API.chat.getMessage(messageId);
      if (targetMsg && preview) {
        preview.innerHTML = `
          <div style="font-size:0.75rem;font-weight:700;color:${targetMsg.is_vinu ? 'var(--accent-vinu)' : 'var(--accent-bhumi)'};margin-bottom:0.2rem;">
            ${targetMsg.sender_clean} • ${targetMsg.date_str} ${targetMsg.time_str}
          </div>
          <div style="font-size:0.9rem;">${targetMsg.content}</div>
        `;

        if (targetMsg.memory) {
          if (memIdInput) memIdInput.value = targetMsg.memory.id;
          if (noteInput && !noteInput.value) noteInput.value = targetMsg.memory.note || "";
          if (btnDelete) btnDelete.classList.remove("hidden");
          if (modalTitle) modalTitle.textContent = "✏️ Edit Memory";
          if (!existingMemory) {
            const memCatRadio = document.querySelector(`input[name='modalCategory'][value='${targetMsg.memory.category}']`);
            if (memCatRadio) memCatRadio.checked = true;
          }
        }
      }
    } catch (err) {
      console.error("Failed to load message details for memory modal:", err);
    }
  },

  showToast(message) {
    const toast = document.getElementById("toastNotification");
    if (!toast) return;

    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3000);
  }
};

// Start application when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  window.App.init();
});
