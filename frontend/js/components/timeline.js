/**
 * Timeline Component
 * - Year and Month tree navigation
 * - Message counts, active days, and memory markers
 * - 1-Click jump to month in chat
 */

const TimelineComponent = {
  async load() {
    const container = document.getElementById("timelineTreeContainer");
    if (!container) return;

    container.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div></div>`;

    try {
      const years = await API.stats.timeline();
      this.renderTimeline(years);
    } catch (err) {
      container.innerHTML = `<div style="color:#f87171;">Failed to load timeline: ${err.message}</div>`;
    }
  },

  renderTimeline(years) {
    const container = document.getElementById("timelineTreeContainer");
    if (!container) return;

    if (!years || years.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);text-align:center;">No timeline data available.</div>`;
      return;
    }

    container.innerHTML = "";

    years.forEach(yr => {
      const yearGroup = document.createElement("div");
      yearGroup.className = "timeline-year-group";

      const monthsHtml = yr.months.map(m => `
        <div class="timeline-month-card" data-first-id="${m.first_message_id}">
          <div class="timeline-month-header">
            <span>📅 ${m.month_name}</span>
            <span style="font-size:0.8rem;color:var(--accent-bhumi);font-weight:700;">${m.total_messages.toLocaleString()} msgs</span>
          </div>
          <div class="timeline-stats-row">
            <span>Vinu: ${m.vinu_messages.toLocaleString()}</span>
            <span>Bhumi: ${m.bhumi_messages.toLocaleString()}</span>
          </div>
          <div class="timeline-stats-row" style="margin-top:0.4rem;border-top:1px dashed var(--border-color);padding-top:0.3rem;">
            <span>🗓️ ${m.active_days} active days</span>
            ${m.memory_count > 0 ? `<span style="color:var(--accent-gold);font-weight:600;">⭐ ${m.memory_count} memories</span>` : '<span style="color:var(--text-faint);">0 memories</span>'}
          </div>
        </div>
      `).join("");

      yearGroup.innerHTML = `
        <div class="timeline-year-title">
          <span>✨ Year ${yr.year}</span>
          <span style="font-size:0.85rem;color:var(--text-muted);">${yr.total_messages.toLocaleString()} Messages • ${yr.active_days} Active Days</span>
        </div>
        <div class="timeline-months-grid">
          ${monthsHtml}
        </div>
      `;

      container.appendChild(yearGroup);
    });

    // Attach click listeners to month cards
    container.querySelectorAll(".timeline-month-card").forEach(card => {
      card.onclick = () => {
        const firstId = parseInt(card.dataset.firstId);
        if (firstId && window.App && typeof window.App.switchToTabAndJump === "function") {
          window.App.switchToTabAndJump("chat", firstId);
        }
      };
    });
  }
};
