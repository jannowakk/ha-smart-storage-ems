/**
 * Smart Storage EMS - Dedicated High-Performance Interactive MPC Chart Card
 * State-of-the-Art Clean UI with 24h Visual Timeline & 3 Intuitive Views
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

const CHART_I18N = {
  pl: {
    defaultTitle: 'Smart Storage EMS: Plan Pracy Baterii i Prognozy',
    timelineTitle: 'Harmonogram Doby (24h):',
    tlCharge: 'Ładowanie',
    tlSelfUse: 'Zasilanie Domu',
    tlHold: 'Czuwanie / Rezerwa',
    tlExport: 'Eksport PV',
    kpiCharge: '⚡ Ładowanie z sieci',
    kpiDischarge: '🔋 Zasilanie z baterii',
    kpiSolar: '☀️ Prognoza PV',
    kpiMinSoc: '🛡️ Min SoC (Rezerwa)',
    tabBattery: '🔋 Bateria & SoC',
    tabSolar: '☀️ Słońce vs Dom',
    tabPrices: '💰 Taryfy i Ceny',
    tabAll: '🔬 Wszystko (Zaawansowane)',
    horizonPrefix: 'Horyzont: 48h (Krok 30m)',
    horizonPrefix24: 'Horyzont: 24h (Krok 30m)',
    zoomToday: '🔍 24h',
    zoom48: '🌐 48h',
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
    waitSub1: 'Wykres pojawi się automatycznie po publikacji sensor.p_batt_forecast',
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
    defaultTitle: 'Smart Storage EMS: Battery Schedule & Forecasts',
    timelineTitle: '24h Daily Timeline:',
    tlCharge: 'Grid Charging',
    tlSelfUse: 'Home Powering',
    tlHold: 'Standby / Reserve',
    tlExport: 'PV Export',
    kpiCharge: '⚡ Grid Charge',
    kpiDischarge: '🔋 Battery Discharge',
    kpiSolar: '☀️ Solar Forecast',
    kpiMinSoc: '🛡️ Min SoC Reserve',
    tabBattery: '🔋 Battery & SoC',
    tabSolar: '☀️ Solar vs Load',
    tabPrices: '💰 Tariffs & Prices',
    tabAll: '🔬 All (Advanced)',
    horizonPrefix: 'Horizon: 48h (30m step)',
    horizonPrefix24: 'Horizon: 24h (30m step)',
    zoomToday: '🔍 24h',
    zoom48: '🌐 48h',
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
    waitSub1: 'The chart will appear automatically once sensor.p_batt_forecast updates',
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
    this._viewTab = this.config.default_view || 'battery'; // 'battery', 'solar', 'prices', 'all'
    this._zoomToday = false; // default false (full 48h horizon)
    this._applyTabVisibility(this._viewTab);
  }

  _applyTabVisibility(tab) {
    this._viewTab = tab;
    if (tab === 'battery') {
      this._visibleSeries = {
        charging: true,
        self_use: true,
        export: false,
        grid_import: false,
        pv: false,
        load: false,
        soc: true,
        min_soc: true,
        tariff: false,
        rce: false,
      };
    } else if (tab === 'solar') {
      this._visibleSeries = {
        charging: false,
        self_use: false,
        export: true,
        grid_import: true,
        pv: true,
        load: true,
        soc: false,
        min_soc: false,
        tariff: false,
        rce: false,
      };
    } else if (tab === 'prices') {
      this._visibleSeries = {
        charging: true,
        self_use: false,
        export: false,
        grid_import: false,
        pv: false,
        load: false,
        soc: true,
        min_soc: false,
        tariff: true,
        rce: true,
      };
    } else {
      // 'all'
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
        /* Visual 24h Timeline Bar */
        .timeline-section {
          background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
          border: 1px solid var(--divider-color, rgba(128, 128, 128, 0.2));
          border-radius: 12px;
          padding: 10px 12px;
        }
        .timeline-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.76rem;
          font-weight: 600;
          color: var(--secondary-text-color, #757575);
          margin-bottom: 6px;
        }
        .timeline-bar {
          display: flex;
          height: 22px;
          border-radius: 6px;
          overflow: hidden;
          background: rgba(128, 128, 128, 0.15);
          width: 100%;
          border: 1px solid rgba(128, 128, 128, 0.2);
        }
        .timeline-slot {
          flex: 1;
          height: 100%;
          transition: opacity 0.15s ease;
          position: relative;
        }
        .timeline-slot:hover {
          filter: brightness(1.2);
          cursor: pointer;
        }
        .timeline-ticks {
          display: flex;
          justify-content: space-between;
          font-size: 0.65rem;
          color: var(--secondary-text-color, #888);
          margin-top: 4px;
          padding: 0 2px;
        }
        .timeline-legend {
          display: flex;
          gap: 12px;
          justify-content: center;
          font-size: 0.70rem;
          margin-top: 6px;
          flex-wrap: wrap;
        }
        .timeline-badge {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }

        /* KPI Cards */
        .kpi-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
        }
        .kpi-card {
          background: var(--secondary-background-color, rgba(0, 0, 0, 0.03));
          border: 1px solid var(--divider-color, rgba(128, 128, 128, 0.2));
          border-radius: 10px;
          padding: 8px 6px;
          text-align: center;
        }
        .kpi-label {
          font-size: 0.68rem;
          color: var(--secondary-text-color, #757575);
          font-weight: 500;
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .kpi-val {
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--primary-text-color, #212121);
        }

        /* View Tabs & Zoom */
        .tabs-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--divider-color, rgba(128, 128, 128, 0.2));
          padding-bottom: 8px;
          gap: 8px;
          flex-wrap: wrap;
        }
        .tab-pills {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }
        .right-controls {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .zoom-btn {
          background: var(--secondary-background-color, rgba(0, 0, 0, 0.04));
          border: 1px solid var(--divider-color, rgba(128, 128, 128, 0.3));
          border-radius: 14px;
          padding: 3px 10px;
          font-size: 0.70rem;
          font-weight: 700;
          cursor: pointer;
          color: var(--primary-text-color, #444);
          transition: all 0.2s ease;
        }
        .zoom-btn:hover {
          background: rgba(128, 128, 128, 0.15);
        }
        .zoom-btn.active {
          background: #673ab7;
          color: #fff;
          border-color: #673ab7;
        }
        .tab-btn {
          background: var(--secondary-background-color, rgba(0, 0, 0, 0.04));
          border: 1px solid var(--divider-color, rgba(128, 128, 128, 0.25));
          border-radius: 16px;
          padding: 4px 12px;
          font-size: 0.74rem;
          font-weight: 600;
          cursor: pointer;
          color: var(--primary-text-color, #333);
          transition: all 0.2s ease;
        }
        .tab-btn:hover {
          background: rgba(3, 169, 244, 0.1);
        }
        .tab-btn.active {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          border-color: var(--primary-color, #03a9f4);
        }
        .sub-info {
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--secondary-text-color, #757575);
        }

        /* Canvas Box */
        .canvas-container {
          position: relative;
          width: 100%;
          height: 320px;
          background: var(--card-background-color, #fff);
          border-radius: 12px;
          border: 1px solid var(--divider-color, rgba(128, 128, 128, 0.2));
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
          gap: 10px;
          font-size: 0.72rem;
          justify-content: center;
          color: var(--secondary-text-color, #666);
          margin-top: 2px;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;
          cursor: pointer;
          padding: 2px 7px;
          border-radius: 10px;
          border: 1px solid transparent;
          transition: opacity 0.15s ease, background-color 0.15s ease;
        }
        .legend-item:hover {
          background: rgba(128, 128, 128, 0.1);
        }
        .legend-item.disabled {
          opacity: 0.35;
          text-decoration: line-through;
        }
        .legend-box {
          width: 10px;
          height: 10px;
          border-radius: 2px;
          display: inline-block;
        }
        .legend-line {
          width: 14px;
          height: 2.5px;
          border-radius: 1px;
          display: inline-block;
        }
        .legend-dash {
          width: 14px;
          height: 0;
          border-top: 2px dashed #888;
          display: inline-block;
        }
        .tooltip-box {
          position: absolute;
          display: none;
          pointer-events: none;
          background: rgba(28, 28, 30, 0.94);
          color: #fff;
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 0.72rem;
          line-height: 1.45;
          z-index: 10;
          box-shadow: 0 4px 14px rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.15);
          backdrop-filter: blur(4px);
        }
      </style>

      <div class="chart-wrapper">
        <!-- Visual 24h Timeline Bar -->
        <div class="timeline-section" id="timelineBox">
          <div class="timeline-header">
            <span>⏱️ ${t.timelineTitle}</span>
            <span id="timelineNow">TERAZ</span>
          </div>
          <div class="timeline-bar" id="timelineBar"></div>
          <div class="timeline-ticks">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
            <span>24:00</span>
          </div>
          <div class="timeline-legend">
            <span class="timeline-badge"><span class="dot" style="background: #4caf50;"></span> ${t.tlCharge}</span>
            <span class="timeline-badge"><span class="dot" style="background: #2196f3;"></span> ${t.tlSelfUse}</span>
            <span class="timeline-badge"><span class="dot" style="background: #ff9800;"></span> ${t.tlExport}</span>
            <span class="timeline-badge"><span class="dot" style="background: rgba(128,128,128,0.4);"></span> ${t.tlHold}</span>
          </div>
        </div>

        <!-- 4 KPI Metrics -->
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

        <!-- Tab Selection (Clean Views) & Zoom 24h -->
        <div class="tabs-row">
          <div class="tab-pills">
            <button class="tab-btn active" data-tab="battery">${t.tabBattery}</button>
            <button class="tab-btn" data-tab="solar">${t.tabSolar}</button>
            <button class="tab-btn" data-tab="prices">${t.tabPrices}</button>
            <button class="tab-btn" data-tab="all">${t.tabAll}</button>
          </div>
          <div class="right-controls">
            <button class="zoom-btn" id="zoomToggleBtn" title="Przełącz widok 24h / 48h">${t.zoomToday}</button>
            <div class="sub-info" id="chartHeaderSubtitle">
              ${t.horizonPrefix}
            </div>
          </div>
        </div>

        <!-- Canvas -->
        <div class="canvas-container" id="canvasBox">
          <canvas id="emsChartCanvas"></canvas>
          <div class="tooltip-box" id="chartTooltip"></div>
        </div>

        <!-- Interactive Legend -->
        <div class="chart-legend" id="chartLegendContainer">
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
          const isVisible = !!this._visibleSeries[key];
          item.classList.toggle('disabled', !isVisible);
          // Show or hide legend item depending on active tab for pristine clean UI
          if (this._viewTab === 'battery') {
            item.style.display = (key === 'charging' || key === 'self_use' || key === 'soc' || key === 'min_soc') ? 'flex' : 'none';
          } else if (this._viewTab === 'solar') {
            item.style.display = (key === 'pv' || key === 'load' || key === 'grid_import' || key === 'export') ? 'flex' : 'none';
          } else if (this._viewTab === 'prices') {
            item.style.display = (key === 'tariff' || key === 'rce' || key === 'charging' || key === 'soc') ? 'flex' : 'none';
          } else {
            item.style.display = 'flex';
          }
        }
      });
    };

    // Tab buttons handler
    this.content.querySelectorAll('.tab-btn').forEach(btn => {
      btn.onclick = (e) => {
        this.content.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        const tab = e.target.getAttribute('data-tab');
        this._applyTabVisibility(tab);
        syncLegendUI();
        this.render();
      };
    });

    // Zoom button handler
    const zoomBtn = this.content.querySelector('#zoomToggleBtn');
    if (zoomBtn) {
      zoomBtn.onclick = () => {
        this._zoomToday = !this._zoomToday;
        zoomBtn.classList.toggle('active', this._zoomToday);
        zoomBtn.textContent = this._zoomToday ? t.zoom48 : t.zoomToday;
        this.render();
      };
    }

    // Individual legend toggle handler
    this.content.querySelectorAll('.legend-item').forEach(item => {
      item.onclick = () => {
        const key = item.getAttribute('data-series');
        if (!key) return;
        this._visibleSeries[key] = !this._visibleSeries[key];
        syncLegendUI();
        this.render();
      };
    });

    // Pointer interactions
    this._canvas.onmousemove = (e) => this._handlePointer(e.offsetX, e.offsetY);
    this._canvas.onmouseleave = () => { this._tooltip.style.display = 'none'; };
    this._canvas.ontouchmove = (e) => {
      const rect = this._canvas.getBoundingClientRect();
      const touch = e.touches[0];
      this._handlePointer(touch.clientX - rect.left, touch.clientY - rect.top);
    };
    this._canvas.ontouchend = () => { this._tooltip.style.display = 'none'; };

    syncLegendUI();
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

      // Align tariff price by timestamp offset
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

  _renderTimeline(points) {
    const bar = this.content.querySelector('#timelineBar');
    if (!bar) return;

    if (!points || points.length === 0) {
      bar.innerHTML = `<div style="width: 100%; text-align: center; font-size: 0.70rem; color: #888; line-height: 22px;">Brak danych harmonogramu</div>`;
      return;
    }

    // Limit to next 24 hours (48 steps of 30 mins)
    const count = Math.min(48, points.length);
    let html = '';

    for (let i = 0; i < count; i++) {
      const p = points[i];
      let color = 'rgba(128, 128, 128, 0.35)'; // Standby / Hold
      let title = 'Standby / Hold';

      if (p.p_batt < -50) {
        color = '#4caf50'; // Charging
        title = `Ładowanie: ${Math.round(Math.abs(p.p_batt))}W`;
      } else if (p.grid < -50 && p.p_batt > 50) {
        color = '#ff9800'; // Export
        title = `Eksport: ${Math.round(Math.abs(p.grid))}W`;
      } else if (p.p_batt > 50) {
        color = '#2196f3'; // Self-use / powering home
        title = `Zasilanie Domu: ${Math.round(p.p_batt)}W`;
      }

      const hours = p.time.getHours().toString().padStart(2, '0');
      const mins = p.time.getMinutes().toString().padStart(2, '0');
      const timeStr = `${hours}:${mins}`;

      html += `<div class="timeline-slot" style="background: ${color};" title="${timeStr} - ${title}"></div>`;
    }

    bar.innerHTML = html;
  }

  render() {
    if (!this._canvas || !this._hass) return;

    const { dataPoints, dynamicMinSoc, hasData, tariffMode, currentSellPrice } = this._extractData();
    this._dataPoints = dataPoints;
    this._tariffMode = tariffMode;

    let displayPoints = dataPoints;
    if (this._zoomToday && dataPoints.length > 0) {
      // Rolling 24 hours from now (exactly 48 steps of 30 mins)
      displayPoints = dataPoints.slice(0, 48);
    }

    const t = this._t();
    const curr = this._currency();
    const subtitle = this.content.querySelector('#chartHeaderSubtitle');
    if (subtitle) {
      let subText = this._zoomToday ? t.horizonPrefix24 : t.horizonPrefix;
      if (currentSellPrice !== undefined && currentSellPrice !== null) {
        subText += ` | ${t.sellNow}: ${parseFloat(currentSellPrice).toFixed(2)} ${curr}`;
      }
      subtitle.textContent = subText;
    }

    const kpiCharge = this.content.querySelector('#kpiCharge');
    const kpiDischarge = this.content.querySelector('#kpiDischarge');
    const kpiSolar = this.content.querySelector('#kpiSolar');
    const kpiMinSoc = this.content.querySelector('#kpiMinSoc');

    if (kpiMinSoc) kpiMinSoc.textContent = `${dynamicMinSoc.toFixed(0)} %`;

    if (hasData) {
      let totalChargeKwh = 0;
      let totalDischargeKwh = 0;
      let totalSolarKwh = 0;

      displayPoints.forEach(p => {
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

    // Render Timeline Bar (GbbOptimizer-style 24h view)
    this._renderTimeline(dataPoints);

    // Render Canvas
    this._drawChart(displayPoints, dynamicMinSoc, hasData);
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
    const padTop = 22;
    const padBottom = 28;
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
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.12)';
    ctx.lineWidth = 1;

    // Zero Line
    const yZero = getYPower(0);
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.35)';
    ctx.moveTo(padLeft, yZero);
    ctx.lineTo(padLeft + plotW, yZero);
    ctx.stroke();

    // Horizontal power grid steps
    const stepCount = 4;
    ctx.fillStyle = 'rgba(128, 128, 128, 0.75)';
    ctx.font = '10px -apple-system, sans-serif';
    ctx.textAlign = 'right';

    for (let i = 0; i <= stepCount; i++) {
      const pVal = minPower + (i / stepCount) * powerRange;
      const yVal = getYPower(pVal);
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(128, 128, 128, 0.08)';
      ctx.moveTo(padLeft, yVal);
      ctx.lineTo(padLeft + plotW, yVal);
      ctx.stroke();
      ctx.fillText(`${Math.round(pVal)}W`, padLeft - 6, yVal + 3);
    }

    // Right SoC Axis Labels
    if (this._visibleSeries.soc) {
      ctx.textAlign = 'left';
      [0, 25, 50, 75, 100].forEach(soc => {
        const ySoc = getYSoc(soc);
        ctx.fillText(`${soc}%`, padLeft + plotW + 6, ySoc + 3);
      });
    }

    const vis = this._visibleSeries;

    // 1B. Draw Tariff / Prices if active
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

      // Stepped tariff buy line
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

      // Stepped RCE sell price line
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
      }
    }

    // 2. Draw Battery Power Areas
    if (vis.charging || vis.self_use || vis.export) {
      const stepW = points.length > 1 ? plotW / (points.length - 1) : plotW;

      points.forEach((p, idx) => {
        const x = getX(idx);
        const pVal = p.p_batt;
        const halfStep = stepW / 2;
        const xLeft = Math.max(padLeft, x - halfStep);
        const xRight = Math.min(padLeft + plotW, x + halfStep);
        const wSeg = xRight - xLeft;

        if (Math.abs(pVal) > 20) {
          if (pVal < -20 && vis.charging) {
            ctx.fillStyle = 'rgba(76, 175, 80, 0.40)';
            const yTop = yZero;
            const yBottom = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yBottom - yTop);
          } else if (p.grid < -50 && pVal > 50 && vis.export) {
            ctx.fillStyle = 'rgba(255, 152, 0, 0.45)';
            const yTop = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yZero - yTop);
          } else if (pVal > 20 && !(p.grid < -50 && pVal > 50) && vis.self_use) {
            ctx.fillStyle = 'rgba(33, 150, 243, 0.40)';
            const yTop = getYPower(pVal);
            ctx.fillRect(xLeft, yTop, wSeg, yZero - yTop);
          }
        }
      });
    }

    // 2B. Grid Import Curve
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

    // 3. Solar & Load Curves
    if (vis.pv) {
      ctx.strokeStyle = '#fbc02d';
      ctx.lineWidth = 2.2;
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
      ctx.strokeStyle = '#90a4ae';
      ctx.lineWidth = 1.6;
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

    // 4. Dynamic Min SoC Reference Line
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

    // 5. SoC Trajectory Line (Glowing Pink)
    if (vis.soc) {
      ctx.strokeStyle = '#e91e63';
      ctx.lineWidth = 2.8;
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
    ctx.fillStyle = 'rgba(128, 128, 128, 0.85)';
    ctx.font = '10px -apple-system, sans-serif';
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
  description: 'Clean high-performance chart with a 24h visual timeline and dedicated views for battery, solar, and prices.'
});
