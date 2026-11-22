/**
 * Smart Storage EMS - Custom Autodiagnostic Dashboard Card
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

const DIAG_I18N = {
  pl: {
    card_title: 'Smart Storage EMS: Autodiagnostyka',
    waiting_title: 'Oczekiwanie na encję diagnostyczną...',
    not_found: 'Nie odnaleziono:',
    no_data: 'Brak danych',
    unknown: 'Nieznany',
    none: 'Brak',
    no_data_or_error: 'Brak danych / Błąd',
    system_healthy: 'System w 100% sprawny',
    tab_health: 'Sensory i Falownik',
    tab_emhass: 'Wektory 48h i Solver',
    tab_logs: 'Decyzje i Logi',
    status_label: 'Status:',
    btn_recalc: 'Przelicz MPC',
    btn_recalc_running: 'Przeliczam...',
    btn_report: 'Raport JSON',
    kpi_emhass: 'EMHASS MPC',
    kpi_tariff: 'Aktywna Taryfa',
    kpi_min_soc: 'Dynamiczny Min SoC',
    vector_prefix: 'Wektor:',
    samples: 'próbek',
    sec_sensors: 'Integralność i Jednostki Sensorów',
    col_sensor: 'Sensor',
    col_value: 'Wartość',
    col_status: 'Status',
    sec_inverter: 'Odczyt Zwrotny Falownika (Home Assistant)',
    steps_48h: 'kroków (48h)',
    stat_min: 'MIN',
    stat_avg: 'ŚREDNIA',
    stat_max: 'MAX',
    emhass_err_title: '⚠️ Ostatni Błąd Komunikacji z EMHASS:',
    conn_err: 'Błąd połączenia',
    err_status: 'Status:',
    err_time: 'Czas:',
    emhass_ok: '✓ Komunikacja z EMHASS bez zakłóceń. Brak zarejestrowanych błędów HTTP.',
    vectors_heading: 'Krzywe Wejściowe Wysłane do Solvera (Horyzont 48h):',
    vec_load: 'Prognoza Zużycia Domu',
    vec_buy: 'Ceny Zakupu Energii (Taryfa)',
    vec_pv: 'Prognoza Produkcji PV',
    vec_sell: 'Wycena Sprzedaży (PSE RCE)',
    no_decisions: 'Brak zarejestrowanych decyzji po starcie.',
    no_logs: 'Brak komunikatów diagnostycznych w buforze RAM.',
    sec_decisions: 'Ostatnie Decyzje Sterujące EMS',
    sec_logs: 'Konsola Logów na Żywo (Bufor RAM)',
    sort_newest: 'Najnowsze u góry',
    sort_oldest: 'Najstarsze u góry',
    issues_detected: (n) => `Wykryto ${n} uwag`
  },
  en: {
    card_title: 'Smart Storage EMS: Autodiagnostics',
    waiting_title: 'Waiting for diagnostic entity...',
    not_found: 'Not found:',
    no_data: 'No data',
    unknown: 'Unknown',
    none: 'None',
    no_data_or_error: 'No data / Error',
    system_healthy: 'System 100% healthy',
    tab_health: 'Sensors & Inverter',
    tab_emhass: '48h Vectors & Solver',
    tab_logs: 'Decisions & Logs',
    status_label: 'Status:',
    btn_recalc: 'Run MPC Now',
    btn_recalc_running: 'Running...',
    btn_report: 'JSON Report',
    kpi_emhass: 'EMHASS MPC',
    kpi_tariff: 'Active Tariff',
    kpi_min_soc: 'Dynamic Min SoC',
    vector_prefix: 'Vector:',
    samples: 'samples',
    sec_sensors: 'Sensor Integrity & Units',
    col_sensor: 'Sensor',
    col_value: 'Value',
    col_status: 'Status',
    sec_inverter: 'Inverter Readback (Home Assistant)',
    steps_48h: 'steps (48h)',
    stat_min: 'MIN',
    stat_avg: 'AVG',
    stat_max: 'MAX',
    emhass_err_title: '⚠️ Last EMHASS Communication Error:',
    conn_err: 'Connection error',
    err_status: 'Status:',
    err_time: 'Time:',
    emhass_ok: '✓ EMHASS communication healthy. No HTTP errors recorded.',
    vectors_heading: 'Input Curves Sent to Solver (48h Horizon):',
    vec_load: 'Home Load Forecast',
    vec_buy: 'Grid Buy Prices (Tariff)',
    vec_pv: 'PV Production Forecast',
    vec_sell: 'Grid Export Prices',
    no_decisions: 'No control decisions recorded since startup.',
    no_logs: 'No diagnostic log entries in RAM buffer.',
    sec_decisions: 'Recent EMS Control Decisions',
    sec_logs: 'Live Log Console (RAM Buffer)',
    sort_newest: 'Newest first',
    sort_oldest: 'Oldest first',
    issues_detected: (n) => `${n} ${n === 1 ? 'issue' : 'issues'} detected`
  }
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

class SmartStorageDiagnosticCard extends HTMLElement {
  constructor() {
    super();
    this._activeTab = 'health';
  }

  _lang() {
    const raw = (this._hass?.locale?.language || this._hass?.language || 'en').toLowerCase();
    return raw.startsWith('pl') ? 'pl' : 'en';
  }

  _t(key, ...args) {
    const lang = this._lang();
    const val = DIAG_I18N[lang][key] ?? DIAG_I18N.en[key] ?? key;
    return typeof val === 'function' ? val(...args) : val;
  }

  _currency() {
    return this._hass?.config?.currency || 'PLN';
  }

  _translateLabel(label) {
    if (!label || this._lang() === 'pl') return label;
    const map = {
      'SoC Baterii': 'Battery SoC',
      'Moc PV': 'PV Power',
      'Moc Domu': 'House Load Power',
      'Import z Sieci': 'Grid Import',
      'Moc Baterii': 'Battery Power',
      'Temperatura Zewnętrzna': 'Outside Temperature',
      'Sensor Off-Grid': 'Off-Grid Sensor',
      'Prognoza PV (wektor)': 'PV Forecast (vector)',
      'Prognoza Zużycia (wektor)': 'Load Forecast (vector)',
      'Ceny Zakupu': 'Buy Prices',
      'Ceny Sprzedaży': 'Sell Prices',
      'Energia PV Dziś': 'PV Energy Today',
      'Energia PV Jutro': 'PV Energy Tomorrow',
      'Tryb EMS': 'EMS Mode',
      'Tryb Inwertera': 'Inverter Mode',
      'Limit Mocy EMS': 'EMS Power Limit',
      'Limit Eksportu': 'Export Limit'
    };
    return map[label] || label;
  }

  _translateIssue(issue) {
    if (!issue || this._lang() === 'pl') return issue;
    return String(issue)
      .replace(/^Encja sterująca (.+) nie istnieje w Home Assistant!$/, 'Control entity $1 does not exist in Home Assistant!')
      .replace(/^Encja (.+) nie istnieje w Home Assistant!$/, 'Entity $1 does not exist in Home Assistant!')
      .replace(/^Encja w stanie niedostępnym \((.+)\)$/, 'Entity is in unavailable state ($1)')
      .replace(/^Wykryto niezgodność jednostki! Oczekiwano 'W', encja raportuje '([^']+)' \(skala 1000x\)$/, "Unit mismatch detected! Expected 'W', entity reports '$1' (1000x scale)")
      .replace(/^Encja istnieje, ale brakuje atrybutu '([^']+)'!$/, "Entity exists, but attribute '$1' is missing!")
      .replace(/^Atrybut '([^']+)' ma tylko (\d+) próbek \(oczekiwano min\. 24\/48\)!$/, "Attribute '$1' has only $2 samples (expected min. 24/48)!");
  }

  _translateBackendText(text) {
    if (!text || this._lang() === 'pl') return text;
    const exact = {
      'Inicjalizacja': 'Initializing',
      'Inicjalizacja / Oczekiwanie na MPC': 'Initializing / Waiting for MPC',
      'Trwa optymalizacja MPC (EMHASS)...': 'MPC optimization in progress (EMHASS)...',
      'Błąd połączenia / optymalizacji EMHASS': 'EMHASS connection / optimization error',
      'Zabezpieczenie Off-Grid (Pauza)': 'Off-Grid Protection (Paused)',
      'Ręczny Standby (Hold)': 'Manual Standby (Hold)',
      'Ręczne Wymuszone Ładowanie': 'Manual Forced Charge',
      'Czysta Autokonsumpcja': 'Pure Self-Consumption',
      'Ochrona Rezerwy (Standby)': 'Reserve Protection (Standby)',
      'Oszczędzanie Baterii (Standby)': 'Battery Preservation (Standby)',
      'Autokonsumpcja (Auto)': 'Self-Consumption (Auto)',
      'Strażnik Importu (Wymuszono Auto)': 'Import Guard (Forced Auto)',
      'Tryb Ręczny': 'Manual Mode',
      'Autokonsumpcja PV': 'PV Self-Consumption',
      'Arbitraż RCE': 'Export Arbitrage',
      'Ochrona Rezerwy': 'Reserve Protection',
      'Autokonsumpcja': 'Self-Consumption',
      'Strażnik Importu': 'Import Guard',
      'Pauza': 'Paused',
      'Wymuszone Ładowanie (3000W)': 'Forced Charge (3000W)',
      'Standby (Zamrożenie)': 'Standby (Hold)',
      'Wymuszono Auto': 'Forced Auto',
      'Wykryto pracę wyspową / off-grid': 'Island / off-grid mode detected',
      'Użytkownik wybrał tryb hold_standby': 'User selected hold_standby mode',
      'Użytkownik wybrał tryb force_charge': 'User selected force_charge mode',
      'Użytkownik wybrał tryb self_use (Bypass EMS)': 'User selected self_use mode (EMS Bypass)',
      'Plan EMHASS w taniej dolinie cenowej': 'EMHASS plan in cheap price valley',
      'EMHASS żądał importu w drogiej strefie taryfowej. Zablokowano ładowanie z sieci.': 'EMHASS requested grid import during peak tariff zone. Grid charging blocked.',
      'Ładowanie darmową energią ze słońca (p_grid <= 50W)': 'Charging with free solar energy (p_grid <= 50W)',
      'Planowana sprzedaż energii w szczycie cenowym RCE': 'Planned energy export during peak feed-in price',
      'Tania strefa cenowa i plan EMHASS 0W – zachowanie energii w baterii na szczyt cenowy.': 'Cheap tariff zone and EMHASS 0W plan – preserving battery energy for peak zone.',
      'Normalne pokrywanie potrzeb domu ze słońca i baterii': 'Normal home load balancing from solar and battery'
    };
    if (exact[text]) return exact[text];
    return String(text)
      .replace(/^Ładowanie z sieci \((\d+W)\)$/, 'Grid Charging ($1)')
      .replace(/^Blokada Szczytu Cenowego \(Auto (\d+W)\)$/, 'Price Peak Blocked (Auto $1)')
      .replace(/^Ładowanie z PV \(Auto (\d+W)\)$/, 'PV Charging (Auto $1)')
      .replace(/^Eksport na sieć \((\d+W)\)$/, 'Grid Export ($1)')
      .replace(/^SoC \(([^)]+)\) <= Min SoC \(([^)]+)\)\. Zabezpieczenie rezerwy\.$/, 'SoC ($1) <= Min SoC ($2). Reserve protection active.')
      .replace(/^Import z sieci \(([^)]+)\) przekroczył próg \(([^)]+)\) przy baterii ([^%]+%)\. Wymuszenie autokonsumpcji\.$/, 'Grid import ($1) exceeded threshold ($2) at $3 battery. Enforcing self-consumption.');
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      const card = document.createElement('ha-card');
      this._card = card;
      card.header = this.config?.title || this._t('card_title');
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    } else if (this._card && !this.config?.title) {
      this._card.header = this._t('card_title');
    }
    this.updateCard();
  }

  setConfig(config) {
    this.config = config || {};
    if (this._card) {
      this._card.header = this.config?.title || this._t('card_title');
    }
  }

  getCardSize() {
    return 6;
  }

  _resolveEntity(configKey, candidates) {
    if (this.config && this.config[configKey]) {
      return this.config[configKey];
    }
    if (!this._hass) return candidates[0];
    for (const id of candidates) {
      if (this._hass.states[id]) {
        return id;
      }
    }
    return candidates[0];
  }

  _downloadJson(data, filename = 'smart_storage_diagnostics.json') {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  updateCard() {
    if (!this._hass || !this.content) return;

    const logConsole = this.content.querySelector('#log-console');
    const prevScrollTop = logConsole ? logConsole.scrollTop : (this._savedLogScrollTop || 0);

    const lang = this._lang();
    const currency = this._currency();

    const diagEntityId = this._resolveEntity('diagnostic_sensor', [
      'sensor.smart_storage_ems_diagnostyka',
      'sensor.smart_storage_ems_diagnostics'
    ]);
    const diagState = this._hass.states[diagEntityId];

    if (!diagState) {
      this.content.innerHTML = `
        <div style="padding: 16px; text-align: center; color: var(--secondary-text-color);">
          <ha-icon icon="mdi:alert-circle-outline" style="color: var(--warning-color); --mdc-icon-size: 40px;"></ha-icon>
          <div style="margin-top: 8px; font-weight: bold;">${escapeHtml(this._t('waiting_title'))}</div>
          <div style="font-size: 0.85em; opacity: 0.8;">${escapeHtml(this._t('not_found'))} ${escapeHtml(diagEntityId)}</div>
        </div>
      `;
      return;
    }

    const attrs = diagState.attributes || {};
    const entitiesHealth = attrs.entities_health || {};
    const inverterReadback = attrs.odczyt_falownika || {};
    const recentDecisions = attrs.ostatnie_decyzje || [];
    const recentLogs = attrs.recent_logs || [];
    const emhassSummary = attrs.emhass_summary || {};
    const emhassError = attrs.blad_emhass;
    const tariffMode = attrs.taryfa || this._t('no_data');
    const dynMinSoc = attrs.dynamiczny_min_soc !== undefined ? attrs.dynamiczny_min_soc + '%' : '--';
    const rawEmhassStatus = attrs.status_emhass;
    const emhassStatus = !rawEmhassStatus
      ? this._t('unknown')
      : (rawEmhassStatus === 'Brak danych / Błąd' && lang !== 'pl' ? this._t('no_data_or_error') : rawEmhassStatus);
    const timeLocale = lang === 'pl' ? 'pl-PL' : 'en-GB';
    const lastMpc = attrs.ostatnie_przeliczenie_mpc ? new Date(attrs.ostatnie_przeliczenie_mpc).toLocaleTimeString(timeLocale) : this._t('none');

    // Count issues
    let errorCount = 0;
    Object.values(entitiesHealth).forEach(e => {
      if (e.issue) errorCount++;
    });
    if (emhassError) errorCount++;

    const statusBadgeColor = errorCount > 0 ? 'var(--error-color, #e53935)' : 'var(--success-color, #43a047)';
    const statusBadgeText = errorCount > 0 ? this._t('issues_detected', errorCount) : this._t('system_healthy');

    // Tabs HTML
    const tabsHtml = `
      <div style="display: flex; gap: 8px; border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.1)); margin-bottom: 16px; padding-bottom: 8px;">
        <button id="tab-health" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'health' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'health' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          ${this._t('tab_health')}
        </button>
        <button id="tab-emhass" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'emhass' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'emhass' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          ${this._t('tab_emhass')}
        </button>
        <button id="tab-logs" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'logs' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'logs' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          ${this._t('tab_logs')} (${recentLogs.length})
        </button>
      </div>
    `;

    // Overview Header
    const overviewHtml = `
      <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; padding: 12px; background: rgba(127,127,127,0.06); border-radius: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <ha-icon icon="${errorCount > 0 ? 'mdi:alert-circle' : 'mdi:check-circle'}" style="color: ${statusBadgeColor}; --mdc-icon-size: 28px;"></ha-icon>
          <div>
            <div style="font-weight: bold; font-size: 1em;">${escapeHtml(statusBadgeText)}</div>
            <div style="font-size: 0.85em; opacity: 0.8;">${escapeHtml(this._t('status_label'))} ${escapeHtml(this._translateBackendText(diagState.state))}</div>
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button id="btn-opt" style="padding: 6px 12px; background: rgba(127,127,127,0.15); border: 1px solid rgba(127,127,127,0.25); border-radius: 6px; cursor: pointer; font-size: 0.85em; color: inherit; display: flex; align-items: center; gap: 4px;">
            <ha-icon icon="mdi:calculator-variant" style="--mdc-icon-size: 16px;"></ha-icon> ${escapeHtml(this._t('btn_recalc'))}
          </button>
          <button id="btn-download" style="padding: 6px 12px; background: var(--primary-color, #03a9f4); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: bold; display: flex; align-items: center; gap: 4px;">
            <ha-icon icon="mdi:download" style="--mdc-icon-size: 16px;"></ha-icon> ${escapeHtml(this._t('btn_report'))}
          </button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-bottom: 16px;">
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">${escapeHtml(this._t('kpi_emhass'))}</div>
          <div style="font-weight: bold; color: ${emhassStatus === 'OK' ? 'var(--success-color, #43a047)' : 'var(--error-color, #e53935)'}; font-size: 0.95em;">${escapeHtml(emhassStatus)} (${escapeHtml(lastMpc)})</div>
        </div>
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">${escapeHtml(this._t('kpi_tariff'))}</div>
          <div style="font-weight: bold; font-size: 0.95em; text-transform: uppercase;">${escapeHtml(tariffMode)}</div>
        </div>
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">${escapeHtml(this._t('kpi_min_soc'))}</div>
          <div style="font-weight: bold; font-size: 0.95em;">${escapeHtml(dynMinSoc)}</div>
        </div>
      </div>
    `;

    // Tab 1 Content: Health & Inverter
    let tabContentHtml = '';
    if (this._activeTab === 'health') {
      let rowsHtml = '';
      Object.entries(entitiesHealth).forEach(([entId, data]) => {
        const isOk = !data.issue;
        const iconColor = isOk ? 'var(--success-color, #43a047)' : 'var(--error-color, #e53935)';
        const iconName = isOk ? 'mdi:check-circle-outline' : 'mdi:alert-circle';
        const rawAttrInfo = data.raw_attribute
          ? `<div style="font-size: 0.75em; opacity: 0.8; color: var(--primary-color);">${escapeHtml(this._t('vector_prefix'))} ${escapeHtml(data.raw_attribute.count)} ${escapeHtml(this._t('samples'))} (min: ${escapeHtml(data.raw_attribute.min)}, max: ${escapeHtml(data.raw_attribute.max)})</div>`
          : '';
        const issueAlert = data.issue
          ? `<div style="font-size: 0.8em; color: var(--error-color, #e53935); font-weight: bold; margin-top: 2px;">⚠️ ${escapeHtml(this._translateIssue(data.issue))}</div>`
          : '';

        rowsHtml += `
          <tr style="border-bottom: 1px solid rgba(127,127,127,0.08);">
            <td style="padding: 6px 4px; vertical-align: top;">
              <div style="font-weight: 500; font-size: 0.9em;">${escapeHtml(this._translateLabel(data.label || entId))}</div>
              <div style="font-size: 0.75em; opacity: 0.6; word-break: break-all;">${escapeHtml(entId)}</div>
              ${rawAttrInfo}
              ${issueAlert}
            </td>
            <td style="padding: 6px 4px; text-align: right; vertical-align: top; font-weight: bold; font-size: 0.9em;">
              ${escapeHtml(data.state !== null && data.state !== undefined ? data.state : '--')} ${escapeHtml(data.unit || '')}
            </td>
            <td style="padding: 6px 4px; text-align: center; vertical-align: top; width: 36px;">
              <ha-icon icon="${iconName}" style="color: ${iconColor}; --mdc-icon-size: 20px;"></ha-icon>
            </td>
          </tr>
        `;
      });

      // Inverter section
      let inverterHtml = '';
      Object.entries(inverterReadback).forEach(([label, state]) => {
        inverterHtml += `
          <div style="display: flex; justify-content: space-between; padding: 6px 8px; background: rgba(127,127,127,0.04); border-radius: 4px; font-size: 0.85em;">
            <span style="opacity: 0.8;">${escapeHtml(this._translateLabel(label))}:</span>
            <span style="font-weight: bold;">${escapeHtml(state)}</span>
          </div>
        `;
      });

      tabContentHtml = `
        <div style="margin-bottom: 16px;">
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:server-network" style="--mdc-icon-size: 18px;"></ha-icon> ${this._t('sec_sensors')}
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
            <thead>
              <tr style="border-bottom: 1px solid rgba(127,127,127,0.2); font-size: 0.8em; opacity: 0.7; text-align: left;">
                <th style="padding: 4px;">${this._t('col_sensor')}</th>
                <th style="padding: 4px; text-align: right;">${this._t('col_value')}</th>
                <th style="padding: 4px; text-align: center;">${this._t('col_status')}</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>

        <div>
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:solar-power" style="--mdc-icon-size: 18px;"></ha-icon> ${this._t('sec_inverter')}
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px;">
            ${inverterHtml}
          </div>
        </div>
      `;
    }

    // Tab 2 Content: EMHASS & 48h Vectors
    else if (this._activeTab === 'emhass') {
      const renderVectorCard = (title, stats, unit, icon) => {
        if (!stats) return '';
        return `
          <div style="padding: 10px; background: rgba(127,127,127,0.05); border-radius: 6px; border: 1px solid rgba(127,127,127,0.1);">
            <div style="display: flex; align-items: center; gap: 6px; font-weight: bold; font-size: 0.85em; margin-bottom: 6px;">
              <ha-icon icon="${icon}" style="--mdc-icon-size: 16px; color: var(--primary-color);"></ha-icon> ${escapeHtml(title)}
              <span style="font-size: 0.8em; opacity: 0.6; margin-left: auto;">${escapeHtml(stats.count)} ${escapeHtml(this._t('steps_48h'))}</span>
            </div>
            <div style="display: flex; justify-content: space-around; text-align: center; font-size: 0.85em;">
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">${escapeHtml(this._t('stat_min'))}</div>
                <div style="font-weight: bold;">${escapeHtml(stats.min)} ${escapeHtml(unit)}</div>
              </div>
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">${escapeHtml(this._t('stat_avg'))}</div>
                <div style="font-weight: bold; color: var(--primary-color);">${escapeHtml(stats.avg)} ${escapeHtml(unit)}</div>
              </div>
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">${escapeHtml(this._t('stat_max'))}</div>
                <div style="font-weight: bold;">${escapeHtml(stats.max)} ${escapeHtml(unit)}</div>
              </div>
            </div>
          </div>
        `;
      };

      const errBlock = emhassError ? `
        <div style="padding: 10px; background: rgba(229, 57, 53, 0.1); border-left: 4px solid var(--error-color, #e53935); border-radius: 4px; margin-bottom: 12px; font-size: 0.85em;">
          <div style="font-weight: bold; color: var(--error-color, #e53935); margin-bottom: 4px;">${escapeHtml(this._t('emhass_err_title'))}</div>
          <div style="opacity: 0.9;"><strong>${escapeHtml(this._t('err_status'))}</strong> ${escapeHtml(emhassError.status || this._t('conn_err'))} (${escapeHtml(emhassError.action || 'MPC')})</div>
          <div style="font-family: monospace; font-size: 0.8em; margin-top: 4px; word-break: break-all; opacity: 0.85;">${escapeHtml(emhassError.error || emhassError.message || '')}</div>
          <div style="font-size: 0.75em; opacity: 0.6; margin-top: 4px;">${escapeHtml(this._t('err_time'))} ${escapeHtml(emhassError.timestamp)}</div>
        </div>
      ` : `
        <div style="padding: 8px 12px; background: rgba(67, 160, 71, 0.08); border-left: 4px solid var(--success-color, #43a047); border-radius: 4px; margin-bottom: 12px; font-size: 0.85em; color: var(--success-color, #43a047); font-weight: 500;">
          ${escapeHtml(this._t('emhass_ok'))}
        </div>
      `;

      tabContentHtml = `
        ${errBlock}
        <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px;">${this._t('vectors_heading')}</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${renderVectorCard(this._t('vec_load'), emhassSummary.load_forecast_stats, 'W', 'mdi:home-lightning-bolt')}
          ${renderVectorCard(this._t('vec_buy'), emhassSummary.buy_price_stats, currency, 'mdi:cash-fast')}
          ${renderVectorCard(this._t('vec_pv'), emhassSummary.pv_forecast_stats, 'W', 'mdi:solar-power-variant')}
          ${renderVectorCard(this._t('vec_sell'), emhassSummary.sell_price_stats, currency, 'mdi:transmission-tower')}
        </div>
      `;
    }

    // Tab 3 Content: Logs & Decisions
    else if (this._activeTab === 'logs') {
      let decisionsHtml = '';
      if (recentDecisions.length === 0) {
        decisionsHtml = `<div style="font-size: 0.85em; opacity: 0.6;">${escapeHtml(this._t('no_decisions'))}</div>`;
      } else {
        recentDecisions.slice(-6).reverse().forEach(d => {
          decisionsHtml += `
            <div style="padding: 6px 8px; border-left: 3px solid var(--primary-color); background: rgba(127,127,127,0.04); border-radius: 0 4px 4px 0; font-size: 0.85em; margin-bottom: 6px;">
              <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 2px;">
                <span>${escapeHtml(this._translateBackendText(d.trigger))} → ${escapeHtml(this._translateBackendText(d.action))}</span>
                <span style="font-size: 0.8em; opacity: 0.6;">${escapeHtml(d.timestamp ? d.timestamp.split(' ')[1] : '')}</span>
              </div>
              <div style="font-size: 0.8em; opacity: 0.85;">${escapeHtml(this._translateBackendText(d.reason))}</div>
            </div>
          `;
        });
      }

      const isNewestFirst = this._logSortNewest !== false;
      const displayLogs = isNewestFirst ? [...recentLogs].reverse() : [...recentLogs];

      let logsHtml = '';
      if (displayLogs.length === 0) {
        logsHtml = `<div style="color: #888;">${escapeHtml(this._t('no_logs'))}</div>`;
      } else {
        displayLogs.forEach(l => {
          let lvlColor = '#81c784'; // INFO
          if (l.level === 'WARNING') lvlColor = '#ffb74d';
          if (l.level === 'ERROR') lvlColor = '#e57373';
          logsHtml += `
            <div style="margin-bottom: 4px; word-break: break-all;">
              <span style="color: #888;">[${escapeHtml(l.timestamp ? l.timestamp.split(' ')[1] : '')}]</span>
              <span style="color: ${lvlColor}; font-weight: bold;">[${escapeHtml(l.level)}]</span>
              <span style="color: #64b5f6;">[${escapeHtml(l.logger)}]</span>
              <span style="color: #eee;">${escapeHtml(l.message)}</span>
            </div>
          `;
        });
      }

      const sortBtnLabel = isNewestFirst ? this._t('sort_newest') : this._t('sort_oldest');
      const sortIcon = isNewestFirst ? 'mdi:sort-clock-descending-outline' : 'mdi:sort-clock-ascending-outline';

      tabContentHtml = `
        <div style="margin-bottom: 16px;">
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:history" style="--mdc-icon-size: 18px;"></ha-icon> ${this._t('sec_decisions')}
          </div>
          <div>${decisionsHtml}</div>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: bold; font-size: 0.95em; display: flex; align-items: center; gap: 6px;">
              <ha-icon icon="mdi:console" style="--mdc-icon-size: 18px;"></ha-icon> ${this._t('sec_logs')}
            </div>
            <button id="btn-toggle-sort" style="background: rgba(127,127,127,0.15); border: 1px solid rgba(127,127,127,0.25); border-radius: 4px; padding: 3px 8px; font-size: 0.78em; cursor: pointer; color: inherit; display: flex; align-items: center; gap: 4px;">
              <ha-icon icon="${sortIcon}" style="--mdc-icon-size: 14px;"></ha-icon>
              <span>${escapeHtml(sortBtnLabel)}</span>
            </button>
          </div>
          <div id="log-console" style="background: #181818; color: #eee; padding: 10px; border-radius: 6px; font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 0.78em; max-height: 240px; overflow-y: auto; line-height: 1.4; border: 1px solid rgba(255,255,255,0.1);">
            ${logsHtml}
          </div>
        </div>
      `;
    }

    // Render full HTML
    this.content.innerHTML = `
      ${overviewHtml}
      ${tabsHtml}
      ${tabContentHtml}
    `;

    // Restore and track scroll position for log console
    const newLogConsole = this.content.querySelector('#log-console');
    if (newLogConsole) {
      newLogConsole.scrollTop = prevScrollTop;
      newLogConsole.onscroll = () => {
        this._savedLogScrollTop = newLogConsole.scrollTop;
      };
    }

    const btnToggleSort = this.content.querySelector('#btn-toggle-sort');
    if (btnToggleSort) {
      btnToggleSort.onclick = () => {
        this._logSortNewest = !(this._logSortNewest !== false);
        this._savedLogScrollTop = 0;
        this.updateCard();
      };
    }

    // Bind Tab Click Handlers
    const tabHealth = this.content.querySelector('#tab-health');
    const tabEmhass = this.content.querySelector('#tab-emhass');
    const tabLogs = this.content.querySelector('#tab-logs');

    if (tabHealth) tabHealth.onclick = () => { this._activeTab = 'health'; this.updateCard(); };
    if (tabEmhass) tabEmhass.onclick = () => { this._activeTab = 'emhass'; this.updateCard(); };
    if (tabLogs) tabLogs.onclick = () => { this._activeTab = 'logs'; this.updateCard(); };

    // Bind Action Buttons
    const btnOpt = this.content.querySelector('#btn-opt');
    if (btnOpt) {
      btnOpt.onclick = () => {
        btnOpt.textContent = this._t('btn_recalc_running');
        const optBtnId = this._resolveEntity('optimize_now', [
          'button.smart_storage_ems_przelicz_mpc_teraz',
          'button.smart_storage_ems_optimize_now'
        ]);
        this._hass.callService('button', 'press', { entity_id: optBtnId });
        setTimeout(() => { btnOpt.innerHTML = `<ha-icon icon="mdi:calculator-variant" style="--mdc-icon-size: 16px;"></ha-icon> ${this._t('btn_recalc')}`; }, 2500);
      };
    }

    const btnDownload = this.content.querySelector('#btn-download');
    if (btnDownload) {
      btnDownload.onclick = () => {
        // Collect entire diagnostic payload available from attributes & coordinator
        const fullReport = {
          timestamp: new Date().toISOString(),
          state: diagState.state,
          attributes: attrs
        };
        this._downloadJson(fullReport, `ems_diagnostics_${new Date().toISOString().slice(0,10)}.json`);
      };
    }
  }
}

customElements.define('smart-storage-diagnostic-card', SmartStorageDiagnosticCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'smart-storage-diagnostic-card',
  name: 'Smart Storage EMS: Autodiagnostics',
  description: 'Interactive autodiagnostic dashboard inspecting sensors, units, inverter readback, EMHASS solver vectors, and live logs.'
});
