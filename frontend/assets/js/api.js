/**
 * api.js — centralized fetch wrapper for the FastAPI backend.
 */

const API_BASE = "https://fundeb-insights.vercel.app";

async function apiFetch(endpoint, params = {}) {
  const url = new URL(API_BASE + endpoint);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined) url.searchParams.set(k, v);
  });
  const response = await fetch(url);
  if (!response.ok) throw new Error(`API ${response.status}: ${url}`);
  return response.json();
}

const api = {
  resumo:     ()               => apiFetch("/api/resumo"),
  filtros:    ()               => apiFetch("/api/filtros"),
  municipios: (uf, nome, p=1, pp=50) => apiFetch("/api/municipios", { uf, nome, pagina: p, por_pagina: pp }),
  municipio:  (cod)            => apiFetch(`/api/municipios/${cod}`),
  ufs:        ()               => apiFetch("/api/ufs"),
  eficiencia: (uf, etapa, per_capita_max) => apiFetch("/api/eficiencia", { uf, etapa, per_capita_max }),
  ufStats:    (uf)             => uf ? apiFetch(`/api/uf/${uf}`) : Promise.resolve(null),
  ranking:    (uf, limite=10, ordem="desc") => apiFetch("/api/ranking", { uf, limite, ordem }),
  correlacao: (uf, per_capita_max) => apiFetch("/api/correlacao", { uf, per_capita_max }),
};
