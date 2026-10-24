/**
 * Search Component
 * - FTS5 fast search with live debounce typing
 * - Snippet highlight rendering
 * - Context thread preview
 * - 1-Click jump to chat position
 */

const SearchComponent = {
  debounceTimer: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const btnSearch = document.getElementById("btnExecuteSearch");
    const input = document.getElementById("searchInput");
    const senderFilter = document.getElementById("searchSenderFilter");
    const startDate = document.getElementById("searchStartDate");
    const endDate = document.getElementById("searchEndDate");
    const resultsList = document.getElementById("searchResultsList");

    if (btnSearch) {
      btnSearch.addEventListener("click", () => this.executeSearch());
    }

    if (input) {
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          clearTimeout(this.debounceTimer);
          this.executeSearch();
        }
      });

      input.addEventListener("input", () => {
        clearTimeout(this.debounceTimer);
        const val = input.value.trim();
        if (val.length >= 2) {
          this.debounceTimer = setTimeout(() => this.executeSearch(), 350);
        } else if (val.length === 0) {
          this.clearResults();
        }
      });
    }

    if (senderFilter) {
      senderFilter.addEventListener("change", () => {
        if (input && input.value.trim()) this.executeSearch();
      });
    }

    if (startDate) {
      startDate.addEventListener("change", () => {
        if (input && input.value.trim()) this.executeSearch();
      });
    }

    if (endDate) {
      endDate.addEventListener("change", () => {
        if (input && input.value.trim()) this.executeSearch();
      });
    }

    // Event delegation on results list for Jump to Conversation button
    if (resultsList) {
      resultsList.addEventListener("click", (e) => {
        const btn = e.target.closest(".btn-jump-to-chat");
        if (btn) {
          const msgId = parseInt(btn.dataset.id);
          if (msgId && window.App && typeof window.App.switchToTabAndJump === "function") {
            window.App.switchToTabAndJump("chat", msgId);
          }
        }
      });
    }
  },

  clearResults() {
    const info = document.getElementById("searchResultsInfo");
    const list = document.getElementById("searchResultsList");
    if (info) info.innerHTML = "";
    if (list) list.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-muted);">Type words, names, or topics above to search through all 17,000+ messages instantly.</div>`;
  },

  async executeSearch() {
    const input = document.getElementById("searchInput");
    const query = input?.value.trim();
    if (!query) {
      this.clearResults();
      return;
    }

    const sender = document.getElementById("searchSenderFilter")?.value || "";
    const startDate = document.getElementById("searchStartDate")?.value || "";
    const endDate = document.getElementById("searchEndDate")?.value || "";

    const info = document.getElementById("searchResultsInfo");
    const list = document.getElementById("searchResultsList");

    if (info) info.innerHTML = `<span>Searching for "<strong>${this.escapeHtml(query)}</strong>"...</span>`;
    if (list) list.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div></div>`;

    try {
      const res = await API.search.query({
        q: query,
        sender,
        start_date: startDate,
        end_date: endDate,
        limit: 100
      });

      if (info) {
        info.innerHTML = `Found <strong>${res.total}</strong> matching messages for "<strong>${this.escapeHtml(query)}</strong>"`;
      }

      this.renderResults(res.results);
    } catch (err) {
      if (info) info.innerHTML = `<span style="color:#f87171;">Search error: ${err.message}</span>`;
      if (list) list.innerHTML = "";
    }
  },

  renderResults(results) {
    const list = document.getElementById("searchResultsList");
    if (!list) return;

    if (!results || results.length === 0) {
      list.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted);">No messages found matching your search criteria.</div>`;
      return;
    }

    list.innerHTML = "";
    results.forEach(item => {
      const card = document.createElement("div");
      card.className = "search-result-card";

      const senderColor = item.is_vinu ? "var(--accent-vinu)" : "var(--accent-bhumi)";
      const highlightContent = item.highlighted_content || this.escapeHtml(item.content);

      // Context preview snippets
      let contextHtml = "";
      if (item.context_preview && item.context_preview.length > 0) {
        contextHtml = `
          <div class="search-result-context">
            <span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;color:var(--text-faint);">Conversation Context:</span>
            ${item.context_preview.map(cp => `
              <div><strong>${this.escapeHtml(cp.sender_clean)}:</strong> ${this.escapeHtml(cp.content)}</div>
            `).join("")}
          </div>
        `;
      }

      card.innerHTML = `
        <div class="search-result-header">
          <span style="font-weight:700;color:${senderColor};">${this.escapeHtml(item.sender_clean)}</span>
          <span style="color:var(--text-faint);">${item.date_str} • ${item.time_str}</span>
        </div>
        <div style="font-size:0.95rem;line-height:1.45;">${highlightContent}</div>
        ${contextHtml}
        <div style="display:flex;justify-content:flex-end;margin-top:0.4rem;">
          <button class="btn btn-sm btn-outline btn-jump-to-chat" data-id="${item.id}">
            💬 View in Conversation ➔
          </button>
        </div>
      `;

      list.appendChild(card);
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
};
