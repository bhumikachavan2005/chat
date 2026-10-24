/**
 * Memories Component
 * - Category filter pills (Special, Emotional, Funny, Difficult, Birthday, Career, Friendship, Important)
 * - Memory card gallery with live search
 * - Edit / Delete / Jump to conversation
 */

const MemoriesComponent = {
  currentCategory: null,
  isInitialized: false,

  init() {
    if (this.isInitialized) return;
    this.isInitialized = true;

    const searchInput = document.getElementById("memorySearchInput");
    if (searchInput) {
      let debounce = null;
      searchInput.addEventListener("input", () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => this.loadMemories(), 300);
      });
    }

    const grid = document.getElementById("memoriesGrid");
    if (grid) {
      grid.addEventListener("click", async (e) => {
        const deleteBtn = e.target.closest(".btn-delete-mem");
        if (deleteBtn) {
          const memId = parseInt(deleteBtn.dataset.id);
          if (memId && confirm("Are you sure you want to delete this memory?")) {
            try {
              await API.memories.delete(memId);
              if (window.App) window.App.showToast("🗑️ Memory removed.");
              await this.load();
              const stats = await API.memories.stats();
              const badge = document.getElementById("navMemoryBadge");
              if (badge) badge.textContent = stats.total || 0;
              if (window.ChatComponent) ChatComponent.reloadChat();
            } catch (err) {
              alert("Failed to delete memory: " + err.message);
            }
          }
          return;
        }

        const jumpBtn = e.target.closest(".btn-jump-chat");
        if (jumpBtn) {
          const msgId = parseInt(jumpBtn.dataset.msgId);
          if (msgId && window.App && typeof window.App.switchToTabAndJump === "function") {
            window.App.switchToTabAndJump("chat", msgId);
          }
          return;
        }

        const editBtn = e.target.closest(".btn-edit-mem");
        if (editBtn) {
          const msgId = parseInt(editBtn.dataset.msgId);
          const memId = parseInt(editBtn.dataset.id);
          const cat = editBtn.dataset.cat || "special";
          const note = editBtn.dataset.note || "";
          const tags = editBtn.dataset.tags || "";
          if (msgId && window.App && typeof window.App.openMemoryModalForMessage === "function") {
            window.App.openMemoryModalForMessage(msgId, cat, { id: memId, category: cat, note, tags });
          }
          return;
        }
      });
    }
  },

  async load() {
    this.init();
    await this.renderCategoriesBar();
    await this.loadMemories();
  },

  async renderCategoriesBar() {
    const bar = document.getElementById("memoryCategoriesBar");
    if (!bar) return;

    try {
      const stats = await API.memories.stats();
      
      // Update nav badge
      const navBadge = document.getElementById("navMemoryBadge");
      if (navBadge) navBadge.textContent = stats.total || 0;

      let html = `
        <button class="cat-pill ${!this.currentCategory ? 'active' : ''}" data-cat="">
          <span>🌟 All Memories</span>
          <span style="opacity:0.7;">(${stats.total})</span>
        </button>
      `;

      stats.categories.forEach(c => {
        const isActive = this.currentCategory === c.key;
        html += `
          <button class="cat-pill ${isActive ? 'active' : ''}" data-cat="${c.key}">
            <span>${c.emoji} ${c.label}</span>
            <span style="opacity:0.7;">(${c.count})</span>
          </button>
        `;
      });

      bar.innerHTML = html;

      bar.querySelectorAll(".cat-pill").forEach(pill => {
        pill.onclick = () => {
          this.currentCategory = pill.dataset.cat || null;
          this.renderCategoriesBar();
          this.loadMemories();
        };
      });
    } catch (err) {
      console.error("Failed to load memory stats:", err);
    }
  },

  async loadMemories() {
    const grid = document.getElementById("memoriesGrid");
    const searchInput = document.getElementById("memorySearchInput");
    const search = searchInput?.value.trim() || "";

    if (!grid) return;
    grid.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div></div>`;

    try {
      const list = await API.memories.list({
        category: this.currentCategory || "",
        search: search
      });

      this.renderGrid(list);
    } catch (err) {
      grid.innerHTML = `<div style="color:#f87171;">Failed to load memories: ${err.message}</div>`;
    }
  },

  renderGrid(memories) {
    const grid = document.getElementById("memoriesGrid");
    if (!grid) return;

    if (!memories || memories.length === 0) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted);background:var(--bg-surface);border-radius:var(--radius-md);border:1px dashed var(--border-color);">
          <div style="font-size:2rem;margin-bottom:0.5rem;">💌</div>
          <h3>No memories saved yet</h3>
          <p style="font-size:0.85rem;margin-top:0.3rem;">Open the Chat tab, hover over any message and click the ❤️ icon to save it into your Memory Vault with custom notes.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = "";

    memories.forEach(mem => {
      const card = document.createElement("div");
      card.className = "memory-card";

      const senderColor = mem.message.is_vinu ? "var(--accent-vinu)" : "var(--accent-bhumi)";

      card.innerHTML = `
        <div class="memory-card-header">
          <span class="memory-badge-label" style="background:${mem.category_color}25;color:${mem.category_color};border:1px solid ${mem.category_color}50;">
            ${mem.category_emoji} ${mem.category_label}
          </span>
          <span style="font-size:0.75rem;color:var(--text-faint);">${mem.message.date_str} • ${mem.message.time_str}</span>
        </div>

        <div class="memory-quote">
          <div style="font-size:0.75rem;font-weight:700;color:${senderColor};margin-bottom:0.2rem;">
            ${this.escapeHtml(mem.message.sender_clean)}
          </div>
          <div style="font-size:0.88rem;color:var(--text-main);white-space:pre-wrap;">${this.escapeHtml(mem.message.content)}</div>
        </div>

        ${mem.note ? `
          <div class="memory-note">
            <span style="font-size:0.72rem;font-weight:700;color:var(--text-faint);text-transform:uppercase;display:block;">Personal Reflection:</span>
            ${this.escapeHtml(mem.note)}
          </div>
        ` : ''}

        ${mem.tags ? `
          <div style="font-size:0.75rem;color:var(--text-muted);">
            🏷️ ${this.escapeHtml(mem.tags)}
          </div>
        ` : ''}

        <div style="display:flex;align-items:center;justify-content:space-between;gap:0.4rem;margin-top:auto;padding-top:0.6rem;border-top:1px solid var(--border-color);flex-wrap:wrap;">
          <button class="btn btn-sm btn-outline btn-edit-mem" 
                  data-id="${mem.id}" 
                  data-msg-id="${mem.message_id}" 
                  data-cat="${mem.category}" 
                  data-note="${this.escapeHtml(mem.note || '')}" 
                  data-tags="${this.escapeHtml(mem.tags || '')}">
            ✏️ Edit Note
          </button>
          <button class="btn btn-sm btn-outline btn-jump-chat" data-msg-id="${mem.message_id}">
            💬 View in Chat
          </button>
          <button class="btn btn-sm btn-danger-outline btn-delete-mem" data-id="${mem.id}" title="Delete Memory">
            🗑️ Delete
          </button>
        </div>
      `;

      grid.appendChild(card);
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
};
