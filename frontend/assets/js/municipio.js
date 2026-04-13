/**
 * municipio.js — Exploração Municipal
 * Handles search autocomplete, municipality card rendering, and comparison bars.
 */

// National averages loaded once from /api/resumo
let nationalAvg = { per_aluno: 0, ideb_iniciais: 0, ideb_finais: 0 };

document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const [resumo, filtros] = await Promise.all([api.resumo(), api.filtros()]);

    nationalAvg = {
      per_aluno: resumo.media_per_aluno_municipal,
      ideb_iniciais: resumo.media_ideb_iniciais,
      ideb_finais: resumo.media_ideb_finais,
    };

    populateUfFilter(filtros.ufs);
    setupSearch();

    // Load from URL param if present (?cod=3550308)
    const params = new URLSearchParams(window.location.search);
    if (params.get("cod")) loadMunicipio(params.get("cod"));

  } catch (err) {
    console.error("Erro ao inicializar:", err);
  }
}

// ── UF Filter ─────────────────────────────────────────────────────────────────

function populateUfFilter(ufs) {
  const sel = document.getElementById("filter-uf");
  ufs.forEach((uf) => {
    const opt = document.createElement("option");
    opt.value = uf;
    opt.textContent = uf;
    sel.appendChild(opt);
  });
}

// ── Search & Autocomplete ──────────────────────────────────────────────────────

function setupSearch() {
  const input = document.getElementById("search-input");
  const list  = document.getElementById("autocomplete-list");
  const ufSel = document.getElementById("filter-uf");

  let debounceTimer;

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (q.length < 2) { hideList(); return; }
    debounceTimer = setTimeout(() => fetchSuggestions(q, ufSel.value), 280);
  });

  ufSel.addEventListener("change", () => {
    const q = input.value.trim();
    if (q.length >= 2) fetchSuggestions(q, ufSel.value);
  });

  // Close list when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-input-wrap")) hideList();
  });

  input.addEventListener("keydown", (e) => {
    const items = list.querySelectorAll(".autocomplete-item");
    const active = list.querySelector(".autocomplete-item.focused");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = active ? active.nextElementSibling : items[0];
      if (next) { active?.classList.remove("focused"); next.classList.add("focused"); next.scrollIntoView({ block: "nearest" }); }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = active?.previousElementSibling;
      if (prev) { active.classList.remove("focused"); prev.classList.add("focused"); prev.scrollIntoView({ block: "nearest" }); }
    } else if (e.key === "Enter" && active) {
      e.preventDefault();
      active.click();
    } else if (e.key === "Escape") {
      hideList();
    }
  });
}

async function fetchSuggestions(nome, uf) {
  const res = await api.municipios(uf || null, nome, 1, 8);
  renderSuggestions(res.data);
}

function renderSuggestions(items) {
  const list = document.getElementById("autocomplete-list");

  if (!items.length) { hideList(); return; }

  list.innerHTML = items.map((m) => `
    <div class="autocomplete-item" data-cod="${m.cod_municipio}">
      <div>
        <span class="ac-name">${m.nome_municipio}</span>
        <span class="ac-uf">${m.uf}</span>
      </div>
      <span class="ac-pc">R$ ${fmtNum(m.fundeb_per_aluno_municipal)} / aluno</span>
    </div>`
  ).join("");

  list.querySelectorAll(".autocomplete-item").forEach((el) => {
    el.addEventListener("click", () => {
      document.getElementById("search-input").value = el.querySelector(".ac-name").textContent;
      hideList();
      loadMunicipio(el.dataset.cod);
    });
  });

  list.classList.remove("hidden");
}

function hideList() {
  document.getElementById("autocomplete-list").classList.add("hidden");
}

// ── Load & render municipality ────────────────────────────────────────────────

async function loadMunicipio(cod) {
  history.replaceState(null, "", `?cod=${cod}`);

  const muni = await api.municipio(cod);
  const ufData = await api.ufStats(muni.uf);

  renderCard(muni, ufData);
}

