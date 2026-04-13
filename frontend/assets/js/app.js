/**
 * app.js — Visão Executiva (index.html)
 * Orchestrates KPI cards, correlation scatter, and ranking tables.
 */

// ── Map state ─────────────────────────────────────────────────────────────────
let _geojson     = null;
let _estadosData = [];

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const [resumo, filtrosData, estadosData] = await Promise.all([
      api.resumo(),
      api.filtros(),
      api.estadosComparativo(),
    ]);

    renderKpis(resumo);
    populateUfFilter(filtrosData.ufs);
    renderMapa(estadosData);   // async, non-blocking
    await renderCorrelacao();
    await renderRankings();

    // Re-render chart and rankings on filter changes
    document.getElementById("filter-uf").addEventListener("change", () => {
      renderCorrelacao();
      renderRankings();
    });
    document.getElementById("filter-etapa").addEventListener("change", renderCorrelacao);
    document.getElementById("filter-outliers").addEventListener("change", renderCorrelacao);
    document.getElementById("map-metric").addEventListener("change", () => {
      if (_estadosData.length && _geojson) {
        drawMapa(_geojson, _estadosData, document.getElementById("map-metric").value);
      }
    });

  } catch (err) {
    console.error("Erro ao carregar dados:", err);
    document.getElementById("kpi-grid").innerHTML = `
      <div class="api-alert">
        <span class="api-alert-icon">⚠️</span>
        <div class="api-alert-body">
          <span class="api-alert-title">Não foi possível conectar à API</span>
          <span class="api-alert-desc">
            Verifique se o servidor está rodando em <code>http://localhost:8001</code>
            ou se a URL de produção está configurada corretamente em <code>api.js</code>.
          </span>
        </div>
      </div>`;
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
      label: "Mediana por aluno (rede municipal)",
      value: new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(d.mediana_per_aluno_municipal),
      sub: `Média: ${new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(d.media_per_aluno_municipal)} · per capita hab.: ${new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(d.media_per_capita)}`,
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
  const maxPc = ocultarOutliers ? 20000 : null;

  const data = await api.correlacao(uf, maxPc);

  const x = data.map((d) => d.fundeb_per_aluno_municipal);
  const y = data.map((d) => d[etapa]);
  const labels = data.map((d) => `${d.nome_municipio} (${d.uf})<br>Por aluno: R$ ${fmtNum(d.fundeb_per_aluno_municipal)}<br>IDEB: ${d[etapa] ?? "—"}<br>Pop.: ${fmtNum(d.populacao)}`);

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
        title: { text: "FUNDEB por aluno — rede municipal (R$)", standoff: 12 },
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
    `${n.toLocaleString("pt-BR")} municípios plotados · correlação de Pearson r = ${corr.toFixed(3)} · ${ocultarOutliers ? "outliers (> R$ 20.000/aluno) ocultados" : "todos os valores incluídos"}`;
}

// ── Ranking tables ─────────────────────────────────────────────────────────────

async function renderRankings() {
  const uf = document.getElementById("filter-uf").value || null;
  const [top, bot] = await Promise.all([
    api.ranking(uf, 10, "desc"),
    api.ranking(uf, 10, "asc"),
  ]);
  renderRankingTable("table-top", top);
  renderRankingTable("table-bot", bot);
  document.getElementById("ranking-subtitle").textContent = uf
    ? `Municípios de ${uf} com maior e menor investimento por aluno`
    : "Municípios com maior e menor investimento por aluno da rede municipal";
}

