/**
 * Standalone Zero-Dependency High-Definition SVG Chart Engine
 * Renders high-resolution SVGs with crisp lines, grid guides, and glowing area fills.
 */

const Charts = {
  
  /**
   * Render Donut Chart (Message Split)
   */
  renderDonut(containerId, data = []) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) {
      container.innerHTML = `<div style="color:var(--text-faint);text-align:center;padding:2rem;">No data to display</div>`;
      return;
    }

    const size = 220;
    const strokeWidth = 28;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const center = size / 2;

    let accumulatedPct = 0;
    const slicesSvg = data.map((item) => {
      const pct = item.value / total;
      const strokeDasharray = `${pct * circumference} ${circumference}`;
      const strokeDashoffset = -accumulatedPct * circumference;
      accumulatedPct += pct;

      return `
        <circle 
          cx="${center}" cy="${center}" r="${radius}"
          fill="none"
          stroke="${item.color}"
          stroke-width="${strokeWidth}"
          stroke-dasharray="${strokeDasharray}"
          stroke-dashoffset="${strokeDashoffset}"
          stroke-linecap="round"
          style="transition: stroke-dasharray 0.6s ease;"
        />
      `;
    }).join("");

    const legendHtml = data.map(item => `
      <div style="display:flex;align-items:center;gap:0.6rem;font-size:0.9rem;">
        <span style="width:12px;height:12px;border-radius:50%;background:${item.color};display:inline-block;box-shadow:0 0 8px ${item.color}80;"></span>
        <span style="font-weight:700;">${item.label}:</span>
        <span style="color:var(--text-muted);">${item.value.toLocaleString()} (${((item.value / total) * 100).toFixed(1)}%)</span>
      </div>
    `).join("");

    container.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;gap:2rem;flex-wrap:wrap;padding:0.5rem 0;">
        <div style="position:relative;width:${size}px;height:${size}px;">
          <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform: rotate(-90deg);">
            ${slicesSvg}
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">
            <span style="font-size:1.5rem;font-weight:800;letter-spacing:-0.5px;">${total.toLocaleString()}</span>
            <span style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Messages</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:0.8rem;">
          ${legendHtml}
        </div>
      </div>
    `;
  },

  /**
   * Render 24-Hour Continuous Spline Line & Area Chart
   */
  renderHourlyRhythm(containerId, hourlyData = []) {
    const container = document.getElementById(containerId);
    if (!container || !hourlyData.length) return;

    const width = 480;
    const height = 200;
    const padding = { top: 25, right: 20, bottom: 35, left: 45 };

    const maxVal = Math.max(...hourlyData.map(d => d.total), 10);
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const getX = (hour) => padding.left + (hour / 23) * chartW;
    const getY = (val) => padding.top + chartH - (val / maxVal) * chartH;

    // Build smooth Bezier path
    let pathD = "";
    let areaD = "";

    hourlyData.forEach((d, i) => {
      const x = getX(d.hour);
      const y = getY(d.total);

      if (i === 0) {
        pathD += `M ${x},${y}`;
        areaD += `M ${x},${getY(0)} L ${x},${y}`;
      } else {
        const prev = hourlyData[i - 1];
        const prevX = getX(prev.hour);
        const prevY = getY(prev.total);
        const cpX1 = prevX + (x - prevX) / 2;
        const cpX2 = prevX + (x - prevX) / 2;
        pathD += ` C ${cpX1},${prevY} ${cpX2},${y} ${x},${y}`;
        areaD += ` C ${cpX1},${prevY} ${cpX2},${y} ${x},${y}`;
      }
    });

    areaD += ` L ${getX(23)},${getY(0)} Z`;

    // Find peak hour
    let peak = hourlyData[0];
    hourlyData.forEach(d => { if (d.total > peak.total) peak = d; });

    const xLabels = [0, 4, 8, 12, 16, 20, 23].map(h => `
      <text x="${getX(h)}" y="${height - 10}" font-size="10.5" fill="var(--text-muted)" text-anchor="middle" font-weight="600">
        ${h === 0 ? '12 AM' : h === 12 ? '12 PM' : h > 12 ? (h - 12) + ' PM' : h + ' AM'}
      </text>
    `).join("");

    // Horizontal Grid Lines
    const yGridSteps = [0, Math.round(maxVal / 2), maxVal];
    const gridLines = yGridSteps.map(val => `
      <g>
        <line x1="${padding.left}" y1="${getY(val)}" x2="${width - padding.right}" y2="${getY(val)}" stroke="rgba(255,255,255,0.12)" stroke-dasharray="${val === 0 ? '0' : '4 4'}"/>
        <text x="${padding.left - 8}" y="${getY(val) + 3}" font-size="9.5" fill="var(--text-faint)" text-anchor="end">${val}</text>
      </g>
    `).join("");

    container.innerHTML = `
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        <defs>
          <linearGradient id="hourlyGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ec4899" stop-opacity="0.5"/>
            <stop offset="60%" stop-color="#8b5cf6" stop-opacity="0.2"/>
            <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0.0"/>
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#ec4899" flood-opacity="0.6"/>
          </filter>
        </defs>

        <!-- Grid Lines & Y Axis Labels -->
        ${gridLines}

        <!-- Filled Area -->
        <path d="${areaD}" fill="url(#hourlyGrad)" />

        <!-- Crisp Glowing Line -->
        <path d="${pathD}" fill="none" stroke="#ec4899" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>

        <!-- Hourly Data Points -->
        ${hourlyData.map(d => `
          <circle cx="${getX(d.hour)}" cy="${getY(d.total)}" r="${d.hour === peak.hour ? 5 : 3}" fill="${d.hour === peak.hour ? '#ec4899' : '#ffffff'}" stroke="#ec4899" stroke-width="2">
            <title>${d.hour}:00 - ${d.total.toLocaleString()} messages</title>
          </circle>
        `).join("")}

        <!-- Peak Indicator Pill -->
        <g transform="translate(${getX(peak.hour)}, ${getY(peak.total) - 12})">
          <rect x="-35" y="-14" width="70" height="16" rx="8" fill="#ec4899" />
          <text x="0" y="-3" font-size="8.5" fill="#ffffff" text-anchor="middle" font-weight="700">🔥 Peak (${peak.total})</text>
        </g>

        <!-- X Axis Labels -->
        ${xLabels}
      </svg>
    `;
  },

  /**
   * Render Monthly Trajectory Spline Line & Area Chart
   */
  renderMonthlyTrend(containerId, monthlyStats = []) {
    const container = document.getElementById(containerId);
    if (!container || !monthlyStats.length) return;

    const width = 480;
    const height = 200;
    const padding = { top: 25, right: 20, bottom: 35, left: 45 };

    const maxVal = Math.max(...monthlyStats.map(d => d.total), 10);
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const count = monthlyStats.length;
    const getX = (i) => padding.left + (i / Math.max(1, count - 1)) * chartW;
    const getY = (val) => padding.top + chartH - (val / maxVal) * chartH;

    // Smooth Bezier Curve Path
    let pathD = "";
    let areaD = "";

    monthlyStats.forEach((d, i) => {
      const x = getX(i);
      const y = getY(d.total);

      if (i === 0) {
        pathD += `M ${x},${y}`;
        areaD += `M ${x},${getY(0)} L ${x},${y}`;
      } else {
        const prevX = getX(i - 1);
        const prevY = getY(monthlyStats[i - 1].total);
        const cpX = prevX + (x - prevX) / 2;
        pathD += ` C ${cpX},${prevY} ${cpX},${y} ${x},${y}`;
        areaD += ` C ${cpX},${prevY} ${cpX},${y} ${x},${y}`;
      }
    });

    areaD += ` L ${getX(count - 1)},${getY(0)} Z`;

    // Grid lines
    const yGridSteps = [0, Math.round(maxVal / 2), maxVal];
    const gridLines = yGridSteps.map(val => `
      <g>
        <line x1="${padding.left}" y1="${getY(val)}" x2="${width - padding.right}" y2="${getY(val)}" stroke="rgba(255,255,255,0.12)" stroke-dasharray="${val === 0 ? '0' : '4 4'}"/>
        <text x="${padding.left - 8}" y="${getY(val) + 3}" font-size="9.5" fill="var(--text-faint)" text-anchor="end">${val.toLocaleString()}</text>
      </g>
    `).join("");

    const monthNames = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const xLabels = monthlyStats.map((d, i) => {
      const parts = d.month.split("-");
      const label = `${monthNames[parseInt(parts[1])] || parts[1]} '${parts[0].substring(2)}`;
      return `
        <text x="${getX(i)}" y="${height - 10}" font-size="10" fill="var(--text-muted)" text-anchor="middle" font-weight="600">
          ${label}
        </text>
      `;
    }).join("");

    container.innerHTML = `
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        <defs>
          <linearGradient id="monthGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#10b981" stop-opacity="0.45"/>
            <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
          </linearGradient>
          <filter id="greenGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#10b981" flood-opacity="0.5"/>
          </filter>
        </defs>

        <!-- Grid Lines & Y Axis -->
        ${gridLines}

        <!-- Gradient Area -->
        <path d="${areaD}" fill="url(#monthGrad)" />

        <!-- Glowing Line -->
        <path d="${pathD}" fill="none" stroke="#10b981" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#greenGlow)"/>

        <!-- Points & Value Labels -->
        ${monthlyStats.map((d, i) => `
          <g>
            <circle cx="${getX(i)}" cy="${getY(d.total)}" r="4.5" fill="#10b981" stroke="#ffffff" stroke-width="2">
              <title>${d.month}: ${d.total.toLocaleString()} messages</title>
            </circle>
            <text x="${getX(i)}" y="${getY(d.total) - 8}" font-size="9.5" fill="var(--text-main)" text-anchor="middle" font-weight="700">
              ${d.total.toLocaleString()}
            </text>
          </g>
        `).join("")}

        <!-- X Labels -->
        ${xLabels}
      </svg>
    `;
  },

  /**
   * Render Day of Week Bar Chart with Top Trend Line & Grid Lines
   */
  renderBarChart(containerId, items = [], labelKey = "label", valueKey = "value", color = "#8b5cf6") {
    const container = document.getElementById(containerId);
    if (!container || !items.length) return;

    const width = 480;
    const height = 200;
    const padding = { top: 25, right: 20, bottom: 35, left: 45 };

    const maxVal = Math.max(...items.map(d => d[valueKey]), 10);
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const barWidth = Math.max(16, (chartW / items.length) - 14);

    // Grid lines
    const yGridSteps = [0, Math.round(maxVal / 2), maxVal];
    const gridLines = yGridSteps.map(val => `
      <g>
        <line x1="${padding.left}" y1="${padding.top + chartH - (val / maxVal) * chartH}" x2="${width - padding.right}" y2="${padding.top + chartH - (val / maxVal) * chartH}" stroke="rgba(255,255,255,0.12)" stroke-dasharray="${val === 0 ? '0' : '4 4'}"/>
        <text x="${padding.left - 8}" y="${padding.top + chartH - (val / maxVal) * chartH + 3}" font-size="9.5" fill="var(--text-faint)" text-anchor="end">${val.toLocaleString()}</text>
      </g>
    `).join("");

    // Trendline connecting tops of bars
    const trendPoints = items.map((d, i) => {
      const x = padding.left + (i * (chartW / items.length)) + (chartW / items.length) / 2;
      const barH = (d[valueKey] / maxVal) * chartH;
      const y = padding.top + chartH - barH;
      return `${x},${y}`;
    }).join(" ");

    const barsSvg = items.map((d, i) => {
      const x = padding.left + (i * (chartW / items.length)) + (chartW / items.length - barWidth) / 2;
      const barH = (d[valueKey] / maxVal) * chartH;
      const y = padding.top + chartH - barH;

      return `
        <g class="chart-bar-group">
          <!-- Background track rail -->
          <rect x="${x}" y="${padding.top}" width="${barWidth}" height="${chartH}" fill="rgba(255,255,255,0.03)" rx="5"/>
          
          <!-- Bar -->
          <rect 
            x="${x}" y="${y}" width="${barWidth}" height="${barH}" 
            fill="${color}" rx="5"
            opacity="0.9"
            style="transition: height 0.4s ease;"
          />
          <text x="${x + barWidth/2}" y="${height - 10}" font-size="10.5" fill="var(--text-muted)" text-anchor="middle" font-weight="600">
            ${d[labelKey]}
          </text>
          <text x="${x + barWidth/2}" y="${y - 6}" font-size="9.5" fill="var(--text-main)" text-anchor="middle" font-weight="700">
            ${d[valueKey] > 0 ? d[valueKey].toLocaleString() : ''}
          </text>
        </g>
      `;
    }).join("");

    container.innerHTML = `
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
        <!-- Grid lines & Y Axis -->
        ${gridLines}

        <!-- Connecting trend line -->
        <polyline points="${trendPoints}" fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="3 3" opacity="0.6"/>

        <!-- Bars -->
        ${barsSvg}
      </svg>
    `;
  }
};
