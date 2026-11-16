/**
 * Smart Storage EMS - Custom Lovelace Dashboard Card
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

class SmartStorageCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = this.config?.title || 'Smart Storage EMS';
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
    return 5;
  }

  _getState(entityId, defaultVal = null) {
    if (!this._hass || !entityId) return defaultVal;
    return this._hass.states[entityId] || defaultVal;
  }

  _resolveEntity(configKey, candidates) {
    if (this.config && this.config[configKey]) {
      return this.config[configKey];
    }
    if (!this._hass) return null;
    for (const id of candidates) {
      if (this._hass.states[id]) {
        return id;
      }
    }
    return candidates[0];
  }

  updateCard() {
    if (!this._hass) return;

    // Resolve entities with automatic fallback to Polish and English slugs
    const statusId = this._resolveEntity('status', [
      'sensor.smart_storage_ems_status'
    ]);
    const powerId = this._resolveEntity('target_power', [
      'sensor.smart_storage_ems_moc_zadana',
      'sensor.smart_storage_ems_target_power'
    ]);
    const minSocId = this._resolveEntity('dynamic_min_soc', [
      'sensor.smart_storage_ems_dynamiczny_min_soc',
      'sensor.smart_storage_ems_dynamic_min_soc'
    ]);
    const modeId = this._resolveEntity('operation_mode', [
      'select.smart_storage_ems_tryb_pracy',
      'select.smart_storage_ems_operation_mode'
    ]);
    const guardId = this._resolveEntity('import_guard', [
      'switch.smart_storage_ems_straznik_importu',
      'switch.smart_storage_ems_import_guard'
    ]);
    const stormId = this._resolveEntity('storm_reserve', [
      'switch.smart_storage_ems_rezerwa_burzowa',
      'switch.smart_storage_ems_storm_reserve'
    ]);
    const optBtnId = this._resolveEntity('optimize_now', [
      'button.smart_storage_ems_przelicz_mpc_teraz',
      'button.smart_storage_ems_optimize_now'
    ]);

    // Live power & solar entities
    const socId = this._resolveEntity('battery_soc', [
      'sensor.goodwe_battery_state_of_charge',
      'sensor.battery_state_of_charge'
    ]);
    const pvId = this._resolveEntity('pv_power', [
      'sensor.goodwe_pv_power',
      'sensor.pv_power'
    ]);
    const loadId = this._resolveEntity('load_power', [
      'sensor.goodwe_house_consumption',
      'sensor.house_consumption'
    ]);
    const battPowerId = this._resolveEntity('battery_power', [
      'sensor.goodwe_battery_power',
      'sensor.battery_power'
    ]);

    // Read values
    const statusState = this._getState(statusId);
    const statusVal = statusState ? statusState.state : 'Aktywny';

    const powerState = this._getState(powerId);
    const targetPower = powerState ? parseFloat(powerState.state) || 0 : 0;

    const minSocState = this._getState(minSocId);
    const dynamicMinSoc = minSocState ? parseFloat(minSocState.state) || 15 : 15;

    const socState = this._getState(socId);
    const currentSoc = socState ? parseFloat(socState.state) || 0 : 0;

    const pvState = this._getState(pvId);
    const pvPower = pvState ? parseFloat(pvState.state) || 0 : 0;

    const loadState = this._getState(loadId);
    const loadPower = loadState ? parseFloat(loadState.state) || 0 : 0;

    const battPowerState = this._getState(battPowerId);
    const battPower = battPowerState ? parseFloat(battPowerState.state) || 0 : 0;

    const modeState = this._getState(modeId);
    const currentMode = modeState ? modeState.state : 'auto_mpc';

    const guardState = this._getState(guardId);
    const guardActive = guardState ? guardState.state === 'on' : true;

    const stormState = this._getState(stormId);
    const stormActive = stormState ? stormState.state === 'on' : false;

    // Power badge styling
    let powerBadgeBg = '#757575';
    let powerLabel = 'Standby (0 W)';

    if (targetPower < -50) {
      powerBadgeBg = '#4caf50'; // Green
      powerLabel = `Ładowanie (${Math.abs(Math.round(targetPower))} W)`;
    } else if (targetPower > 50) {
      powerBadgeBg = '#2196f3'; // Blue
      powerLabel = `Autokonsumpcja (${Math.round(targetPower)} W)`;
    }

    // Battery power format (GoodWe / EMHASS convention: negative = charging, positive = discharging)
    let battPowerFormatted = `${Math.abs(Math.round(battPower))} W`;
    let battPowerColor = '#616161';
    if (battPower < -50) {
      battPowerFormatted = `-${Math.abs(Math.round(battPower))} W (Ładowanie)`;
      battPowerColor = '#388e3c';
    } else if (battPower > 50) {
      battPowerFormatted = `+${Math.round(battPower)} W (Rozładowanie)`;
      battPowerColor = '#1976d2';
    }

    this.content.innerHTML = `
      <style>
        .ems-container {
          display: flex;
          flex-direction: column;
          gap: 14px;
          font-family: inherit;
        }
        .ems-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }
        .ems-status-badge {
          background-color: var(--primary-color, #03a9f4);
          color: white;
          padding: 5px 12px;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.85rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .ems-power-badge {
          background-color: ${powerBadgeBg};
          color: white;
          padding: 5px 12px;
          border-radius: 12px;
          font-weight: 700;
          font-size: 0.85rem;
          white-space: nowrap;
        }
        .ems-metrics-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }
        .ems-metric-card {
          background: var(--secondary-background-color, #f9f9f9);
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 10px;
          padding: 10px;
          text-align: center;
        }
        .ems-metric-label {
          font-size: 0.75rem;
          color: var(--secondary-text-color, #757575);
          font-weight: 500;
          margin-bottom: 4px;
        }
        .ems-metric-val {
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--primary-text-color, #212121);
        }
        .ems-battery-box {
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 12px;
          padding: 14px;
        }
        .ems-soc-row {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          font-size: 1rem;
          font-weight: 600;
        }
        .ems-progress-bg {
          background: #e0e0e0;
          border-radius: 8px;
          height: 24px;
          position: relative;
          overflow: hidden;
          margin-top: 14px;
        }
        .ems-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #ff9800 0%, #4caf50 100%);
          width: ${Math.min(100, Math.max(0, currentSoc))}%;
          transition: width 0.4s ease-in-out;
        }
        .ems-min-marker {
          position: absolute;
          top: 0;
          bottom: 0;
          left: ${Math.min(100, Math.max(0, dynamicMinSoc))}%;
          width: 3px;
          background: #d32f2f;
          z-index: 2;
        }
        .ems-min-marker-label {
          position: absolute;
          top: -18px;
          left: ${Math.min(100, Math.max(0, dynamicMinSoc))}%;
          transform: translateX(-50%);
          font-size: 0.72rem;
          color: #d32f2f;
          font-weight: 700;
        }
        .ems-actions-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 6px;
        }
        .ems-btn {
          background: var(--secondary-background-color, #f5f5f5);
          color: var(--primary-text-color, #212121);
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 8px;
          padding: 8px 4px;
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          text-align: center;
          transition: background 0.2s;
        }
        .ems-btn.active {
          background: var(--primary-color, #03a9f4);
          color: white;
          border-color: var(--primary-color, #03a9f4);
        }
        .ems-toggles-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 8px;
          border-top: 1px solid var(--divider-color, #eee);
          flex-wrap: wrap;
          gap: 10px;
        }
      </style>

      <div class="ems-container">
        <!-- Header -->
        <div class="ems-header-row">
          <span class="ems-status-badge">${statusVal}</span>
          <span class="ems-power-badge">${powerLabel}</span>
        </div>

        <!-- Metrics Grid -->
        <div class="ems-metrics-grid">
          <div class="ems-metric-card">
            <div class="ems-metric-label">☀️ PV Produkcja</div>
            <div class="ems-metric-val" style="color: #f57f17;">${Math.round(pvPower)} W</div>
          </div>
          <div class="ems-metric-card">
            <div class="ems-metric-label">🏠 Dom Zużycie</div>
            <div class="ems-metric-val">${Math.round(loadPower)} W</div>
          </div>
          <div class="ems-metric-card">
            <div class="ems-metric-label">🔋 Moc Baterii</div>
            <div class="ems-metric-val" style="color: ${battPowerColor}; font-size: 0.95rem;">${battPowerFormatted}</div>
          </div>
        </div>

        <!-- Battery SoC Box -->
        <div class="ems-battery-box">
          <div class="ems-soc-row">
            <span>Poziom Naładowania (SoC)</span>
            <span style="font-size: 1.25rem;">${currentSoc.toFixed(1)}%</span>
          </div>
          <div style="position: relative;">
            <div class="ems-min-marker-label">Min: ${dynamicMinSoc.toFixed(0)}%</div>
            <div class="ems-progress-bg">
              <div class="ems-min-marker"></div>
              <div class="ems-progress-fill"></div>
            </div>
          </div>
        </div>

        <!-- Mode Buttons -->
        <div class="ems-actions-grid">
          <button class="ems-btn ${currentMode === 'auto_mpc' ? 'active' : ''}" data-mode="auto_mpc">Auto MPC</button>
          <button class="ems-btn ${currentMode === 'hold_standby' ? 'active' : ''}" data-mode="hold_standby">Standby</button>
          <button class="ems-btn ${currentMode === 'force_charge' ? 'active' : ''}" data-mode="force_charge">Ładuj</button>
          <button class="ems-btn ${currentMode === 'self_use' ? 'active' : ''}" data-mode="self_use">Autokonsumpcja</button>
        </div>

        <!-- Toggles and Optimize Button -->
        <div class="ems-toggles-row">
          <div style="display: flex; gap: 14px; font-size: 0.85rem;">
            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
              <input type="checkbox" id="guardToggle" ${guardActive ? 'checked' : ''} />
              Strażnik Importu
            </label>
            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
              <input type="checkbox" id="stormToggle" ${stormActive ? 'checked' : ''} />
              Rezerwa Burzowa
            </label>
          </div>
          <button class="ems-btn" id="optimizeNowBtn" style="padding: 6px 12px; font-size: 0.82rem;">Przelicz MPC</button>
        </div>
      </div>
    `;

    // Event Handlers
    this.content.querySelectorAll('.ems-btn[data-mode]').forEach(btn => {
      btn.onclick = (e) => {
        const mode = e.currentTarget.getAttribute('data-mode');
        this._hass.callService('select', 'select_option', {
          entity_id: modeId,
          option: mode
        });
      };
    });

    const guardToggle = this.content.querySelector('#guardToggle');
    if (guardToggle) {
      guardToggle.onchange = (e) => {
        this._hass.callService('switch', e.target.checked ? 'turn_on' : 'turn_off', {
          entity_id: guardId
        });
      };
    }

    const stormToggle = this.content.querySelector('#stormToggle');
    if (stormToggle) {
      stormToggle.onchange = (e) => {
        this._hass.callService('switch', e.target.checked ? 'turn_on' : 'turn_off', {
          entity_id: stormId
        });
      };
    }

    const optBtn = this.content.querySelector('#optimizeNowBtn');
    if (optBtn) {
      optBtn.onclick = () => {
        optBtn.textContent = 'Obliczam...';
        this._hass.callService('button', 'press', {
          entity_id: optBtnId
        });
        setTimeout(() => { optBtn.textContent = 'Przelicz MPC'; }, 2000);
      };
    }
  }
}

customElements.define('smart-storage-card', SmartStorageCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'smart-storage-card',
  name: 'Smart Storage EMS Card',
  description: 'Interaktywna karta sterowania magazynem energii, produkcją PV i EMHASS.'
});
