/**
 * Statistics Component
 * - Factual metrics summary cards
 * - Reply speed & dynamics (Vinu vs Bhuu)
 * - Friendship Milestones ribbon (1st, 1K, 5K, 10K, 15K msgs)
 * - Message split Donut Chart
 * - 24-Hour chatting rhythm Area Chart
 * - Day of Week & Monthly Bar Charts
 * - Top Emojis & Words leaderboards
 */

const StatsComponent = {
  async load() {
    try {
      const data = await API.stats.overview();
      this.renderTopCards(data);
      this.renderDynamicsCards(data);
      this.renderMilestones(data);
      this.renderCharts(data);
      this.renderLeaderboards(data);
    } catch (err) {
      console.error("Failed to load statistics:", err);
    }
  },

  renderTopCards(data) {
    const container = document.getElementById("statsTopCards");
    if (!container) return;

    const bhuuMsgs = data.bhuu_messages || data.bhumi_messages || 0;
    const bhuuPct = data.bhuu_percentage || data.bhumi_percentage || 0;

    container.innerHTML = `
      <div class="metric-card">
        <span class="metric-title">Total Messages</span>
        <span class="metric-value" style="background:linear-gradient(135deg,#ec4899,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          ${data.total_messages?.toLocaleString() || 0}
        </span>
        <span class="metric-sub">${data.start_date} to ${data.end_date}</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">Bhuu's Messages</span>
        <span class="metric-value text-bhumi">
          ${bhuuMsgs.toLocaleString()}
        </span>
        <span class="metric-sub">${bhuuPct}% of total archive</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">Vinu's Messages</span>
        <span class="metric-value text-vinu">
          ${data.vinu_messages?.toLocaleString() || 0}
        </span>
        <span class="metric-sub">${data.vinu_percentage}% of total archive</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">Active Days</span>
        <span class="metric-value">${data.active_days || 0}</span>
        <span class="metric-sub">~${data.average_messages_per_day} msgs/day</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">Longest Streak</span>
        <span class="metric-value" style="color:var(--accent-gold);">
          🔥 ${data.streak_info?.longest_streak || 0} <span style="font-size:1rem;font-weight:600;">Days</span>
        </span>
        <span class="metric-sub">${data.streak_info?.longest_streak_dates || ''}</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">Peak Day</span>
        <span class="metric-value" style="font-size:1.4rem;">
          ${data.most_active_day?.date || ''}
        </span>
        <span class="metric-sub">${data.most_active_day?.count?.toLocaleString() || 0} messages in 24h</span>
      </div>
    `;
  },

  renderDynamicsCards(data) {
    const container = document.getElementById("statsDynamicsCards");
    if (!container || !data.dynamics) return;

    const dyn = data.dynamics;

    container.innerHTML = `
      <div class="metric-card">
        <span class="metric-title">⚡ Vinu's Reply Speed</span>
        <span class="metric-value text-vinu" style="font-size:1.5rem;">
          ${dyn.vinu_avg_response_formatted}
        </span>
        <span class="metric-sub">Average active reply delay</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">⚡ Bhuu's Reply Speed</span>
        <span class="metric-value text-bhumi" style="font-size:1.5rem;">
          ${dyn.bhuu_avg_response_formatted}
        </span>
        <span class="metric-sub">Average active reply delay</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">💬 Chat Starters</span>
        <span class="metric-value" style="font-size:1.3rem;">
          Vinu: ${dyn.starters?.vinu_pct}% • Bhuu: ${dyn.starters?.bhuu_pct}%
        </span>
        <span class="metric-sub">Initiations after > 2h silence</span>
      </div>

      <div class="metric-card">
        <span class="metric-title">🌙 Late-Night Messages</span>
        <span class="metric-value" style="color:var(--accent-purple);font-size:1.5rem;">
          ${dyn.late_night?.total?.toLocaleString() || 0}
        </span>
        <span class="metric-sub">Exchanged between 11 PM & 5 AM</span>
      </div>
    `;
  },

  renderMilestones(data) {
    const ribbon = document.getElementById("milestonesRibbon");
    if (!ribbon || !data.milestones) return;

    ribbon.innerHTML = data.milestones.map(m => `
      <div class="milestone-item btn-jump-to-chat" data-id="${m.message_id}">
        <span class="milestone-badge">🎯 ${m.milestone}</span>
        <span style="font-size:0.75rem;color:var(--text-faint);">${m.date_str} ${m.time_str}</span>
        <span style="font-size:0.75rem;font-weight:700;color:${m.sender_clean.includes('Vinu') ? 'var(--accent-vinu)' : 'var(--accent-bhumi)'};">
          ${m.sender_clean}:
        </span>
        <span class="milestone-content">${m.content}</span>
      </div>
    `).join("");

    ribbon.querySelectorAll(".btn-jump-to-chat").forEach(btn => {
      btn.onclick = () => {
        const msgId = parseInt(btn.dataset.id);
        if (window.App && typeof window.App.switchToTabAndJump === "function") {
          window.App.switchToTabAndJump("chat", msgId);
        }
      };
    });
  },

  renderCharts(data) {
    const bhuuMsgs = data.bhuu_messages || data.bhumi_messages || 0;

    // 1. Message Share Donut
    Charts.renderDonut("chartMessageSplit", [
      { label: "Bhuu 🎀", value: bhuuMsgs, color: "#ec4899" },
      { label: "Vinu 💝🎀", value: data.vinu_messages || 0, color: "#10b981" }
    ]);

    // 2. 24-Hour Hourly Rhythm
    if (data.hourly_stats) {
      Charts.renderHourlyRhythm("chartHourlyHeatmap", data.hourly_stats);
    }

    // 3. Day of Week
    if (data.dow_stats) {
      const dowFormatted = data.dow_stats.map(d => ({
        label: d.day_name.substring(0, 3),
        value: d.total
      }));
      Charts.renderBarChart("chartDayOfWeek", dowFormatted, "label", "value", "#8b5cf6");
    }

    // 4. Monthly Trend Continuous Spline & Area Chart
    if (data.monthly_stats) {
      Charts.renderMonthlyTrend("chartMonthlyTrend", data.monthly_stats);
    }
  },

  renderLeaderboards(data) {
    // Top Emojis
    const emojiList = document.getElementById("topEmojisList");
    if (emojiList && data.top_emojis) {
      emojiList.innerHTML = data.top_emojis.slice(0, 8).map(em => {
        const bhuuCount = em.bhuu || em.bhumi || 0;
        return `
          <div class="leaderboard-item">
            <span style="font-size:1.3rem;">${em.emoji}</span>
            <span style="font-weight:700;">${em.count.toLocaleString()} times</span>
            <span style="font-size:0.78rem;color:var(--text-muted);">
              (Vinu: ${em.vinu} • Bhuu: ${bhuuCount})
            </span>
          </div>
        `;
      }).join("");
    }

    // Top Words
    const wordList = document.getElementById("topWordsList");
    if (wordList && data.top_words) {
      wordList.innerHTML = data.top_words.map(w => `
        <span class="word-pill" title="${w.count} occurrences">
          <strong>${w.word}</strong> <span style="color:var(--text-faint);font-size:0.75rem;">${w.count}</span>
        </span>
      `).join("");
    }
  }
};