function renderCard(m, uf) {
  // Show card, hide empty state
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("municipio-card").classList.remove("hidden");

  // Header
  document.getElementById("muni-uf").textContent   = m.uf;
  document.getElementById("muni-name").textContent  = m.nome_municipio;
  document.getElementById("muni-cod").textContent   = `Código IBGE: ${m.cod_municipio} · FUNDEB ${m.ano}`;
  document.getElementById("muni-pop").textContent   = m.populacao ? fmtNum(m.populacao) + " hab." : "Não disponível";

  // Financial
  document.getElementById("fin-total").textContent        = fmtBRL(m.total_receitas);
  document.getElementById("fin-per-capita").textContent   = m.fundeb_per_aluno_municipal ? fmtBRL(m.fundeb_per_aluno_municipal) + " / aluno" : "—";
  document.getElementById("fin-contribuicao").textContent = fmtBRL(m.receita_contribuicao);
  document.getElementById("fin-vaaf").textContent         = m.comp_vaaf  ? fmtBRL(m.comp_vaaf)  : "—";
  document.getElementById("fin-vaat").textContent         = m.comp_vaat  ? fmtBRL(m.comp_vaat)  : "—";
  document.getElementById("fin-vaar").textContent         = m.comp_vaar  ? fmtBRL(m.comp_vaar)  : "—";
  document.getElementById("fin-uniao").textContent        = m.comp_uniao_total ? fmtBRL(m.comp_uniao_total) : "—";

  // Per aluno comparison bars
  renderComparisons("pc-comparisons", m.fundeb_per_aluno_municipal, [
    { label: `Mediana ${m.uf}`, value: uf?.mediana_per_aluno_municipal },
    { label: "Mediana nacional", value: nationalAvg.per_aluno },
  ], 0, Math.max(nationalAvg.per_aluno * 3, (m.fundeb_per_aluno_municipal ?? 0) * 1.2));

  // IDEB scores
  renderIdebCard("ideb-iniciais-card", "ideb-iniciais", m.ideb_anos_iniciais_2023, nationalAvg.ideb_iniciais);
  renderIdebCard("ideb-finais-card",   "ideb-finais",   m.ideb_anos_finais_2023,   nationalAvg.ideb_finais);

  // IDEB comparison bars
  renderComparisons("ideb-comparisons", m.ideb_anos_iniciais_2023, [
    { label: `Média ${m.uf}`, value: uf?.media_ideb_iniciais },
    { label: "Média nacional", value: nationalAvg.ideb_iniciais },
  ], 0, 10);

  renderComparisons("ideb-finais-comparisons", m.ideb_anos_finais_2023, [
    { label: `Média ${m.uf}`, value: uf?.media_ideb_finais },
    { label: "Média nacional", value: nationalAvg.ideb_finais },
  ], 0, 10);

  // Scroll to card
  document.getElementById("municipio-card").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderIdebCard(cardId, scoreId, value, avg) {
  const card  = document.getElementById(cardId);
  const score = document.getElementById(scoreId);

  card.classList.remove("above-avg", "below-avg", "no-data");

  if (value === null || value === undefined) {
    score.textContent = "—";
    card.classList.add("no-data");
    return;
  }

  score.textContent = value.toFixed(1);
  card.classList.add(value >= avg ? "above-avg" : "below-avg");
}

function renderComparisons(containerId, muniValue, benchmarks, min, max) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const range = max - min || 1;
  const muniPct = muniValue != null ? Math.min(100, ((muniValue - min) / range) * 100) : null;

  const benchmarkHtml = benchmarks
    .filter((b) => b.value != null)
    .map((b) => {
      const bPct = Math.min(100, ((b.value - min) / range) * 100);
      const isAbove = muniValue != null && muniValue >= b.value;
      const fillClass = muniValue == null ? "bar-fill--muni" : isAbove ? "bar-fill--above" : "bar-fill--below";

      return `
        <div class="comparison-item">
          <div class="comparison-item-header">
            <span class="ci-label">${b.label}</span>
            <span class="ci-value">${typeof b.value === "number" && b.value > 100 ? fmtBRL(b.value) : b.value?.toFixed(1)}</span>
          </div>
          <div class="bar-track">
            ${muniPct != null ? `<div class="bar-fill ${fillClass}" style="width:${muniPct}%"></div>` : ""}
            <div class="bar-marker" style="left:${bPct}%"></div>
            <div class="bar-marker-label" style="left:${bPct}%">${b.label.split(" ")[1] || b.label}</div>
          </div>
        </div>`;
    })
    .join("");

  container.innerHTML = benchmarkHtml || `<p class="metric-label">Comparação não disponível.</p>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtBRL(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);
}

function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(n);
}
