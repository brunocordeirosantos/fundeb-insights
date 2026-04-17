/**
 * desempenho.js — Investimento vs Desempenho (desempenho.html)
 * Scatter FUNDEB × IDEB + IDEB por estado.
 */

let correlacaoData = [];
let ufsData = [];

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const [filtros, resumo, ufs] = await Promise.all([
      api.filtros(),
      api.resumo(),
      api.ufs(),
    ]);

    ufsData = ufs;

    renderKpis(resumo);
    populateUfFilter(filtros.ufs);
    await renderScatter();
    renderIdebUfs();

    document.getElementById("filter-uf").addEventListener("change", renderScatter);
    document.getElementById("filter-etapa").addEventListener("change", renderScatter);
    document.getElementById("filter-outliers").addEventListener("change", renderScatter);
    document.getElementById("filter-etapa-ufs").addEventListener("change", renderIdebUfs);
    document.getElementById("filter-ordem-ufs").addEventListener("change", renderIdebUfs);

  } catch (err) {
    console.error("Erro ao inicializar:", err);
    document.getElementById("kpi-grid").innerHTML = `
      <div class="api-alert">
        <span class="api-alert-icon">⚠️</span>
        <div class="api-alert-body">
          <span class="api-alert-title">Não foi possível conectar à API</span>
          <span class="api-alert-desc">
            Verifique se o servidor está rodando em <code>http://localhost:8001</code>.
          </span>
        </div>
      </div>`;
  }
}

// ── KPI Cards ──────────────────────────────────────────────────────────────────

function renderKpis(d) {
  const cards = [
    {
      label: "IDEB Médio — Anos Iniciais",
      value: d.media_ideb_iniciais.toFixed(2),
      sub: `Escala 0–10 · Rede pública · INEP ${d.ano_ideb}`,
      cls: "accent",
    },
    {
      label: "IDEB Médio — Anos Finais",
      value: d.media_ideb_finais.toFixed(2),
      sub: `Escala 0–10 · Rede pública · INEP ${d.ano_ideb}`,
      cls: "primary",
    },
    {
      label: "Municípios com IDEB",
      value: d.total_municipios_com_ideb.toLocaleString("pt-BR"),
      sub: `de ${d.total_municipios.toLocaleString("pt-BR")} municípios na base`,
      cls: "",
    },
    {
      label: "Correlação FUNDEB × IDEB",
      value: "r = —",
      sub: "calculado ao carregar o scatter",
      cls: "warn",
      id: "kpi-correlation",
    },
  ];

  document.getElementById("kpi-grid").innerHTML = cards
    .map(c => `
      <div class="kpi-card ${c.cls}"${c.id ? ` id="${c.id}"` : ""}>
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value kpi-corr-value">${c.value}</div>
        <div class="kpi-sub kpi-corr-sub">${c.sub}</div>
      </div>`)
    .join("");
}

// ── Scatter ────────────────────────────────────────────────────────────────────

async function renderScatter() {
  const uf = document.getElementById("filter-uf").value || null;
  const etapa = document.getElementById("filter-etapa").value;
  const ocultarOutliers = document.getElementById("filter-outliers").checked;
  const maxPc = ocultarOutliers ? 20000 : null;

  correlacaoData = await api.correlacao(uf, maxPc);

  const validos = correlacaoData.filter(d => d[etapa] !== null && d[etapa] !== undefined);
  const x = validos.map(d => d.fundeb_per_aluno_municipal);
  const y = validos.map(d => d[etapa]);
  const labels = validos.map(d =>
    `${d.nome_municipio} (${d.uf})<br>Por aluno: R$ ${fmtNum(d.fundeb_per_aluno_municipal)}<br>IDEB: ${d[etapa]}<br>Pop.: ${fmtNum(d.populacao)}`
  );

  const etapaLabel = etapa.includes("iniciais") ? "Anos Iniciais" : "Anos Finais";
  const r = pearson(x, y);

  // Update callout + correlation KPI card
  document.getElementById("insight-r").textContent = `r = ${r.toFixed(2)}`;
  const corrCard = document.getElementById("kpi-correlation");
  if (corrCard) {
    corrCard.querySelector(".kpi-corr-value").textContent = `r = ${r.toFixed(2)}`;
    const etapaLabel = etapa.includes("iniciais") ? "Anos Iniciais" : "Anos Finais";
    corrCard.querySelector(".kpi-corr-sub").textContent =
      `${etapaLabel} · ${ocultarOutliers ? "outliers > R$ 20.000/aluno ocultados" : "todos os valores"}`;
  }

  Plotly.react(
    "chart-scatter",
    [{
      type: "scatter",
      mode: "markers",
      x,
      y,
      text: labels,
      hovertemplate: "%{text}<extra></extra>",
      marker: {
        size: 6,
        color: y,
        colorscale: [[0, "#f85149"], [0.5, "#d29922"], [1, "#3fb950"]],
        showscale: true,
        colorbar: { title: "IDEB", thickness: 12, len: 0.75, tickfont: { color: "#8b949e" }, titlefont: { color: "#8b949e" } },
        opacity: 0.7,
      },
    }],
    mobileLayout({
      paper_bgcolor: "transparent",
      plot_bgcolor: "#161b22",
      font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
      xaxis: {
        title: { text: "FUNDEB por aluno — rede municipal (R$)", standoff: 12 },
        gridcolor: "#30363d", zerolinecolor: "#30363d",
        tickformat: ",.0f", tickprefix: "R$ ",
      },
      yaxis: {
        title: { text: `IDEB ${etapaLabel} 2023`, standoff: 12 },
        gridcolor: "#30363d", zerolinecolor: "#30363d",
        range: [2, 10.5],
      },
      margin: { t: 20, r: 20, b: 60, l: 60 },
      hovermode: "closest",
    }),
    { responsive: true, displayModeBar: false }
  );

  document.getElementById("scatter-note").textContent =
    `${validos.length.toLocaleString("pt-BR")} municípios · correlação de Pearson r = ${r.toFixed(3)} · ` +
    (ocultarOutliers ? "outliers (> R$ 20.000/aluno) ocultados" : "todos os valores incluídos");
}

