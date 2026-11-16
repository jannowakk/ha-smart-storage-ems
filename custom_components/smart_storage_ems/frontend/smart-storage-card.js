/**
 * Smart Storage EMS - Custom Lovelace Dashboard Card
 * Pure vanilla Web Component for Home Assistant (Zero external dependencies)
 */

class SmartStorageCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = 'Smart Storage EMS';
      this.content = document.createElement('div');
      this.content.style.padding = '16px';
      card.appendChild(this.content);
      this.appendChild(card);
    }
    this.updateCard();
  }

  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    return 4;
  }

  updateCard() {
    if (!this._hass) return;

    // Discover entities
    const statusEntity = this._findEntity('sensor', '_status');
    const powerEntity = this._findEntity('sensor', '_target_power');
    const minSocEntity = this._findEntity('sensor', '_dynamic_min_soc');
    const modeSelectEntity = this._findEntity('select', '_operation_mode');
    const guardSwitchEntity = this._findEntity('switch', '_import_guard');
    const optimizeBtnEntity = this._findEntity('button', '_optimize_now');

    const statusVal = statusEntity ? statusEntity.state : 'Aktywny';
    const targetPower = powerEntity ? parseFloat(powerEntity.state) : 0;
    const dynamicMinSoc = minSocEntity ? parseFloat(minSocEntity.state) : 15;
    const currentMode = modeSelectEntity ? modeSelectEntity.state : 'auto_mpc';
    const guardActive = guardSwitchEntity ? guardSwitchEntity.state === 'on' : true;

    // Detect general battery SoC if available in HA
    const socState = this._hass.states['sensor.goodwe_battery_state_of_charge'] ||
                     this._hass.states['sensor.battery_state_of_charge'] ||
                     { state: '50' };
    const currentSoc = parseFloat(socState.state) || 50;

    let powerBadgeColor = '#9e9e9e';
    let powerIcon = 'mdi:pause-circle-outline';
    let powerLabel = 'Standby (0 W)';

    if (targetPower < -50) {
      powerBadgeColor = '#4caf50'; // Green - Charge
      powerIcon = 'mdi:battery-charging-high';
      powerLabel = `Ładowanie (${Math.abs(targetPower)} W)`;
    } else if (targetPower > 50) {
      powerBadgeColor = '#2196f3'; // Blue - Self Use
      powerIcon = 'mdi:battery-arrow-down';
      powerLabel = `Autokonsumpcja (${targetPower} W)`;
    }

    this.content.innerHTML = `
      <style>
        .ems-container {
          display: flex;
          flex-direction: column;
          gap: 16px;
          font-family: inherit;
        }
        .ems-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .ems-status-badge {
          background-color: var(--primary-color, #03a9f4);
          color: white;
          padding: 4px 12px;
          border-radius: 12px;
          font-weight: 500;
          font-size: 0.85rem;
        }
        .ems-power-badge {
          background-color: ${powerBadgeColor};
          color: white;
          padding: 4px 12px;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.85rem;
        }
        .ems-battery-box {
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 12px;
          padding: 16px;
          position: relative;
        }
        .ems-soc-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-weight: 600;
          font-size: 1.1rem;
        }
        .ems-progress-bg {
          background: #eeeeee;
          border-radius: 8px;
          height: 22px;
          position: relative;
          overflow: hidden;
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
          left: ${dynamicMinSoc}%;
          width: 3px;
          background: red;
          z-index: 2;
        }
        .ems-min-marker-label {
          position: absolute;
          top: -18px;
          left: ${dynamicMinSoc}%;
          transform: translateX(-50%);
          font-size: 0.7rem;
          color: red;
          font-weight: bold;
        }
        .ems-actions-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
        }
        .ems-btn {
          background: var(--secondary-background-color, #f5f5f5);
          color: var(--primary-text-color, #212121);
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 8px;
          padding: 8px 4px;
          font-size: 0.8rem;
          font-weight: 600;
          cursor: pointer;
          text-align: center;
        }
        .ems-btn.active {
          background: var(--primary-color, #03a9f4);
          color: white;
          border-color: var(--primary-color, #03a9f4);
        }
        .ems-footer-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 8px;
          border-top: 1px solid var(--divider-color, #eee);
        }
      </style>

      <div class="ems-container">
        <div class="ems-header-row">
          <span class="ems-status-badge">${statusVal}</span>
          <span class="ems-power-badge">${powerLabel}</span>
        </div>

        <div class="ems-battery-box">
          <div class="ems-soc-row">
            <span>Poziom Baterii</span>
            <span>${currentSoc.toFixed(1)}%</span>
          </div>
          <div style="position: relative; margin-top: 14px;">
            <div class="ems-min-marker-label">Min: ${dynamicMinSoc}%</div>
            <div class="ems-progress-bg">
              <div class="ems-min-marker"></div>
              <div class="ems-progress-fill"></div>
            </div>
          </div>
        </div>

        <div class="ems-actions-grid">
          <button class="ems-btn ${currentMode === 'auto_mpc' ? 'active' : ''}" data-mode="auto_mpc">Auto MPC</button>
          <button class="ems-btn ${currentMode === 'hold_standby' ? 'active' : ''}" data-mode="hold_standby">Standby</button>
          <button class="ems-btn ${currentMode === 'force_charge' ? 'active' : ''}" data-mode="force_charge">Ładuj</button>
          <button class="ems-btn ${currentMode === 'self_use' ? 'active' : ''}" data-mode="self_use">Autokonsumpcja</button>
        </div>

        <div class="ems-footer-row">
          <label style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; cursor: pointer;">
            <input type="checkbox" id="guardToggle" ${guardActive ? 'checked' : ''} />
            Strażnik Importu
          </label>
          <button class="ems-btn" id="optimizeNowBtn" style="padding: 6px 12px;">Przelicz MPC Teraz</button>
        </div>
      </div>
    `;

    // Event Listeners
    this.content.querySelectorAll('.ems-btn[data-mode]').forEach(btn => {
      btn.onclick = (e) => {
        const mode = e.currentTarget.getAttribute('data-mode');
        if (modeSelectEntity) {
          this._hass.callService('select', 'select_option', {
            entity_id: modeSelectEntity.entity_id,
            option: mode
          });
        }
      };
    });

    const guardToggle = this.content.querySelector('#guardToggle');
    if (guardToggle && guardSwitchEntity) {
      guardToggle.onchange = (e) => {
        this._hass.callService('switch', e.target.checked ? 'turn_on' : 'turn_off', {
          entity_id: guardSwitchEntity.entity_id
        });
      };
    }

    const optBtn = this.content.querySelector('#optimizeNowBtn');
    if (optBtn && optimizeBtnEntity) {
      optBtn.onclick = () => {
        optBtn.textContent = 'Obliczam...';
        this._hass.callService('button', 'press', {
          entity_id: optimizeBtnEntity.entity_id
        });
        setTimeout(() => { optBtn.textContent = 'Przelicz MPC Teraz'; }, 2000);
      };
    }
  }

  _findEntity(domain, suffix) {
    if (!this._hass) return null;
    const key = Object.keys(this._hass.states).find(
      k => k.startsWith(domain + '.smart_storage_ems') && k.endsWith(suffix)
    );
    return key ? this._hass.states[key] : null;
  }
}

customElements.define('smart-storage-card', SmartStorageCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'smart-storage-card',
  name: 'Smart Storage EMS Card',
  description: 'Interaktywna karta sterowania magazynem energii i optymalizacją EMHASS.'
});
