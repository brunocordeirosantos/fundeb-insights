/**
 * estados.js — Análise Estadual (estados.html)
 *
 * Sections:
 *   1. KPI cards nacionais
 *   2. Grouped bar chart: per aluno estadual vs mediana municipal
 *   3. Scatter: per aluno estadual × IDEB médio
 *   4. Tabela sortável de todos os estados
 *   5. Painel de detalhes ao clicar numa linha
 */

let allData      = [];   // full comparativo payload
let tableData    = [];   // currently rendered subset
let sortCol      = "fundeb_per_aluno_estadual";
let sortDir      = "desc";

document.addEventListener("DOMContentLoaded", init);

// ── Bootstrap ──────────────────────────────────────────────────────────────────

async function init() {
  try {
    const [comparativo, resumo] = await Promise.all([
      api.estadosComparativo(),
      api.estadosResumo(),
    ]);

    allData = comparativo;

    renderKpis(resumo, comparativo);
    renderCharts(comparativo);
    renderTable(comparativo);

    document.getElementById("filter-regiao").addEventListener("change", onFilter);
    document.getElementById("filter-regiao-table").addEventListener("change", onFilterTable);
    document.getElementById("filter-ordem-bar").addEventListener("change", onFilter);
    document.getElementById("detail-close").addEventListener("click", closeDetail);

    // Table sort
    document.querySelectorAll(".estados-table th.sortable").forEach(th => {
      th.addEventListener("click", () => onSort(th.dataset.col));
    });

  } catch (err) {
    console.error("Erro ao inicializar:", err);
    document.getElementById("kpi-grid").innerHTML = `
      <div class="api-alert">
        <span class="api-alert-icon">⚠️</span>
        <div class="api-alert-body">
          <span class="api-alert-title">Não foi possível conectar à API</span>
          <span class="api-alert-desc">Verifique se o servidor está rodando em <code>http://localhost:8001</code>.</span>
        </div>
      </div>`;
  }
}

// ── Filters ─────────────────────────────────────────────────────────────────────

function filterByRegiao(data, selectId) {
  const regiao = document.getElementById(selectId).value;
  return regiao ? data.filter(d => d.regiao === regiao) : data;
}

function onFilter() {
  const filtered = filterByRegiao(allData, "filter-regiao");
  renderCharts(filtered);
}

function onFilterTable() {
  const filtered = filterByRegiao(allData, "filter-regiao-table");
  renderTable(filtered);
}

// ── KPI Cards ──────────────────────────────────────────────────────────────────

function renderKpis(resumo, comparativo) {
  const estadualMaior = comparativo.filter(d => d.razao_per_aluno && d.razao_per_aluno > 1).length;

  const cards = [
    {
      label: "FUNDEB rede estadual (Brasil)",
      value: fmtBRL(resumo.fundeb_estadual_brasil, true),
      sub: `${resumo.total_estados} governos estaduais · 2026`,
      cls: "primary",
    },
    {
      label: "FUNDEB rede municipal (Brasil)",
      value: fmtBRL(resumo.fundeb_municipal_brasil, true),
      sub: "Soma de todos os municípios",
      cls: "",
    },
    {
      label: "Alunos rede estadual",
      value: fmtInt(resumo.mat_estadual_brasil),
      sub: "Matrículas em escolas estaduais · Censo 2023",
      cls: "",
    },
    {
      label: "Alunos rede municipal",
      value: fmtInt(resumo.mat_municipal_brasil),
      sub: "Matrículas em escolas municipais · Censo 2023",
      cls: "accent",
    },
    {
      label: "Mediana nacional (estadual)",
      value: fmtBRL(resumo.mediana_per_aluno_estadual),
      sub: `${estadualMaior} estados com estado investindo mais que municípios`,
      cls: "",
    },
  ];

  document.getElementById("kpi-grid").innerHTML = cards.map(c => `
    <div class="kpi-card ${c.cls}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-sub">${c.sub}</div>
    </div>`).join("");
}

// ── Charts ──────────────────────────────────────────────────────────────────────

function renderCharts(data) {
  renderBarChart(data);
  renderScatter(data);
}