// ── IDEB por UF ────────────────────────────────────────────────────────────────

function renderIdebUfs() {
  const etapa = document.getElementById("filter-etapa-ufs").value;
  const ordem = document.getElementById("filter-ordem-ufs").value;

  const filtered = ufsData
    .filter(u => u[etapa] !== null)
    .sort((a, b) => ordem === "desc" ? b[etapa] - a[etapa] : a[etapa] - b[etapa]);

  const labels = filtered.map(u => u.uf);
  const values = filtered.map(u => u[etapa]);

  // Color: green above national avg, red below
  const avg = values.reduce((s, v) => s + v, 0) / values.length;
  const colors = values.map(v => v >= avg ? "#3fb950" : "#f85149");

  const etapaLabel = etapa.includes("iniciais") ? "Anos Iniciais" : "Anos Finais";

  Plotly.react(
    "chart-ideb-ufs",
    [{
      type: "bar",
      orientation: "h",
      x: values,
      y: labels,
      text: values.map(v => v.toFixed(2)),
      textposition: "outside",
      hovertemplate: "<b>%{y}</b><br>IDEB: %{x:.2f}<extra></extra>",
      marker: { color: colors },
    },
    // Linha da média nacional
    {
      type: "scatter",
      mode: "lines",
      x: [avg, avg],
      y: [labels[0], labels[labels.length - 1]],
      line: { color: "#d29922", width: 1.5, dash: "dot" },
      hovertemplate: `Média nacional: ${avg.toFixed(2)}<extra></extra>`,
      name: `Média: ${avg.toFixed(2)}`,
    }],
    mobileLayout({
      paper_bgcolor: "transparent",
      plot_bgcolor: "#161b22",
      font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
      xaxis: {
        title: { text: `IDEB ${etapaLabel} — média dos municípios`, standoff: 10 },
        gridcolor: "#30363d", zerolinecolor: "#30363d",
        range: [0, 10],
      },
      yaxis: { gridcolor: "#30363d", automargin: true },
      margin: { t: 10, r: 80, b: 60, l: 50 },
      hovermode: "closest",
      showlegend: true,
      legend: { x: 1, xanchor: "right", y: 0, bgcolor: "transparent", font: { color: "#8b949e", size: 11 } },
    }),
    { responsive: true, displayModeBar: false }
  );
}

// ── UF filter ──────────────────────────────────────────────────────────────────

function populateUfFilter(ufs) {
  const sel = document.getElementById("filter-uf");
  ufs.forEach(uf => {
    const opt = document.createElement("option");
    opt.value = uf;
    opt.textContent = uf;
    sel.appendChild(opt);
  });
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(n);
}

function pearson(xs, ys) {
  const pairs = xs.map((x, i) => [x, ys[i]]).filter(([, y]) => y !== null && y !== undefined);
  const n = pairs.length;
  if (n < 2) return 0;
  const mx = pairs.reduce((s, [x]) => s + x, 0) / n;
  const my = pairs.reduce((s, [, y]) => s + y, 0) / n;
  const num = pairs.reduce((s, [x, y]) => s + (x - mx) * (y - my), 0);
  const den = Math.sqrt(
    pairs.reduce((s, [x]) => s + (x - mx) ** 2, 0) *
    pairs.reduce((s, [, y]) => s + (y - my) ** 2, 0)
  );
  return den === 0 ? 0 : num / den;
}
