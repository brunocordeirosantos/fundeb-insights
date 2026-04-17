/**
 * distribuicao.js — Distribuição de Recursos (distribuicao.html)
 * Renders UF bar chart and filterable municipal ranking table.
 */

let ufsData = [];

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const [ufs, filtros, resumo] = await Promise.all([
      api.ufs(),
      api.filtros(),
      api.resumo(),
    ]);

    ufsData = ufs;

    renderKpis(resumo, ufs);
    renderInsight(ufs);
    populateUfFilter(filtros.ufs);
    renderChartUfs();
    await renderRanking();

    document.getElementById("filter-metrica").addEventListener("change", renderChartUfs);
    document.getElementById("filter-ordem").addEventListener("change", renderChartUfs);
    document.getElementById("rank-uf").addEventListener("change", renderRanking);
    document.getElementById("rank-ordem").addEventListener("change", renderRanking);
    document.getElementById("rank-limite").addEventListener("change", renderRanking);

  } catch (err) {
    console.error("Erro ao inicializar página:", err);
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

function renderKpis(resumo, ufs) {
  const fmtR = (n) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 }).format(n);
  const fmtPC = (n) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n);

  const ufMax = ufs.filter(u => u.media_per_aluno_municipal).reduce((a, b) => (b.media_per_aluno_municipal > (a.media_per_aluno_municipal ?? 0) ? b : a), ufs[0]);
  const ufMin = ufs.filter(u => u.media_per_aluno_municipal).reduce((a, b) => (b.media_per_aluno_municipal < a.media_per_aluno_municipal ? b : a));

  const cards = [
    {
      label: "Total FUNDEB previsto",
      value: fmtR(resumo.soma_total_receitas),
      sub: `Referência ${resumo.ano_fundeb}`,
      cls: "accent",
    },
    {
      label: "Mediana por aluno (rede municipal)",
      value: fmtPC(resumo.mediana_per_aluno_municipal),
      sub: `Média: ${fmtPC(resumo.media_per_aluno_municipal)} · per capita hab.: ${fmtPC(resumo.media_per_capita)}`,
      cls: "primary",
    },
    {
      label: "Estado com maior média por aluno",
      value: ufMax.uf,
      sub: `${fmtPC(ufMax.media_per_aluno_municipal)} por aluno (rede municipal)`,
      cls: "warn",
    },
    {
      label: "Estado com menor média por aluno",
      value: ufMin.uf,
      sub: `${fmtPC(ufMin.media_per_aluno_municipal)} por aluno (rede municipal)`,
      cls: "",
    },
  ];

  document.getElementById("kpi-grid").innerHTML = cards
    .map(c => `
      <div class="kpi-card ${c.cls}">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value">${c.value}</div>
        <div class="kpi-sub">${c.sub}</div>
      </div>`)
    .join("");
}

// ── Insight callout ────────────────────────────────────────────────────────────

function renderInsight(ufs) {
  const withData = ufs.filter(u => u.media_per_aluno_municipal);
  if (!withData.length) return;

  const maxUf = withData.reduce((a, b) => b.media_per_aluno_municipal > a.media_per_aluno_municipal ? b : a);
  const minUf = withData.reduce((a, b) => b.media_per_aluno_municipal < a.media_per_aluno_municipal ? b : a);
  const ratio = maxUf.media_per_aluno_municipal / minUf.media_per_aluno_municipal;

  document.getElementById("insight-ratio").textContent = `${ratio.toFixed(0)}×`;
  document.getElementById("insight-body").innerHTML =
    `A média de investimento por aluno da rede municipal varia de
    <strong>${fmtCurrency(minUf.media_per_aluno_municipal)}</strong> (${minUf.uf}) a
    <strong>${fmtCurrency(maxUf.media_per_aluno_municipal)}</strong> (${maxUf.uf}) entre os estados.
    Essa diferença reflete fatores estruturais: estados com redes menores e menos matrículas recebem
    proporcionalmente mais do VAAF — o componente redistributivo do FUNDEB —
    resultando em médias por aluno mais altas, mesmo com totais de transferência menores.`;
}

// ── Bar chart por UF ───────────────────────────────────────────────────────────

