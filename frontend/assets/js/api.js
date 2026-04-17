/**
 * api.js — centralized fetch wrapper for the FastAPI backend.
 */

const API_BASE = "https://fundeb-insights.onrender.com";

// Shows a warm-up banner if the first request takes more than 3s (Render cold start)
let _warmupTimer = null;
let _warmupBannerShown = false;

function showWarmupBanner() {
  if (_warmupBannerShown) return;
  _warmupBannerShown = true;
  const banner = document.createElement("div");
  banner.id = "warmup-banner";
  banner.style.cssText = [
    "position:fixed", "bottom:20px", "left:50%", "transform:translateX(-50%)",
    "background:#161b22", "border:1px solid #30363d", "border-left:3px solid #58a6ff",
    "border-radius:10px", "padding:12px 20px", "font-size:0.82rem",
    "color:#8b949e", "z-index:9999", "white-space:nowrap",
    "box-shadow:0 4px 20px rgba(0,0,0,0.4)",
  ].join(";");
  banner.textContent = "⚡ API iniciando no servidor... aguarde alguns instantes";
  document.body.appendChild(banner);
}

function hideWarmupBanner() {
  clearTimeout(_warmupTimer);
  const banner = document.getElementById("warmup-banner");
  if (banner) banner.remove();
}

async function apiFetch(endpoint, params = {}) {
  const url = new URL(API_BASE + endpoint);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined) url.searchParams.set(k, v);
  });

  _warmupTimer = setTimeout(showWarmupBanner, 3000);

  try {
    const response = await fetch(url);
    hideWarmupBanner();
    if (!response.ok) throw new Error(`API ${response.status}: ${url}`);
    return response.json();
  } catch (err) {
    hideWarmupBanner();
    throw err;
  }
}

const api = {
  // Municípios
  resumo:     ()               => apiFetch("/api/resumo"),
  filtros:    ()               => apiFetch("/api/filtros"),
  municipios: (uf, nome, p=1, pp=50) => apiFetch("/api/municipios", { uf, nome, pagina: p, por_pagina: pp }),
  municipio:  (cod)            => apiFetch(`/api/municipios/${cod}`),
  ufs:        ()               => apiFetch("/api/ufs"),
  eficiencia: (uf, etapa, per_capita_max) => apiFetch("/api/eficiencia", { uf, etapa, per_capita_max }),
  ufStats:    (uf)             => uf ? apiFetch(`/api/uf/${uf}`) : Promise.resolve(null),
  ranking:    (uf, limite=10, ordem="desc") => apiFetch("/api/ranking", { uf, limite, ordem }),
  correlacao: (uf, per_capita_max) => apiFetch("/api/correlacao", { uf, per_capita_max }),
  // Estados
  estadosResumo:      ()           => apiFetch("/api/estados/resumo"),
  estadosLista:       (regiao)     => apiFetch("/api/estados", { regiao }),
  estadosRanking:     (metrica, ordem, regiao) => apiFetch("/api/estados/ranking", { metrica, ordem, regiao }),
  estadosComparativo: ()           => apiFetch("/api/estados/comparativo"),
  estadoDetalhe:      (uf)         => apiFetch(`/api/estados/${uf}`),
};