function sortedForBar(data) {
  const ordem = document.getElementById("filter-ordem-bar").value;
  const d = data.filter(r => r.fundeb_per_aluno_estadual && r.mediana_per_aluno_municipal);
  switch (ordem) {
    case "estadual_desc": return [...d].sort((a, b) => b.fundeb_per_aluno_estadual - a.fundeb_per_aluno_estadual);
    case "estadual_asc":  return [...d].sort((a, b) => a.fundeb_per_aluno_estadual - b.fundeb_per_aluno_estadual);
    case "razao_desc":    return [...d].sort((a, b) => (b.razao_per_aluno ?? 0) - (a.razao_per_aluno ?? 0));
    case "razao_asc":     return [...d].sort((a, b) => (a.razao_per_aluno ?? 0) - (b.razao_per_aluno ?? 0));
    case "uf_asc":        return [...d].sort((a, b) => a.uf.localeCompare(b.uf));
    default:              return d;
  }
}

function renderBarChart(data) {
  const sorted = sortedForBar(data);
  if (!sorted.length) return;

  const ufs      = sorted.map(d => d.uf);
  const estadual = sorted.map(d => d.fundeb_per_aluno_estadual);
  const municipal = sorted.map(d => d.mediana_per_aluno_municipal);

  const colorsEstadual = sorted.map(d =>
    d.razao_per_aluno > 1.05 ? "#58a6ff" :
    d.razao_per_aluno < 0.95 ? "#8b949e" : "#79c0ff"
  );

  const traces = [
    {
      type: "bar",
      name: "Rede Estadual",
      x: ufs,
      y: estadual,
      marker: { color: colorsEstadual },
      text: sorted.map(d => `R$ ${fmtNum(d.fundeb_per_aluno_estadual)}`),
      hovertemplate: "<b>%{x}</b> — Estadual<br>R$ %{y:,.0f}/aluno<extra></extra>",
    },
    {
      type: "bar",
      name: "Mediana Municipal",
      x: ufs,
      y: municipal,
      marker: { color: "#3fb950", opacity: 0.8 },
      hovertemplate: "<b>%{x}</b> — Municipal (mediana)<br>R$ %{y:,.0f}/aluno<extra></extra>",
    },
  ];

  const layout = {
    barmode: "group",
    paper_bgcolor: "transparent",
    plot_bgcolor: "#161b22",
    font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
    xaxis: { gridcolor: "#30363d", tickangle: -35 },
    yaxis: {
      title: { text: "R$/aluno", standoff: 8 },
      gridcolor: "#30363d", zerolinecolor: "#30363d",
      tickformat: ",.0f", tickprefix: "R$ ",
    },
    margin: { t: 20, r: 20, b: 80, l: 80 },
    legend: { x: 0, y: 1.05, orientation: "h", font: { color: "#8b949e", size: 11 } },
    hovermode: "x unified",
  };

  Plotly.react("chart-bar", traces, layout, { responsive: true, displayModeBar: false });

  const note = document.getElementById("chart-bar-note");
  note.textContent = `${sorted.length} estados · ordenado por ${document.getElementById("filter-ordem-bar").selectedOptions[0].text.toLowerCase()}`;
}

