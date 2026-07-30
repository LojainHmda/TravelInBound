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
    modalStatusFilters: new Set(['REQUEST', 'CONFIRMED', 'INVOICED']),
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

  function formatPrintTs() {
    const now = new Date();
    return now.toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  function dateRangeLabel() {
    const from = state.appliedDateFrom || state.dateFrom;
    const to = state.appliedDateTo || state.dateTo;
    if (from === to) return formatDateDisplay(from);
    return `${formatDateDisplay(from)} – ${formatDateDisplay(to)}`;
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
      el.textContent = `Selected period: ${dateRangeLabel()} · Printed: ${state.printTs || formatPrintTs()}`;
    }
    const hdr = $('rdPrintHeaderDates');
    if (hdr) {
      hdr.innerHTML = `<strong>Selected period:</strong> ${dateRangeLabel()}<br><strong>Printed:</strong> ${state.printTs || formatPrintTs()}`;
    }
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

      state.modalStatusFilters = new Set(['REQUEST', 'CONFIRMED', 'INVOICED']);
      document.querySelectorAll('[data-rd-sts]').forEach((chip) => chip.classList.add('on'));

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
    if (!state.modalStatusFilters.size) return true;
    const bucket = STATUS_FILTER_MAP[(status || 'REQUEST').toUpperCase()] || 'REQUEST';
    return state.modalStatusFilters.has(bucket);
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
              <th>Notes</th>
              <th>Restaurant Note</th>
              <th>Status</th>
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
                <td>${escapeHtml(r.notes || '—')}</td>
                <td>${escapeHtml(r.restaurant_note || '—')}</td>
                <td>${statusBadge(r.status)}</td>
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
                <td><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
              </tr>
              <tr class="rd-transport-detail-row">
                <td colspan="10">
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
              <th>Status</th>
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
              <th>Status</th>
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

  function toggleModalStatus(statusKey) {
    if (state.modalStatusFilters.has(statusKey)) {
      state.modalStatusFilters.delete(statusKey);
    } else {
      state.modalStatusFilters.add(statusKey);
    }

    document.querySelectorAll('[data-rd-sts]').forEach((chip) => {
      const key = chip.dataset.rdSts;
      const bucket = key;
      const cls = key === 'REQUEST' ? 'requested' : key === 'CONFIRMED' ? 'confirmed' : 'invoiced';
      chip.classList.toggle('on', state.modalStatusFilters.has(bucket));
      chip.classList.toggle(cls, true);
    });

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

      state.modalStatusFilters = new Set(['REQUEST', 'CONFIRMED', 'INVOICED']);
      document.querySelectorAll('[data-rd-sts]').forEach((chip) => chip.classList.add('on'));

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

    document.querySelectorAll('[data-rd-sts]').forEach((chip) => {
      chip.addEventListener('click', () => toggleModalStatus(chip.dataset.rdSts));
    });

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

    const fromEl = $('rdDateFrom');
    const toEl = $('rdDateTo');
    if (fromEl) fromEl.addEventListener('change', hideDateAppliedIndicator);
    if (toEl) toEl.addEventListener('change', hideDateAppliedIndicator);
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
    updatePrintMeta();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
