/**
 * Run Down page — date-filtered supplier lookup per service category.
 */
(function () {
  'use strict';

  const STATUS_CLASS = {
    REQUEST: 'sts-request',
    QUOTED: 'sts-quoted',
    RESERVED: 'sts-reserved',
    CONFIRMED: 'sts-confirmed',
    INVOICED: 'sts-invoiced',
    COMPLETED: 'sts-completed',
    CANCELLED: 'sts-cancelled',
  };

  /** Map service statuses to modal filter buckets. */
  const STATUS_FILTER_MAP = {
    REQUEST: 'REQUEST',
    QUOTED: 'REQUEST',
    RESERVED: 'CONFIRMED',
    CONFIRMED: 'CONFIRMED',
    BOOKED: 'CONFIRMED',
    INVOICED: 'INVOICED',
    COMPLETED: 'CONFIRMED',
  };

  // Supplier/service tables that use the exact-match, single-select status filter
  // (Requested / Confirmed / Waiting List / Cancelled / All). Other tables
  // (Agent, Meet & Assist, Optional) keep the legacy bucket filter below.
  const SERVICE_STATUS_TABLES = new Set(['MEAL', 'GUIDE', 'HOTEL', 'TRANSPORT']);

  /** Single-select filter options for supplier tables. 'ALL' shows every row. */
  const SERVICE_FILTER_OPTIONS = [
    { key: 'REQUESTED', label: 'Requested', cls: 'requested' },
    { key: 'CONFIRMED', label: 'Confirmed', cls: 'confirmed' },
    { key: 'WAITING_LIST', label: 'Waiting List', cls: 'waiting' },
    { key: 'CANCELLED', label: 'Cancelled', cls: 'cancelled' },
    { key: 'ALL', label: 'All', cls: 'all' },
  ];

  /** Legacy multi-select filter options for the remaining tables. */
  const LEGACY_FILTER_OPTIONS = [
    { key: 'REQUEST', label: 'Requested', cls: 'requested' },
    { key: 'CONFIRMED', label: 'Confirmed', cls: 'confirmed' },
    { key: 'INVOICED', label: 'Invoiced', cls: 'invoiced' },
  ];

  /** Normalize a raw service status to one of the SERVICE_FILTER_OPTIONS keys.
   *  Legacy 'REQUEST' is treated as 'REQUESTED'. Unknown/legacy values (e.g.
   *  QUOTED, RESERVED) match nothing but 'All'. */
  function normalizeServiceStatus(status) {
    const s = String(status || 'REQUESTED').toUpperCase();
    if (s === 'REQUEST' || s === 'REQUESTED') return 'REQUESTED';
    if (s === 'WAITING_LIST' || s === 'WAITING') return 'WAITING_LIST';
    if (s === 'CANCELLED' || s === 'CANCELED') return 'CANCELLED';
    if (s === 'CONFIRMED') return 'CONFIRMED';
    return s;
  }

  const state = {
    dateFrom: '',
    dateTo: '',
    appliedDateFrom: '',
    appliedDateTo: '',
    services: {},
    agent: {
      agentName: '',
      query: '',
      results: [],
      open: false,
      loading: false,
    },
    modal: null,
    modalOpen: false,
    modalStatusFilters: new Set(['REQUEST', 'CONFIRMED', 'INVOICED']),
    modalFilterMode: 'legacy',
    modalServiceFilter: 'ALL',
    printTs: '',
  };

  let modalInstance = null;
  let searchTimers = {};

  function $(id) { return document.getElementById(id); }

  function formatDateDisplay(iso) {
    if (!iso) return '—';
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  /** DD/MM/YYYY for the field display (independent of browser locale). */
  function formatDMY(iso) {
    if (!iso) return '—';
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
  }

  /** Short weekday (Sat, Mon…) for the in-field label. */
  function formatDow(iso) {
    if (!iso) return '';
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString('en-GB', { weekday: 'short' });
  }

  function formatPrintTs() {
    const now = new Date();
    return now.toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  /** Compact applied-range label, e.g. "1 - 31 Aug 2026", "28 Aug - 3 Sep 2026",
   *  "28 Dec 2025 - 3 Jan 2026", or a single "5 Aug 2026". */
  function dateRangeLabel() {
    const from = state.appliedDateFrom || state.dateFrom;
    const to = state.appliedDateTo || state.dateTo;
    if (!from || !to) return '—';

    const df = new Date(from + 'T00:00:00');
    const dt = new Date(to + 'T00:00:00');
    const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const fd = df.getDate(), fm = df.getMonth(), fy = df.getFullYear();
    const td = dt.getDate(), tm = dt.getMonth(), ty = dt.getFullYear();

    if (from === to) return `${fd} ${MON[fm]} ${fy}`;
    if (fy === ty && fm === tm) return `${fd} - ${td} ${MON[tm]} ${ty}`;
    if (fy === ty) return `${fd} ${MON[fm]} - ${td} ${MON[tm]} ${ty}`;
    return `${fd} ${MON[fm]} ${fy} - ${td} ${MON[tm]} ${ty}`;
  }

  /** Inclusive number of days in the applied range. */
  function dayCount() {
    const from = state.appliedDateFrom || state.dateFrom;
    const to = state.appliedDateTo || state.dateTo;
    if (!from || !to) return 0;
    const df = new Date(from + 'T00:00:00');
    const dt = new Date(to + 'T00:00:00');
    return Math.round((dt - df) / 86400000) + 1;
  }

  function syncUrl() {
    const url = new URL(window.location.href);
    url.searchParams.set('date_from', state.appliedDateFrom);
    url.searchParams.set('date_to', state.appliedDateTo);
    window.history.replaceState({}, '', url.toString());
  }

  function updatePrintMeta() {
    const el = $('rdPrintMeta');
    if (el) {
      const days = dayCount();
      el.textContent = `Selected period: ${dateRangeLabel()} · ${days} day${days === 1 ? '' : 's'}`;
    }
    // Print-only header keeps its own dates + printed timestamp (unchanged).
    const hdr = $('rdPrintHeaderDates');
    if (hdr) {
      hdr.innerHTML = `<strong>Selected period:</strong> ${dateRangeLabel()}<br><strong>Printed:</strong> ${state.printTs || formatPrintTs()}`;
    }
  }

  /** Mirror a native date input's ISO value into its DD/MM/YYYY + weekday display. */
  function updateFieldDisplay(which) {
    const input = which === 'from' ? $('rdDateFrom') : $('rdDateTo');
    const disp = which === 'from' ? $('rdDateFromDisplay') : $('rdDateToDisplay');
    const dow = which === 'from' ? $('rdDateFromDow') : $('rdDateToDow');
    if (!input) return;
    if (disp) disp.textContent = formatDMY(input.value);
    if (dow) dow.textContent = formatDow(input.value);
  }

  function initServiceState(key) {
    if (!state.services[key]) {
      state.services[key] = {
        supplierId: null,
        supplierName: '',
        query: '',
        results: [],
        open: false,
        loading: false,
      };
    }
    return state.services[key];
  }

  function closeAllDropdowns(exceptKey) {
    Object.keys(state.services).forEach((key) => {
      if (key !== exceptKey) {
        state.services[key].open = false;
        renderDropdown(key);
      }
    });
    if (exceptKey !== 'agent') {
      state.agent.open = false;
      renderAgentDropdown();
    }
  }

  function renderDropdown(serviceKey) {
    const svc = state.services[serviceKey];
    const list = document.querySelector(`[data-rd-dropdown="${serviceKey}"]`);
    if (!list) return;

    if (!svc.open) {
      list.classList.remove('open');
      list.innerHTML = '';
      return;
    }

    list.classList.add('open');
    if (svc.loading) {
      list.innerHTML = '<div class="rd-dd-item rd-dd-muted"><i class="fas fa-spinner fa-spin"></i> Searching…</div>';
      return;
    }
    if (!svc.results.length) {
      list.innerHTML = '<div class="rd-dd-item rd-dd-muted">No suppliers found</div>';
      return;
    }

    list.innerHTML = svc.results.map((s) => {
      const meta = [s.city, s.country].filter(Boolean).join(', ');
      return `<button type="button" class="rd-dd-item" data-rd-pick="${serviceKey}" data-id="${s.id}" data-name="${escapeAttr(s.name)}">
        <span class="rd-dd-name">${escapeHtml(s.name)}</span>
        ${meta ? `<span class="rd-dd-meta">${escapeHtml(meta)}</span>` : ''}
      </button>`;
    }).join('');
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function escapeAttr(str) {
    return escapeHtml(str).replace(/'/g, '&#39;');
  }

  async function fetchSuppliers(serviceKey, query) {
    const svc = initServiceState(serviceKey);
    svc.loading = true;
    svc.open = true;
    renderDropdown(serviceKey);

    const url = `/inbound/run-down/suppliers?service=${encodeURIComponent(serviceKey)}`
      + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`
      + (query ? `&q=${encodeURIComponent(query)}` : '');

    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Search failed');
      svc.results = data.suppliers || [];
    } catch (err) {
      console.error('Supplier search error', err);
      svc.results = [];
    } finally {
      svc.loading = false;
      renderDropdown(serviceKey);
    }
  }

  function debouncedSearch(serviceKey, query) {
    clearTimeout(searchTimers[serviceKey]);
    searchTimers[serviceKey] = setTimeout(() => fetchSuppliers(serviceKey, query), 220);
  }

  function selectSupplier(serviceKey, id, name) {
    const svc = initServiceState(serviceKey);
    svc.supplierId = id;
    svc.supplierName = name;
    svc.query = name;
    svc.open = false;
    renderDropdown(serviceKey);

    const input = document.querySelector(`[data-rd-input="${serviceKey}"]`);
    if (input) input.value = name;

    const card = document.querySelector(`[data-rd-card="${serviceKey}"]`);
    if (card) card.classList.toggle('has-supplier', Boolean(id));
  }

  function clearSupplier(serviceKey) {
    const svc = initServiceState(serviceKey);
    svc.supplierId = null;
    svc.supplierName = '';
    svc.query = '';
    svc.results = [];
    svc.open = false;
    renderDropdown(serviceKey);

    const input = document.querySelector(`[data-rd-input="${serviceKey}"]`);
    if (input) input.value = '';

    const card = document.querySelector(`[data-rd-card="${serviceKey}"]`);
    if (card) card.classList.remove('has-supplier');
  }

  function renderAgentDropdown() {
    const list = document.querySelector('[data-rd-agent-dropdown]');
    if (!list) return;

    if (!state.agent.open) {
      list.classList.remove('open');
      list.innerHTML = '';
      return;
    }

    list.classList.add('open');
    if (state.agent.loading) {
      list.innerHTML = '<div class="rd-dd-item rd-dd-muted"><i class="fas fa-spinner fa-spin"></i> Searching…</div>';
      return;
    }
    if (!state.agent.results.length) {
      list.innerHTML = '<div class="rd-dd-item rd-dd-muted">No agents found</div>';
      return;
    }

    list.innerHTML = state.agent.results.map((a) => {
      return `<button type="button" class="rd-dd-item" data-rd-pick-agent data-name="${escapeAttr(a.name)}">
        <span class="rd-dd-name">${escapeHtml(a.name)}</span>
      </button>`;
    }).join('');
  }

  async function fetchAgents(query) {
    state.agent.loading = true;
    state.agent.open = true;
    renderAgentDropdown();

    const url = `/inbound/run-down/agents?`
      + `date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`
      + (query ? `&q=${encodeURIComponent(query)}` : '');

    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Search failed');
      state.agent.results = data.agents || [];
    } catch (err) {
      console.error('Agent search error', err);
      state.agent.results = [];
    } finally {
      state.agent.loading = false;
      renderAgentDropdown();
    }
  }

  function debouncedAgentSearch(query) {
    clearTimeout(searchTimers['agent']);
    searchTimers['agent'] = setTimeout(() => fetchAgents(query), 220);
  }

  function selectAgent(name) {
    state.agent.agentName = name;
    state.agent.query = name;
    state.agent.open = false;
    renderAgentDropdown();

    const input = document.querySelector('[data-rd-agent-input]');
    if (input) input.value = name;

    const card = document.querySelector('[data-rd-agent-card]');
    if (card) card.classList.toggle('has-supplier', Boolean(name));
  }

  function clearAgent() {
    state.agent.agentName = '';
    state.agent.query = '';
    state.agent.results = [];
    state.agent.open = false;
    renderAgentDropdown();

    const input = document.querySelector('[data-rd-agent-input]');
    if (input) input.value = '';

    const card = document.querySelector('[data-rd-agent-card]');
    if (card) card.classList.remove('has-supplier');
  }

  async function applyAgent() {
    if (!state.agent.agentName) {
      const input = document.querySelector('[data-rd-agent-input]');
      if (input) input.focus();
      return;
    }

    const applyBtn = document.querySelector('[data-rd-agent-apply]');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = `/inbound/run-down/agent-requests?agent=${encodeURIComponent(state.agent.agentName)}`
      + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load requests');

      setupModalFilters('AGENT');

      state.modal = {
        serviceKey: 'AGENT',
        serviceLabel: 'Agents',
        agentName: data.agent,
        agentType: data.agent_type || 'Direct',
        dateLabel: data.date_from === data.date_to
          ? data.date_from_display
          : `${data.date_from_display} – ${data.date_to_display}`,
        requests: data.requests || [],
        total: data.total || 0,
      };
      openModal();
    } catch (err) {
      console.error('Apply error', err);
      alert('Could not load agent requests. Please try again.');
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  function applyDateRange() {
    const fromEl = $('rdDateFrom');
    const toEl = $('rdDateTo');
    if (!fromEl || !toEl) return;

    let from = fromEl.value;
    let to = toEl.value;
    if (from && to && from > to) {
      to = from;
      toEl.value = to;
      updateFieldDisplay('to');
    }

    state.dateFrom = from;
    state.dateTo = to;
    state.appliedDateFrom = from;
    state.appliedDateTo = to;

    syncUrl();
    updatePrintMeta();

    Object.keys(state.services).forEach((key) => {
      const svc = state.services[key];
      if (svc.query || svc.open) {
        debouncedSearch(key, svc.query);
      }
    });

    if (state.agent.query || state.agent.open) {
      debouncedAgentSearch(state.agent.query);
    }

    // Option A: an already-open modal auto-refreshes to the new range,
    // reusing the same supplier/agent it was opened for.
    refreshOpenModal();

    // Refresh accommodation inline section for new date range
    refreshAccomOnDateChange();
  }

  /* ── Preset date ranges (fill only — never load data) ── */

  function toISO(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function presetRange(kind) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    if (kind === 'today') {
      return [toISO(today), toISO(today)];
    }
    if (kind === 'tomorrow') {
      const t = new Date(today);
      t.setDate(t.getDate() + 1);
      return [toISO(t), toISO(t)];
    }
    if (kind === 'week') {
      // Monday–Sunday of the current week.
      const dow = today.getDay();            // 0 Sun … 6 Sat
      const toMon = (dow + 6) % 7;
      const mon = new Date(today);
      mon.setDate(mon.getDate() - toMon);
      const sun = new Date(mon);
      sun.setDate(sun.getDate() + 6);
      return [toISO(mon), toISO(sun)];
    }
    if (kind === 'month') {
      const first = new Date(today.getFullYear(), today.getMonth(), 1);
      const last = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      return [toISO(first), toISO(last)];
    }
    return [toISO(today), toISO(today)];
  }

  function highlightPreset(kind) {
    document.querySelectorAll('[data-rd-preset]').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.rdPreset === kind);
    });
  }

  function clearPresetHighlight() {
    document.querySelectorAll('[data-rd-preset]').forEach((btn) => {
      btn.classList.remove('active');
    });
  }

  /** Fill the From/To fields from a preset. Does NOT load any data. */
  function applyPreset(kind) {
    const [from, to] = presetRange(kind);
    const fromEl = $('rdDateFrom');
    const toEl = $('rdDateTo');
    if (fromEl) { fromEl.value = from; updateFieldDisplay('from'); }
    if (toEl) { toEl.value = to; updateFieldDisplay('to'); }
    highlightPreset(kind);
    hideDateAppliedIndicator();
  }

  /* ── Open-modal auto-refresh (Option A) ── */

  function showModalLoading(on) {
    const body = $('rdModalBody');
    if (!body) return;
    const existing = body.querySelector('.rd-modal-loading');
    if (on) {
      if (existing) return;
      body.style.position = 'relative';
      const overlay = document.createElement('div');
      overlay.className = 'rd-modal-loading';
      overlay.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      body.appendChild(overlay);
    } else if (existing) {
      existing.remove();
    }
  }

  function clearModalError() {
    const body = $('rdModalBody');
    if (!body) return;
    const err = body.querySelector('.rd-modal-refresh-error');
    if (err) err.remove();
  }

  function showModalError(msg) {
    const body = $('rdModalBody');
    if (!body) return;
    clearModalError();
    body.insertAdjacentHTML('afterbegin',
      `<div class="rd-modal-refresh-error"><i class="fas fa-exclamation-triangle"></i>${escapeHtml(msg)}</div>`);
  }

  /** Re-fetch the open modal's data for the newly-applied range, keeping the
   *  same supplier/agent and the current status-filter selection. Shows a
   *  loading overlay; on failure keeps the previous rows and shows an inline
   *  error instead of blanking the modal. */
  async function refreshOpenModal() {
    if (!state.modalOpen || !state.modal) return;
    const m = state.modal;

    let url;
    if (m.serviceKey === 'AGENT') {
      if (!state.agent.agentName) return;
      url = `/inbound/run-down/agent-requests?agent=${encodeURIComponent(state.agent.agentName)}`
        + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
        + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    } else {
      const svc = state.services[m.serviceKey];
      if (!svc || !svc.supplierId) return;
      url = `/inbound/run-down/supplier-requests?service=${encodeURIComponent(m.serviceKey)}`
        + `&supplier_id=${svc.supplierId}`
        + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
        + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    }

    showModalLoading(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to refresh');

      m.requests = data.requests || [];
      m.total = data.total || 0;
      m.dateLabel = data.date_from === data.date_to
        ? data.date_from_display
        : `${data.date_from_display} – ${data.date_to_display}`;

      const subtitle = $('rdModalSubtitle');
      if (subtitle) subtitle.textContent = `Requests for ${m.dateLabel}`;

      clearModalError();
      refreshModalTable();  // replaces body content (also clears the overlay)
    } catch (err) {
      console.error('Modal refresh error', err);
      showModalLoading(false);
      showModalError('Could not refresh. Showing previous results.');
    } finally {
      showModalLoading(false);
    }
  }

  function readDateInputs() {
    const fromEl = $('rdDateFrom');
    const toEl = $('rdDateTo');
    if (fromEl) state.dateFrom = fromEl.value;
    if (toEl) state.dateTo = toEl.value;
  }

  function statusBadge(status) {
    const cls = STATUS_CLASS[status] || 'sts-request';
    return `<span class="sts-badge ${cls}">${escapeHtml(status || 'REQUEST')}</span>`;
  }

  function matchesStatusFilter(status) {
    if (state.modalFilterMode === 'service') {
      if (state.modalServiceFilter === 'ALL') return true;
      return normalizeServiceStatus(status) === state.modalServiceFilter;
    }
    if (!state.modalStatusFilters.size) return true;
    const bucket = STATUS_FILTER_MAP[(status || 'REQUEST').toUpperCase()] || 'REQUEST';
    return state.modalStatusFilters.has(bucket);
  }

  /** Render the modal's status filter chips for the current filter mode. */
  function renderModalFilters() {
    const wrap = $('rdModalFilterChips');
    if (!wrap) return;

    if (state.modalFilterMode === 'service') {
      wrap.innerHTML = SERVICE_FILTER_OPTIONS.map((opt) => {
        const on = state.modalServiceFilter === opt.key ? ' on' : '';
        return `<button type="button" class="rd-sts-chip ${opt.cls}${on}" data-rd-sts="${opt.key}">${opt.label}</button>`;
      }).join('');
    } else {
      wrap.innerHTML = LEGACY_FILTER_OPTIONS.map((opt) => {
        const on = state.modalStatusFilters.has(opt.key) ? ' on' : '';
        return `<button type="button" class="rd-sts-chip ${opt.cls}${on}" data-rd-sts="${opt.key}">${opt.label}</button>`;
      }).join('');
    }
  }

  // Tables whose "Filter by status" bar is hidden from the UI for now. The
  // filter logic/state below is kept intact so it can be restored by simply
  // removing keys from this set.
  const HIDDEN_FILTER_TABLES = new Set(['AGENT', 'GROUND_HANDLER']);

  /** Configure the filter mode + defaults for a modal being opened. */
  function setupModalFilters(serviceKey) {
    if (SERVICE_STATUS_TABLES.has(serviceKey)) {
      state.modalFilterMode = 'service';
      state.modalServiceFilter = 'ALL';
    } else {
      state.modalFilterMode = 'legacy';
      state.modalStatusFilters = new Set(['REQUEST', 'CONFIRMED', 'INVOICED']);
    }
    renderModalFilters();

    // UI-only: hide the whole filter bar for selected tables (logic unchanged).
    const filtersEl = $('rdModalFilters');
    if (filtersEl) {
      filtersEl.style.display = HIDDEN_FILTER_TABLES.has(serviceKey) ? 'none' : '';
    }
  }

  function getFilteredModalRequests() {
    if (!state.modal) return [];
    return (state.modal.requests || []).filter((r) => matchesStatusFilter(r.status));
  }

  function updateModalCount() {
    const count = $('rdModalCount');
    const filtered = getFilteredModalRequests();
    const total = state.modal ? state.modal.requests.length : 0;
    if (count) {
      if (filtered.length === total) {
        count.textContent = `${total} record${total === 1 ? '' : 's'}`;
      } else {
        count.textContent = `${filtered.length} of ${total}`;
      }
    }
  }

  function renderModalRows(requests) {
    if (!requests.length) {
      return `<div class="rd-modal-empty">
        <i class="fas fa-inbox"></i>
        <p>No requests match the selected status filters for this period.</p>
      </div>`;
    }

    // Determine service type for different column layouts
    const isMealService = state.modal && state.modal.serviceKey === 'MEAL';
    const isHotelService = state.modal && state.modal.serviceKey === 'HOTEL';
    const isGuideService = state.modal && state.modal.serviceKey === 'GUIDE';
    const isTransportService = state.modal && state.modal.serviceKey === 'TRANSPORT';
    const isGroundHandlerService = state.modal && state.modal.serviceKey === 'GROUND_HANDLER';

    if (isMealService) {
      // Restaurant table with extended columns
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Date</th>
              <th>Request</th>
              <th>Group Name</th>
              <th>Nationality</th>
              <th>Meal</th>
              <th>PAX No</th>
              <th>Restaurant Note</th>
              <th>Status</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.day_of_week || '—')}</td>
                <td>${escapeHtml(r.date_display)}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td>${escapeHtml(r.meal || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.restaurant_note || '—')}</td>
                <td>${statusBadge(r.status)}</td>
                <td>${statusBadge(r.file_status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else if (isGuideService) {
      // Guides table with extended columns
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Date From</th>
              <th>Date To</th>
              <th>Request</th>
              <th>Group Name</th>
              <th>PAX</th>
              <th>Nationality</th>
              <th>Language</th>
              <th>Guide Notes</th>
              <th>Status</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.date_from || '—')}</td>
                <td>${escapeHtml(r.date_to || '—')}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td>${escapeHtml(r.language || '—')}</td>
                <td>${escapeHtml(r.guide_note || '—')}</td>
                <td>${statusBadge(r.status)}</td>
                <td>${statusBadge(r.file_status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else if (isTransportService) {
      // Transportation table with extended columns
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Num</th>
              <th>Date From</th>
              <th>Date To</th>
              <th>Request</th>
              <th>Group Name</th>
              <th>Nationality</th>
              <th>PAX</th>
              <th>Transportation Notes</th>
              <th>Status</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r, idx) => `
              <tr>
                <td class="num">${idx + 1}</td>
                <td>${escapeHtml(r.date_from || '—')}</td>
                <td>${escapeHtml(r.date_to || '—')}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.transport_note || '—')}</td>
                <td>${statusBadge(r.status)}</td>
                <td>${statusBadge(r.file_status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
              <tr class="rd-transport-detail-row">
                <td colspan="11">
                  <div class="rd-transport-details">
                    <div class="rd-transport-day"><strong>Day:</strong> ${escapeHtml(r.day_of_week || '—')}</div>
                    <div class="rd-transport-itinerary"><strong>Itinerary:</strong> ${escapeHtml(r.pickup_location || '—')} → ${escapeHtml(r.dropoff_location || '—')}</div>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else if (isGroundHandlerService) {
      // Meet & Assist table with extended columns
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Request</th>
              <th>Group Name</th>
              <th>PAX</th>
              <th>Nationality</th>
              <th>Description</th>
              <th>Time</th>
              <th>Flight Number</th>
              <th>M&A Notes</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.date_display)}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td>${escapeHtml(r.description || '—')}</td>
                <td style="white-space:nowrap;">${escapeHtml(r.time || '—')}</td>
                <td>${escapeHtml(r.flight_number || '—')}</td>
                <td>${escapeHtml(r.ma_notes || '—')}</td>
                <td>${statusBadge(r.status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else if (isHotelService) {
      // Accommodation table with extended columns
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Date From</th>
              <th>Date To</th>
              <th>Request</th>
              <th>Group Name</th>
              <th>PAX</th>
              <th>Nationality</th>
              <th>Meal Plan</th>
              <th>Nights</th>
              <th>Room Category</th>
              <th>SGL</th>
              <th>DBL</th>
              <th>TRPL</th>
              <th>Total</th>
              <th>Status</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.date_display)}</td>
                <td>${escapeHtml(r.check_out_date || '—')}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td>${escapeHtml(r.meal_plan || '—')}</td>
                <td class="num">${r.nights || 0}</td>
                <td>${escapeHtml(r.room_category || '—')}</td>
                <td class="num">${r.sgl || 0}</td>
                <td class="num">${r.dbl || 0}</td>
                <td class="num">${r.trpl || 0}</td>
                <td class="num">${r.total || 0}</td>
                <td>${statusBadge(r.status)}</td>
                <td>${statusBadge(r.file_status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else if (state.modal && state.modal.serviceKey === 'AGENT') {
      // Agent table with request details
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>From Date</th>
              <th>To Date</th>
              <th>Request ID</th>
              <th>Contact Name</th>
              <th>Group Name</th>
              <th>PAX</th>
              <th>Nationality</th>
              <th>File Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.from_date || '—')}</td>
                <td>${escapeHtml(r.to_date || '—')}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.contact_name || '—')}</td>
                <td>${escapeHtml(r.group_name || '—')}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.nationality || '—')}</td>
                <td>${statusBadge(r.status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    } else {
      // Original table for other services
      return `<div class="rd-modal-table-wrap">
        <table class="rd-modal-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Request</th>
              <th>Contact</th>
              <th>PAX</th>
              <th>Description</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${requests.map((r) => `
              <tr>
                <td>${escapeHtml(r.date_display)}</td>
                <td><strong>${escapeHtml(r.request_number)}</strong></td>
                <td>${escapeHtml(r.contact_name)}</td>
                <td class="num">${r.pax}</td>
                <td>${escapeHtml(r.description)}</td>
                <td>${statusBadge(r.status)}</td>
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
    }
  }

  function refreshModalTable() {
    const body = $('rdModalBody');
    if (body) body.innerHTML = renderModalRows(getFilteredModalRequests());
    updateModalCount();
  }

  function onFilterChipClick(statusKey) {
    if (state.modalFilterMode === 'service') {
      // Single-select: chosen status (or 'ALL') becomes the only active filter.
      state.modalServiceFilter = statusKey;
    } else {
      // Legacy multi-select toggle.
      if (state.modalStatusFilters.has(statusKey)) {
        state.modalStatusFilters.delete(statusKey);
      } else {
        state.modalStatusFilters.add(statusKey);
      }
    }

    renderModalFilters();
    refreshModalTable();
  }

  async function applySupplier(serviceKey) {
    const svc = initServiceState(serviceKey);
    if (!svc.supplierId) {
      const input = document.querySelector(`[data-rd-input="${serviceKey}"]`);
      if (input) input.focus();
      return;
    }

    const applyBtn = document.querySelector(`[data-rd-apply="${serviceKey}"]`);
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = `/inbound/run-down/supplier-requests?service=${encodeURIComponent(serviceKey)}`
      + `&supplier_id=${svc.supplierId}`
      + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load requests');

      setupModalFilters(serviceKey);

      state.modal = {
        serviceKey,
        serviceLabel: data.service_label,
        supplierName: data.supplier.name,
        dateLabel: data.date_from === data.date_to
          ? data.date_from_display
          : `${data.date_from_display} – ${data.date_to_display}`,
        requests: data.requests || [],
        total: data.total || 0,
      };
      openModal();
    } catch (err) {
      console.error('Apply error', err);
      alert('Could not load supplier requests. Please try again.');
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  function openModal() {
    const m = state.modal;
    if (!m) return;

    const title = $('rdModalTitle');
    const subtitle = $('rdModalSubtitle');

    if (m.serviceKey === 'AGENT') {
      if (title) title.textContent = `${m.serviceLabel} — ${m.agentName} — ${m.agentType}`;
    } else {
      if (title) title.textContent = `${m.serviceLabel} — ${m.supplierName}`;
    }
    if (subtitle) subtitle.textContent = `Requests for ${m.dateLabel}`;

    refreshModalTable();

    const el = $('rdRequestsModal');
    if (!el) return;
    if (!modalInstance) {
      modalInstance = bootstrap.Modal.getOrCreateInstance(el);
    }
    state.modalOpen = true;
    modalInstance.show();
  }

  function printPage() {
    state.printTs = formatPrintTs();
    updatePrintMeta();
    window.print();
  }

  function showDateAppliedIndicator() {
    const indicator = $('rdDateApplySuccess');
    if (indicator) indicator.classList.add('show');
  }

  function hideDateAppliedIndicator() {
    const indicator = $('rdDateApplySuccess');
    if (indicator) indicator.classList.remove('show');
  }

  function bindEvents() {
    const dateApplyBtn = $('rdDateApply');
    if (dateApplyBtn) {
      dateApplyBtn.addEventListener('click', () => {
        applyDateRange();
        showDateAppliedIndicator();
      });
    }

    const printBtn = $('rdPrintBtn');
    if (printBtn) printBtn.addEventListener('click', printPage);

    const filterChips = $('rdModalFilterChips');
    if (filterChips) {
      filterChips.addEventListener('click', (e) => {
        const chip = e.target.closest('[data-rd-sts]');
        if (chip) onFilterChipClick(chip.dataset.rdSts);
      });
    }

    document.querySelectorAll('[data-rd-input]').forEach((input) => {
      const serviceKey = input.dataset.rdInput;
      initServiceState(serviceKey);

      input.addEventListener('focus', () => {
        closeAllDropdowns(serviceKey);
        const svc = state.services[serviceKey];
        debouncedSearch(serviceKey, svc.query || input.value);
      });

      input.addEventListener('input', () => {
        const svc = state.services[serviceKey];
        svc.query = input.value;
        svc.supplierId = null;
        svc.supplierName = '';
        closeAllDropdowns(serviceKey);
        debouncedSearch(serviceKey, svc.query);
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          state.services[serviceKey].open = false;
          renderDropdown(serviceKey);
        }
      });
    });

    document.querySelectorAll('[data-rd-clear]').forEach((btn) => {
      btn.addEventListener('click', () => clearSupplier(btn.dataset.rdClear));
    });

    document.querySelectorAll('[data-rd-apply]').forEach((btn) => {
      btn.addEventListener('click', () => applySupplier(btn.dataset.rdApply));
    });

    document.addEventListener('click', (e) => {
      const pick = e.target.closest('[data-rd-pick]');
      if (pick) {
        selectSupplier(pick.dataset.rdPick, Number(pick.dataset.id), pick.dataset.name);
        return;
      }
      const pickAgent = e.target.closest('[data-rd-pick-agent]');
      if (pickAgent) {
        selectAgent(pickAgent.dataset.name);
        return;
      }
      if (!e.target.closest('.rd-supplier-wrap') && !e.target.closest('[data-rd-agent-wrap]')) {
        closeAllDropdowns(null);
      }
    });

    const agentInput = document.querySelector('[data-rd-agent-input]');
    if (agentInput) {
      agentInput.addEventListener('focus', () => {
        state.agent.open = true;
        debouncedAgentSearch(state.agent.query || agentInput.value);
      });

      agentInput.addEventListener('input', () => {
        state.agent.query = agentInput.value;
        state.agent.agentName = '';
        debouncedAgentSearch(state.agent.query);
      });

      agentInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          state.agent.open = false;
          renderAgentDropdown();
        }
      });
    }

    const agentClearBtn = document.querySelector('[data-rd-agent-clear]');
    if (agentClearBtn) {
      agentClearBtn.addEventListener('click', clearAgent);
    }

    const agentApplyBtn = document.querySelector('[data-rd-agent-apply]');
    if (agentApplyBtn) {
      agentApplyBtn.addEventListener('click', applyAgent);
    }

    // Preset buttons — fill fields only, never load data.
    document.querySelectorAll('[data-rd-preset]').forEach((btn) => {
      btn.addEventListener('click', () => applyPreset(btn.dataset.rdPreset));
    });

    // Clicking a styled field opens the native picker (mirrored value → display).
    document.querySelectorAll('.rd-date-native').forEach((input) => {
      input.addEventListener('click', () => {
        if (typeof input.showPicker === 'function') {
          try { input.showPicker(); } catch (_) { /* fall back to default */ }
        }
      });
    });

    const fromEl = $('rdDateFrom');
    const toEl = $('rdDateTo');
    const onDateChange = (which) => {
      updateFieldDisplay(which);
      hideDateAppliedIndicator();   // check disappears as soon as dates change
      clearPresetHighlight();       // manual edit no longer matches a preset
    };
    if (fromEl) fromEl.addEventListener('change', () => onDateChange('from'));
    if (toEl) toEl.addEventListener('change', () => onDateChange('to'));
  }

  /* ═══════════════════════════════════════════════════════════════════
     Accommodation inline section
     ═══════════════════════════════════════════════════════════════════ */

  const accomState = {
    city: '',
    category: '',
    hotelName: '',
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { cities: [], categories: [], hotel_names: [] },
    hotelDropdownOpen: false,
  };

  const ACCOM_STATUS_OPTIONS = [
    { key: 'REQUESTED', label: 'Requested', cls: 'requested' },
    { key: 'CONFIRMED', label: 'Confirmed', cls: 'confirmed' },
    { key: 'WAITING_LIST', label: 'Waiting List', cls: 'waiting' },
    { key: 'CANCELLED', label: 'Cancelled', cls: 'cancelled' },
    { key: 'ALL', label: 'All', cls: 'all' },
  ];

  function initAccomSection() {
    const hotelCard = document.querySelector('[data-rd-card="HOTEL"]');
    const template = $('rdAccomTemplate');
    if (!hotelCard || !template) return;

    const clone = template.content.cloneNode(true);
    hotelCard.parentNode.insertBefore(clone, hotelCard);
    hotelCard.remove();

    renderAccomPills();
    bindAccomEvents();
    fetchAccomFilters();
  }

  function renderAccomPills() {
    const wrap = $('rdAccomPills');
    if (!wrap) return;
    wrap.innerHTML = ACCOM_STATUS_OPTIONS.map((opt) => {
      const on = accomState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-accom-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onAccomPillClick(key) {
    if (key === 'ALL') {
      accomState.statuses.clear();
      accomState.statuses.add('ALL');
    } else {
      accomState.statuses.delete('ALL');
      if (accomState.statuses.has(key)) {
        accomState.statuses.delete(key);
      } else {
        accomState.statuses.add(key);
      }
      if (accomState.statuses.size === 0) {
        accomState.statuses.add('ALL');
      }
    }
    renderAccomPills();
  }

  function buildAccomUrl(includeStatuses) {
    let url = `/inbound/run-down/accommodation-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (accomState.city) url += `&city=${encodeURIComponent(accomState.city)}`;
    if (accomState.category) url += `&category=${encodeURIComponent(accomState.category)}`;
    if (accomState.hotelName) url += `&hotel_name=${encodeURIComponent(accomState.hotelName)}`;
    if (includeStatuses && !accomState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...accomState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchAccomFilters() {
    const url = buildAccomUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      accomState.total = data.total || 0;
      accomState.filterOptions = data.filters || { cities: [], categories: [], hotel_names: [] };
      updateAccomDropdowns();
      updateAccomCounts();
    } catch (err) {
      console.error('Accom filter fetch error', err);
    }
  }

  function updateAccomDropdowns() {
    const catSel = $('rdAccomCategory');
    const citySel = $('rdAccomCity');

    if (catSel) {
      const prev = catSel.value;
      catSel.innerHTML = '<option value="">All categories</option>' +
        accomState.filterOptions.categories.map(c => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
      if (accomState.filterOptions.categories.map(c => c.toLowerCase()).includes(prev.toLowerCase())) {
        catSel.value = prev;
      } else {
        catSel.value = '';
        accomState.category = '';
      }
    }

    if (citySel) {
      const prev = citySel.value;
      citySel.innerHTML = '<option value="">All cities</option>' +
        accomState.filterOptions.cities.map(c => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
      if (accomState.filterOptions.cities.map(c => c.toLowerCase()).includes(prev.toLowerCase())) {
        citySel.value = prev;
      } else {
        citySel.value = '';
        accomState.city = '';
      }
    }

    updateAccomHotelDropdown();
  }

  function updateAccomHotelDropdown() {
    const dropdown = $('rdAccomHotelDropdown');
    if (!dropdown) return;
    const input = $('rdAccomHotelInput');
    const query = (input ? input.value : '').toLowerCase();
    const names = accomState.filterOptions.hotel_names || [];
    const filtered = query ? names.filter(n => n.toLowerCase().includes(query)) : names;

    let html = `<button type="button" class="rd-accom-hotel-option${!accomState.hotelName ? ' active' : ''}" data-accom-hotel="">All hotels</button>`;
    html += filtered.map(n => {
      const active = n.toLowerCase() === (accomState.hotelName || '').toLowerCase() ? ' active' : '';
      return `<button type="button" class="rd-accom-hotel-option${active}" data-accom-hotel="${escapeAttr(n)}">${escapeHtml(n)}</button>`;
    }).join('');
    dropdown.innerHTML = html;
  }

  function updateAccomCounts() {
    const totalEl = $('rdAccomTotal');
    const showingEl = $('rdAccomShowing');
    if (totalEl) totalEl.textContent = accomState.total;
    if (showingEl) {
      showingEl.textContent = accomState.tableVisible ? `Showing ${accomState.filtered}` : '';
    }
  }

  async function applyAccom() {
    const applyBtn = $('rdAccomApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildAccomUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      accomState.total = data.total || 0;
      accomState.filtered = data.filtered || 0;
      accomState.tableVisible = true;
      renderAccomTable(data.hotels || []);
      updateAccomCounts();
    } catch (err) {
      console.error('Accom apply error', err);
      const results = $('rdAccomResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load accommodation data. Please try again.</p></div>`;
      }
      accomState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  function renderAccomTable(rows) {
    const results = $('rdAccomResults');
    if (!results) return;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No accommodation records match the selected filters for this period.</p></div>`;
      return;
    }

    const groups = {};
    const cityOrder = [];
    rows.forEach(r => {
      const city = r.city || 'Other';
      if (!groups[city]) {
        groups[city] = [];
        cityOrder.push(city);
      }
      groups[city].push(r);
    });

    let html = '<div class="rd-modal-table-wrap"><table class="rd-modal-table"><thead><tr>' +
      '<th>Date From</th><th>Date To</th><th>Request</th><th>Group Name</th>' +
      '<th>PAX</th><th>Nationality</th><th>Meal Plan</th><th>Nights</th>' +
      '<th>Room Category</th><th>SGL</th><th>DBL</th><th>TRPL</th><th>Total</th>' +
      '<th>Status</th><th>File Status</th><th></th>' +
      '</tr></thead><tbody>';

    cityOrder.forEach(city => {
      html += `<tr><td colspan="16" class="rd-accom-city-header">${escapeHtml(city)}</td></tr>`;
      groups[city].forEach(r => {
        html += `<tr>
          <td>${escapeHtml(r.date_display)}</td>
          <td>${escapeHtml(r.check_out_date || '—')}</td>
          <td><strong>${escapeHtml(r.request_number)}</strong></td>
          <td>${escapeHtml(r.group_name || '—')}</td>
          <td class="num">${r.pax}</td>
          <td>${escapeHtml(r.nationality || '—')}</td>
          <td>${escapeHtml(r.meal_plan || '—')}</td>
          <td class="num">${r.nights || 0}</td>
          <td>${escapeHtml(r.room_category || '—')}</td>
          <td class="num">${r.sgl || 0}</td>
          <td class="num">${r.dbl || 0}</td>
          <td class="num">${r.trpl || 0}</td>
          <td class="num">${r.total || 0}</td>
          <td>${statusBadge(r.status)}</td>
          <td>${statusBadge(r.file_status)}</td>
          <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
        </tr>`;
      });
    });

    html += '</tbody></table></div>';
    results.innerHTML = html;
  }

  function bindAccomEvents() {
    const toggle = $('rdAccomToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        accomState.collapsed = !accomState.collapsed;
        const body = $('rdAccomBody');
        const chevron = $('rdAccomChevron');
        if (body) body.classList.toggle('collapsed', accomState.collapsed);
        if (chevron) chevron.classList.toggle('open', !accomState.collapsed);
      });
    }

    const catSel = $('rdAccomCategory');
    if (catSel) {
      catSel.addEventListener('change', () => {
        accomState.category = catSel.value;
        accomState.city = '';
        accomState.hotelName = '';
        const input = $('rdAccomHotelInput');
        if (input) input.value = '';
        fetchAccomFilters();
      });
    }

    const citySel = $('rdAccomCity');
    if (citySel) {
      citySel.addEventListener('change', () => {
        accomState.city = citySel.value;
        accomState.hotelName = '';
        const input = $('rdAccomHotelInput');
        if (input) input.value = '';
        fetchAccomFilters();
      });
    }

    // Searchable hotel dropdown
    const hotelInput = $('rdAccomHotelInput');
    const hotelDropdown = $('rdAccomHotelDropdown');
    const hotelClear = $('rdAccomHotelClear');

    if (hotelInput && hotelDropdown) {
      hotelInput.addEventListener('focus', () => {
        accomState.hotelDropdownOpen = true;
        hotelDropdown.classList.add('open');
        updateAccomHotelDropdown();
      });

      hotelInput.addEventListener('input', () => {
        accomState.hotelDropdownOpen = true;
        hotelDropdown.classList.add('open');
        updateAccomHotelDropdown();
      });

      hotelInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          accomState.hotelDropdownOpen = false;
          hotelDropdown.classList.remove('open');
        }
      });

      hotelDropdown.addEventListener('click', (e) => {
        const opt = e.target.closest('[data-accom-hotel]');
        if (!opt) return;
        const name = opt.dataset.accomHotel;
        accomState.hotelName = name;
        hotelInput.value = name || '';
        hotelInput.placeholder = name ? name : 'All hotels';
        accomState.hotelDropdownOpen = false;
        hotelDropdown.classList.remove('open');
      });

      document.addEventListener('click', (e) => {
        if (!e.target.closest('#rdAccomHotelWrap')) {
          accomState.hotelDropdownOpen = false;
          hotelDropdown.classList.remove('open');
        }
      });
    }

    if (hotelClear) {
      hotelClear.addEventListener('click', () => {
        accomState.hotelName = '';
        if (hotelInput) {
          hotelInput.value = '';
          hotelInput.placeholder = 'All hotels';
        }
      });
    }

    // Status pills
    const pillsWrap = $('rdAccomPills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-accom-sts]');
        if (pill) onAccomPillClick(pill.dataset.accomSts);
      });
    }

    // Apply
    const applyBtn = $('rdAccomApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyAccom);
    }
  }

  function refreshAccomOnDateChange() {
    fetchAccomFilters();
    if (accomState.tableVisible) {
      applyAccom();
    }
  }


  function init() {
    const root = $('runDownApp');
    if (!root) return;

    state.dateFrom = root.dataset.dateFrom || '';
    state.dateTo = root.dataset.dateTo || '';
    state.appliedDateFrom = state.dateFrom;
    state.appliedDateTo = state.dateTo;

    (root.dataset.services || '').split(',').filter(Boolean).forEach(initServiceState);

    bindEvents();
    updateFieldDisplay('from');
    updateFieldDisplay('to');
    updatePrintMeta();

    // Track modal visibility so date-Apply only refreshes a genuinely open modal.
    const modalEl = $('rdRequestsModal');
    if (modalEl) {
      modalEl.addEventListener('hidden.bs.modal', () => { state.modalOpen = false; });
    }

    // Initialize accommodation inline section
    initAccomSection();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
