/**
 * app.js — Visão Executiva (index.html)
 * Orchestrates KPI cards, correlation scatter, and ranking tables.
 */

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const [resumo, filtrosData] = await Promise.all([
      api.resumo(),
      api.filtros(),
    ]);

    renderKpis(resumo);
    populateUfFilter(filtrosData.ufs);
    await renderCorrelacao();
    await renderRankings();

    // Re-render chart on filter changes
    document.getElementById("filter-uf").addEventListener("change", renderCorrelacao);
    document.getElementById("filter-etapa").addEventListener("change", renderCorrelacao);
    document.getElementById("filter-outliers").addEventListener("change", renderCorrelacao);

  } catch (err) {
    console.error("Erro ao carregar dados:", err);
    document.getElementById("kpi-grid").innerHTML =
      `<p style="color:var(--color-danger);grid-column:1/-1">
        Não foi possível conectar à API. Certifique-se de que o servidor está rodando em
        <code>http://localhost:8000</code>.
      </p>`;
  }
}

// ── KPI Cards ─────────────────────────────────────────────────────────────────

function renderKpis(d) {
  const fmt = (n) => new Intl.NumberFormat("pt-BR").format(n);
  const fmtR = (n) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 }).format(n);

  const cards = [
    {
      label: "Municípios",
      value: fmt(d.total_municipios),
      sub: `${fmt(d.total_municipios_com_ideb)} com IDEB disponível`,
      cls: "",
    },
    {
      label: "Total FUNDEB previsto",
      value: fmtR(d.soma_total_receitas),
      sub: `Ano de referência ${d.ano_fundeb}`,
      cls: "accent",
    },
    {
      label: "Média per capita",
      value: new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(d.media_per_capita),
      sub: `Mediana: ${new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(d.mediana_per_capita)}`,
      cls: "primary",
    },
    {
      label: "IDEB Médio — Anos Iniciais",
      value: d.media_ideb_iniciais.toFixed(1),
      sub: `Escala 0–10 · Rede pública · INEP ${d.ano_ideb}`,
      cls: "warn",
    },
    {
      label: "IDEB Médio — Anos Finais",
      value: d.media_ideb_finais.toFixed(1),
      sub: `Escala 0–10 · Rede pública · INEP ${d.ano_ideb}`,
      cls: "",
    },
  ];

  document.getElementById("kpi-grid").innerHTML = cards
    .map(
      (c) => `
    <div class="kpi-card ${c.cls}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-sub">${c.sub}</div>
    </div>`
    )
    .join("");
}

// ── UF filter ─────────────────────────────────────────────────────────────────

function populateUfFilter(ufs) {
  const sel = document.getElementById("filter-uf");
  ufs.forEach((uf) => {
    const opt = document.createElement("option");
    opt.value = uf;
    opt.textContent = uf;
    sel.appendChild(opt);
  });
}

// ── Scatter chart ─────────────────────────────────────────────────────────────

async function renderCorrelacao() {
  const uf = document.getElementById("filter-uf").value || null;
  const etapa = document.getElementById("filter-etapa").value;
  const ocultarOutliers = document.getElementById("filter-outliers").checked;
  const maxPc = ocultarOutliers ? 5000 : null;

  const data = await api.correlacao(uf, maxPc);

  const x = data.map((d) => d.total_receitas_per_capita);
  const y = data.map((d) => d[etapa]);
  const labels = data.map((d) => `${d.nome_municipio} (${d.uf})<br>Per capita: R$ ${fmtNum(d.total_receitas_per_capita)}<br>IDEB: ${d[etapa] ?? "—"}<br>Pop.: ${fmtNum(d.populacao)}`);

  const etapaLabel = etapa.includes("iniciais") ? "Anos Iniciais" : "Anos Finais";

  Plotly.react(
    "chart-correlacao",
    [
      {
        type: "scatter",
        mode: "markers",
        x,
        y,
        text: labels,
        hovertemplate: "%{text}<extra></extra>",
        marker: {
          size: 6,
          color: y,
          colorscale: [
            [0, "#f85149"],
            [0.5, "#d29922"],
            [1, "#3fb950"],
          ],
          showscale: true,
          colorbar: { title: "IDEB", thickness: 12, len: 0.8 },
          opacity: 0.75,
        },
      },
    ],
    {
      paper_bgcolor: "transparent",
      plot_bgcolor: "#161b22",
      font: { color: "#8b949e", family: "Inter, system-ui, sans-serif", size: 12 },
      xaxis: {
        title: { text: "Receita FUNDEB per capita (R$)", standoff: 12 },
        gridcolor: "#30363d",
        zerolinecolor: "#30363d",
        tickformat: ",.0f",
        tickprefix: "R$ ",
      },
      yaxis: {
        title: { text: `IDEB ${etapaLabel} 2023`, standoff: 12 },
        gridcolor: "#30363d",
        zerolinecolor: "#30363d",
        range: [2, 10.5],
      },
      margin: { t: 20, r: 20, b: 60, l: 60 },
      hovermode: "closest",
    },
    { responsive: true, displayModeBar: false }
  );

  const n = data.filter((d) => d[etapa] !== null).length;
  const corr = pearson(x, y);
  document.getElementById("chart-note").textContent =
    `${n.toLocaleString("pt-BR")} municípios plotados · correlação de Pearson r = ${corr.toFixed(3)} · ${ocultarOutliers ? "outliers (> R$ 5.000) ocultados" : "todos os valores incluídos"}`;
}

// ── Ranking tables ─────────────────────────────────────────────────────────────

async function renderRankings() {
  const [top, bot] = await Promise.all([
    api.ranking(null, 10, "desc"),
    api.ranking(null, 10, "asc"),
  ]);
  renderRankingTable("table-top", top);
  renderRankingTable("table-bot", bot);
}

function renderRankingTable(id, rows) {
  const el = document.getElementById(id);
  el.innerHTML = `
    <thead>
      <tr>
        <th>#</th><th>Município</th><th>UF</th><th>Per capita</th><th>IDEB</th>
      </tr>
    </thead>
    <tbody>
      ${rows
        .map(
          (r) => `
        <tr>
          <td class="rank-pos">${r.posicao}</td>
          <td>${r.nome_municipio}</td>
          <td>${r.uf}</td>
          <td class="rank-value">R$ ${fmtNum(r.total_receitas_per_capita)}</td>
          <td>${r.ideb_anos_iniciais_2023 ?? "—"}</td>
        </tr>`
        )
        .join("")}
    </tbody>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(n);
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
