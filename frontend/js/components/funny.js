/**
 * Funny Moments Component
 * - Humor signals detection deck (😂, 🤣, 💀, haha, lol)
 * - Surrounding thread viewer
 * - Confirm as Funny Memory or Dismiss
 */

const FunnyComponent = {
  async load() {
    const grid = document.getElementById("funnyMomentsGrid");
    if (!grid) return;

    grid.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div></div>`;

    try {
      const res = await API.insights.funnyMoments();
      this.renderMoments(res.moments);
    } catch (err) {
      grid.innerHTML = `<div style="color:#f87171;">Failed to load funny moments: ${err.message}</div>`;
    }
  },

  renderMoments(moments) {
    const grid = document.getElementById("funnyMomentsGrid");
    if (!grid) return;

    if (!moments || moments.length === 0) {
      grid.innerHTML = `<div style="color:var(--text-muted);text-align:center;">No candidate funny moments found.</div>`;
      return;
    }

    grid.innerHTML = "";

    moments.forEach(m => {
      const card = document.createElement("div");
      card.className = "funny-card";
      card.id = `funny-card-${m.message_id}`;

      const signalsHtml = m.signals.map(s => `<span>${s}</span>`).join(" ");

      const threadHtml = m.context_thread.map(ct => `
        <div class="funny-msg-line ${ct.is_target ? 'highlight-target' : ''}">
          <span style="font-weight:700;color:${ct.is_vinu ? 'var(--accent-vinu)' : 'var(--accent-bhumi)'};">
            ${this.escapeHtml(ct.sender_clean)}:
          </span>
          <span>${this.escapeHtml(ct.content)}</span>
        </div>
      `).join("");

      card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div class="funny-signals-row">
            ${signalsHtml}
          </div>
          <span style="font-size:0.75rem;color:var(--text-faint);">
            ${m.target_message.date_str} • ${m.target_message.time_str}
          </span>
        </div>

        <div class="funny-thread">
          ${threadHtml}
        </div>

        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:auto;padding-top:0.6rem;border-top:1px solid var(--border-color);">
          <div style="display:flex;gap:0.4rem;">
            <button class="btn btn-sm btn-primary btn-save-funny-mem" data-id="${m.message_id}">
              ⭐ Save Memory
            </button>
            <button class="btn btn-sm btn-outline btn-dismiss-funny" data-id="${m.message_id}">
              Dismiss
            </button>
          </div>
          <button class="btn btn-sm btn-outline btn-jump-chat" data-id="${m.message_id}">
            💬 View Chat
          </button>
        </div>
      `;

      grid.appendChild(card);
    });

    // Attach button listeners
    grid.querySelectorAll(".btn-save-funny-mem").forEach(btn => {
      btn.onclick = () => {
        const msgId = parseInt(btn.dataset.id);
        if (window.App && typeof window.App.openMemoryModalForMessage === "function") {
          window.App.openMemoryModalForMessage(msgId, "funny");
        }
      };
    });

    grid.querySelectorAll(".btn-dismiss-funny").forEach(btn => {
      btn.onclick = async () => {
        const msgId = parseInt(btn.dataset.id);
        try {
          await API.insights.setFunnyStatus(msgId, "dismissed");
          const cardEl = document.getElementById(`funny-card-${msgId}`);
          if (cardEl) cardEl.remove();
          if (window.App) window.App.showToast("Dismissed from funny suggestions.");
        } catch (err) {
          console.error(err);
        }
      };
    });

    grid.querySelectorAll(".btn-jump-chat").forEach(btn => {
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
