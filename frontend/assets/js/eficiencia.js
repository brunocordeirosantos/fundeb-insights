/**
 * eficiencia.js — Eficiência Educacional (eficiencia.html)
 * Scatter com linha de regressão + rankings de resíduo.
 */

let efData = [];

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const filtros = await api.filtros();
    populateUfFilter(filtros.ufs);
    await load();

    document.getElementById("filter-uf").addEventListener("change", load);
    document.getElementById("filter-etapa").addEventListener("change", load);
    document.getElementById("filter-outliers").addEventListener("change", load);

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

async function load() {
  const uf     = document.getElementById("filter-uf").value || null;
  const etapa  = document.getElementById("filter-etapa").value;
  const maxPc  = document.getElementById("filter-outliers").checked ? 20000 : null;

  efData = await api.eficiencia(uf, etapa, maxPc);

  renderKpis(efData, etapa);
  renderScatter(efData, etapa);
  renderTables(efData);
}

// ── KPI Cards ──────────────────────────────────────────────────────────────────

function renderKpis(data, etapa) {
  if (!data.length) return;

  const acima  = data.filter(d => d.residuo > 0).length;
  const abaixo = data.filter(d => d.residuo < 0).length;
  const top    = data[0];
  const bot    = data[data.length - 1];
  const etapaLabel = etapa === "iniciais" ? "Anos Iniciais" : "Anos Finais";

  const cards = [
    {
      label: "Municípios acima da curva",
      value: acima.toLocaleString("pt-BR"),
      sub: `entregam mais do que o esperado — ${pct(acima, data.length)} do total`,
      cls: "accent",
    },
    {
      label: "Municípios abaixo da curva",
      value: abaixo.toLocaleString("pt-BR"),
      sub: `entregam menos do que o esperado — ${pct(abaixo, data.length)} do total`,
      cls: "warn",
    },
    {
      label: `Maior resíduo positivo · ${etapaLabel}`,
      value: top.nome_municipio,
      sub: `${top.uf} · IDEB ${top.ideb_real.toFixed(1)} vs esperado ${top.ideb_esperado.toFixed(1)} (+${top.residuo.toFixed(2)})`,
      cls: "",
    },
    {
      label: `Maior resíduo negativo · ${etapaLabel}`,
      value: bot.nome_municipio,
      sub: `${bot.uf} · IDEB ${bot.ideb_real.toFixed(1)} vs esperado ${bot.ideb_esperado.toFixed(1)} (${bot.residuo.toFixed(2)})`,
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

// ── Scatter + linha de regressão ───────────────────────────────────────────────

function renderScatter(data, etapa) {
  if (!data.length) return;

  const etapaLabel = etapa === "iniciais" ? "Anos Iniciais" : "Anos Finais";

  // Scatter colorido pelo resíduo
  const scatter = {
    type: "scatter",
    mode: "markers",
    name: "Municípios",
    x: data.map(d => d.fundeb_per_aluno_municipal),
    y: data.map(d => d.ideb_real),
    text: data.map(d =>
      `<b>${d.nome_municipio} (${d.uf})</b><br>` +
      `Por aluno: R$ ${fmtNum(d.fundeb_per_aluno_municipal)}<br>` +
      `IDEB real: ${d.ideb_real.toFixed(2)}<br>` +
      `IDEB esperado: ${d.ideb_esperado.toFixed(2)}<br>` +
      `Resíduo: ${d.residuo >= 0 ? "+" : ""}${d.residuo.toFixed(2)}`
    ),
    hovertemplate: "%{text}<extra></extra>",
    marker: {
      size: 6,
      color: data.map(d => d.residuo),
      colorscale: [[0, "#f85149"], [0.5, "#d29922"], [1, "#3fb950"]],
      showscale: true,
      colorbar: {
        title: "Resíduo", thickness: 12, len: 0.75,
        tickfont: { color: "#8b949e" }, titlefont: { color: "#8b949e" },
      },
      opacity: 0.75,
      cmin: -Math.max(...data.map(d => Math.abs(d.residuo))),
      cmax:  Math.max(...data.map(d => Math.abs(d.residuo))),
    },
  };

  // Linha de regressão
  const xSorted = [...data.map(d => d.fundeb_per_aluno_municipal)].sort((a, b) => a - b);
  const xMin = xSorted[0];
  const xMax = xSorted[xSorted.length - 1];

  // Recalcular a e b no frontend para desenhar a linha
  const xs = data.map(d => d.fundeb_per_aluno_municipal);
  const ys = data.map(d => d.ideb_esperado);
  const regLine = {
    type: "scatter",
    mode: "lines",
    name: "Tendência esperada",
    x: [xMin, xMax],
    y: [ys[xs.indexOf(xMin)] ?? linearAt(data, xMin), linearAt(data, xMax)],
    line: { color: "#58a6ff", width: 2, dash: "dash" },
    hovertemplate: "Tendência esperada<extra></extra>",
  };

  Plotly.react(
    "chart-scatter",
    [scatter, regLine],
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
      showlegend: true,
      legend: { x: 1, xanchor: "right", y: 1, bgcolor: "transparent", font: { color: "#8b949e", size: 11 } },
    }),
    { responsive: true, displayModeBar: false }
  );

  const acima = data.filter(d => d.residuo > 0).length;
  document.getElementById("scatter-note").textContent =
    `${data.length.toLocaleString("pt-BR")} municípios · ${acima.toLocaleString("pt-BR")} acima da linha de tendência (${pct(acima, data.length)})`;
}

// ── Tabelas de ranking ─────────────────────────────────────────────────────────

function renderTables(data) {
  const top10 = data.slice(0, 10);
  const bot10 = [...data].reverse().slice(0, 10);

  fillTable("table-efficient",   top10, 1);
  fillTable("table-inefficient", bot10, 1);
}

function fillTable(id, rows, startPos) {
  const tbody = document.querySelector(`#${id} tbody`);
  tbody.innerHTML = rows.map((r, i) => `
    <tr>
      <td class="rank-pos">${i + startPos}</td>
      <td><a href="municipio.html?cod=${r.cod_municipio}">${r.nome_municipio}</a></td>
      <td>${r.uf}</td>
      <td>R$ ${fmtNum(r.fundeb_per_aluno_municipal)}</td>
      <td>${r.ideb_real.toFixed(2)}</td>
      <td class="ideb-expected">${r.ideb_esperado.toFixed(2)}</td>
      <td class="${r.residuo >= 0 ? "residuo-pos" : "residuo-neg"}">
        ${r.residuo >= 0 ? "+" : ""}${r.residuo.toFixed(2)}
      </td>
    </tr>`).join("");
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

function pct(part, total) {
  return total ? `${((part / total) * 100).toFixed(0)}%` : "—";
}

// Estima ideb_esperado em x usando os dois pontos extremos da série
function linearAt(data, x) {
  if (!data.length) return 0;
  const sorted = [...data].sort((a, b) => a.fundeb_per_aluno_municipal - b.fundeb_per_aluno_municipal);
  const p1 = sorted[0];
  const p2 = sorted[sorted.length - 1];
  if (p1.fundeb_per_aluno_municipal === p2.fundeb_per_aluno_municipal) return p1.ideb_esperado;
  const t = (x - p1.fundeb_per_aluno_municipal) / (p2.fundeb_per_aluno_municipal - p1.fundeb_per_aluno_municipal);
  return p1.ideb_esperado + t * (p2.ideb_esperado - p1.ideb_esperado);
}
