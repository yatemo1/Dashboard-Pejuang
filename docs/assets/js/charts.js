// charts.js
// Lightweight, dependency-free SVG chart primitives (tanpa CDN eksternal,
// supaya dashboard tetap tampil walau GitHub Pages/browser membatasi
// pemuatan skrip pihak ketiga). Mengikuti palet kategorikal yang sudah
// divalidasi (lightness band, chroma floor, CVD separation) — lihat
// dataviz skill reference.

// Fixed-order categorical palette (validated) — never cycled/reassigned per filter.
const CAT_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const INK_PRIMARY = "#0b0b0b";
const INK_SECOND = "#52514e";
const INK_MUTED = "#898781";
const GRID = "#e1e0d9";

function svg(tag, attrs = {}) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function fmtVal(v) {
  return new Intl.NumberFormat("id-ID").format(Math.round(v));
}

/**
 * Horizontal bar chart — best for category comparison + direct labels
 * (avoids donut/pie ambiguity, satisfies "relief" requirement for
 * low-contrast palette slots since every value is printed, not color-only).
 */
function renderHBar(containerId, entries, opts = {}) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  if (!entries.length) {
    container.innerHTML = `<p style="color:${INK_MUTED};font-size:.85rem">Belum ada data.</p>`;
    return;
  }
  const max = Math.max(...entries.map((e) => e.value), 1);
  const rowH = 34;
  const width = container.clientWidth || 320;
  const height = entries.length * rowH + 10;
  const labelW = opts.labelWidth || 96;
  const chartW = width - labelW - 50;

  const root = svg("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": opts.ariaLabel || "Grafik batang" });

  entries.forEach((e, i) => {
    const y = i * rowH;
    const barW = Math.max((e.value / max) * chartW, 3);
    const color = opts.singleHue ? opts.singleHue : CAT_PALETTE[i % CAT_PALETTE.length];

    const label = svg("text", { x: 0, y: y + rowH / 2 + 4, "font-size": 12, fill: INK_SECOND, "font-weight": 600 });
    label.textContent = e.label.length > 16 ? e.label.slice(0, 15) + "…" : e.label;
    root.appendChild(label);

    const track = svg("rect", { x: labelW, y: y + 7, width: chartW, height: 14, rx: 7, fill: "#f1efe9" });
    root.appendChild(track);

    const bar = svg("rect", {
      x: labelW,
      y: y + 7,
      width: barW,
      height: 14,
      rx: 7,
      fill: color,
    });
    bar.appendChild(svg("title")).textContent = `${e.label}: ${fmtVal(e.value)}`;
    root.appendChild(bar);

    const valText = svg("text", {
      x: labelW + barW + 8,
      y: y + rowH / 2 + 4,
      "font-size": 12,
      fill: INK_PRIMARY,
      "font-weight": 700,
    });
    valText.textContent = fmtVal(e.value) + (opts.suffix || "");
    root.appendChild(valText);
  });

  container.appendChild(root);
}

/**
 * Simple line chart for a single time series (one axis, no dual-axis).
 */
function renderLine(containerId, points, opts = {}) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  if (!points.length) {
    container.innerHTML = `<p style="color:${INK_MUTED};font-size:.85rem">Belum ada data.</p>`;
    return;
  }
  const width = container.clientWidth || 320;
  const height = 220;
  const padL = 44, padR = 16, padT = 16, padB = 34;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const maxV = Math.max(...points.map((p) => p.value), 1);

  const root = svg("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": opts.ariaLabel || "Grafik tren" });

  // gridlines + y ticks
  const steps = 4;
  for (let s = 0; s <= steps; s++) {
    const y = padT + (plotH / steps) * s;
    root.appendChild(svg("line", { x1: padL, x2: width - padR, y1: y, y2: y, stroke: GRID, "stroke-width": 1 }));
    const val = maxV - (maxV / steps) * s;
    const t = svg("text", { x: padL - 8, y: y + 4, "font-size": 10, fill: INK_MUTED, "text-anchor": "end" });
    t.textContent = fmtVal(val);
    root.appendChild(t);
  }

  const stepX = points.length > 1 ? plotW / (points.length - 1) : 0;
  const coords = points.map((p, i) => ({
    x: padL + stepX * i,
    y: padT + plotH - (p.value / maxV) * plotH,
    ...p,
  }));

  const pathD = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x},${c.y}`).join(" ");
  root.appendChild(svg("path", { d: pathD, fill: "none", stroke: CAT_PALETTE[0], "stroke-width": 2.5, "stroke-linecap": "round", "stroke-linejoin": "round" }));

  const areaD = `${pathD} L${coords[coords.length - 1].x},${padT + plotH} L${coords[0].x},${padT + plotH} Z`;
  root.appendChild(svg("path", { d: areaD, fill: CAT_PALETTE[0], opacity: 0.08 }));

  coords.forEach((c) => {
    const dot = svg("circle", { cx: c.x, cy: c.y, r: 4, fill: "#fff", stroke: CAT_PALETTE[0], "stroke-width": 2.5 });
    dot.appendChild(svg("title")).textContent = `${c.label}: ${fmtVal(c.value)}`;
    root.appendChild(dot);

    const lbl = svg("text", { x: c.x, y: height - 10, "font-size": 10, fill: INK_MUTED, "text-anchor": "middle" });
    lbl.textContent = c.label;
    root.appendChild(lbl);
  });

  container.appendChild(root);
}

window.PejuangCharts = { renderHBar, renderLine, CAT_PALETTE };