function renderScatter(data) {
  const d = data.filter(r => r.fundeb_per_aluno_estadual && r.media_ideb_iniciais);

  const REGIAO_COLORS = {
    "Norte":        "#58a6ff",
    "Nordeste":     "#d29922",
    "Sudeste":      "#3fb950",
    "Sul":          "#a5d6ff",
    "Centro-Oeste": "#bc8cff",
  };

  const byRegiao = {};
  d.forEach(row => {
    const r = row.regiao;
    if (!byRegiao[r]) byRegiao[r] = [];
    byRegiao[r].push(row);
  });

  const traces = Object.entries(byRegiao).map(([regiao, rows]) => ({
    type: "scatter",
    mode: "markers+text",
    name: regiao,
    x: rows.map(r => r.fundeb_per_aluno_estadual),
    y: rows.map(r => r.media_ideb_iniciais),
    text: rows.map(r => r.uf),
    textposition: "top center",
    textfont: { size: 10, color: "#e6edf3" },
    marker: {
      size: rows.map(r => Math.sqrt((r.mat_estadual_total || 50000) / 500) + 8),
      color: REGIAO_COLORS[regiao] || "#8b949e",
      opacity: 0.85,
      line: { width: 1, color: "rgba(0,0,0,0.3)" },
    },
    hovertemplate: rows.map(r =>
      `<b>${r.uf} — ${r.nome_estado}</b><br>` +
      `Per aluno estadual: R$ ${fmtNum(r.fundeb_per_aluno_estadual)}<br>` +
      `IDEB médio: ${r.media_ideb_iniciais?.toFixed(2) ?? "—"}<br>` +
      `Alunos rede estadual: ${fmtInt(r.mat_estadual_total)}<br>` +
      `Razão estado/municipal: ${r.razao_per_aluno?.toFixed(3) ?? "—"}`
    ).map(t => t + "<extra></extra>"),
  }));

  Plotly.react("chart-scatter", traces, {
    paper_bgcolor: "transparent",
    plot_bgcolor: "#161b22",
    font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
    xaxis: {
      title: { text: "FUNDEB por aluno — rede estadual (R$)", standoff: 12 },
      gridcolor: "#30363d", zerolinecolor: "#30363d",
      tickformat: ",.0f", tickprefix: "R$ ",
    },
    yaxis: {
      title: { text: "IDEB médio dos municípios (Anos Iniciais 2023)", standoff: 12 },
      gridcolor: "#30363d", zerolinecolor: "#30363d",
      range: [3, 8],
    },
    margin: { t: 20, r: 20, b: 60, l: 70 },
    hovermode: "closest",
    legend: { x: 1, xanchor: "right", y: 1, bgcolor: "transparent", font: { color: "#8b949e", size: 11 } },
  }, { responsive: true, displayModeBar: false });
}

// ── Table ───────────────────────────────────────────────────────────────────────

function onSort(col) {
  if (sortCol === col) {
    sortDir = sortDir === "desc" ? "asc" : "desc";
  } else {
    sortCol = col;
    sortDir = "desc";
  }
  // Update header indicators
  document.querySelectorAll(".estados-table th").forEach(th => {
    th.classList.remove("sort-asc", "sort-desc");
    if (th.dataset.col === sortCol) th.classList.add(`sort-${sortDir}`);
  });
  renderTable(tableData);
}

function renderTable(data) {
  tableData = data;

  const sorted = [...data].sort((a, b) => {
    const av = a[sortCol] ?? (typeof a[sortCol] === "string" ? "" : -Infinity);
    const bv = b[sortCol] ?? (typeof b[sortCol] === "string" ? "" : -Infinity);
    if (typeof av === "string") return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    return sortDir === "asc" ? av - bv : bv - av;
  });

  const tbody = document.getElementById("estados-tbody");
  tbody.innerHTML = sorted.map(row => {
    const razao = row.razao_per_aluno;
    const razaoClass = !razao ? "parity" : razao > 1.05 ? "above" : razao < 0.95 ? "below" : "parity";
    const razaoLabel = razao ? `${razao.toFixed(3)}` : "—";

    return `<tr data-uf="${row.uf}">
      <td><span class="uf-badge">${row.uf}</span></td>
      <td>${row.nome_estado}</td>
      <td><span class="regiao-badge">${row.regiao}</span></td>
      <td class="num">${row.fundeb_per_aluno_estadual ? "R$ " + fmtNum(row.fundeb_per_aluno_estadual) : "—"}</td>
      <td class="num">${row.mediana_per_aluno_municipal ? "R$ " + fmtNum(row.mediana_per_aluno_municipal) : "—"}</td>
      <td class="num"><span class="razao-chip ${razaoClass}">${razaoLabel}</span></td>
      <td class="num">${row.pct_mat_estadual != null ? row.pct_mat_estadual.toFixed(1) + "%" : "—"}</td>
      <td class="num">${row.media_ideb_iniciais?.toFixed(2) ?? "—"}</td>
    </tr>`;
  }).join("");

  document.getElementById("table-note").textContent =
    `${sorted.length} estado${sorted.length !== 1 ? "s" : ""} · clique em uma linha para ver detalhes`;

  // Row click → load detail
  tbody.querySelectorAll("tr").forEach(tr => {
    tr.addEventListener("click", () => loadDetail(tr.dataset.uf, tr));
  });
}

// ── Detail Panel ─────────────────────────────────────────────────────────────────

