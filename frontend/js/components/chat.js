/**
 * Chat Component
 * - Large-scale Message Rendering (Up to 5,000+ messages per session)
 * - WhatsApp-style chat bubbles with lossless date rendering
 * - Multi-Day & Single-Day Full View modes (No artificial message limits)
 * - Bidirectional Infinite Streaming (Load Earlier ⬆ & Load Next ⬇)
 * - Dynamic Date Picker auto-navigation
 * - Memory bookmarking with modal
 */

const ChatComponent = {
  startOffset: 0,
  currentOffset: 0,
  pageSize: 400,
  totalMessages: 0,
  isLoading: false,
  hasMore: true,
  lastRenderedDate: null,
  filters: {
    sender: "",
    startDate: "",
    endDate: "",
    mediaOnly: false,
    memoriesOnly: false,
    preset: ""
  },

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Event delegation on messages list for Save Memory (❤️) button
    const messagesList = document.getElementById("chatMessagesList");
    if (messagesList) {
      messagesList.addEventListener("click", (e) => {
        const memBtn = e.target.closest(".btn-add-memory");
        if (memBtn) {
          e.preventDefault();
          e.stopPropagation();
          const msgId = parseInt(memBtn.dataset.id);
          if (msgId && window.App && typeof window.App.openMemoryModalForMessage === "function") {
            window.App.openMemoryModalForMessage(msgId);
          }
        }
      });
    }

    const senderFilter = document.getElementById("chatSenderFilter");
    if (senderFilter) {
      senderFilter.addEventListener("change", (e) => {
        this.filters.sender = e.target.value;
        this.reloadChat();
      });
    }

    const mediaCheck = document.getElementById("chatMediaOnly");
    if (mediaCheck) {
      mediaCheck.addEventListener("change", (e) => {
        this.filters.mediaOnly = e.target.checked;
        this.reloadChat();
      });
    }

    const memCheck = document.getElementById("chatMemoriesOnly");
    if (memCheck) {
      memCheck.addEventListener("change", (e) => {
        this.filters.memoriesOnly = e.target.checked;
        this.reloadChat();
      });
    }

    const btnJumpDate = document.getElementById("btnJumpToDate");
    const btnFilterDay = document.getElementById("btnFilterDay");
    const btnClearDate = document.getElementById("btnClearDateFilter");
    const btnDismissBanner = document.getElementById("btnDismissFilterBanner");
    const dateInput = document.getElementById("chatDateJumpInput");

    // Auto-jump whenever a date is picked from the date picker
    if (dateInput) {
      dateInput.addEventListener("change", () => {
        if (dateInput.value) {
          this.jumpToDate(dateInput.value);
        }
      });
    }

    if (btnJumpDate && dateInput) {
      btnJumpDate.addEventListener("click", () => {
        if (dateInput.value) {
          this.jumpToDate(dateInput.value);
        } else {
          if (window.App) window.App.showToast("Please select a date first.");
        }
      });
    }

    if (btnFilterDay && dateInput) {
      btnFilterDay.addEventListener("click", () => {
        if (dateInput.value) {
          this.filterDay(dateInput.value);
        } else {
          if (window.App) window.App.showToast("Please select a date first.");
        }
      });
    }

    if (btnClearDate) {
      btnClearDate.addEventListener("click", () => {
        this.clearDateFilter();
      });
    }

    if (btnDismissBanner) {
      btnDismissBanner.addEventListener("click", () => {
        this.clearDateFilter();
      });
    }

    const btnSurprise = document.getElementById("btnSurpriseMemory");
    if (btnSurprise) {
      btnSurprise.addEventListener("click", () => {
        this.jumpToRandomMemory();
      });
    }

    const btnJumpStart = document.getElementById("btnJumpStart");
    if (btnJumpStart) {
      btnJumpStart.addEventListener("click", () => {
        this.jumpToStart();
      });
    }

    const btnJumpEnd = document.getElementById("btnJumpEnd");
    if (btnJumpEnd) {
      btnJumpEnd.addEventListener("click", () => {
        this.jumpToLatest();
      });
    }

    // Viewport Scroll Listener for Infinite Loading & Scroll-to-bottom button
    const viewport = document.getElementById("chatViewport");
    const btnScrollBottom = document.getElementById("btnScrollBottom");

    if (viewport) {
      viewport.addEventListener("scroll", () => {
        // Show scroll bottom button if not near bottom
        const distFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
        if (btnScrollBottom) {
          if (distFromBottom > 300) {
            btnScrollBottom.classList.remove("hidden");
          } else {
            btnScrollBottom.classList.add("hidden");
          }
        }

        // Infinite load more downward when scrolling near bottom
        if (distFromBottom < 500 && !this.isLoading && this.hasMore) {
          this.loadNextPage();
        }
      });
    }

    // Quick Filter Pills
    const pills = document.querySelectorAll("#quickPillsBar .pill-btn");
    pills.forEach(pill => {
      pill.addEventListener("click", () => {
        pills.forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        this.filters.preset = pill.dataset.preset || "";
        this.reloadChat();
      });
    });

    if (btnScrollBottom && viewport) {
      btnScrollBottom.addEventListener("click", () => {
        viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
      });
    }
  },

  async reloadChat() {
    this.startOffset = 0;
    this.currentOffset = 0;
    this.hasMore = true;
    this.lastRenderedDate = null;
    const list = document.getElementById("chatMessagesList");
    if (list) list.innerHTML = "";
    await this.loadNextPage(true);
  },

  async loadInitial() {
    if (this.currentOffset === 0) {
      await this.reloadChat();
    }
  },

  async loadNextPage(scrollToTop = false, customLimit = null) {
    if (this.isLoading || !this.hasMore) return;
    this.isLoading = true;
    this.showLoading(true);

    const limitToFetch = customLimit || this.pageSize;

    try {
      const res = await API.chat.getMessages({
        limit: limitToFetch,
        offset: this.currentOffset,
        sender: this.filters.sender,
        start_date: this.filters.startDate,
        end_date: this.filters.endDate,
        media_only: this.filters.mediaOnly,
        memories_only: this.filters.memoriesOnly,
        preset: this.filters.preset,
        sort: "asc"
      });

      this.totalMessages = res.total;
      this.currentOffset += res.messages.length;
      if (this.currentOffset >= res.total || res.messages.length === 0) {
        this.hasMore = false;
      }

      this.renderMessages(res.messages, true);
      this.updateEarlierButton();

      if (scrollToTop) {
        const viewport = document.getElementById("chatViewport");
        if (viewport) viewport.scrollTop = 0;
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
    } finally {
      this.isLoading = false;
      this.showLoading(false);
    }
  },

  async loadEarlierMessages() {
    if (this.isLoading || this.startOffset <= 0) return;
    this.isLoading = true;
    this.showLoading(true);

    const fetchLimit = Math.min(this.startOffset, this.pageSize);
    const newStartOffset = Math.max(0, this.startOffset - fetchLimit);

    const viewport = document.getElementById("chatViewport");
    const oldScrollHeight = viewport ? viewport.scrollHeight : 0;
    const oldScrollTop = viewport ? viewport.scrollTop : 0;

    try {
      const res = await API.chat.getMessages({
        limit: fetchLimit,
        offset: newStartOffset,
        sender: this.filters.sender,
        start_date: this.filters.startDate,
        end_date: this.filters.endDate,
        media_only: this.filters.mediaOnly,
        memories_only: this.filters.memoriesOnly,
        preset: this.filters.preset,
        sort: "asc"
      });

      this.startOffset = newStartOffset;
      this.prependMessages(res.messages);
      this.updateEarlierButton();

      // Preserve scroll position
      if (viewport) {
        const heightDiff = viewport.scrollHeight - oldScrollHeight;
        viewport.scrollTop = oldScrollTop + heightDiff;
      }
    } catch (err) {
      console.error("Error loading earlier messages:", err);
    } finally {
      this.isLoading = false;
      this.showLoading(false);
    }
  },

  updateEarlierButton() {
    let topBtn = document.getElementById("btnLoadEarlierMessages");
    const list = document.getElementById("chatMessagesList");
    if (!list) return;

    if (this.startOffset > 0) {
      if (!topBtn) {
        topBtn = document.createElement("button");
        topBtn.id = "btnLoadEarlierMessages";
        topBtn.className = "btn btn-sm btn-outline";
        topBtn.style.cssText = "align-self:center;margin:0.5rem auto 1.2rem;display:block;";
        topBtn.onclick = () => this.loadEarlierMessages();
        list.insertBefore(topBtn, list.firstChild);
      }
      topBtn.textContent = `⬆️ Load Earlier Messages (${this.startOffset.toLocaleString()} remaining)`;
      topBtn.style.display = "block";
    } else if (topBtn) {
      topBtn.style.display = "none";
    }
  },

  createMessageBubble(msg) {
    const row = document.createElement("div");
    row.id = `msg-${msg.id}`;
    row.dataset.msgId = msg.id;

    let rowClass = "chat-bubble-row ";
    if (msg.is_system) {
      rowClass += "system-event";
    } else if (msg.is_vinu) {
      rowClass += "sent-by-vinu";
    } else {
      rowClass += "sent-by-bhumi";
    }
    row.className = rowClass;

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    let bubbleHtml = "";

    // Memory Badge if present
    if (msg.memory) {
      bubbleHtml += `
        <div class="bubble-memory-tag" title="Saved in Memories">
          <span>⭐ ${msg.memory.category.toUpperCase()}</span>
          ${msg.memory.note ? `<span style="font-weight:normal;opacity:0.85;">— "${msg.memory.note}"</span>` : ''}
        </div>
      `;
    }

    // Sender Title (for non-system)
    if (!msg.is_system) {
      bubbleHtml += `<div class="bubble-sender">${this.escapeHtml(msg.sender_clean)}</div>`;
    }

    // Content / Media
    if (msg.is_deleted) {
      bubbleHtml += `<div class="bubble-content badge-deleted">🚫 <em>This message was deleted</em></div>`;
    } else if (msg.message_type === "media") {
      bubbleHtml += `
        <div class="media-card">
          <span class="media-icon">📎</span>
          <div style="font-size:0.85rem;word-break:break-all;">${this.escapeHtml(msg.content)}</div>
        </div>
      `;
    } else if (msg.message_type === "call") {
      bubbleHtml += `
        <div class="media-card" style="background:rgba(239,68,68,0.15);">
          <span class="media-icon">📞</span>
          <div style="font-size:0.85rem;color:#f87171;">${this.escapeHtml(msg.content)}</div>
        </div>
      `;
    } else {
      bubbleHtml += `<div class="bubble-content">${this.escapeHtml(msg.content)}</div>`;
    }

    // Meta (Timestamp + Edited badge)
    bubbleHtml += `
      <div class="bubble-meta">
        ${msg.is_edited ? `<span class="badge-edited">edited</span>` : ''}
        <span>${msg.time_str || ''}</span>
      </div>
    `;

    // Quick action bar (Add/Edit memory)
    bubbleHtml += `
      <div class="bubble-action-bar">
        <button class="btn-bubble-action btn-add-memory" title="Save / Edit Memory" data-id="${msg.id}">
          ❤️
        </button>
      </div>
    `;

    bubble.innerHTML = bubbleHtml;
    row.appendChild(bubble);
    return row;
  },

  renderMessages(messages, append = true) {
    const list = document.getElementById("chatMessagesList");
    if (!list) return;

    const fragment = document.createDocumentFragment();

    messages.forEach(msg => {
      // Date separator
      if (msg.date_str && msg.date_str !== this.lastRenderedDate) {
        this.lastRenderedDate = msg.date_str;
        const dateSep = document.createElement("div");
        dateSep.className = "date-separator";
        dateSep.textContent = this.formatDisplayDate(msg.date_str);
        fragment.appendChild(dateSep);
      }

      fragment.appendChild(this.createMessageBubble(msg));
    });

    if (append) {
      list.appendChild(fragment);
    } else {
      list.innerHTML = "";
      list.appendChild(fragment);
    }
  },

  prependMessages(messages) {
    const list = document.getElementById("chatMessagesList");
    if (!list || !messages.length) return;

    const fragment = document.createDocumentFragment();
    let prevDate = null;

    messages.forEach(msg => {
      if (msg.date_str && msg.date_str !== prevDate) {
        prevDate = msg.date_str;
        const dateSep = document.createElement("div");
        dateSep.className = "date-separator";
        dateSep.textContent = this.formatDisplayDate(msg.date_str);
        fragment.appendChild(dateSep);
      }
      fragment.appendChild(this.createMessageBubble(msg));
    });

    const topBtn = document.getElementById("btnLoadEarlierMessages");
    if (topBtn && topBtn.nextSibling) {
      list.insertBefore(fragment, topBtn.nextSibling);
    } else {
      list.insertBefore(fragment, list.firstChild);
    }
  },

  async jumpToMessage(messageId) {
    try {
      this.showLoading(true);
      const offsetRes = await API.chat.getOffset(messageId, {
        sender: this.filters.sender,
        start_date: this.filters.startDate,
        end_date: this.filters.endDate,
        media_only: this.filters.mediaOnly,
        memories_only: this.filters.memoriesOnly,
        preset: this.filters.preset
      });

      const targetOffset = offsetRes.offset || 0;
      this.startOffset = Math.max(0, targetOffset - 50);
      this.currentOffset = this.startOffset;
      this.hasMore = true;
      this.lastRenderedDate = null;

      const list = document.getElementById("chatMessagesList");
      if (list) list.innerHTML = "";

      await this.loadNextPage(false, 300);

      // Highlight and scroll to target element
      setTimeout(() => {
        const targetEl = document.getElementById(`msg-${messageId}`);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
          targetEl.style.animation = "pulseHighlight 2s ease";
        }
      }, 200);
    } catch (err) {
      console.error("Jump to message error:", err);
      if (window.App) window.App.showToast("Could not locate message in current view.");
    } finally {
      this.showLoading(false);
    }
  },

  async jumpToDate(isoDate) {
    try {
      this.showLoading(true);
      const res = await API.chat.jumpDate(isoDate);
      if (res && res.message_id) {
        this.filters.startDate = "";
        this.filters.endDate = "";
        this.updateFilterBanner(false);

        const dayTotal = res.day_stats ? res.day_stats.total : 0;
        // Fetch up to 1,500 messages at once so the complete day is 100% loaded
        const batchSize = Math.max(500, dayTotal + 150);

        this.startOffset = res.offset || 0;
        this.currentOffset = this.startOffset;
        this.hasMore = true;
        this.lastRenderedDate = null;

        const list = document.getElementById("chatMessagesList");
        if (list) list.innerHTML = "";

        await this.loadNextPage(true, batchSize);

        if (window.App) {
          window.App.showToast(`📅 Loaded ${this.formatDisplayDate(isoDate)}: all ${dayTotal} messages for this day!`);
        }
      }
    } catch (err) {
      console.error("Jump to date error:", err);
      if (window.App) window.App.showToast("No messages found on or after this date.");
    } finally {
      this.showLoading(false);
    }
  },

  async filterDay(isoDate) {
    try {
      this.showLoading(true);
      this.filters.startDate = isoDate;
      this.filters.endDate = isoDate;
      this.updateFilterBanner(true, isoDate);

      // Fetch the complete day's chat in full detail (up to 5,000 messages)
      this.startOffset = 0;
      this.currentOffset = 0;
      this.hasMore = true;
      this.lastRenderedDate = null;
      const list = document.getElementById("chatMessagesList");
      if (list) list.innerHTML = "";

      await this.loadNextPage(true, 5000);

      if (window.App) {
        window.App.showToast(`📅 Showing full day chat for ${this.formatDisplayDate(isoDate)} (${this.totalMessages} messages)`);
      }
    } catch (err) {
      console.error("Filter day error:", err);
    } finally {
      this.showLoading(false);
    }
  },

  clearDateFilter() {
    this.filters.startDate = "";
    this.filters.endDate = "";
    const dateInput = document.getElementById("chatDateJumpInput");
    if (dateInput) dateInput.value = "";
    this.updateFilterBanner(false);
    this.reloadChat();
    if (window.App) window.App.showToast("Showing all chat history.");
  },

  updateFilterBanner(show, isoDate = "") {
    const banner = document.getElementById("chatFilterBanner");
    const bannerText = document.getElementById("chatFilterBannerText");
    const btnClear = document.getElementById("btnClearDateFilter");

    if (show && banner && bannerText) {
      bannerText.textContent = `📅 Filtered to Full Day: ${this.formatDisplayDate(isoDate)} (${this.totalMessages || 0} messages)`;
      banner.classList.remove("hidden");
      if (btnClear) btnClear.classList.remove("hidden");
    } else if (banner) {
      banner.classList.add("hidden");
      if (btnClear) btnClear.classList.add("hidden");
    }
  },

  async jumpToRandomMemory() {
    try {
      const res = await API.chat.getRandom();
      if (res && res.target_id) {
        await this.jumpToMessage(res.target_id);
        if (window.App) window.App.showToast("✨ Teleported to a random chat memory!");
      }
    } catch (err) {
      console.error(err);
    }
  },

  async jumpToStart() {
    this.clearDateFilter();
  },

  async jumpToLatest() {
    try {
      const bounds = await API.chat.getBounds();
      if (bounds && bounds.last_id) {
        await this.jumpToMessage(bounds.last_id);
      }
    } catch (err) {
      console.error(err);
    }
  },

  showLoading(show) {
    const el = document.getElementById("chatLoadingIndicator");
    if (el) {
      if (show) el.classList.remove("hidden");
      else el.classList.add("hidden");
    }
  },

  formatDisplayDate(dateStr) {
    if (!dateStr) return "";
    return dateStr;
  },

  escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
};
