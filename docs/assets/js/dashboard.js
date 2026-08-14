// dashboard.js
// Membaca docs/data/data.json (dihasilkan oleh scripts/fetch_data.py atau
// scripts/seed_from_snapshot.py) dan me-render seluruh komponen dashboard:
// KPI, chart, filter, kartu anak asuh, prestasi, dan galeri berita.

let STATE = { data: null, filters: { wilayah: "all", jenjang: "all", status: "all" } };

async function loadData() {
  const res = await fetch("data/data.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Gagal memuat data.json");
  return res.json();
}

function fmtNumber(n) {
  return new Intl.NumberFormat("id-ID").format(Math.round(n));
}

function fmtDate(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}

function renderKPI(d) {
  const r = d.ringkasan;
  const el = document.getElementById("kpi-grid");
  const items = [
    { label: "Total Anak Asuh", value: r.total_anak, cls: "green" },
    { label: "Aktif Terdampingi", value: r.total_aktif, cls: "" },
    { label: "Status Yatim", value: r.total_yatim, cls: "pink" },
    { label: "Status Piatu", value: r.total_piatu, cls: "pink" },
    { label: "Yatim Piatu", value: r.total_yatim_piatu, cls: "gold" },
    { label: "Wilayah Dampingan", value: r.total_wilayah, cls: "" },
    { label: "Prestasi Tercatat", value: r.total_prestasi, cls: "gold" },
    { label: "Total Bantuan Tersalurkan", value: "Rp " + fmtNumber(r.total_bantuan) + "rb", cls: "green" },
  ];
  el.innerHTML = items
    .map(
      (i) => `<div class="kpi-card ${i.cls}"><div class="kpi-value">${i.value}</div><div class="kpi-label">${i.label}</div></div>`
    )
    .join("");
}

function groupCount(arr, key) {
  const m = {};
  arr.forEach((x) => {
    const k = x[key] || "Tidak diketahui";
    m[k] = (m[k] || 0) + 1;
  });
  return m;
}

function toEntries(obj) {
  return Object.entries(obj)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
}

function renderCharts(d) {
  const anak = d.anak_asuh;
  const { renderHBar, renderLine } = window.PejuangCharts;

  renderHBar("chart-jenjang", toEntries(groupCount(anak, "jenjang")), { singleHue: "#2a78d6", ariaLabel: "Jumlah anak per jenjang pendidikan" });
  renderHBar("chart-gender", toEntries(groupCount(anak, "gender")), { ariaLabel: "Proporsi gender anak asuh" });
  renderHBar("chart-status", toEntries(groupCount(anak, "status_yatim")), { ariaLabel: "Sebaran status yatim/piatu" });
  renderHBar("chart-wilayah", toEntries(groupCount(anak, "wilayah")), { singleHue: "#1baf7a", ariaLabel: "Jumlah anak per wilayah dampingan" });
  renderHBar("chart-biaya-kategori", toEntries(d.biaya.per_kategori), { ariaLabel: "Total bantuan per kategori", labelWidth: 130 });

  const bulanEntries = Object.entries(d.biaya.per_bulan)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([label, value]) => ({ label, value }));
  renderLine("chart-biaya-bulan", bulanEntries, { ariaLabel: "Tren bantuan tersalurkan per bulan" });
}

function populateFilterOptions(anak) {
  const wilayahSel = document.getElementById("filter-wilayah");
  const jenjangSel = document.getElementById("filter-jenjang");
  const wilayahs = [...new Set(anak.map((a) => a.wilayah))].sort();
  const jenjangs = [...new Set(anak.map((a) => a.jenjang).filter((j) => j && j !== "-"))].sort();
  wilayahs.forEach((w) => wilayahSel.insertAdjacentHTML("beforeend", `<option value="${w}">${w}</option>`));
  jenjangs.forEach((j) => jenjangSel.insertAdjacentHTML("beforeend", `<option value="${j}">${j}</option>`));
}

function statusBadgeClass(s) {
  if (s === "Yatim") return "status-yatim";
  if (s === "Piatu") return "status-piatu";
  if (s === "Yatim Piatu") return "status-yp";
  return "";
}

function renderAnakGrid(d) {
  const { wilayah, jenjang, status } = STATE.filters;
  let list = d.anak_asuh.filter(
    (a) =>
      (wilayah === "all" || a.wilayah === wilayah) &&
      (jenjang === "all" || a.jenjang === jenjang) &&
      (status === "all" || a.status_yatim === status)
  );
  const grid = document.getElementById("anak-grid");
  document.getElementById("anak-count").textContent = list.length;
  grid.innerHTML = list
    .map(
      (a) => `
    <div class="anak-card">
      <img class="avatar" src="${a.avatar}" alt="Avatar ilustrasi ${a.gender === "Perempuan" ? "anak perempuan" : "anak laki-laki"}" />
      <div class="nama">${a.nama}</div>
      <div class="meta">${a.jenjang !== "-" ? a.jenjang : "Usia dini"} &middot; ${a.wilayah}</div>
      <div class="badge-row">
        <span class="badge ${statusBadgeClass(a.status_yatim)}">${a.status_yatim}</span>
        ${!a.aktif ? '<span class="badge inaktif">Nonaktif</span>' : ""}
        ${a.perlu_pendampingan ? '<span class="badge pendamping">Perlu perhatian</span>' : ""}
      </div>
    </div>`
    )
    .join("");
}

function renderPrestasi(d) {
  const el = document.getElementById("prestasi-list");
  if (!d.prestasi.length) {
    el.innerHTML = `<p style="color:var(--muted)">Belum ada prestasi tercatat.</p>`;
    return;
  }
  el.innerHTML = d.prestasi
    .map(
      (p) => `
    <div class="prestasi-item">
      <div class="medal">🏅</div>
      <div>
        <div class="title">${p.judul} — ${p.nama}</div>
        <div class="sub">${p.tingkat} &middot; ${fmtDate(p.tanggal)} &middot; ${p.deskripsi}</div>
      </div>
    </div>`
    )
    .join("");
}

function renderBerita(d) {
  const el = document.getElementById("berita-grid");
  el.innerHTML = d.berita
    .map(
      (b) => `
    <div class="berita-card">
      <img src="${b.gambar}" alt="Dokumentasi kegiatan" loading="lazy" onerror="this.style.display='none'" />
      <div class="berita-body">
        <div class="berita-date">${fmtDate(b.tanggal)}</div>
        <div class="berita-text">${b.isi}</div>
      </div>
    </div>`
    )
    .join("");
}

function bindFilters(d) {
  ["wilayah", "jenjang", "status"].forEach((key) => {
    document.getElementById(`filter-${key}`).addEventListener("change", (e) => {
      STATE.filters[key] = e.target.value;
      renderAnakGrid(d);
    });
  });
}

async function init() {
  try {
    const d = await loadData();
    STATE.data = d;
    document.getElementById("last-updated").textContent = fmtDate(d.generated_at);
    renderKPI(d);
    renderCharts(d);
    populateFilterOptions(d.anak_asuh);
    renderAnakGrid(d);
    renderPrestasi(d);
    renderBerita(d);
    bindFilters(d);
  } catch (err) {
    console.error(err);
    document.body.insertAdjacentHTML(
      "afterbegin",
      `<div style="background:#fdeef4;color:#b23163;padding:14px;text-align:center;font-weight:700">Gagal memuat data dashboard. Pastikan docs/data/data.json tersedia.</div>`
    );
  }
}

document.addEventListener("DOMContentLoaded", init);