async function loadDetail(uf, tr) {
  // Highlight row
  document.querySelectorAll(".estados-table tbody tr").forEach(r => r.classList.remove("row-selected"));
  tr.classList.add("row-selected");

  const panel = document.getElementById("detail-panel");
  panel.style.display = "block";
  panel.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const d = await api.estadoDetalhe(uf);
    fillDetail(d);
  } catch (err) {
    console.error("Erro ao carregar detalhe:", err);
  }
}

function fillDetail(d) {
  document.getElementById("detail-uf").textContent    = d.uf;
  document.getElementById("detail-nome").textContent  = d.nome_estado;
  document.getElementById("detail-regiao").textContent = `${d.regiao} · ${d.total_municipios} municípios`;

  document.getElementById("d-fundeb-est").textContent   = fmtBRL(d.fundeb_estadual_total, true);
  document.getElementById("d-mat-est").textContent      = fmtInt(d.mat_estadual_total);
  document.getElementById("d-per-aluno-est").textContent = d.fundeb_per_aluno_estadual ? "R$ " + fmtNum(d.fundeb_per_aluno_estadual) : "—";
  document.getElementById("d-comp-uniao").textContent   = d.comp_uniao_total ? fmtBRL(d.comp_uniao_total, true) : "—";

  document.getElementById("d-fundeb-mun").textContent   = fmtBRL(d.fundeb_municipal_total, true);
  document.getElementById("d-mat-mun").textContent      = fmtInt(d.mat_municipal_total_uf);
  document.getElementById("d-per-aluno-mun").textContent = d.mediana_per_aluno_municipal ? "R$ " + fmtNum(d.mediana_per_aluno_municipal) : "—";
  document.getElementById("d-n-mun").textContent        = d.total_municipios?.toLocaleString("pt-BR") ?? "—";

  // Distribution bar
  const pctEst  = d.pct_mat_estadual ?? 0;
  const pctMun  = d.mat_publica_total_uf && d.mat_municipal_total_uf
    ? (d.mat_municipal_total_uf / d.mat_publica_total_uf * 100)
    : (100 - pctEst);
  const pctPriv = Math.max(0, 100 - pctEst - pctMun);

  document.getElementById("d-dist-bar").innerHTML = `
    <div class="dist-seg estadual"  style="width:${pctEst.toFixed(1)}%"  title="Estadual ${pctEst.toFixed(1)}%"></div>
    <div class="dist-seg municipal" style="width:${pctMun.toFixed(1)}%"  title="Municipal ${pctMun.toFixed(1)}%"></div>
    <div class="dist-seg privada"   style="width:${pctPriv.toFixed(1)}%" title="Privada ${pctPriv.toFixed(1)}%"></div>
  `;

  document.getElementById("d-pct-est").textContent = d.pct_mat_estadual != null ? d.pct_mat_estadual.toFixed(1) + "%" : "—";
  document.getElementById("d-ideb").textContent    = d.media_ideb_iniciais?.toFixed(2) ?? "—";

  const razao = d.razao_per_aluno;
  const razaoEl = document.getElementById("d-razao");
  if (razao != null) {
    const cls = razao > 1.05 ? "above" : razao < 0.95 ? "below" : "parity";
    const msg = razao > 1.05 ? "estado investe mais" : razao < 0.95 ? "municípios investem mais" : "paridade";
    razaoEl.innerHTML = `<span class="razao-chip ${cls}">${razao.toFixed(3)}</span> <small style="color:var(--color-muted)">${msg}</small>`;
  } else {
    razaoEl.textContent = "—";
  }
}

function closeDetail() {
  document.getElementById("detail-panel").style.display = "none";
  document.querySelectorAll(".estados-table tbody tr").forEach(r => r.classList.remove("row-selected"));
}

// ── Formatters ──────────────────────────────────────────────────────────────────

function fmtNum(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(n);
}

function fmtInt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("pt-BR").format(Math.round(n));
}

function fmtBRL(n, compact = false) {
  if (n == null) return "—";
  if (compact) {
    if (n >= 1e9)  return "R$ " + (n / 1e9).toLocaleString("pt-BR",  { maximumFractionDigits: 1 }) + " bi";
    if (n >= 1e6)  return "R$ " + (n / 1e6).toLocaleString("pt-BR",  { maximumFractionDigits: 1 }) + " mi";
  }
  return "R$ " + new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(n);
}
