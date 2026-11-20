/**
 * Smart Storage EMS - Dedicated High-Performance Interactive MPC Chart Card
 * State-of-the-Art Dual-Axis 48h Optimization Horizon Canvas Renderer
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

const CHART_I18N = {
  pl: {
    defaultTitle: 'Smart Storage EMS: Plan Optymalizacji MPC (48h)',
    kpiCharge: '⚡ Zaplanowane Ładowanie',
    kpiDischarge: '🔋 Zaplanowane Rozładowanie',
    kpiSolar: '☀️ Prognoza PV (Suma)',
    kpiMinSoc: '🛡️ Dynamiczny Min SoC',
    filterAll: 'Wszystko',
    filterBattery: 'Bateria & SoC',
    filterSolar: 'Słońce vs Dom',
    horizonPrefix: 'Horyzont: 48h (Krok 30m)',
    sellNow: 'RCE Teraz',
    legCharging: 'Ładowanie Baterii (W)',
    legSelfUse: 'Autokonsumpcja (W)',
    legExport: 'Eksport Sieciowy (W)',
    legImport: 'Import Sieciowy (W)',
    legPv: 'Produkcja PV (W)',
    legLoad: 'Prognoza Dom (W)',
    legSoc: 'Krzywa SoC (%)',
    legMinSoc: 'Linia Rezerwy Min SoC',
    legTariff: 'Zakup / Taryfa',
    legRce: 'Sprzedaż RCE',
    waitTitle: '⏳ Oczekiwanie na wyniki optymalizacji z EMHASS',
    waitSub1: 'Wykres 48h pojawi się automatycznie po publikacji sensor.p_batt_forecast',
    waitSub2: '(Kliknij "Przelicz MPC Teraz" lub sprawdź URL EMHASS w konfiguracji)',
    nowMarker: 'TERAZ',
    locale: 'pl-PL',
    ttStandby: 'Standby (0 W)',
    ttCharging: 'Ładowanie',
    ttSelfUse: 'Autokonsumpcja',
    ttNoGrid: '0 W (Brak wymiany)',
    ttImport: 'Import',
    ttExport: 'Eksport',
    ttBuy: 'Zakup',
    ttSell: 'Sprzedaż (RCE)',
    ttBattPlan: 'Plan Baterii',
    ttGrid: 'Sieć OSD',
    ttSoc: 'Krzywa SoC',
    ttReserve: 'Rezerwa',
    ttPv: 'Prognoza PV',
    ttLoad: 'Prognoza Dom',
  },
  en: {
    defaultTitle: 'Smart Storage EMS: 48h MPC Optimization Plan',
    kpiCharge: '⚡ Scheduled Charge',
    kpiDischarge: '🔋 Scheduled Discharge',
    kpiSolar: '☀️ Solar PV Forecast',
    kpiMinSoc: '🛡️ Dynamic Min SoC',
    filterAll: 'All',
    filterBattery: 'Battery & SoC',
    filterSolar: 'Solar vs Load',
    horizonPrefix: 'Horizon: 48h (30m step)',
    sellNow: 'Sell Price Now',
    legCharging: 'Battery Charging (W)',
    legSelfUse: 'Self-Consumption (W)',
    legExport: 'Grid Export (W)',
    legImport: 'Grid Import (W)',
    legPv: 'Solar PV (W)',
    legLoad: 'House Load Forecast (W)',
    legSoc: 'SoC Trajectory (%)',
    legMinSoc: 'Min SoC Reserve',
    legTariff: 'Buy Tariff',
    legRce: 'Sell Price (RCE)',
    waitTitle: '⏳ Waiting for EMHASS optimization results',
    waitSub1: 'The 48h chart will appear automatically once sensor.p_batt_forecast updates',
    waitSub2: '(Click "Optimize MPC" or check your EMHASS URL in settings)',
    nowMarker: 'NOW',
    locale: 'en-GB',
    ttStandby: 'Standby (0 W)',
    ttCharging: 'Charging',
    ttSelfUse: 'Self-Use',
    ttNoGrid: '0 W (Balanced)',
    ttImport: 'Import',
    ttExport: 'Export',
    ttBuy: 'Buy',
    ttSell: 'Sell (RCE)',
    ttBattPlan: 'Battery Plan',
    ttGrid: 'Grid Power',
    ttSoc: 'SoC Trajectory',
    ttReserve: 'Reserve',
    ttPv: 'PV Forecast',
    ttLoad: 'Load Forecast',
  },
};

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

class SmartStorageChartCard extends HTMLElement {
  _lang() {
    const raw = (this._hass?.locale?.language || this._hass?.language || 'en').toLowerCase();
    return raw.startsWith('pl') ? 'pl' : 'en';
  }

  _t() {
    return CHART_I18N[this._lang()];
  }

  _currency() {
    return this._hass?.config?.currency || (this._lang() === 'pl' ? 'zł' : 'PLN');
  }

  set hass(hass) {
    this._hass = hass;
    const t = this._t();
    if (!this.content) {
      this._card = document.createElement('ha-card');
      this._card.header = this.config?.title || t.defaultTitle;
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      this.content.style.position = 'relative';
      this._card.appendChild(this.content);
      this.appendChild(this._card);
      this._lastRenderedLang = this._lang();
      this._initCanvas();
    } else if (this._lastRenderedLang !== this._lang()) {
      this._lastRenderedLang = this._lang();
      if (!this.config?.title) this._card.header = t.defaultTitle;
      this._initCanvas();
    }
    this.render();
  }

  setConfig(config) {
    this.config = config || {};
    this._horizonHours = this.config.horizon_hours || 48;
    this._filterMode = 'all'; // 'all', 'battery', 'solar'
    this._visibleSeries = {
      charging: true,
      self_use: true,
      export: true,
      grid_import: true,
      pv: true,
      load: true,
      soc: true,
      min_soc: true,
      tariff: true,
      rce: true,
    };
  }

  getCardSize() {
    return 6;
  }

  _initCanvas() {
    const t = this._t();
    const curr = this._currency();
    this.content.innerHTML = `
      <style>
        .chart-wrapper {
          display: flex;
          flex-direction: column;
          gap: 12px;
          font-family: inherit;
          user-select: none;
        }
        .kpi-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
        }
        .kpi-card {
          background: var(--secondary-background-color, #f9f9f9);
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 10px;
          padding: 8px;
          text-align: center;
        }
        .kpi-label {
          font-size: 0.72rem;
          color: var(--secondary-text-color, #757575);
          font-weight: 500;
          margin-bottom: 2px;
        }
        .kpi-val {
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--primary-text-color, #212121);
        }
        .filter-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .filter-pills {
          display: flex;
          gap: 6px;
        }
        .pill-btn {
          background: var(--secondary-background-color, #f0f0f0);
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 16px;
          padding: 4px 10px;
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          color: var(--primary-text-color, #333);
        }
        .pill-btn.active {
          background: var(--primary-color, #03a9f4);
          color: white;
          border-color: var(--primary-color, #03a9f4);
        }
        .canvas-container {
          position: relative;
          width: 100%;
          height: 320px;
          background: var(--card-background-color, #fff);
          border-radius: 12px;
          border: 1px solid var(--divider-color, #e0e0e0);
          overflow: hidden;
        }
        canvas {
          width: 100%;
          height: 100%;
          display: block;
        }
        .chart-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          font-size: 0.75rem;
          justify-content: center;
          color: var(--secondary-text-color, #666);
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;
          cursor: pointer;
          padding: 3px 8px;
          border-radius: 12px;
          border: 1px solid transparent;
          transition: opacity 0.15s ease, background-color 0.15s ease;
        }
        .legend-item:hover {
          background: var(--secondary-background-color, rgba(128, 128, 128, 0.1));
        }
        .legend-item.disabled {
          opacity: 0.35;
          text-decoration: line-through;
        }
        .legend-box {
          width: 12px;
          height: 10px;
          border-radius: 2px;
        }
        .legend-line {
          width: 14px;
          height: 3px;
          border-radius: 1px;
        }
        .legend-dash {
          width: 14px;
          height: 0px;
          border-top: 2px dashed #90a4ae;
        }
        .tooltip-box {
          position: absolute;
          display: none;
          pointer-events: none;
          background: rgba(33, 33, 33, 0.92);
          color: white;
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 0.75rem;
          line-height: 1.4;
          box-shadow: 0 4px 12px rgba(0,0,0,0.25);
          z-index: 10;
          white-space: nowrap;
        }
      </style>

      <div class="chart-wrapper">
        <div class="kpi-row">
          <div class="kpi-card">
            <div class="kpi-label">${t.kpiCharge}</div>
            <div class="kpi-val" id="kpiCharge" style="color: #4caf50;">-- kWh</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">${t.kpiDischarge}</div>
            <div class="kpi-val" id="kpiDischarge" style="color: #2196f3;">-- kWh</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">${t.kpiSolar}</div>
            <div class="kpi-val" id="kpiSolar" style="color: #f57f17;">-- kWh</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">${t.kpiMinSoc}</div>
            <div class="kpi-val" id="kpiMinSoc" style="color: #d32f2f;">-- %</div>
          </div>
        </div>

        <div class="filter-row">
          <div class="filter-pills">
            <button class="pill-btn active" data-filter="all">${t.filterAll}</button>
            <button class="pill-btn" data-filter="battery">${t.filterBattery}</button>
            <button class="pill-btn" data-filter="solar">${t.filterSolar}</button>
          </div>
          <div style="font-size: 0.75rem; font-weight: 600; color: var(--secondary-text-color, #757575);" id="chartHeaderSubtitle">
            ${t.horizonPrefix}
          </div>
        </div>

        <div class="canvas-container" id="canvasBox">
          <canvas id="emsChartCanvas"></canvas>
          <div class="tooltip-box" id="chartTooltip"></div>
        </div>

        <div class="chart-legend">
          <div class="legend-item" data-series="charging"><div class="legend-box" style="background: #4caf50;"></div> ${t.legCharging}</div>
          <div class="legend-item" data-series="self_use"><div class="legend-box" style="background: #2196f3;"></div> ${t.legSelfUse}</div>
          <div class="legend-item" data-series="export"><div class="legend-box" style="background: #ff9800;"></div> ${t.legExport}</div>
          <div class="legend-item" data-series="grid_import"><div class="legend-line" style="background: #ff5722;"></div> ${t.legImport}</div>
          <div class="legend-item" data-series="pv"><div class="legend-line" style="background: #fbc02d;"></div> ${t.legPv}</div>
          <div class="legend-item" data-series="load"><div class="legend-dash" style="border-top-color: #90a4ae;"></div> ${t.legLoad}</div>
          <div class="legend-item" data-series="soc"><div class="legend-line" style="background: #e91e63;"></div> ${t.legSoc}</div>
          <div class="legend-item" data-series="min_soc"><div class="legend-dash" style="border-top-color: #d32f2f;"></div> ${t.legMinSoc}</div>
          <div class="legend-item" data-series="tariff"><div class="legend-line" style="background: #ab47bc;"></div> ${escapeHtml(t.legTariff)} (${escapeHtml(curr)}/kWh)</div>
          <div class="legend-item" data-series="rce"><div class="legend-line" style="background: #00bcd4;"></div> ${t.legRce} (${curr}/kWh)</div>
        </div>
      </div>
    `;

    this._canvas = this.content.querySelector('#emsChartCanvas');
    this._tooltip = this.content.querySelector('#chartTooltip');
    this._canvasBox = this.content.querySelector('#canvasBox');

    const syncLegendUI = () => {
      this.content.querySelectorAll('.legend-item').forEach(item => {
        const key = item.getAttribute('data-series');
        if (key) {
          item.classList.toggle('disabled', !this._visibleSeries[key]);
        }
      });
    };

    // Filter pill buttons (presets that update individual series toggles)
    this.content.querySelectorAll('.pill-btn').forEach(btn => {
      btn.onclick = (e) => {
        this.content.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        this._filterMode = e.target.getAttribute('data-filter');
        if (this._filterMode === 'all') {
          Object.keys(this._visibleSeries).forEach(k => { this._visibleSeries[k] = true; });
        } else if (this._filterMode === 'battery') {
          this._visibleSeries = {
            charging: true, self_use: true, export: true, grid_import: true,
            pv: false, load: false,
            soc: true, min_soc: true, tariff: true, rce: true,
          };
        } else if (this._filterMode === 'solar') {
          this._visibleSeries = {
            charging: false, self_use: false, export: true, grid_import: false,
            pv: true, load: true,
            soc: false, min_soc: false, tariff: false, rce: true,
          };
        }
        syncLegendUI();
        this.render();
      };
    });

    // Interactive legend toggles (click any item to show/hide that curve)
    this.content.querySelectorAll('.legend-item').forEach(item => {
      item.onclick = () => {
        const key = item.getAttribute('data-series');
        if (!key) return;
        this._visibleSeries[key] = !this._visibleSeries[key];
        syncLegendUI();
        this.render();
      };
    });

    // Mouse / Touch interaction
    this._canvas.onmousemove = (e) => this._handlePointer(e.offsetX, e.offsetY);
    this._canvas.onmouseleave = () => { this._tooltip.style.display = 'none'; };
    this._canvas.ontouchmove = (e) => {
      const rect = this._canvas.getBoundingClientRect();
      const touch = e.touches[0];
      this._handlePointer(touch.clientX - rect.left, touch.clientY - rect.top);
    };
    this._canvas.ontouchend = () => { this._tooltip.style.display = 'none'; };
  }

  _extractData() {
    const battForecastEntity = this._hass.states['sensor.p_batt_forecast'];
    const socForecastEntity = this._hass.states['sensor.soc_batt_forecast'];
    const pvForecastEntity = this._hass.states['sensor.p_pv_forecast'];
    const loadForecastEntity = this._hass.states['sensor.p_load_forecast'];
    const gridForecastEntity = this._hass.states['sensor.p_grid_forecast'];
    const minSocEntity = this._hass.states['sensor.smart_storage_ems_dynamiczny_min_soc']
      || this._hass.states['sensor.smart_storage_ems_dynamic_min_soc'];
    const statusEntity = this._hass.states['sensor.smart_storage_ems_status'];

    const battList = battForecastEntity?.attributes?.forecasts || battForecastEntity?.attributes?.battery_scheduled_power || [];
    const socList = socForecastEntity?.attributes?.battery_scheduled_soc || socForecastEntity?.attributes?.forecasts || [];
    const pvList = pvForecastEntity?.attributes?.forecasts || [];
    const loadList = loadForecastEntity?.attributes?.forecasts || [];
    const gridList = gridForecastEntity?.attributes?.forecasts || [];

    const buyPrices = statusEntity?.attributes?.buy_prices || [];
    const sellPrices = statusEntity?.attributes?.sell_prices || [];
    const currentSellPrice = statusEntity?.attributes?.current_sell_price;
    const sellPriceMode = statusEntity?.attributes?.sell_price_mode || 'pse_rce';
    const tariffMode = (statusEntity?.attributes?.tariff_mode || 'g13').toUpperCase();
    const pricesStartIso = statusEntity?.attributes?.buy_prices_start_time;
    const sellPricesStartIso = statusEntity?.attributes?.sell_prices_start_time || pricesStartIso;

    const dynamicMinSoc = minSocEntity ? parseFloat(minSocEntity.state) || 15 : 15;

    const hasData = (battList.length > 0 || socList.length > 0);
    const stepsCount = hasData ? Math.max(battList.length, socList.length) : 0;
    const dataPoints = [];

    const now = new Date();
    const startMinutes = now.getMinutes() >= 30 ? 30 : 0;
    const baseTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), startMinutes);
    const pricesBaseMs = pricesStartIso ? new Date(pricesStartIso).getTime() : baseTime.getTime();
    const sellPricesBaseMs = sellPricesStartIso ? new Date(sellPricesStartIso).getTime() : baseTime.getTime();

    for (let i = 0; i < stepsCount; i++) {
      const bItem = battList[i] || {};
      const sItem = socList[i] || {};
      const pItem = pvList[i] || {};
      const lItem = loadList[i] || {};
      const gItem = gridList[i] || {};

      let pointTime;
      const rawDate = bItem.date || sItem.date || pItem.date;
      if (rawDate) {
        pointTime = new Date(rawDate);
      } else {
        pointTime = new Date(baseTime.getTime() + i * 30 * 60000);
      }

      // Align tariff price by timestamp offset (fallback to index if no start time)
      let buyPrice = null;
      if (buyPrices.length > 0) {
        const priceIdx = Math.round((pointTime.getTime() - pricesBaseMs) / (30 * 60000));
        if (priceIdx >= 0 && priceIdx < buyPrices.length) {
          buyPrice = parseFloat(buyPrices[priceIdx]);
        } else if (i < buyPrices.length) {
          buyPrice = parseFloat(buyPrices[i]);
        }
      }

      // Align RCE sell price by timestamp offset
      let sellPrice = null;
      if (sellPrices.length > 0) {
        const priceIdx = Math.round((pointTime.getTime() - sellPricesBaseMs) / (30 * 60000));
        if (priceIdx >= 0 && priceIdx < sellPrices.length) {
          sellPrice = parseFloat(sellPrices[priceIdx]);
        } else if (i < sellPrices.length) {
          sellPrice = parseFloat(sellPrices[i]);
        }
      }

      // Resilient parsing across all EMHASS naming conventions
      const rawBatt = bItem.p_batt_forecast ?? bItem.P_batt ?? bItem.p_batt ?? bItem.battery_power ?? 0;
      const rawSoc = sItem.soc_batt_forecast ?? sItem.battery_scheduled_soc ?? sItem.SOC_opt ?? sItem.soc_batt ?? sItem.soc ?? 0;
      const rawPv = pItem.p_pv_forecast ?? pItem.P_PV ?? pItem.p_pv ?? pItem.pv_power ?? 0;
      const rawLoad = lItem.p_load_forecast ?? lItem.P_Load ?? lItem.p_load ?? lItem.load_power ?? 0;
      const rawGrid = gItem.p_grid_forecast ?? gItem.P_grid ?? gItem.p_grid ?? gItem.grid_power ?? 0;

      let socVal = parseFloat(rawSoc) || 0;
      if (socVal > 0 && socVal <= 1.0) {
        socVal = socVal * 100.0;
      }

      const gridVal = parseFloat(rawGrid) || 0;

      dataPoints.push({
        time: pointTime,
        p_batt: parseFloat(rawBatt) || 0,
        soc: socVal,
        pv: parseFloat(rawPv) || 0,
        load: parseFloat(rawLoad) || 0,
        grid: gridVal,
        grid_import: Math.max(0, gridVal),
        grid_export: Math.max(0, -gridVal),
        min_soc: dynamicMinSoc,
        buy_price: buyPrice,
        sell_price: sellPrice,
      });
    }

    return { dataPoints, dynamicMinSoc, hasData, tariffMode, currentSellPrice, sellPriceMode };
  }

  render() {
    if (!this._canvas || !this._hass) return;

    const { dataPoints, dynamicMinSoc, hasData, tariffMode, currentSellPrice, sellPriceMode } = this._extractData();
    this._dataPoints = dataPoints;
    this._tariffMode = tariffMode;
    this._currentSellPrice = currentSellPrice;
    this._sellPriceMode = sellPriceMode;

    const t = this._t();
    const curr = this._currency();
    const subtitle = this.content.querySelector('#chartHeaderSubtitle');
    if (subtitle) {
      let subText = t.horizonPrefix;
      if (currentSellPrice !== undefined && currentSellPrice !== null) {
        subText += ` | ${t.sellNow}: ${parseFloat(currentSellPrice).toFixed(2)} ${curr}`;
      }
      subtitle.textContent = subText;
    }
    this._tariffMode = tariffMode;

    const kpiCharge = this.content.querySelector('#kpiCharge');
    const kpiDischarge = this.content.querySelector('#kpiDischarge');
    const kpiSolar = this.content.querySelector('#kpiSolar');
    const kpiMinSoc = this.content.querySelector('#kpiMinSoc');

    if (kpiMinSoc) kpiMinSoc.textContent = `${dynamicMinSoc.toFixed(0)} %`;

    if (hasData) {
      let totalChargeKwh = 0;
      let totalDischargeKwh = 0;
      let totalSolarKwh = 0;

      dataPoints.forEach(p => {
        if (p.p_batt < 0) totalChargeKwh += Math.abs(p.p_batt) * 0.5 / 1000.0;
        if (p.p_batt > 0) totalDischargeKwh += p.p_batt * 0.5 / 1000.0;
        totalSolarKwh += p.pv * 0.5 / 1000.0;
      });

      if (kpiCharge) kpiCharge.textContent = `${totalChargeKwh.toFixed(1)} kWh`;
      if (kpiDischarge) kpiDischarge.textContent = `${totalDischargeKwh.toFixed(1)} kWh`;
      if (kpiSolar) kpiSolar.textContent = `${totalSolarKwh.toFixed(1)} kWh`;
    } else {
      if (kpiCharge) kpiCharge.textContent = `-- kWh`;
      if (kpiDischarge) kpiDischarge.textContent = `-- kWh`;
      if (kpiSolar) kpiSolar.textContent = `-- kWh`;
    }

    // Render Canvas
    this._drawChart(dataPoints, dynamicMinSoc, hasData);
  }

  _drawChart(points, dynamicMinSoc, hasData = true) {
    const canvas = this._canvas;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    const t = this._t();
    if (!hasData || points.length === 0) {
      ctx.fillStyle = 'rgba(128, 128, 128, 0.7)';
      ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(t.waitTitle, w / 2, h / 2 - 12);
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.fillStyle = 'rgba(128, 128, 128, 0.5)';
      ctx.fillText(t.waitSub1, w / 2, h / 2 + 10);
      ctx.fillText(t.waitSub2, w / 2, h / 2 + 28);
      return;
    }

    const padLeft = 46;
    const padRight = 42;
    const padTop = 24;
    const padBottom = 30;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    // Power Bounds (Watts)
    let maxPower = 4000;
    let minPower = -4000;
    points.forEach(p => {
      if (p.p_batt > maxPower) maxPower = p.p_batt;
      if (p.p_batt < minPower) minPower = p.p_batt;
      if (p.pv > maxPower) maxPower = p.pv;
      if (p.load > maxPower) maxPower = p.load;
      if (p.grid > maxPower) maxPower = p.grid;
      if (p.grid < minPower) minPower = p.grid;
    });
    maxPower = Math.ceil(maxPower / 1000) * 1000;
    minPower = Math.floor(minPower / 1000) * 1000;
    if (minPower > -2000) minPower = -2000;
    if (maxPower < 3000) maxPower = 3000;

    const powerRange = maxPower - minPower;
    const getYPower = (watts) => padTop + plotH - ((watts - minPower) / powerRange) * plotH;
    const getYSoc = (socPct) => padTop + plotH - (socPct / 100.0) * plotH;
    const getX = (idx) => padLeft + (idx / (points.length - 1)) * plotW;

    this._plotParams = { padLeft, padRight, padTop, padBottom, plotW, plotH, minPower, maxPower, powerRange };

    // 1. Draw Grid Lines
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.15)';
    ctx.lineWidth = 1;

    // Zero Line
    const yZero = getYPower(0);
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.4)';
    ctx.moveTo(padLeft, yZero);
    ctx.lineTo(padLeft + plotW, yZero);
    ctx.stroke();

    // Horizontal power grid steps
    const stepCount = 4;
    ctx.fillStyle = 'rgba(128, 128, 128, 0.8)';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    for (let i = 0; i <= stepCount; i++) {
      const pVal = minPower + (i / stepCount) * powerRange;
      const yVal = getYPower(pVal);
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(128, 128, 128, 0.1)';
      ctx.moveTo(padLeft, yVal);
      ctx.lineTo(padLeft + plotW, yVal);
      ctx.stroke();
      ctx.fillText(`${Math.round(pVal)}W`, padLeft - 6, yVal + 3);
    }

    // Right SoC Axis Labels
    ctx.textAlign = 'left';
    [0, 25, 50, 75, 100].forEach(soc => {
      const ySoc = getYSoc(soc);
      ctx.fillText(`${soc}%`, padLeft + plotW + 6, ySoc + 3);
    });

    const vis = this._visibleSeries || {
      charging: true, self_use: true, export: true, grid_import: true,
      pv: true, load: true, soc: true, min_soc: true, tariff: true, rce: true,
    };

    // 1B. Draw Tariff / Buy Price and RCE Sell Price Stepped Curves
    const validBuyPrices = vis.tariff ? points.map(p => p.buy_price).filter(v => v !== null && !isNaN(v)) : [];
    const validSellPrices = vis.rce ? points.map(p => p.sell_price).filter(v => v !== null && !isNaN(v)) : [];
    const allValidPrices = [...validBuyPrices, ...validSellPrices];

    if (allValidPrices.length > 0) {
      const minPrice = Math.min(0, ...allValidPrices);
      const maxPrice = Math.max(1.2, ...allValidPrices);
      const priceCeil = Math.max(maxPrice * 1.15, 0.5);
      const getYPrice = (price) => padTop + plotH - ((price - minPrice) / (priceCeil - minPrice)) * (plotH * 0.42);
      const stepW = points.length > 1 ? plotW / (points.length - 1) : plotW;

      // Subtle purple background column for peak/higher-cost buy zones
      if (vis.tariff && validBuyPrices.length > 0) {
        const minBuy = Math.min(...validBuyPrices);
        const maxBuy = Math.max(...validBuyPrices);
        if (maxBuy > minBuy) {
          points.forEach((p, idx) => {
            if (p.buy_price !== null && p.buy_price > minBuy * 1.10) {
              const x = getX(idx);
              const xLeft = Math.max(padLeft, x - stepW / 2);
              const xRight = Math.min(padLeft + plotW, x + stepW / 2);
              const intensity = Math.min(0.12, 0.04 + ((p.buy_price - minBuy) / (maxBuy - minBuy)) * 0.08);
              ctx.fillStyle = `rgba(171, 71, 188, ${intensity.toFixed(3)})`;
              ctx.fillRect(xLeft, padTop, xRight - xLeft, plotH);
            }
          });
        }
      }

      // Stepped tariff buy line (Purple #ab47bc)
      if (vis.tariff && validBuyPrices.length > 0) {
        ctx.strokeStyle = 'rgba(171, 71, 188, 0.85)';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let started = false;
        let prevY = null;
        points.forEach((p, idx) => {
          if (p.buy_price === null || isNaN(p.buy_price)) return;
          const x = getX(idx);
          const y = getYPrice(p.buy_price);
          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, prevY);
            ctx.lineTo(x, y);
          }
          prevY = y;
        });
        ctx.stroke();
      }

      // Stepped RCE sell price line (Cyan #00bcd4)
      if (vis.rce && validSellPrices.length > 0) {
        ctx.strokeStyle = '#00bcd4';
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        let started = false;
        let prevY = null;
        points.forEach((p, idx) => {
          if (p.sell_price === null || isNaN(p.sell_price)) return;
          const x = getX(idx);
          const y = getYPrice(p.sell_price);
          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, prevY);
            ctx.lineTo(x, y);
          }
          prevY = y;
        });
        ctx.stroke();

        // If any price is negative, draw red dashed zero line
        if (minPrice < 0) {
          const yZeroP = getYPrice(0);
          ctx.strokeStyle = 'rgba(244, 67, 54, 0.7)';
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 3]);
          ctx.beginPath();
          ctx.moveTo(padLeft, yZeroP);
          ctx.lineTo(padLeft + plotW, yZeroP);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    }

    // 2. Draw Battery Power Areas and Continuous Line
    if (vis.charging || vis.self_use || vis.export) {
      const stepW = points.length > 1 ? plotW / (points.length - 1) : plotW;

      // 2A. Shaded power areas (under / above zero line)
      points.forEach((p, idx) => {
        const x = getX(idx);
        const pVal = p.p_batt;
        const halfStep = stepW / 2;
        const xLeft = Math.max(padLeft, x - halfStep);
        const xRight = Math.min(padLeft + plotW, x + halfStep);
        const wSeg = xRight - xLeft;

        if (Math.abs(pVal) > 20) {
          if (pVal < -20 && vis.charging) {
            // Charging from Grid/PV (Green Area below zero)
            ctx.fillStyle = 'rgba(76, 175, 80, 0.45)';
            const yTop = yZero;
            const yBottom = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yBottom - yTop);
          } else if (p.grid < -50 && pVal > 50 && vis.export) {
            // Export to Grid (Amber/Orange Area above zero)
            ctx.fillStyle = 'rgba(255, 152, 0, 0.50)';
            const yTop = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yZero - yTop);
          } else if (pVal > 20 && !(p.grid < -50 && pVal > 50) && vis.self_use) {
            // Self-consumption to House (Blue Area above zero)
            ctx.fillStyle = 'rgba(33, 150, 243, 0.45)';
            const yTop = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yZero - yTop);
          }
        }
      });

      // 2B. Continuous Battery Power Outline Curve (respecting toggles)
      const isPointVisible = (p) => {
        if (p.p_batt < -20) return vis.charging;
        if (p.grid < -50 && p.p_batt > 50) return vis.export;
        if (p.p_batt > 20) return vis.self_use;
        return vis.charging || vis.self_use || vis.export;
      };

      ctx.lineWidth = 2;
      for (let i = 0; i < points.length - 1; i++) {
        const p1 = points[i];
        const p2 = points[i + 1];
        if (!isPointVisible(p1) && !isPointVisible(p2)) continue;

        const x1 = getX(i);
        const y1 = getYPower(isPointVisible(p1) ? p1.p_batt : 0);
        const x2 = getX(i + 1);
        const y2 = getYPower(isPointVisible(p2) ? p2.p_batt : 0);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);

        if ((p1.p_batt < -20 || p2.p_batt < -20) && vis.charging) {
          ctx.strokeStyle = '#4caf50'; // Green: charging
        } else if (((p1.grid < -50 && p1.p_batt > 50) || (p2.grid < -50 && p2.p_batt > 50)) && vis.export) {
          ctx.strokeStyle = '#ff9800'; // Orange: export
        } else if ((p1.p_batt > 20 || p2.p_batt > 20) && vis.self_use) {
          ctx.strokeStyle = '#2196f3'; // Blue: self-consumption
        } else {
          ctx.strokeStyle = 'rgba(128, 128, 128, 0.4)'; // Neutral / zero
        }
        ctx.stroke();
      }
    }

    // 2C. Draw Grid Import Curve (Coral / Orange-Red line #ff5722)
    if (vis.grid_import) {
      ctx.strokeStyle = '#ff5722';
      ctx.lineWidth = 2;
      ctx.beginPath();
      points.forEach((p, idx) => {
        const x = getX(idx);
        const y = getYPower(p.grid_import);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    // 3. Draw Solar & Load Curves
    if (vis.pv) {
      // Solar Curve (Yellow)
      ctx.strokeStyle = '#fbc02d';
      ctx.lineWidth = 2;
      ctx.beginPath();
      points.forEach((p, idx) => {
        const x = getX(idx);
        const y = getYPower(p.pv);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    if (vis.load) {
      // Load Curve (Light Grey Dashed)
      ctx.strokeStyle = '#90a4ae';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      points.forEach((p, idx) => {
        const x = getX(idx);
        const y = getYPower(p.load);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 4. Draw Dynamic Min SoC Reference Line (Red Horizontal)
    if (vis.min_soc) {
      const yMinSoc = getYSoc(dynamicMinSoc);
      ctx.strokeStyle = 'rgba(211, 47, 47, 0.7)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 3]);
      ctx.beginPath();
      ctx.moveTo(padLeft, yMinSoc);
      ctx.lineTo(padLeft + plotW, yMinSoc);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 5. Draw SoC Trajectory Line (Glowing Pink/Magenta)
    if (vis.soc) {
      ctx.strokeStyle = '#e91e63';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      points.forEach((p, idx) => {
        const x = getX(idx);
        const y = getYSoc(p.soc);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    // 6. Time Labels on X axis
    ctx.fillStyle = 'rgba(128, 128, 128, 0.9)';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';

    const labelInterval = Math.max(4, Math.floor(points.length / 8));
    points.forEach((p, idx) => {
      if (idx % labelInterval === 0 || idx === points.length - 1) {
        const x = getX(idx);
        const hours = p.time.getHours().toString().padStart(2, '0');
        const mins = p.time.getMinutes().toString().padStart(2, '0');
        ctx.fillText(`${hours}:${mins}`, x, padTop + plotH + 18);
      }
    });

    // 7. "TERAZ" Current Time Marker Line
    ctx.strokeStyle = '#00e676';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padLeft, padTop);
    ctx.lineTo(padLeft, padTop + plotH);
    ctx.stroke();

    ctx.fillStyle = '#00e676';
    ctx.font = 'bold 9px sans-serif';
    ctx.fillText(t.nowMarker, padLeft + 16, padTop + 10);
  }

  _handlePointer(mouseX, mouseY) {
    if (!this._dataPoints || !this._plotParams) return;
    const { padLeft, plotW, plotH, padTop } = this._plotParams;
    const t = this._t();
    const curr = this._currency();

    if (mouseX < padLeft || mouseX > padLeft + plotW) {
      this._tooltip.style.display = 'none';
      return;
    }

    const relX = (mouseX - padLeft) / plotW;
    const idx = Math.min(this._dataPoints.length - 1, Math.max(0, Math.round(relX * (this._dataPoints.length - 1))));
    const point = this._dataPoints[idx];
    if (!point) return;

    const timeStr = `${point.time.toLocaleDateString(t.locale, { weekday: 'short', day: 'numeric', month: 'numeric' })} ${point.time.getHours().toString().padStart(2, '0')}:${point.time.getMinutes().toString().padStart(2, '0')}`;

    let battState = t.ttStandby;
    if (point.p_batt < -20) battState = `${t.ttCharging}: ${Math.abs(Math.round(point.p_batt))} W`;
    else if (point.p_batt > 20) battState = `${t.ttSelfUse}: ${Math.round(point.p_batt)} W`;

    let gridState = t.ttNoGrid;
    if (point.grid > 20) {
      gridState = `${t.ttImport}: ${Math.round(point.grid)} W`;
    } else if (point.grid < -20) {
      gridState = `${t.ttExport}: ${Math.round(Math.abs(point.grid))} W`;
    }

    const tariffLine = (point.buy_price !== null && !isNaN(point.buy_price))
      ? `<div>💰 <b>${escapeHtml(t.ttBuy)} (${escapeHtml(this._tariffMode || 'EMS')}):</b> ${point.buy_price.toFixed(2)} ${escapeHtml(curr)}/kWh</div>`
      : '';

    const rceLine = (point.sell_price !== null && !isNaN(point.sell_price))
      ? `<div>📈 <b>${escapeHtml(t.ttSell)}:</b> ${point.sell_price.toFixed(3)} ${escapeHtml(curr)}/kWh</div>`
      : '';

    this._tooltip.innerHTML = `
      <div style="font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 4px; margin-bottom: 4px;">
        🕒 ${escapeHtml(timeStr)}
      </div>
      <div>🔋 <b>${escapeHtml(t.ttBattPlan)}:</b> ${escapeHtml(battState)}</div>
      <div>🔌 <b>${escapeHtml(t.ttGrid)}:</b> ${escapeHtml(gridState)}</div>
      <div>📊 <b>${escapeHtml(t.ttSoc)}:</b> ${point.soc.toFixed(1)}% (${escapeHtml(t.ttReserve)}: ${point.min_soc}%)</div>
      <div>☀️ <b>${escapeHtml(t.ttPv)}:</b> ${Math.round(point.pv)} W</div>
      <div>🏠 <b>${escapeHtml(t.ttLoad)}:</b> ${Math.round(point.load)} W</div>
      ${tariffLine}
      ${rceLine}
    `;

    this._tooltip.style.display = 'block';
    const tooltipWidth = this._tooltip.offsetWidth || 180;
    let posX = mouseX + 15;
    if (posX + tooltipWidth > this._canvasBox.offsetWidth - 10) {
      posX = mouseX - tooltipWidth - 15;
    }
    this._tooltip.style.left = `${posX}px`;
    this._tooltip.style.top = `${Math.min(padTop + plotH - 60, Math.max(10, mouseY - 40))}px`;
  }
}

customElements.define('smart-storage-chart-card', SmartStorageChartCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'smart-storage-chart-card',
  name: 'Smart Storage EMS: 48h MPC Chart',
  description: 'Interactive dual-axis chart showing the 48h battery schedule, solar PV forecast, house load, and prices.'
});
