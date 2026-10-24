/**
 * Evolution Component
 * - 2025 vs 2026 side-by-side comparison
 * - Factual velocity and communication style metrics
 */

const EvolutionComponent = {
  async load() {
    const container = document.getElementById("evolutionContent");
    if (!container) return;

    container.innerHTML = `<div style="text-align:center;padding:2rem;"><div class="spinner"></div></div>`;

    try {
      const data = await API.stats.evolution();
      this.renderEvolution(data);
    } catch (err) {
      container.innerHTML = `<div style="color:#f87171;">Failed to load evolution data: ${err.message}</div>`;
    }
  },

  renderEvolution(data) {
    const container = document.getElementById("evolutionContent");
    if (!container) return;

    const p1 = data.period_1;
    const p2 = data.period_2;
    const cmp = data.comparison;

    container.innerHTML = `
      <!-- Highlight Banner -->
      <div style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:var(--radius-md);padding:1.2rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem;">
        <span style="font-size:2rem;">🚀</span>
        <div>
          <h4 style="font-size:1rem;font-weight:700;">Evolution Summary</h4>
          <p style="font-size:0.85rem;color:var(--text-muted);">${cmp.summary}</p>
        </div>
      </div>

      <!-- Side-by-Side Cards -->
      <div class="evolution-cards-pair">
        
        <!-- Period 1: 2025 -->
        <div class="evolution-box">
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-color);padding-bottom:0.6rem;">
            <h3 style="font-size:1.1rem;font-weight:700;">🌱 ${p1.label}</h3>
            <span style="font-size:0.8rem;color:var(--text-muted);">${p1.period}</span>
          </div>

          <table class="evolution-table">
            <tr>
              <td style="color:var(--text-muted);">Total Messages</td>
              <td style="text-align:right;font-weight:700;">${p1.total_messages.toLocaleString()}</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Active Days</td>
              <td style="text-align:right;font-weight:700;">${p1.active_days}</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Daily Velocity</td>
              <td style="text-align:right;font-weight:700;">${p1.msgs_per_day} msgs/day</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Bhuu's Share</td>
              <td style="text-align:right;font-weight:700;color:var(--accent-bhumi);">${p1.bhuu_pct || p1.bhumi_pct}%</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Vinu's Share</td>
              <td style="text-align:right;font-weight:700;color:var(--accent-vinu);">${p1.vinu_pct}%</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Avg Word Length</td>
              <td style="text-align:right;font-weight:700;">${p1.avg_words} words/msg</td>
            </tr>
          </table>

          <div>
            <h4 style="font-size:0.82rem;text-transform:uppercase;color:var(--text-faint);margin-bottom:0.4rem;">Top Emojis (2025)</h4>
            <div style="display:flex;gap:0.4rem;font-size:1.2rem;">
              ${p1.top_emojis.length > 0 ? p1.top_emojis.slice(0, 6).map(e => `<span>${e.emoji}</span>`).join("") : '<span style="font-size:0.8rem;color:var(--text-faint);">None recorded</span>'}
            </div>
          </div>
        </div>

        <!-- Period 2: 2026 -->
        <div class="evolution-box" style="border-color:var(--accent-bhumi);">
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-color);padding-bottom:0.6rem;">
            <h3 style="font-size:1.1rem;font-weight:700;color:var(--accent-bhumi);">🔥 ${p2.label}</h3>
            <span style="font-size:0.8rem;color:var(--text-muted);">${p2.period}</span>
          </div>

          <table class="evolution-table">
            <tr>
              <td style="color:var(--text-muted);">Total Messages</td>
              <td style="text-align:right;font-weight:700;">${p2.total_messages.toLocaleString()}</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Active Days</td>
              <td style="text-align:right;font-weight:700;">${p2.active_days}</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Daily Velocity</td>
              <td style="text-align:right;font-weight:700;color:var(--accent-gold);">${p2.msgs_per_day} msgs/day</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Bhuu's Share</td>
              <td style="text-align:right;font-weight:700;color:var(--accent-bhumi);">${p2.bhuu_pct || p2.bhumi_pct}%</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Vinu's Share</td>
              <td style="text-align:right;font-weight:700;color:var(--accent-vinu);">${p2.vinu_pct}%</td>
            </tr>
            <tr>
              <td style="color:var(--text-muted);">Avg Word Length</td>
              <td style="text-align:right;font-weight:700;">${p2.avg_words} words/msg</td>
            </tr>
          </table>

          <div>
            <h4 style="font-size:0.82rem;text-transform:uppercase;color:var(--text-faint);margin-bottom:0.4rem;">Top Emojis (2026)</h4>
            <div style="display:flex;gap:0.4rem;font-size:1.2rem;">
              ${p2.top_emojis.length > 0 ? p2.top_emojis.slice(0, 6).map(e => `<span>${e.emoji}</span>`).join("") : '<span style="font-size:0.8rem;color:var(--text-faint);">None</span>'}
            </div>
          </div>
        </div>

      </div>
    `;
  }
};
