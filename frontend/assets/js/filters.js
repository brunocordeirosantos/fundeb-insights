/**
 * filters.js — global filter state (year, region, UF).
 * Other modules read from `filterState` and subscribe via `onFilterChange`.
 */

const filterState = {
  ano: 2021,
  regiao: null,
  uf: null,
};

const filterListeners = [];

function onFilterChange(fn) {
  filterListeners.push(fn);
}

function setFilter(key, value) {
  filterState[key] = value;
  filterListeners.forEach((fn) => fn({ ...filterState }));
}
