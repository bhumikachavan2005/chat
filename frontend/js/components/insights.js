/**
 * Private Offline Insights Component
 * - 100% Local Question-Answering
 * - Distinguishes Factual Observation from Interpretations
 * - Verified message receipts with jump to conversation
 */

const InsightsComponent = {
  async load() {
    this.bindEvents();
    await this.loadPrebuilt();
  },

  bindEvents() {
    const btnAsk = document.getElementById("btnAskInsight");
    const input = document.getElementById("customInsightInput");

    if (btnAsk) {
      btnAsk.addEventListener("click", () => this.askCustom());
    }

    if (input) {
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this.askCustom();
      });
    }
  },

  async loadPrebuilt() {
    const grid = document.getElementById("prebuiltInsightsGrid");
    if (!grid) return;

    try {
      const res = await API.insights.prebuilt();
      grid.innerHTML = res.insights.map(item => `
        <div class="prebuilt-card" data-id="${item.id}">
          <span style="font-size:1.4rem;">${item.icon}</span>
          <span style="font-size:0.75rem;font-weight:700;color:var(--text-faint);text-transform:uppercase;">${item.topic}</span>
          <h4 style="font-size:0.95rem;font-weight:600;">${item.question}</h4>
        </div>
      `).join("");

      grid.querySelectorAll(".prebuilt-card").forEach(card => {
        card.onclick = () => {
          this.queryInsight(card.dataset.id);
        };
      });
    } catch (err) {
      console.error("Failed to load prebuilt insights:", err);
    }
  },

  async queryInsight(insightId) {
    const container = document.getElementById("insightAnswerContainer");
    if (!container) return;

    container.classList.remove("hidden");
    container.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div> Resolving inquiry locally...</div>`;
    container.scrollIntoView({ behavior: "smooth", block: "nearest" });

    try {
      const res = await API.insights.query(insightId);
      this.renderAnswer(res);
    } catch (err) {
      container.innerHTML = `<div style="color:#f87171;">Failed to resolve insight: ${err.message}</div>`;
    }
  },

  async askCustom() {
    const input = document.getElementById("customInsightInput");
    const query = input?.value.trim();
    if (!query) return;

    const container = document.getElementById("insightAnswerContainer");
    if (!container) return;

    container.classList.remove("hidden");
    container.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div> Searching chat database...</div>`;
    container.scrollIntoView({ behavior: "smooth", block: "nearest" });

    try {
      const res = await API.insights.ask(query);
      this.renderAnswer(res);
    } catch (err) {
      container.innerHTML = `<div style="color:#f87171;">Query error: ${err.message}</div>`;
    }
  },

  renderAnswer(res) {
    const container = document.getElementById("insightAnswerContainer");
    if (!container) return;

    const factsHtml = res.factual_data?.map(f => `<li>${this.escapeHtml(f)}</li>`).join("") || "";

    const sourcesHtml = res.sources?.map(s => `
      <div style="background:var(--bg-surface-elevated);border:1px solid var(--border-color);border-radius:var(--radius-sm);padding:0.75rem;display:flex;flex-direction:column;gap:0.3rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;font-size:0.75rem;">
          <span style="font-weight:700;color:${s.is_vinu ? 'var(--accent-vinu)' : 'var(--accent-bhumi)'};">${this.escapeHtml(s.sender_clean)}</span>
          <span style="color:var(--text-faint);">${s.date_str} • ${s.time_str}</span>
        </div>
        <div style="font-size:0.88rem;">${this.escapeHtml(s.content)}</div>
        <div style="display:flex;justify-content:flex-end;margin-top:0.2rem;">
          <button class="btn btn-sm btn-outline btn-jump-chat" data-id="${s.id}">💬 View in Chat</button>
        </div>
      </div>
    `).join("") || '<div style="color:var(--text-faint);font-size:0.85rem;">No source messages to display.</div>';

    container.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-color);padding-bottom:0.8rem;">
        <h3 style="font-size:1.2rem;font-weight:700;">💡 ${res.question || res.query}</h3>
        <span style="font-size:0.75rem;padding:0.2rem 0.6rem;background:rgba(16,185,129,0.15);color:var(--accent-vinu);border-radius:var(--radius-full);font-weight:700;">
          🛡️ 100% Offline Local Analysis
        </span>
      </div>

      <div style="font-size:1.05rem;line-height:1.5;">
        ${res.answer}
      </div>

      ${factsHtml ? `
        <div style="background:var(--bg-surface-elevated);padding:1rem;border-radius:var(--radius-sm);border-left:3px solid var(--accent-vinu);">
          <h4 style="font-size:0.82rem;text-transform:uppercase;color:var(--text-faint);margin-bottom:0.4rem;">Factual Observations</h4>
          <ul style="padding-left:1.2rem;font-size:0.88rem;color:var(--text-main);line-height:1.6;">
            ${factsHtml}
          </ul>
        </div>
      ` : ''}

      <div>
        <h4 style="font-size:0.85rem;text-transform:uppercase;color:var(--text-faint);margin-bottom:0.6rem;">Verified Message Receipts (${res.sources?.length || 0})</h4>
        <div class="insight-receipts">
          ${sourcesHtml}
        </div>
      </div>
    `;

    // Attach listeners to jump buttons
    container.querySelectorAll(".btn-jump-chat").forEach(btn => {
      btn.onclick = () => {
        const msgId = parseInt(btn.dataset.id);
        if (window.App && typeof window.App.switchToTabAndJump === "function") {
          window.App.switchToTabAndJump("chat", msgId);
        }
      };
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
};