function renderChartUfs() {
  const metrica = document.getElementById("filter-metrica").value;
  const ordem = document.getElementById("filter-ordem").value;

  const filtered = ufsData
    .filter(u => u[metrica] !== null)
    .sort((a, b) => ordem === "desc" ? b[metrica] - a[metrica] : a[metrica] - b[metrica]);

  const labels = filtered.map(u => u.uf);
  const values = filtered.map(u => u[metrica]);

  const isMonetary = metrica !== "total_municipios";
  const tickPrefix = isMonetary ? "R$ " : "";

  const metricaLabels = {
    media_per_aluno_municipal: "Média por aluno — rede municipal (R$)",
    mediana_per_aluno_municipal: "Mediana por aluno — rede municipal (R$)",
    soma_receitas: "Total FUNDEB (R$)",
    media_per_capita: "Média per capita — população (R$)",
    mediana_per_capita: "Mediana per capita — população (R$)",
  };

  // Color gradient: green (high) → yellow → red (low)
  const normalized = values.map(v => {
    const min = Math.min(...values);
    const max = Math.max(...values);
    return max === min ? 0.5 : (v - min) / (max - min);
  });

  const colors = normalized.map(n => {
    if (n >= 0.6) return "#3fb950";
    if (n >= 0.35) return "#d29922";
    return "#f85149";
  });

  const hoverText = filtered.map(u => {
    const pc = u.media_per_capita !== null
      ? `Média: ${fmtCurrency(u.media_per_capita)}<br>Mediana: ${fmtCurrency(u.mediana_per_capita)}`
      : "Sem dados";
    return `<b>${u.uf}</b><br>${pc}<br>Total: ${fmtCompact(u.soma_receitas)}<br>Municípios: ${u.total_municipios}`;
  });

  Plotly.react(
    "chart-ufs",
    [{
      type: "bar",
      orientation: "h",
      x: values,
      y: labels,
      text: values.map(v => isMonetary ? fmtCurrency(v) : v),
      textposition: "outside",
      hovertemplate: "%{customdata}<extra></extra>",
      customdata: hoverText,
      marker: { color: colors },
    }],
    mobileLayout({
      paper_bgcolor: "transparent",
      plot_bgcolor: "#161b22",
      font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
      xaxis: {
        title: { text: metricaLabels[metrica], standoff: 10 },
        gridcolor: "#30363d",
        zerolinecolor: "#30363d",
        tickprefix: tickPrefix,
        tickformat: metrica === "soma_receitas" ? ".2s" : ",.0f",
      },
      yaxis: { gridcolor: "#30363d", automargin: true },
      margin: { t: 10, r: 100, b: 60, l: 50 },
      hovermode: "closest",
    }),
    { responsive: true, displayModeBar: false }
  );

  document.getElementById("chart-ufs-note").textContent =
    `${filtered.length} estados · ${metricaLabels[metrica]} · ordenado ${ordem === "desc" ? "do maior para o menor" : "do menor para o maior"}`;
}

// ── Ranking table ──────────────────────────────────────────────────────────────

async function renderRanking() {
  const uf    = document.getElementById("rank-uf").value || null;
  const ordem = document.getElementById("rank-ordem").value;
  const limite = parseInt(document.getElementById("rank-limite").value, 10);
  const tbody = document.getElementById("ranking-body");

  tbody.innerHTML = `<tr><td colspan="7" class="table-loading">Carregando...</td></tr>`;
  document.getElementById("ranking-error").style.display = "none";

  try {
    const rows = await api.ranking(uf, limite, ordem);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td class="rank-pos">${r.posicao}</td>
        <td><a href="municipio.html?cod=${r.cod_municipio}">${r.nome_municipio}</a></td>
        <td>${r.uf}</td>
        <td>${r.populacao ? fmtNum(r.populacao) : "—"}</td>
        <td>${fmtCurrency(r.total_receitas)}</td>
        <td class="rank-value">${r.fundeb_per_aluno_municipal ? fmtCurrency(r.fundeb_per_aluno_municipal) : "—"}</td>
        <td>${r.ideb_anos_iniciais_2023 ?? "—"}</td>
      </tr>`).join("");
  } catch (err) {
    tbody.innerHTML = "";
    document.getElementById("ranking-error").style.display = "flex";
  }
}

// ── UF filter ──────────────────────────────────────────────────────────────────

function populateUfFilter(ufs) {
  const sel = document.getElementById("rank-uf");
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

function fmtCurrency(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(n);
}

function fmtCompact(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 }).format(n);
}
