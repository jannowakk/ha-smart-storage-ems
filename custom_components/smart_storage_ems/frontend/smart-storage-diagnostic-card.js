/**
 * Smart Storage EMS - Custom Autodiagnostic Dashboard Card
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

class SmartStorageDiagnosticCard extends HTMLElement {
  constructor() {
    super();
    this._activeTab = 'health';
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = this.config?.title || 'Smart Storage EMS: Autodiagnostyka';
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    }
    this.updateCard();
  }

  setConfig(config) {
    this.config = config || {};
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

    const diagEntityId = this._resolveEntity('diagnostic_sensor', [
      'sensor.smart_storage_ems_diagnostyka',
      'sensor.smart_storage_ems_diagnostics'
    ]);
    const diagState = this._hass.states[diagEntityId];

    if (!diagState) {
      this.content.innerHTML = `
        <div style="padding: 16px; text-align: center; color: var(--secondary-text-color);">
          <ha-icon icon="mdi:alert-circle-outline" style="color: var(--warning-color); --mdc-icon-size: 40px;"></ha-icon>
          <div style="margin-top: 8px; font-weight: bold;">Oczekiwanie na encję diagnostyczną...</div>
          <div style="font-size: 0.85em; opacity: 0.8;">Nie odnaleziono: ${diagEntityId}</div>
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
    const tariffMode = attrs.taryfa || 'Brak danych';
    const dynMinSoc = attrs.dynamiczny_min_soc !== undefined ? attrs.dynamiczny_min_soc + '%' : '--';
    const emhassStatus = attrs.status_emhass || 'Nieznany';
    const lastMpc = attrs.ostatnie_przeliczenie_mpc ? new Date(attrs.ostatnie_przeliczenie_mpc).toLocaleTimeString('pl-PL') : 'Brak';
    const issues = attrs.problemy_encji || [];
    const hasIssues = Array.isArray(issues) ? issues.length > 0 : (issues !== 'Brak uwag (Wszystkie encje OK)');

    // Count issues
    let errorCount = 0;
    Object.values(entitiesHealth).forEach(e => {
      if (e.issue) errorCount++;
    });
    if (emhassError) errorCount++;

    const statusBadgeColor = errorCount > 0 ? 'var(--error-color, #e53935)' : 'var(--success-color, #43a047)';
    const statusBadgeText = errorCount > 0 ? `Wykryto ${errorCount} uwag` : 'System w 100% sprawny';

    // Tabs HTML
    const tabsHtml = `
      <div style="display: flex; gap: 8px; border-bottom: 1px solid var(--divider-color, rgba(255,255,255,0.1)); margin-bottom: 16px; padding-bottom: 8px;">
        <button id="tab-health" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'health' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'health' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          Sensory i Falownik
        </button>
        <button id="tab-emhass" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'emhass' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'emhass' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          Wektory 48h i Solver
        </button>
        <button id="tab-logs" style="flex: 1; padding: 8px; border: none; border-radius: 6px; cursor: pointer; background: ${this._activeTab === 'logs' ? 'var(--primary-color, #03a9f4)' : 'rgba(127,127,127,0.1)'}; color: ${this._activeTab === 'logs' ? '#fff' : 'inherit'}; font-weight: bold; font-size: 0.9em;">
          Decyzje i Logi (${recentLogs.length})
        </button>
      </div>
    `;

    // Overview Header
    const overviewHtml = `
      <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; padding: 12px; background: rgba(127,127,127,0.06); border-radius: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <ha-icon icon="${errorCount > 0 ? 'mdi:alert-circle' : 'mdi:check-circle'}" style="color: ${statusBadgeColor}; --mdc-icon-size: 28px;"></ha-icon>
          <div>
            <div style="font-weight: bold; font-size: 1em;">${statusBadgeText}</div>
            <div style="font-size: 0.85em; opacity: 0.8;">Status: ${diagState.state}</div>
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button id="btn-opt" style="padding: 6px 12px; background: rgba(127,127,127,0.15); border: 1px solid rgba(127,127,127,0.25); border-radius: 6px; cursor: pointer; font-size: 0.85em; color: inherit; display: flex; align-items: center; gap: 4px;">
            <ha-icon icon="mdi:calculator-variant" style="--mdc-icon-size: 16px;"></ha-icon> Przelicz MPC
          </button>
          <button id="btn-download" style="padding: 6px 12px; background: var(--primary-color, #03a9f4); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: bold; display: flex; align-items: center; gap: 4px;">
            <ha-icon icon="mdi:download" style="--mdc-icon-size: 16px;"></ha-icon> Raport JSON
          </button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-bottom: 16px;">
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">EMHASS MPC</div>
          <div style="font-weight: bold; color: ${emhassStatus === 'OK' ? 'var(--success-color, #43a047)' : 'var(--error-color, #e53935)'}; font-size: 0.95em;">${emhassStatus} (${lastMpc})</div>
        </div>
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">Aktywna Taryfa</div>
          <div style="font-weight: bold; font-size: 0.95em; text-transform: uppercase;">${tariffMode}</div>
        </div>
        <div style="padding: 8px; background: rgba(127,127,127,0.04); border-radius: 6px; text-align: center;">
          <div style="font-size: 0.75em; opacity: 0.7;">Dynamiczny Min SoC</div>
          <div style="font-weight: bold; font-size: 0.95em;">${dynMinSoc}</div>
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
          ? `<div style="font-size: 0.75em; opacity: 0.8; color: var(--primary-color);">Wektor: ${data.raw_attribute.count} próbek (min: ${data.raw_attribute.min}, max: ${data.raw_attribute.max})</div>`
          : '';
        const issueAlert = data.issue
          ? `<div style="font-size: 0.8em; color: var(--error-color, #e53935); font-weight: bold; margin-top: 2px;">⚠️ ${data.issue}</div>`
          : '';

        rowsHtml += `
          <tr style="border-bottom: 1px solid rgba(127,127,127,0.08);">
            <td style="padding: 6px 4px; vertical-align: top;">
              <div style="font-weight: 500; font-size: 0.9em;">${data.label || entId}</div>
              <div style="font-size: 0.75em; opacity: 0.6; word-break: break-all;">${entId}</div>
              ${rawAttrInfo}
              ${issueAlert}
            </td>
            <td style="padding: 6px 4px; text-align: right; vertical-align: top; font-weight: bold; font-size: 0.9em;">
              ${data.state !== null && data.state !== undefined ? data.state : '--'} ${data.unit || ''}
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
            <span style="opacity: 0.8;">${label}:</span>
            <span style="font-weight: bold;">${state}</span>
          </div>
        `;
      });

      tabContentHtml = `
        <div style="margin-bottom: 16px;">
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:server-network" style="--mdc-icon-size: 18px;"></ha-icon> Integralność i Jednostki Sensorów
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
            <thead>
              <tr style="border-bottom: 1px solid rgba(127,127,127,0.2); font-size: 0.8em; opacity: 0.7; text-align: left;">
                <th style="padding: 4px;">Sensor</th>
                <th style="padding: 4px; text-align: right;">Wartość</th>
                <th style="padding: 4px; text-align: center;">Status</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>

        <div>
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:solar-power" style="--mdc-icon-size: 18px;"></ha-icon> Odczyt Zwrotny Falownika (Home Assistant)
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
              <ha-icon icon="${icon}" style="--mdc-icon-size: 16px; color: var(--primary-color);"></ha-icon> ${title}
              <span style="font-size: 0.8em; opacity: 0.6; margin-left: auto;">${stats.count} kroków (48h)</span>
            </div>
            <div style="display: flex; justify-content: space-around; text-align: center; font-size: 0.85em;">
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">MIN</div>
                <div style="font-weight: bold;">${stats.min} ${unit}</div>
              </div>
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">ŚREDNIA</div>
                <div style="font-weight: bold; color: var(--primary-color);">${stats.avg} ${unit}</div>
              </div>
              <div>
                <div style="font-size: 0.75em; opacity: 0.6;">MAX</div>
                <div style="font-weight: bold;">${stats.max} ${unit}</div>
              </div>
            </div>
          </div>
        `;
      };

      const errBlock = emhassError ? `
        <div style="padding: 10px; background: rgba(229, 57, 53, 0.1); border-left: 4px solid var(--error-color, #e53935); border-radius: 4px; margin-bottom: 12px; font-size: 0.85em;">
          <div style="font-weight: bold; color: var(--error-color, #e53935); margin-bottom: 4px;">⚠️ Ostatni Błąd Komunikacji z EMHASS:</div>
          <div style="opacity: 0.9;"><strong>Status:</strong> ${emhassError.status || 'Błąd połączenia'} (${emhassError.action || 'MPC'})</div>
          <div style="font-family: monospace; font-size: 0.8em; margin-top: 4px; word-break: break-all; opacity: 0.85;">${emhassError.error || emhassError.message || ''}</div>
          <div style="font-size: 0.75em; opacity: 0.6; margin-top: 4px;">Czas: ${emhassError.timestamp}</div>
        </div>
      ` : `
        <div style="padding: 8px 12px; background: rgba(67, 160, 71, 0.08); border-left: 4px solid var(--success-color, #43a047); border-radius: 4px; margin-bottom: 12px; font-size: 0.85em; color: var(--success-color, #43a047); font-weight: 500;">
          ✓ Komunikacja z EMHASS bez zakłóceń. Brak zarejestrowanych błędów HTTP.
        </div>
      `;

      tabContentHtml = `
        ${errBlock}
        <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px;">Krzywe Wejściowe Wysłane do Solvera (Horyzont 48h):</div>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${renderVectorCard('Prognoza Zużycia Domu', emhassSummary.load_forecast_stats, 'W', 'mdi:home-lightning-bolt')}
          ${renderVectorCard('Ceny Zakupu Energii (Taryfa)', emhassSummary.buy_price_stats, 'PLN', 'mdi:cash-fast')}
          ${renderVectorCard('Prognoza Produkcji PV', emhassSummary.pv_forecast_stats, 'W', 'mdi:solar-power-variant')}
          ${renderVectorCard('Wycena Sprzedaży (PSE RCE)', emhassSummary.sell_price_stats, 'PLN', 'mdi:transmission-tower')}
        </div>
      `;
    }

    // Tab 3 Content: Decisions & Terminal Logs
    else if (this._activeTab === 'logs') {
      let decisionsHtml = '';
      if (recentDecisions.length === 0) {
        decisionsHtml = '<div style="font-size: 0.85em; opacity: 0.6;">Brak zarejestrowanych decyzji po starcie.</div>';
      } else {
        recentDecisions.slice(-6).reverse().forEach(d => {
          decisionsHtml += `
            <div style="padding: 6px 8px; border-left: 3px solid var(--primary-color); background: rgba(127,127,127,0.04); border-radius: 0 4px 4px 0; font-size: 0.85em; margin-bottom: 6px;">
              <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 2px;">
                <span>${d.trigger} → ${d.action}</span>
                <span style="font-size: 0.8em; opacity: 0.6;">${d.timestamp ? d.timestamp.split(' ')[1] : ''}</span>
              </div>
              <div style="font-size: 0.8em; opacity: 0.85;">${d.reason}</div>
            </div>
          `;
        });
      }

      let logsHtml = '';
      if (recentLogs.length === 0) {
        logsHtml = '<div style="color: #888;">Brak komunikatów diagnostycznych w buforze RAM.</div>';
      } else {
        recentLogs.forEach(l => {
          let lvlColor = '#81c784'; // INFO
          if (l.level === 'WARNING') lvlColor = '#ffb74d';
          if (l.level === 'ERROR') lvlColor = '#e57373';
          logsHtml += `
            <div style="margin-bottom: 4px; word-break: break-all;">
              <span style="color: #888;">[${l.timestamp ? l.timestamp.split(' ')[1] : ''}]</span>
              <span style="color: ${lvlColor}; font-weight: bold;">[${l.level}]</span>
              <span style="color: #64b5f6;">[${l.logger}]</span>
              <span style="color: #eee;">${l.message}</span>
            </div>
          `;
        });
      }

      tabContentHtml = `
        <div style="margin-bottom: 16px;">
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:history" style="--mdc-icon-size: 18px;"></ha-icon> Ostatnie Decyzje Sterujące EMS
          </div>
          <div>${decisionsHtml}</div>
        </div>

        <div>
          <div style="font-weight: bold; font-size: 0.95em; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <ha-icon icon="mdi:console" style="--mdc-icon-size: 18px;"></ha-icon> Konsola Logów na Żywo (Bufor RAM)
          </div>
          <div style="background: #181818; color: #eee; padding: 10px; border-radius: 6px; font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 0.78em; max-height: 240px; overflow-y: auto; line-height: 1.4; border: 1px solid rgba(255,255,255,0.1);">
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
        btnOpt.textContent = 'Przeliczam...';
        const optBtnId = this._resolveEntity('optimize_now', ['button.smart_storage_ems_przelicz_mpc_teraz']);
        this._hass.callService('button', 'press', { entity_id: optBtnId });
        setTimeout(() => { btnOpt.innerHTML = '<ha-icon icon="mdi:calculator-variant" style="--mdc-icon-size: 16px;"></ha-icon> Przelicz MPC'; }, 2500);
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
  name: 'Smart Storage EMS: Autodiagnostyka',
  description: 'Interaktywny pulpit autodiagnostyczny sprawdzający sensory, jednostki, falownik, solver EMHASS oraz logi.'
});
