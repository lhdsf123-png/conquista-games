// Configuração das cidades
const CITY_CONFIGS = {
  tres_coracoes: {
    name: "Três Corações (MG)",
    grid: { cols: 16, rows: 12 },
    startMoney: 3000,
    startPower: 20,
    modifiers: { income: 1.0, powerCost: 1.0, happinessBase: 60 },
    terrain: "vales e café",
  },
  tres_lagoas: {
    name: "Três Lagoas (MS)",
    grid: { cols: 18, rows: 12 },
    startMoney: 3200,
    startPower: 18,
    modifiers: { income: 1.1, powerCost: 1.0, happinessBase: 58 },
    terrain: "lagos e indústria de celulose",
  },
  tres_rios: {
    name: "Três Rios (RJ)",
    grid: { cols: 14, rows: 12 },
    startMoney: 3100,
    startPower: 22,
    modifiers: { income: 0.95, powerCost: 0.9, happinessBase: 62 },
    terrain: "confluência de rios e logística",
  },
};

// Custos e efeitos dos edifícios
const BUILDINGS = {
  house: {
    label: "Casa",
    cost: 100,
    power: -1,
    population: +5,
    income: +2, // impostos por mês
    happiness: +1,
  },
  factory: {
    label: "Fábrica",
    cost: 400,
    power: -4,
    population: +0,
    income: +30,
    happiness: -3,
  },
  power: {
    label: "Usina",
    cost: 600,
    power: +10,
    population: +0,
    income: +0,
    happiness: -1,
  },
  park: {
    label: "Parque",
    cost: 200,
    power: 0,
    population: +0,
    income: +0,
    happiness: +4,
  },
};

const state = {
  currentCityKey: "tres_coracoes",
  cities: {},
  selectedBuild: null,
  bulldozeMode: false,
};

// Inicializa uma cidade
function initCity(key) {
  const cfg = CITY_CONFIGS[key];
  const cells = Array(cfg.grid.rows * cfg.grid.cols).fill(null).map(() => ({ type: "empty" }));
  state.cities[key] = {
    name: cfg.name,
    grid: cfg.grid,
    cells,
    money: cfg.startMoney,
    power: cfg.startPower,
    population: 10,
    happiness: cfg.modifiers.happinessBase,
    month: 1,
    modifiers: cfg.modifiers,
  };
}

// Renderização
function render() {
  const city = state.cities[state.currentCityKey];
  document.getElementById("cityName").textContent = city.name;
  document.getElementById("money").textContent = city.money;
  document.getElementById("power").textContent = city.power;
  document.getElementById("population").textContent = city.population;
  document.getElementById("happiness").textContent = city.happiness;
  document.getElementById("month").textContent = city.month;

  const map = document.getElementById("map");
  map.style.gridTemplateColumns = `repeat(${city.grid.cols}, 36px)`;
  map.style.gridTemplateRows = `repeat(${city.grid.rows}, 36px)`;
  map.innerHTML = "";

  city.cells.forEach((cell, idx) => {
    const div = document.createElement("div");
    div.className = `cell ${cell.type}`;
    div.dataset.idx = idx;
    div.title = tooltipForCell(cell);
    div.textContent = symbolForCell(cell.type);
    div.addEventListener("click", () => onCellClick(idx));
    map.appendChild(div);
  });
}

function symbolForCell(type) {
  switch (type) {
    case "house": return "H";
    case "factory": return "F";
    case "power": return "⚡";
    case "park": return "P";
    default: return "";
  }
}

function tooltipForCell(cell) {
  if (cell.type === "empty") return "Vazio";
  const b = BUILDINGS[cell.type];
  return `${b.label} — Custo: ${b.cost}, Energia: ${b.power}, Pop: ${b.population}, Renda: ${b.income}, Satisfação: ${b.happiness}`;
}

// Interações
function onCellClick(idx) {
  const city = state.cities[state.currentCityKey];
  const cell = city.cells[idx];

  if (state.bulldozeMode) {
    if (cell.type !== "empty") {
      refund(city, cell.type);
      city.cells[idx] = { type: "empty" };
      render();
    }
    return;
  }

  if (!state.selectedBuild) return;
  if (cell.type !== "empty") return;

  const buildType = state.selectedBuild;
  const b = BUILDINGS[buildType];
  if (city.money < b.cost) return;

  // Construir
  city.money -= b.cost;
  city.power += b.power;
  city.population += b.population;
  city.happiness = clamp(city.happiness + b.happiness, 0, 100);
  city.cells[idx] = { type: buildType };
  render();
}

function refund(city, type) {
  const b = BUILDINGS[type];
  const refundRate = 0.5;
  city.money += Math.floor(b.cost * refundRate);
  city.power -= b.power;
  city.population -= b.population;
  city.happiness = clamp(city.happiness - b.happiness, 0, 100);
}

// Economia por “mês”
function tickMonth() {
  const city = state.cities[state.currentCityKey];
  const mod = city.modifiers;

  // Renda de edifícios
  let income = 0;
  city.cells.forEach(c => {
    if (c.type !== "empty") income += BUILDINGS[c.type].income;
  });
  income = Math.floor(income * mod.income);

  // Custo de energia (se negativo, penaliza satisfação e dinheiro)
  let powerDeficit = city.power < 0 ? Math.abs(city.power) : 0;
  let powerCost = Math.floor(powerDeficit * 10 * mod.powerCost);

  // Ajustes de satisfação por déficit
  if (powerDeficit > 0) {
    city.happiness = clamp(city.happiness - Math.min(5, powerDeficit), 0, 100);
  } else {
    city.happiness = clamp(city.happiness + 1, 0, 100);
  }

  // Crescimento populacional baseado em satisfação
  const growth = Math.floor((city.happiness - 50) / 10);
  city.population = Math.max(0, city.population + growth);

  // Aplicar saldo
  city.money += income - powerCost;
  city.month += 1;

  render();
}

// Util
function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

// UI
function bindUI() {
  const select = document.getElementById("citySelect");
  select.addEventListener("change", e => {
    state.currentCityKey = e.target.value;
    ensureCityInitialized(state.currentCityKey);
    render();
  });

  document.querySelectorAll("button[data-build]").forEach(btn => {
    btn.addEventListener("click", () => {
      state.selectedBuild = btn.getAttribute("data-build");
      state.bulldozeMode = false;
      highlightSelected(btn);
    });
  });

  document.getElementById("bulldoze").addEventListener("click", () => {
    state.selectedBuild = null;
    state.bulldozeMode = true;
    clearHighlights();
    document.getElementById("bulldoze").classList.add("active");
  });

  document.getElementById("tick").addEventListener("click", tickMonth);
}

function highlightSelected(activeBtn) {
  clearHighlights();
  activeBtn.classList.add("active");
}
function clearHighlights() {
  document.querySelectorAll(".toolbar button").forEach(b => b.classList.remove("active"));
}

function ensureCityInitialized(key) {
  if (!state.cities[key]) initCity(key);
}

// Boot
window.addEventListener("DOMContentLoaded", () => {
  ensureCityInitialized("tres_coracoes");
  ensureCityInitialized("tres_lagoas");
  ensureCityInitialized("tres_rios");
  bindUI();
  render();
});