function renderRankingTable(id, rows) {
  const el = document.getElementById(id);
  el.innerHTML = `
    <thead>
      <tr>
        <th>#</th><th>Município</th><th>UF</th><th>Por aluno (mun.)</th><th>IDEB</th>
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
          <td class="rank-value">R$ ${fmtNum(r.fundeb_per_aluno_municipal)}</td>
          <td>${r.ideb_anos_iniciais_2023 ?? "—"}</td>
        </tr>`
        )
        .join("")}
    </tbody>`;
}

// ── Choropleth map ────────────────────────────────────────────────────────────

const UF_IBGE_CODE = {
  AC:"12", AL:"27", AM:"13", AP:"16", BA:"29", CE:"23", DF:"53", ES:"32",
  GO:"52", MA:"21", MG:"31", MS:"50", MT:"51", PA:"15", PB:"25", PE:"26",
  PI:"22", PR:"41", RJ:"33", RN:"24", RO:"11", RR:"14", RS:"43", SC:"42",
  SE:"28", SP:"35", TO:"17",
};

async function renderMapa(estadosData) {
  _estadosData = estadosData;
  try {
    if (!_geojson) {
      const r = await fetch("assets/geojson/brazil_states.json");
      _geojson = await r.json();
    }
    drawMapa(_geojson, estadosData, document.getElementById("map-metric").value);
  } catch (err) {
    console.warn("Mapa indisponível:", err);
    document.getElementById("chart-mapa").innerHTML =
      '<p style="color:var(--color-muted);text-align:center;padding:3rem 1rem">Mapa não pôde ser carregado.</p>';
  }
}

function drawMapa(geojson, data, metric) {
  const METRIC_LABEL = {
    fundeb_per_aluno_estadual: "R$/aluno estadual",
    razao_per_aluno:           "Razão estadual / municipal",
    media_ideb_iniciais:       "IDEB médio (Anos Iniciais)",
  };
  const METRIC_FMT = {
    fundeb_per_aluno_estadual: v => v != null ? "R$ " + fmtNum(v) : "—",
    razao_per_aluno:           v => v != null ? v.toFixed(3) : "—",
    media_ideb_iniciais:       v => v != null ? v.toFixed(2) : "—",
  };
  const COLORSCALES = {
    fundeb_per_aluno_estadual: [[0,"#2a4a7f"],[0.5,"#1c7ed6"],[1,"#74c0fc"]],
    razao_per_aluno:           [[0,"#da3633"],[0.5,"#d29922"],[1,"#3fb950"]],
    media_ideb_iniciais:       [[0,"#da3633"],[0.5,"#d29922"],[1,"#3fb950"]],
  };

  const valid = data.filter(d => d[metric] != null && UF_IBGE_CODE[d.uf]);
  const locations = valid.map(d => UF_IBGE_CODE[d.uf]);
  const zValues   = valid.map(d => d[metric]);
  const hoverText = valid.map(d =>
    `<b>${d.uf} — ${d.nome_estado}</b><br>` +
    `Região: ${d.regiao}<br>` +
    `R$/aluno estadual: ${METRIC_FMT.fundeb_per_aluno_estadual(d.fundeb_per_aluno_estadual)}<br>` +
    `Mediana municipal: ${METRIC_FMT.fundeb_per_aluno_estadual(d.mediana_per_aluno_municipal)}<br>` +
    `Razão: ${METRIC_FMT.razao_per_aluno(d.razao_per_aluno)}<br>` +
    `IDEB: ${METRIC_FMT.media_ideb_iniciais(d.media_ideb_iniciais)}`
  );

  Plotly.react("chart-mapa", [{
    type:         "choropleth",
    geojson:      geojson,
    locations:    locations,
    z:            zValues,
    featureidkey: "properties.codarea",
    text:         hoverText,
    hovertemplate:"%{text}<extra></extra>",
    colorscale:   COLORSCALES[metric],
    colorbar: {
      title:     { text: METRIC_LABEL[metric], side: "right", font: { color: "#8b949e", size: 11 } },
      thickness: 14,
      len:       0.65,
      tickfont:  { color: "#8b949e", size: 10 },
      bgcolor:   "rgba(0,0,0,0)",
      bordercolor:"rgba(0,0,0,0)",
    },
    marker: { line: { color: "#0d1117", width: 0.8 } },
  }], {
    geo: {
      fitbounds:      "locations",
      visible:        true,
      bgcolor:        "#161b22",
      showland:       false,
      showocean:      false,
      showlakes:      false,
      showrivers:     false,
      showcoastlines: false,
      showframe:      false,
      showsubunits:   false,
      projection:     { type: "mercator" },
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor:  "rgba(0,0,0,0)",
    margin: { t: 0, r: 40, b: 0, l: 0 },
    font:   { color: "#8b949e", family: "Inter, system-ui, sans-serif" },
  }, { responsive: true, displayModeBar: false });

  document.getElementById("map-subtitle").textContent =
    `${METRIC_LABEL[metric]} · ${valid.length} estados · FUNDEB 2026`;
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
