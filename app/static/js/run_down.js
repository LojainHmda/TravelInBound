/**
 * Run Down page — date-filtered supplier lookup per service category.
 */
(function () {
  'use strict';

  const STATUS_CLASS = {
    REQUEST: 'sts-request',
    REQUESTED: 'sts-request',
    QUOTED: 'sts-quoted',
    RESERVED: 'sts-reserved',
    CONFIRMED: 'sts-confirmed',
    INVOICED: 'sts-invoiced',
    COMPLETED: 'sts-completed',
    CANCELLED: 'sts-cancelled',
    DELETED: 'sts-cancelled',
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

  /* Deep link to the exact service item behind a row: the request page opens
     the mapped tab and the item itself. section_key comes from the API
     (RUN_DOWN_SECTIONS server-side) — never hardcoded here. Falls back to the
     plain request URL when either part is missing. */
  function deepLinkUrl(r) {
    if (!r || !r.section_key || !r.record_id) return (r && r.view_url) || '';
    return `${r.view_url}?section=${encodeURIComponent(r.section_key)}&item=${encodeURIComponent(r.record_id)}`;
  }

  /* ════════════════════════════════════════════════════════════════
     Client-side pagination for the inline results tables.

     Purely a display concern: the server still returns the complete filtered
     + sorted row list, and every section keeps showing its full `filtered`
     count. Each renderXxxTable() slices the already-filtered, already-sorted
     array before its existing grouping walk, so the table columns, grouping
     and row order are untouched.
     ════════════════════════════════════════════════════════════════ */

  const RD_PAGE_SIZE = 15;

  /* True only while a section is being re-rendered for printing. Print output
     ignores pagination entirely: every row of the filtered set is laid down as
     one continuous flow. The rows are already in memory (sectionState.allRows),
     so this costs no extra request. */
  let printingAllRows = false;

  /** Clamp `page` into range and return that page's slice of `rows`.
   *  While `printingAllRows` is set every row is returned instead: `page` is
   *  passed straight back so the caller's `state.page = pg.page` keeps the page
   *  the user is on, and `totalPages: 1` makes paginationHtml() render nothing. */
  function paginate(rows, page) {
    const totalPages = Math.max(1, Math.ceil(rows.length / RD_PAGE_SIZE));
    const current = Math.min(Math.max(parseInt(page, 10) || 1, 1), totalPages);
    if (printingAllRows) {
      return { pageRows: rows, page: current, totalPages: 1, start: 0 };
    }
    const start = (current - 1) * RD_PAGE_SIZE;
    return {
      pageRows: rows.slice(start, start + RD_PAGE_SIZE),
      page: current,
      totalPages: totalPages,
      start: start,
    };
  }

  /** Page-number window: always first + last, current ±1, '…' for the gaps. */
  function paginationPages(current, totalPages) {
    const out = [];
    for (let p = 1; p <= totalPages; p++) {
      if (p !== 1 && p !== totalPages && Math.abs(p - current) > 1) continue;
      const prev = out[out.length - 1];
      if (typeof prev === 'number' && p - prev > 1) out.push('…');
      out.push(p);
    }
    return out;
  }

  /** Controls strip rendered below a results table. '' when there is 1 page. */
  function paginationHtml(pg, totalRows) {
    if (pg.totalPages <= 1) return '';
    const first = pg.start + 1;
    const last = pg.start + pg.pageRows.length;
    const btn = (label, page, opts) => {
      const o = opts || {};
      const cls = 'rd-page-btn' + (o.active ? ' active' : '') + (o.disabled ? ' disabled' : '');
      const attr = o.disabled ? ' disabled' : ` data-rd-page="${page}"`;
      return `<button type="button" class="${cls}"${attr}>${label}</button>`;
    };
    let btns = btn('<i class="fas fa-chevron-left"></i> Prev', pg.page - 1, { disabled: pg.page <= 1 });
    paginationPages(pg.page, pg.totalPages).forEach((p) => {
      btns += (p === '…')
        ? '<span class="rd-page-gap">…</span>'
        : btn(String(p), p, { active: p === pg.page });
    });
    btns += btn('Next <i class="fas fa-chevron-right"></i>', pg.page + 1, { disabled: pg.page >= pg.totalPages });
    return `<div class="rd-pagination">
        <span class="rd-page-info">${first}–${last} of ${totalRows}</span>
        <div class="rd-page-btns">${btns}</div>
      </div>`;
  }

  /** One delegated listener per results container; bound once at section init. */
  function bindPagination(container, sectionState, rerender) {
    if (!container) return;
    container.addEventListener('click', (e) => {
      const btn = e.target.closest('.rd-page-btn[data-rd-page]');
      if (!btn || !container.contains(btn)) return;
      e.preventDefault();
      const page = parseInt(btn.getAttribute('data-rd-page'), 10);
      if (!page || page === sectionState.page) return;
      sectionState.page = page;
      rerender();
    });
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

    // Option A: an already-open modal auto-refreshes to the new range,
    // reusing the same supplier it was opened for.
    refreshOpenModal();

    // Refresh agent inline section for new date range
    refreshAgentOnDateChange();

    // Refresh accommodation inline section for new date range
    refreshAccomOnDateChange();

    // Refresh transportation inline section for new date range
    refreshTransportOnDateChange();

    // Refresh guide inline section for new date range
    refreshGuideOnDateChange();

    // Refresh restaurant inline section for new date range
    refreshRestaurantOnDateChange();

    // Refresh Meet & Assist inline section for new date range
    refreshMeetAssistOnDateChange();

    // Refresh the cut-off table, if one is showing, for new date range
    refreshCutOffOnDateChange();
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
   *  same supplier and the current status-filter selection. Shows a
   *  loading overlay; on failure keeps the previous rows and shows an inline
   *  error instead of blanking the modal. */
  async function refreshOpenModal() {
    if (!state.modalOpen || !state.modal) return;
    const m = state.modal;

    const svc = state.services[m.serviceKey];
    if (!svc || !svc.supplierId) return;
    const url = `/inbound/run-down/supplier-requests?service=${encodeURIComponent(m.serviceKey)}`
      + `&supplier_id=${svc.supplierId}`
      + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;

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
  const HIDDEN_FILTER_TABLES = new Set(['GROUND_HANDLER']);

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

    if (title) title.textContent = `${m.serviceLabel} — ${m.supplierName}`;
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

  /** Section id -> print label + the section's own re-render. Built on demand so
   *  the per-section state consts are all initialised by the time it is read. */
  function sectionPrintTargets() {
    return {
      rdAccomSection: { label: 'Accommodation', rerender: () => renderAccomTable(accomState.allRows) },
      rdTransportSection: { label: 'Transportation', rerender: () => renderTransportTable(transportState.allRows) },
      rdGuideSection: { label: 'Guide', rerender: () => renderGuideTable(guideState.allRows) },
      rdRestaurantSection: { label: 'Restaurant', rerender: () => renderRestaurantTable(restaurantState.allRows) },
      rdMeetAssistSection: { label: 'Meet & Assist', rerender: () => renderMeetAssistTable(meetAssistState.allRows) },
      rdAgentSection: { label: 'Agent', rerender: () => renderAgentTable(agentState.allRows) },
      rdCutOffSection: { label: cutOffPrintLabel(), rerender: () => renderCutOffTable(cutOffState.allRows) },
    };
  }

  /** Print one inline section's table on its own — same window.print() + print
   *  CSS mechanism as printPage(), scoped to `sectionId` by body.rd-printing-section
   *  and .rd-print-target. The section is re-rendered with every row first, then
   *  restored to the page it was showing once the print dialog closes. */
  function printSection(sectionId) {
    const target = sectionPrintTargets()[sectionId];
    const section = $(sectionId);
    if (!target || !section) return;

    state.printTs = formatPrintTs();
    updatePrintMeta();

    const heading = $('rdPrintHeaderTitle');
    const headingText = heading ? heading.textContent : '';
    if (heading) heading.textContent = target.label;

    printingAllRows = true;
    target.rerender();
    section.classList.add('rd-print-target');
    document.body.classList.add('rd-printing-section');

    let restored = false;
    const restore = () => {
      if (restored) return;
      restored = true;
      window.removeEventListener('afterprint', restore);
      document.body.classList.remove('rd-printing-section');
      section.classList.remove('rd-print-target');
      if (heading) heading.textContent = headingText;
      printingAllRows = false;
      target.rerender();
    };

    window.addEventListener('afterprint', restore);
    try {
      window.print();
    } finally {
      // Fallback for browsers that never fire afterprint; no-op once restored.
      setTimeout(restore, 1000);
    }
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

    // Per-section Print buttons. Delegated: the sections are cloned out of
    // <template> and injected after this runs.
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-rd-print-section]');
      if (btn) printSection(btn.getAttribute('data-rd-print-section'));
    });

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
      if (!e.target.closest('.rd-supplier-wrap')) {
        closeAllDropdowns(null);
      }
    });

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
    page: 1,
    allRows: [],
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
      updateStatCard('HOTEL', data.stats);
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
      accomState.page = 1;
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

    // Grouping order: city (server order, first-seen wins), then hotel name A-Z,
    // then date ascending. Sorted before paginate so a hotel's rows stay
    // contiguous. Reorders only — same rows in, same rows out.
    const cityRank = new Map();
    rows.forEach((r) => {
      const city = r.city || 'Other';
      if (!cityRank.has(city)) cityRank.set(city, cityRank.size);
    });
    rows = rows.slice().sort((a, b) => {
      const ca = cityRank.get(a.city || 'Other');
      const cb = cityRank.get(b.city || 'Other');
      if (ca !== cb) return ca - cb;
      const ha = (a.hotel_name || '').toLowerCase();
      const hb = (b.hotel_name || '').toLowerCase();
      if (ha !== hb) return ha < hb ? -1 : 1;
      return (a.date || '').localeCompare(b.date || '');
    });

    accomState.allRows = rows;
    const pg = paginate(rows, accomState.page);
    accomState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No accommodation records match the selected filters for this period.</p></div>`;
      return;
    }

    // Group by City → Hotel, preserving the sorted order above. Each group gets a
    // single "City — Hotel" heading; the table columns are unchanged.
    const groups = {};
    const order = [];
    rows.forEach((r) => {
      const city = r.city || 'Other';
      const name = r.hotel_name || 'Not Assigned';
      const key = `${city} ${name}`;
      if (!groups[key]) { groups[key] = { label: `${city} — ${name}`, rows: [] }; order.push(key); }
      groups[key].rows.push(r);
    });

    let html = '<div class="rd-modal-table-wrap"><table class="rd-modal-table"><thead><tr>' +
      '<th>Date From</th><th>Date To</th><th>Request</th><th>Group Name</th>' +
      '<th>PAX</th><th>Nationality</th><th>Meal Plan</th><th>Nights</th>' +
      '<th>Room Category</th><th>SGL</th><th>DBL</th><th>TRPL</th><th>Total</th>' +
      '<th>Status</th><th class="rd-col-file-status">File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead><tbody>';

    order.forEach((key) => {
      html += `<tr><td colspan="16" class="rd-accom-city-header">${escapeHtml(groups[key].label)}<span class="rd-accom-group-count">${groups[key].rows.length}</span></td></tr>`;
      groups[key].rows.forEach((r) => {
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
          <td class="rd-col-file-status">${statusBadge(r.file_status)}</td>
          <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
        </tr>`;
      });
    });

    html += '</tbody></table></div>';
    results.innerHTML = html + paginationHtml(pg, accomState.allRows.length);
  }

  function bindAccomEvents() {
    bindPagination($('rdAccomResults'), accomState, () => renderAccomTable(accomState.allRows));
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

  /* ═══════════════════════════════════════════════════════════════════
     Transportation inline section

     Mirrors the Accommodation section (same layout / status pills / inline
     results) but the Vehicle, Company and Assignment filters are INDEPENDENT
     — selecting one never changes the options offered by another. All filters
     combine with the applied date range. When "All Vehicles" is selected the
     results are grouped by vehicle; otherwise a single table is shown.
     ═══════════════════════════════════════════════════════════════════ */

  const transportState = {
    vehicle: '',
    company: '',
    assignment: '',          // '' = All, 'ASSIGNED', 'NOT_ASSIGNED'
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { vehicles: [], companies: [] },
    page: 1,
    allRows: [],
  };

  function initTransportSection() {
    const transportCard = document.querySelector('[data-rd-card="TRANSPORT"]');
    const template = $('rdTransportTemplate');
    if (!transportCard || !template) return;

    const clone = template.content.cloneNode(true);
    transportCard.parentNode.insertBefore(clone, transportCard);
    transportCard.remove();

    renderTransportPills();
    bindTransportEvents();
    syncTransportCompanyDisabled();
    fetchTransportFilters();
  }

  function renderTransportPills() {
    const wrap = $('rdTransportPills');
    if (!wrap) return;
    // Reuse the shared Accommodation status options for identical look & behaviour.
    wrap.innerHTML = ACCOM_STATUS_OPTIONS.map((opt) => {
      const on = transportState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-transport-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onTransportPillClick(key) {
    if (key === 'ALL') {
      transportState.statuses.clear();
      transportState.statuses.add('ALL');
    } else {
      transportState.statuses.delete('ALL');
      if (transportState.statuses.has(key)) {
        transportState.statuses.delete(key);
      } else {
        transportState.statuses.add(key);
      }
      if (transportState.statuses.size === 0) {
        transportState.statuses.add('ALL');
      }
    }
    renderTransportPills();
  }

  /** Company can't be combined with "Not Assigned" — disable & reset it. */
  function syncTransportCompanyDisabled() {
    const companySel = $('rdTransportCompany');
    if (!companySel) return;
    const notAssigned = transportState.assignment === 'NOT_ASSIGNED';
    companySel.disabled = notAssigned;
    if (notAssigned) {
      companySel.value = '';
      transportState.company = '';
    }
  }

  function buildTransportUrl(includeStatuses) {
    let url = `/inbound/run-down/transportation-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (transportState.vehicle) url += `&vehicle=${encodeURIComponent(transportState.vehicle)}`;
    if (transportState.company) url += `&company=${encodeURIComponent(transportState.company)}`;
    if (transportState.assignment) url += `&assignment=${encodeURIComponent(transportState.assignment)}`;
    if (includeStatuses && !transportState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...transportState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchTransportFilters() {
    const url = buildTransportUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      transportState.total = data.total || 0;
      updateStatCard('TRANSPORT', data.stats);
      transportState.filterOptions = data.filters || { vehicles: [], companies: [] };
      updateTransportDropdowns();
      updateTransportCounts();
    } catch (err) {
      console.error('Transport filter fetch error', err);
    }
  }

  function updateTransportDropdowns() {
    const vehicleSel = $('rdTransportVehicle');
    const companySel = $('rdTransportCompany');

    if (vehicleSel) {
      const prev = vehicleSel.value;
      vehicleSel.innerHTML = '<option value="">All Vehicles</option>' +
        transportState.filterOptions.vehicles.map(v => `<option value="${escapeAttr(v)}">${escapeHtml(v)}</option>`).join('');
      if (transportState.filterOptions.vehicles.map(v => v.toLowerCase()).includes(prev.toLowerCase())) {
        vehicleSel.value = prev;
      } else {
        vehicleSel.value = '';
        transportState.vehicle = '';
      }
    }

    if (companySel) {
      const prev = companySel.value;
      companySel.innerHTML = '<option value="">All Companies</option>' +
        transportState.filterOptions.companies.map(c => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
      if (transportState.filterOptions.companies.map(c => c.toLowerCase()).includes(prev.toLowerCase())) {
        companySel.value = prev;
      } else {
        companySel.value = '';
        transportState.company = '';
      }
    }

    syncTransportCompanyDisabled();
  }

  function updateTransportCounts() {
    const totalEl = $('rdTransportTotal');
    const showingEl = $('rdTransportShowing');
    if (totalEl) totalEl.textContent = transportState.total;
    if (showingEl) {
      showingEl.textContent = transportState.tableVisible ? `Showing ${transportState.filtered}` : '';
    }
  }

  async function applyTransport() {
    const applyBtn = $('rdTransportApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildTransportUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      transportState.total = data.total || 0;
      transportState.filtered = data.filtered || 0;
      transportState.tableVisible = true;
      transportState.page = 1;
      renderTransportTable(data.transports || []);
      updateTransportCounts();
    } catch (err) {
      console.error('Transport apply error', err);
      const results = $('rdTransportResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load transportation data. Please try again.</p></div>`;
      }
      transportState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  /** Render one Transportation record as its main row + detail sub-row.
   *  Markup/columns are identical to the existing popup table. */
  /* Group labels for the transportation table. company comes from the row's
     supplier_name — the same field the request page shows. */
  function transportCompanyOf(r) {
    return (r.company || '').trim() || 'Not Assigned';
  }

  function transportVehicleOf(r) {
    return (r.vehicle || '').trim() || 'Unspecified';
  }

  function transportRowPair(r, num) {
    return `<tr>
        <td class="num">${num}</td>
        <td>${escapeHtml(r.date_from || '—')}</td>
        <td>${escapeHtml(r.date_to || '—')}</td>
        <td><strong>${escapeHtml(r.request_number)}</strong></td>
        <td>${escapeHtml(r.group_name || '—')}</td>
        <td>${escapeHtml(r.nationality || '—')}</td>
        <td class="num">${r.pax}</td>
        <td>${escapeHtml(r.transport_note || '—')}</td>
        <td>${statusBadge(r.status)}</td>
        <td class="rd-col-file-status">${statusBadge(r.file_status)}</td>
        <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>
      <tr class="rd-transport-detail-row">
        <td colspan="11">
          <div class="rd-transport-details">
            <div class="rd-transport-day"><strong>Day:</strong> ${escapeHtml(r.day_of_week || '—')}</div>
            <div class="rd-transport-itinerary"><strong>Itinerary:</strong> ${escapeHtml(r.pickup_location || '—')} → ${escapeHtml(r.dropoff_location || '—')}</div>
          </div>
        </td>
      </tr>`;
  }

  function renderTransportTable(rows) {
    const results = $('rdTransportResults');
    if (!results) return;

    // Grouping order: assigned companies A-Z first and everything not assigned
    // last (the convention Meet & Assist already uses), then vehicle A-Z, then
    // date ascending. Sorted before paginate so a vehicle's rows stay contiguous.
    // Reorders only — same rows in, same rows out.
    rows = rows.slice().sort((a, b) => {
      const ua = (a.company || '').trim() ? 0 : 1;
      const ub = (b.company || '').trim() ? 0 : 1;
      if (ua !== ub) return ua - ub;
      const ca = transportCompanyOf(a).toLowerCase();
      const cb = transportCompanyOf(b).toLowerCase();
      if (ca !== cb) return ca < cb ? -1 : 1;
      const va = transportVehicleOf(a).toLowerCase();
      const vb = transportVehicleOf(b).toLowerCase();
      if (va !== vb) return va < vb ? -1 : 1;
      return (a.date || '').localeCompare(b.date || '');
    });

    transportState.allRows = rows;
    const pg = paginate(rows, transportState.page);
    transportState.page = pg.page;
    rows = pg.pageRows;
    let rowNum = pg.start;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No transportation records match the selected filters for this period.</p></div>`;
      return;
    }

    const thead = '<thead><tr>' +
      '<th>Num</th><th>Date From</th><th>Date To</th><th>Request</th>' +
      '<th>Group Name</th><th>Nationality</th><th>PAX</th>' +
      '<th>Transportation Notes</th><th>Status</th><th class="rd-col-file-status">File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead>';

    // company -> vehicle -> rows, both levels keeping the order set by the sort
    // above. Both headers always render, whichever filters are applied.
    const groups = {};
    const companyOrder = [];
    rows.forEach((r) => {
      const company = transportCompanyOf(r);
      if (!groups[company]) {
        groups[company] = { vehicles: {}, order: [] };
        companyOrder.push(company);
      }
      const vehicle = transportVehicleOf(r);
      if (!groups[company].vehicles[vehicle]) {
        groups[company].vehicles[vehicle] = [];
        groups[company].order.push(vehicle);
      }
      groups[company].vehicles[vehicle].push(r);
    });

    let body = '';
    companyOrder.forEach((company) => {
      body += `<tr><td colspan="11" class="rd-accom-city-header rd-transport-group-company">${escapeHtml(company)}</td></tr>`;
      groups[company].order.forEach((vehicle) => {
        const vehicleRows = groups[company].vehicles[vehicle];
        body += `<tr><td colspan="11" class="rd-accom-city-header rd-transport-group-vehicle">${escapeHtml(vehicle)}<span class="rd-accom-group-count">${vehicleRows.length}</span></td></tr>`;
        vehicleRows.forEach((r) => { body += transportRowPair(r, ++rowNum); });
      });
    });

    results.innerHTML = `<div class="rd-modal-table-wrap"><table class="rd-modal-table">${thead}<tbody>${body}</tbody></table></div>` + paginationHtml(pg, transportState.allRows.length);
  }

  function bindTransportEvents() {
    bindPagination($('rdTransportResults'), transportState, () => renderTransportTable(transportState.allRows));
    const toggle = $('rdTransportToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        transportState.collapsed = !transportState.collapsed;
        const body = $('rdTransportBody');
        const chevron = $('rdTransportChevron');
        if (body) body.classList.toggle('collapsed', transportState.collapsed);
        if (chevron) chevron.classList.toggle('open', !transportState.collapsed);
      });
    }

    // Vehicle / Company / Assignment are INDEPENDENT — a change never refetches
    // the other dropdowns' options (no cascade). Assignment only toggles the
    // Company enabled state.
    const vehicleSel = $('rdTransportVehicle');
    if (vehicleSel) {
      vehicleSel.addEventListener('change', () => { transportState.vehicle = vehicleSel.value; });
    }

    const companySel = $('rdTransportCompany');
    if (companySel) {
      companySel.addEventListener('change', () => { transportState.company = companySel.value; });
    }

    const assignmentSel = $('rdTransportAssignment');
    if (assignmentSel) {
      assignmentSel.addEventListener('change', () => {
        transportState.assignment = assignmentSel.value;
        syncTransportCompanyDisabled();
      });
    }

    const pillsWrap = $('rdTransportPills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-transport-sts]');
        if (pill) onTransportPillClick(pill.dataset.transportSts);
      });
    }

    const applyBtn = $('rdTransportApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyTransport);
    }
  }

  function refreshTransportOnDateChange() {
    fetchTransportFilters();
    if (transportState.tableVisible) {
      applyTransport();
    }
  }

  /* ═══════════════════════════════════════════════════════════════════
     Guide inline section

     Mirrors the Transportation section (same layout / status pills / inline
     results). Language, Guide Name and Assignment are INDEPENDENT filters —
     selecting one never changes the options offered by another, and all
     combine with the applied date range.

     • Language and Guide Name are searchable dropdowns (reusing the
       Accommodation searchable-dropdown component).
     • Assignment is decided solely by Guide Name presence (server-side); when
       "Not Assigned" is selected the Guide Name filter is disabled & reset.
     • Results are grouped by Language whenever "All Languages" is selected;
       otherwise a single flat table is shown.
     ═══════════════════════════════════════════════════════════════════ */

  const guideState = {
    language: '',
    guideName: '',
    assignment: '',          // '' = All, 'ASSIGNED', 'NOT_ASSIGNED'
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { languages: [], guides: [] },
    page: 1,
    allRows: [],
  };

  let guideLangCtl = null;
  let guideNameCtl = null;

  function initGuideSection() {
    const guideCard = document.querySelector('[data-rd-card="GUIDE"]');
    const template = $('rdGuideTemplate');
    if (!guideCard || !template) return;

    const clone = template.content.cloneNode(true);
    guideCard.parentNode.insertBefore(clone, guideCard);
    guideCard.remove();

    renderGuidePills();
    bindGuideEvents();
    syncGuideNameDisabled();
    fetchGuideFilters();
  }

  function renderGuidePills() {
    const wrap = $('rdGuidePills');
    if (!wrap) return;
    // Reuse the shared Accommodation status options for identical look & behaviour.
    wrap.innerHTML = ACCOM_STATUS_OPTIONS.map((opt) => {
      const on = guideState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-guide-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onGuidePillClick(key) {
    if (key === 'ALL') {
      guideState.statuses.clear();
      guideState.statuses.add('ALL');
    } else {
      guideState.statuses.delete('ALL');
      if (guideState.statuses.has(key)) {
        guideState.statuses.delete(key);
      } else {
        guideState.statuses.add(key);
      }
      if (guideState.statuses.size === 0) {
        guideState.statuses.add('ALL');
      }
    }
    renderGuidePills();
  }

  /** Guide Name can't be combined with "Not Assigned" — disable & reset it. */
  function syncGuideNameDisabled() {
    const input = $('rdGuideNameInput');
    const clear = $('rdGuideNameClear');
    const notAssigned = guideState.assignment === 'NOT_ASSIGNED';
    if (input) {
      input.disabled = notAssigned;
      if (notAssigned) {
        input.value = '';
        input.placeholder = 'All Guides';
      }
    }
    if (clear) clear.disabled = notAssigned;
    if (notAssigned) {
      guideState.guideName = '';
      const dropdown = $('rdGuideNameDropdown');
      if (dropdown) dropdown.classList.remove('open');
    }
  }

  /** Build a searchable dropdown bound to a guideState key. Returns { render }. */
  function makeGuideSearchable(cfg) {
    const input = $(cfg.inputId);
    const dropdown = $(cfg.dropdownId);
    const clear = $(cfg.clearId);
    if (!input || !dropdown) return { render() {} };

    function render() {
      const query = input.value.toLowerCase();
      const opts = cfg.getOptions() || [];
      const filtered = query ? opts.filter((o) => o.toLowerCase().includes(query)) : opts;
      const selected = guideState[cfg.stateKey] || '';
      let html = `<button type="button" class="rd-accom-hotel-option${!selected ? ' active' : ''}" data-guide-opt="">${cfg.allLabel}</button>`;
      html += filtered.map((o) => {
        const active = o.toLowerCase() === selected.toLowerCase() ? ' active' : '';
        return `<button type="button" class="rd-accom-hotel-option${active}" data-guide-opt="${escapeAttr(o)}">${escapeHtml(o)}</button>`;
      }).join('');
      dropdown.innerHTML = html;
    }

    input.addEventListener('focus', () => {
      if (input.disabled) return;
      dropdown.classList.add('open');
      render();
    });
    input.addEventListener('input', () => {
      dropdown.classList.add('open');
      render();
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') dropdown.classList.remove('open');
    });
    dropdown.addEventListener('click', (e) => {
      const opt = e.target.closest('[data-guide-opt]');
      if (!opt) return;
      const val = opt.dataset.guideOpt;
      guideState[cfg.stateKey] = val;
      input.value = val || '';
      input.placeholder = val || cfg.allLabel;
      dropdown.classList.remove('open');
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest(cfg.wrapSel)) dropdown.classList.remove('open');
    });
    if (clear) {
      clear.addEventListener('click', () => {
        if (clear.disabled) return;
        guideState[cfg.stateKey] = '';
        input.value = '';
        input.placeholder = cfg.allLabel;
        render();
      });
    }
    return { render };
  }

  function buildGuideUrl(includeStatuses) {
    let url = `/inbound/run-down/guide-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (guideState.language) url += `&language=${encodeURIComponent(guideState.language)}`;
    if (guideState.guideName) url += `&guide_name=${encodeURIComponent(guideState.guideName)}`;
    if (guideState.assignment) url += `&assignment=${encodeURIComponent(guideState.assignment)}`;
    if (includeStatuses && !guideState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...guideState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchGuideFilters() {
    const url = buildGuideUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      guideState.total = data.total || 0;
      updateStatCard('GUIDE', data.stats);
      guideState.filterOptions = data.filters || { languages: [], guides: [] };
      updateGuideDropdowns();
      updateGuideCounts();
    } catch (err) {
      console.error('Guide filter fetch error', err);
    }
  }

  function updateGuideDropdowns() {
    // Drop a stale selection that is no longer offered for the current range.
    const langs = guideState.filterOptions.languages || [];
    if (guideState.language && !langs.map((l) => l.toLowerCase()).includes(guideState.language.toLowerCase())) {
      guideState.language = '';
      const input = $('rdGuideLanguageInput');
      if (input) input.value = '';
    }
    const names = guideState.filterOptions.guides || [];
    if (guideState.guideName && !names.map((n) => n.toLowerCase()).includes(guideState.guideName.toLowerCase())) {
      guideState.guideName = '';
      const input = $('rdGuideNameInput');
      if (input) input.value = '';
    }
    if (guideLangCtl) guideLangCtl.render();
    if (guideNameCtl) guideNameCtl.render();
  }

  function updateGuideCounts() {
    const totalEl = $('rdGuideTotal');
    const showingEl = $('rdGuideShowing');
    if (totalEl) totalEl.textContent = guideState.total;
    if (showingEl) {
      showingEl.textContent = guideState.tableVisible ? `Showing ${guideState.filtered}` : '';
    }
  }

  async function applyGuide() {
    const applyBtn = $('rdGuideApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildGuideUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      guideState.total = data.total || 0;
      guideState.filtered = data.filtered || 0;
      guideState.tableVisible = true;
      guideState.page = 1;
      renderGuideTable(data.guides || []);
      updateGuideCounts();
    } catch (err) {
      console.error('Guide apply error', err);
      const results = $('rdGuideResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load guide data. Please try again.</p></div>`;
      }
      guideState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  /* Group labels for the guide table. guide_name comes from the row's
     guide_name — the same field the request page shows. An empty language
     reaches the client as the em-dash placeholder, so treat that as empty. */
  function guideLanguageOf(r) {
    const l = (r.language || '').trim();
    return l === '—' ? '' : l;
  }

  function guideNameOf(r) {
    return (r.guide_name || '').trim();
  }

  /** "Language — Guide", or the guide alone when the language is empty. */
  function guideGroupLabel(r) {
    const lang = guideLanguageOf(r);
    const name = guideNameOf(r) || 'Not Assigned';
    return lang ? `${lang} — ${name}` : name;
  }

  /** Render one Guide record — columns identical to the existing popup table. */
  function guideRow(r) {
    return `<tr>
        <td>${escapeHtml(r.date_from || '—')}</td>
        <td>${escapeHtml(r.date_to || '—')}</td>
        <td><strong>${escapeHtml(r.request_number)}</strong></td>
        <td>${escapeHtml(r.group_name || '—')}</td>
        <td class="num">${r.pax}</td>
        <td>${escapeHtml(r.language || '—')}</td>
        <td>${escapeHtml(r.guide_note || '—')}</td>
        <td>${statusBadge(r.status)}</td>
        <td class="rd-col-file-status">${statusBadge(r.file_status)}</td>
        <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>`;
  }

  function renderGuideTable(rows) {
    const results = $('rdGuideResults');
    if (!results) return;

    // Grouping order: named languages first, in the order the server sent them,
    // and every empty language last; within a language assigned guides A-Z with
    // everything not assigned last (the convention Transportation uses), then
    // date ascending. Sorted before paginate so a guide's rows stay contiguous.
    // Reorders only — same rows in, same rows out.
    const langRank = new Map();
    rows.forEach((r) => {
      const l = guideLanguageOf(r);
      if (l && !langRank.has(l)) langRank.set(l, langRank.size);
    });
    rows = rows.slice().sort((a, b) => {
      const ea = guideLanguageOf(a) ? 0 : 1;
      const eb = guideLanguageOf(b) ? 0 : 1;
      if (ea !== eb) return ea - eb;
      if (!ea) {
        const la = langRank.get(guideLanguageOf(a));
        const lb = langRank.get(guideLanguageOf(b));
        if (la !== lb) return la - lb;
      }
      const ua = guideNameOf(a) ? 0 : 1;
      const ub = guideNameOf(b) ? 0 : 1;
      if (ua !== ub) return ua - ub;
      const ga = guideNameOf(a).toLowerCase();
      const gb = guideNameOf(b).toLowerCase();
      if (ga !== gb) return ga < gb ? -1 : 1;
      return (a.date || '').localeCompare(b.date || '');
    });

    guideState.allRows = rows;
    const pg = paginate(rows, guideState.page);
    guideState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No guide records match the selected filters for this period.</p></div>`;
      return;
    }

    const thead = '<thead><tr>' +
      '<th>Date From</th><th>Date To</th><th>Request</th><th>Group Name</th>' +
      '<th>PAX</th><th>Language</th><th>Guide Notes</th>' +
      '<th>Status</th><th class="rd-col-file-status">File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead>';

    // Group by Language → Guide, preserving the sorted order above. Each group
    // gets a single "Language — Guide" heading, whichever filter is applied;
    // the table columns are unchanged.
    const groups = {};
    const order = [];
    rows.forEach((r) => {
      const key = `${guideLanguageOf(r)} ${guideNameOf(r)}`;
      if (!groups[key]) { groups[key] = { label: guideGroupLabel(r), rows: [] }; order.push(key); }
      groups[key].rows.push(r);
    });

    let body = '';
    order.forEach((key) => {
      body += `<tr><td colspan="10" class="rd-accom-city-header">${escapeHtml(groups[key].label)}<span class="rd-accom-group-count">${groups[key].rows.length}</span></td></tr>`;
      groups[key].rows.forEach((r) => { body += guideRow(r); });
    });

    results.innerHTML = `<div class="rd-modal-table-wrap"><table class="rd-modal-table">${thead}<tbody>${body}</tbody></table></div>` + paginationHtml(pg, guideState.allRows.length);
  }

  function bindGuideEvents() {
    bindPagination($('rdGuideResults'), guideState, () => renderGuideTable(guideState.allRows));
    const toggle = $('rdGuideToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        guideState.collapsed = !guideState.collapsed;
        const body = $('rdGuideBody');
        const chevron = $('rdGuideChevron');
        if (body) body.classList.toggle('collapsed', guideState.collapsed);
        if (chevron) chevron.classList.toggle('open', !guideState.collapsed);
      });
    }

    // Language / Guide Name are INDEPENDENT searchable dropdowns (no cascade).
    guideLangCtl = makeGuideSearchable({
      inputId: 'rdGuideLanguageInput',
      dropdownId: 'rdGuideLanguageDropdown',
      clearId: 'rdGuideLanguageClear',
      wrapSel: '#rdGuideLanguageWrap',
      stateKey: 'language',
      allLabel: 'All Languages',
      getOptions: () => guideState.filterOptions.languages || [],
    });
    guideNameCtl = makeGuideSearchable({
      inputId: 'rdGuideNameInput',
      dropdownId: 'rdGuideNameDropdown',
      clearId: 'rdGuideNameClear',
      wrapSel: '#rdGuideNameWrap',
      stateKey: 'guideName',
      allLabel: 'All Guides',
      getOptions: () => guideState.filterOptions.guides || [],
    });

    const assignmentSel = $('rdGuideAssignment');
    if (assignmentSel) {
      assignmentSel.addEventListener('change', () => {
        guideState.assignment = assignmentSel.value;
        syncGuideNameDisabled();
      });
    }

    const pillsWrap = $('rdGuidePills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-guide-sts]');
        if (pill) onGuidePillClick(pill.dataset.guideSts);
      });
    }

    const applyBtn = $('rdGuideApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyGuide);
    }
  }

  function refreshGuideOnDateChange() {
    fetchGuideFilters();
    if (guideState.tableVisible) {
      applyGuide();
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     Restaurant inline section

     Mirrors the Accommodation section: City → Restaurant Name CASCADES (a
     chosen City narrows the Restaurant dropdown), while Assignment and Status
     stay independent. All filters combine with the applied date range.

     • City is a plain select; Restaurant Name is a searchable dropdown
       (reusing the Accommodation searchable-dropdown component/styles).
     • Assignment is decided server-side by Restaurant Name presence; when
       "Not Assigned" is selected the Restaurant Name filter is disabled & reset.
     • Results are grouped by City → Restaurant. Each group shows a single
       "City — Restaurant" heading above the existing (unchanged) table columns.
     ═══════════════════════════════════════════════════════════════════ */

  const restaurantState = {
    city: '',
    restaurantName: '',
    assignment: '',          // '' = All, 'ASSIGNED', 'NOT_ASSIGNED'
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { cities: [], restaurant_names: [] },
    page: 1,
    allRows: [],
  };

  function initRestaurantSection() {
    const mealCard = document.querySelector('[data-rd-card="MEAL"]');
    const template = $('rdRestaurantTemplate');
    if (!mealCard || !template) return;

    const clone = template.content.cloneNode(true);
    mealCard.parentNode.insertBefore(clone, mealCard);
    mealCard.remove();

    renderRestaurantPills();
    bindRestaurantEvents();
    syncRestaurantNameDisabled();
    fetchRestaurantFilters();
  }

  function renderRestaurantPills() {
    const wrap = $('rdRestaurantPills');
    if (!wrap) return;
    // Reuse the shared Accommodation status options for identical look & behaviour.
    wrap.innerHTML = ACCOM_STATUS_OPTIONS.map((opt) => {
      const on = restaurantState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-restaurant-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onRestaurantPillClick(key) {
    if (key === 'ALL') {
      restaurantState.statuses.clear();
      restaurantState.statuses.add('ALL');
    } else {
      restaurantState.statuses.delete('ALL');
      if (restaurantState.statuses.has(key)) {
        restaurantState.statuses.delete(key);
      } else {
        restaurantState.statuses.add(key);
      }
      if (restaurantState.statuses.size === 0) {
        restaurantState.statuses.add('ALL');
      }
    }
    renderRestaurantPills();
  }

  /** Restaurant Name can't be combined with "Not Assigned" — disable & reset it. */
  function syncRestaurantNameDisabled() {
    const input = $('rdRestaurantNameInput');
    const clear = $('rdRestaurantNameClear');
    const notAssigned = restaurantState.assignment === 'NOT_ASSIGNED';
    if (input) {
      input.disabled = notAssigned;
      if (notAssigned) {
        input.value = '';
        input.placeholder = 'All Restaurants';
      }
    }
    if (clear) clear.disabled = notAssigned;
    if (notAssigned) {
      restaurantState.restaurantName = '';
      const dropdown = $('rdRestaurantNameDropdown');
      if (dropdown) dropdown.classList.remove('open');
    }
  }

  function buildRestaurantUrl(includeStatuses) {
    let url = `/inbound/run-down/restaurant-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (restaurantState.city) url += `&city=${encodeURIComponent(restaurantState.city)}`;
    if (restaurantState.restaurantName) url += `&restaurant_name=${encodeURIComponent(restaurantState.restaurantName)}`;
    if (restaurantState.assignment) url += `&assignment=${encodeURIComponent(restaurantState.assignment)}`;
    if (includeStatuses && !restaurantState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...restaurantState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchRestaurantFilters() {
    const url = buildRestaurantUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      restaurantState.total = data.total || 0;
      updateStatCard('MEAL', data.stats);
      restaurantState.filterOptions = data.filters || { cities: [], restaurant_names: [] };
      updateRestaurantDropdowns();
      updateRestaurantCounts();
    } catch (err) {
      console.error('Restaurant filter fetch error', err);
    }
  }

  function updateRestaurantDropdowns() {
    const citySel = $('rdRestaurantCity');
    if (citySel) {
      const prev = citySel.value;
      citySel.innerHTML = '<option value="">All Cities</option>' +
        restaurantState.filterOptions.cities.map((c) => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
      if (restaurantState.filterOptions.cities.map((c) => c.toLowerCase()).includes(prev.toLowerCase())) {
        citySel.value = prev;
      } else {
        citySel.value = '';
        restaurantState.city = '';
      }
    }

    // Drop a stale restaurant selection no longer offered for the current city/range.
    const names = restaurantState.filterOptions.restaurant_names || [];
    if (restaurantState.restaurantName && !names.map((n) => n.toLowerCase()).includes(restaurantState.restaurantName.toLowerCase())) {
      restaurantState.restaurantName = '';
      const input = $('rdRestaurantNameInput');
      if (input) input.value = '';
    }
    updateRestaurantNameDropdown();
  }

  function updateRestaurantNameDropdown() {
    const dropdown = $('rdRestaurantNameDropdown');
    if (!dropdown) return;
    const input = $('rdRestaurantNameInput');
    const query = (input ? input.value : '').toLowerCase();
    const names = restaurantState.filterOptions.restaurant_names || [];
    const filtered = query ? names.filter((n) => n.toLowerCase().includes(query)) : names;

    let html = `<button type="button" class="rd-accom-hotel-option${!restaurantState.restaurantName ? ' active' : ''}" data-restaurant-name="">All Restaurants</button>`;
    html += filtered.map((n) => {
      const active = n.toLowerCase() === (restaurantState.restaurantName || '').toLowerCase() ? ' active' : '';
      return `<button type="button" class="rd-accom-hotel-option${active}" data-restaurant-name="${escapeAttr(n)}">${escapeHtml(n)}</button>`;
    }).join('');
    dropdown.innerHTML = html;
  }

  function updateRestaurantCounts() {
    const totalEl = $('rdRestaurantTotal');
    const showingEl = $('rdRestaurantShowing');
    if (totalEl) totalEl.textContent = restaurantState.total;
    if (showingEl) {
      showingEl.textContent = restaurantState.tableVisible ? `Showing ${restaurantState.filtered}` : '';
    }
  }

  async function applyRestaurant() {
    const applyBtn = $('rdRestaurantApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildRestaurantUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      restaurantState.total = data.total || 0;
      restaurantState.filtered = data.filtered || 0;
      restaurantState.tableVisible = true;
      restaurantState.page = 1;
      renderRestaurantTable(data.restaurants || []);
      updateRestaurantCounts();
    } catch (err) {
      console.error('Restaurant apply error', err);
      const results = $('rdRestaurantResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load restaurant data. Please try again.</p></div>`;
      }
      restaurantState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  /** Render one Restaurant/meal record — columns identical to the existing popup. */
  function restaurantRow(r) {
    return `<tr>
        <td>${escapeHtml(r.day_of_week || '—')}</td>
        <td>${escapeHtml(r.date_display)}</td>
        <td><strong>${escapeHtml(r.request_number)}</strong></td>
        <td>${escapeHtml(r.group_name || '—')}</td>
        <td>${escapeHtml(r.meal || '—')}</td>
        <td class="num">${r.pax}</td>
        <td>${escapeHtml(r.restaurant_note || '—')}</td>
        <td>${statusBadge(r.status)}</td>
        <td class="rd-col-file-status">${statusBadge(r.file_status)}</td>
        <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>`;
  }

  function renderRestaurantTable(rows) {
    const results = $('rdRestaurantResults');
    if (!results) return;

    restaurantState.allRows = rows;
    const pg = paginate(rows, restaurantState.page);
    restaurantState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No restaurant records match the selected filters for this period.</p></div>`;
      return;
    }

    const thead = '<thead><tr>' +
      '<th>Day</th><th>Date</th><th>Request</th><th>Group Name</th>' +
      '<th>Meal</th><th>PAX No</th><th>Restaurant Note</th>' +
      '<th>Status</th><th class="rd-col-file-status">File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead>';

    // Group by City → Restaurant, preserving the server-sorted order. Each group
    // gets a single "City — Restaurant" heading; the table columns are unchanged.
    const groups = {};
    const order = [];
    rows.forEach((r) => {
      const city = r.city || 'Unspecified City';
      const name = r.restaurant_name || 'Not Assigned';
      const key = `${city} ${name}`;
      if (!groups[key]) { groups[key] = { label: `${city} — ${name}`, rows: [] }; order.push(key); }
      groups[key].rows.push(r);
    });

    let body = '';
    order.forEach((key) => {
      body += `<tr><td colspan="10" class="rd-accom-city-header">${escapeHtml(groups[key].label)}</td></tr>`;
      groups[key].rows.forEach((r) => { body += restaurantRow(r); });
    });

    results.innerHTML = `<div class="rd-modal-table-wrap"><table class="rd-modal-table">${thead}<tbody>${body}</tbody></table></div>` + paginationHtml(pg, restaurantState.allRows.length);
  }

  function bindRestaurantEvents() {
    bindPagination($('rdRestaurantResults'), restaurantState, () => renderRestaurantTable(restaurantState.allRows));
    const toggle = $('rdRestaurantToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        restaurantState.collapsed = !restaurantState.collapsed;
        const body = $('rdRestaurantBody');
        const chevron = $('rdRestaurantChevron');
        if (body) body.classList.toggle('collapsed', restaurantState.collapsed);
        if (chevron) chevron.classList.toggle('open', !restaurantState.collapsed);
      });
    }

    // City CASCADES into Restaurant Name — changing City re-fetches the narrowed
    // restaurant option list and resets any prior restaurant selection.
    const citySel = $('rdRestaurantCity');
    if (citySel) {
      citySel.addEventListener('change', () => {
        restaurantState.city = citySel.value;
        restaurantState.restaurantName = '';
        const input = $('rdRestaurantNameInput');
        if (input) input.value = '';
        fetchRestaurantFilters();
      });
    }

    // Searchable Restaurant Name dropdown.
    const nameInput = $('rdRestaurantNameInput');
    const nameDropdown = $('rdRestaurantNameDropdown');
    const nameClear = $('rdRestaurantNameClear');

    if (nameInput && nameDropdown) {
      nameInput.addEventListener('focus', () => {
        if (nameInput.disabled) return;
        nameDropdown.classList.add('open');
        updateRestaurantNameDropdown();
      });
      nameInput.addEventListener('input', () => {
        nameDropdown.classList.add('open');
        updateRestaurantNameDropdown();
      });
      nameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') nameDropdown.classList.remove('open');
      });
      nameDropdown.addEventListener('click', (e) => {
        const opt = e.target.closest('[data-restaurant-name]');
        if (!opt) return;
        const name = opt.dataset.restaurantName;
        restaurantState.restaurantName = name;
        nameInput.value = name || '';
        nameInput.placeholder = name || 'All Restaurants';
        nameDropdown.classList.remove('open');
      });
      document.addEventListener('click', (e) => {
        if (!e.target.closest('#rdRestaurantNameWrap')) nameDropdown.classList.remove('open');
      });
    }

    if (nameClear) {
      nameClear.addEventListener('click', () => {
        if (nameClear.disabled) return;
        restaurantState.restaurantName = '';
        if (nameInput) {
          nameInput.value = '';
          nameInput.placeholder = 'All Restaurants';
        }
        updateRestaurantNameDropdown();
      });
    }

    const assignmentSel = $('rdRestaurantAssignment');
    if (assignmentSel) {
      assignmentSel.addEventListener('change', () => {
        restaurantState.assignment = assignmentSel.value;
        syncRestaurantNameDisabled();
      });
    }

    const pillsWrap = $('rdRestaurantPills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-restaurant-sts]');
        if (pill) onRestaurantPillClick(pill.dataset.restaurantSts);
      });
    }

    const applyBtn = $('rdRestaurantApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyRestaurant);
    }
  }

  function refreshRestaurantOnDateChange() {
    fetchRestaurantFilters();
    if (restaurantState.tableVisible) {
      applyRestaurant();
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     Meet & Assist inline section

     Replaces the old GROUND_HANDLER supplier popup with the shared inline
     pattern. Three filters plus Status, all independent (no cascade) and
     combined with the applied date range:
       • Meet & Assist Name — searchable dropdown over the representative
         names actually used in range. Disabled and reset to "All Names"
         whenever Assignment is "Not Assigned", so the two can never conflict.
       • Meet & Assist — Arrival / Departure / Arrival & Departure (default).
         "Arrival & Departure" is a UNION, not an intersection.
       • Assignment — All / Assigned / Not Assigned, decided purely by whether
         the Meet & Assist Name is populated.
       • Status — the record's own Meet & Assist status (never File Status).

     Rendering: Arrival and Departure NEVER share a table. Each type gets its
     own heading + table, and inside a table rows are grouped by name with a
     "Type — Name" heading row, unnamed records last under "Not Assigned".
     The server pre-sorts the rows so grouping is a single ordered walk.
     ═══════════════════════════════════════════════════════════════════ */

  const meetAssistState = {
    maName: '',
    maType: 'BOTH',          // 'BOTH' = Arrival & Departure (default)
    assignment: '',          // '' = All, 'ASSIGNED', 'NOT_ASSIGNED'
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { ma_names: [] },
    page: 1,
    allRows: [],
  };

  let meetAssistNameCtl = null;

  function initMeetAssistSection() {
    const maCard = document.querySelector('[data-rd-card="GROUND_HANDLER"]');
    const template = $('rdMeetAssistTemplate');
    if (!maCard || !template) return;

    const clone = template.content.cloneNode(true);
    maCard.parentNode.insertBefore(clone, maCard);
    maCard.remove();

    renderMeetAssistPills();
    bindMeetAssistEvents();
    syncMeetAssistNameDisabled();
    fetchMeetAssistFilters();
  }

  function renderMeetAssistPills() {
    const wrap = $('rdMeetAssistPills');
    if (!wrap) return;
    // Reuse the shared Accommodation status options for identical look & behaviour.
    wrap.innerHTML = ACCOM_STATUS_OPTIONS.map((opt) => {
      const on = meetAssistState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-ma-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onMeetAssistPillClick(key) {
    if (key === 'ALL') {
      meetAssistState.statuses.clear();
      meetAssistState.statuses.add('ALL');
    } else {
      meetAssistState.statuses.delete('ALL');
      if (meetAssistState.statuses.has(key)) {
        meetAssistState.statuses.delete(key);
      } else {
        meetAssistState.statuses.add(key);
      }
      if (meetAssistState.statuses.size === 0) {
        meetAssistState.statuses.add('ALL');
      }
    }
    renderMeetAssistPills();
  }

  /** Name can't be combined with "Not Assigned" — disable & reset it. */
  function syncMeetAssistNameDisabled() {
    const input = $('rdMeetAssistNameInput');
    const clear = $('rdMeetAssistNameClear');
    const notAssigned = meetAssistState.assignment === 'NOT_ASSIGNED';
    if (input) {
      input.disabled = notAssigned;
      if (notAssigned) {
        input.value = '';
        input.placeholder = 'All Names';
      }
    }
    if (clear) clear.disabled = notAssigned;
    if (notAssigned) {
      meetAssistState.maName = '';
      const dropdown = $('rdMeetAssistNameDropdown');
      if (dropdown) dropdown.classList.remove('open');
    }
  }

  /** Searchable Meet & Assist Name dropdown. Returns { render }. */
  function makeMeetAssistSearchable(cfg) {
    const input = $(cfg.inputId);
    const dropdown = $(cfg.dropdownId);
    const clear = $(cfg.clearId);
    if (!input || !dropdown) return { render() {} };

    function render() {
      const query = input.value.toLowerCase();
      const opts = cfg.getOptions() || [];
      const filtered = query ? opts.filter((o) => o.toLowerCase().includes(query)) : opts;
      const selected = meetAssistState[cfg.stateKey] || '';
      let html = `<button type="button" class="rd-accom-hotel-option${!selected ? ' active' : ''}" data-ma-opt="">${cfg.allLabel}</button>`;
      html += filtered.map((o) => {
        const active = o.toLowerCase() === selected.toLowerCase() ? ' active' : '';
        return `<button type="button" class="rd-accom-hotel-option${active}" data-ma-opt="${escapeAttr(o)}">${escapeHtml(o)}</button>`;
      }).join('');
      dropdown.innerHTML = html;
    }

    input.addEventListener('focus', () => {
      if (input.disabled) return;
      dropdown.classList.add('open');
      render();
    });
    input.addEventListener('input', () => {
      dropdown.classList.add('open');
      render();
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') dropdown.classList.remove('open');
    });
    dropdown.addEventListener('click', (e) => {
      const opt = e.target.closest('[data-ma-opt]');
      if (!opt) return;
      const val = opt.dataset.maOpt;
      meetAssistState[cfg.stateKey] = val;
      input.value = val || '';
      input.placeholder = val || cfg.allLabel;
      dropdown.classList.remove('open');
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest(cfg.wrapSel)) dropdown.classList.remove('open');
    });
    if (clear) {
      clear.addEventListener('click', () => {
        if (clear.disabled) return;
        meetAssistState[cfg.stateKey] = '';
        input.value = '';
        input.placeholder = cfg.allLabel;
        render();
      });
    }
    return { render };
  }

  function buildMeetAssistUrl(includeStatuses) {
    let url = `/inbound/run-down/meet-assist-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (meetAssistState.maName) url += `&ma_name=${encodeURIComponent(meetAssistState.maName)}`;
    if (meetAssistState.maType) url += `&ma_type=${encodeURIComponent(meetAssistState.maType)}`;
    if (meetAssistState.assignment) url += `&assignment=${encodeURIComponent(meetAssistState.assignment)}`;
    if (includeStatuses && !meetAssistState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...meetAssistState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchMeetAssistFilters() {
    const url = buildMeetAssistUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      meetAssistState.total = data.total || 0;
      updateStatCard('GROUND_HANDLER', data.stats);
      meetAssistState.filterOptions = data.filters || { ma_names: [] };
      updateMeetAssistDropdowns();
      updateMeetAssistCounts();
    } catch (err) {
      console.error('Meet & Assist filter fetch error', err);
    }
  }

  function updateMeetAssistDropdowns() {
    // Drop a stale selection that is no longer offered for the current range.
    const names = meetAssistState.filterOptions.ma_names || [];
    if (meetAssistState.maName && !names.map((n) => n.toLowerCase()).includes(meetAssistState.maName.toLowerCase())) {
      meetAssistState.maName = '';
      const input = $('rdMeetAssistNameInput');
      if (input) input.value = '';
    }
    if (meetAssistNameCtl) meetAssistNameCtl.render();
  }

  function updateMeetAssistCounts() {
    const totalEl = $('rdMeetAssistTotal');
    const showingEl = $('rdMeetAssistShowing');
    if (totalEl) totalEl.textContent = meetAssistState.total;
    if (showingEl) {
      showingEl.textContent = meetAssistState.tableVisible ? `Showing ${meetAssistState.filtered}` : '';
    }
  }

  async function applyMeetAssist() {
    const applyBtn = $('rdMeetAssistApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildMeetAssistUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      meetAssistState.total = data.total || 0;
      meetAssistState.filtered = data.filtered || 0;
      meetAssistState.tableVisible = true;
      meetAssistState.page = 1;
      renderMeetAssistTable(data.meet_assists || []);
      updateMeetAssistCounts();
    } catch (err) {
      console.error('Meet & Assist apply error', err);
      const results = $('rdMeetAssistResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load Meet &amp; Assist data. Please try again.</p></div>`;
      }
      meetAssistState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  /** Render one Meet & Assist record — columns identical to the previous popup
   *  table, plus the Status column (M&A status) beside the untouched File Status. */
  function meetAssistRow(r) {
    return `<tr>
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
        <td class="rd-col-file-status">${statusBadge(r.file_status)}</td>
        <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>`;
  }

  /** One Arrival or Departure block: heading + its own table, grouped by name. */
  function meetAssistTypeBlock(typeLabel, icon, rows) {
    const thead = '<thead><tr>' +
      '<th>Date</th><th>Request</th><th>Group Name</th><th>PAX</th>' +
      '<th>Nationality</th><th>Description</th><th>Time</th><th>Flight Number</th>' +
      '<th>M&A Notes</th><th>Status</th><th class="rd-col-file-status">File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead>';

    // Group by name, preserving the server order (named first, unnamed last).
    const groups = {};
    const order = [];
    rows.forEach((r) => {
      const name = r.ma_name || 'Not Assigned';
      if (!groups[name]) { groups[name] = []; order.push(name); }
      groups[name].push(r);
    });

    let body = '';
    order.forEach((name) => {
      body += `<tr><td colspan="12" class="rd-accom-city-header">${escapeHtml(`${typeLabel} — ${name}`)}</td></tr>`;
      groups[name].forEach((r) => { body += meetAssistRow(r); });
    });

    return `<div class="rd-ma-type-block">
        <div class="rd-ma-type-heading"><i class="fas ${icon}"></i>${escapeHtml(typeLabel)}</div>
        <div class="rd-modal-table-wrap"><table class="rd-modal-table">${thead}<tbody>${body}</tbody></table></div>
      </div>`;
  }

  function renderMeetAssistTable(rows) {
    const results = $('rdMeetAssistResults');
    if (!results) return;

    meetAssistState.allRows = rows;
    const pg = paginate(rows, meetAssistState.page);
    meetAssistState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No Meet &amp; Assist records match the selected filters for this period.</p></div>`;
      return;
    }

    // Arrival and Departure never share a table, even when both are shown.
    const arrivals = rows.filter((r) => r.ma_type === 'ARRIVAL');
    const departures = rows.filter((r) => r.ma_type === 'DEPARTURE');

    let html = '';
    if (arrivals.length) html += meetAssistTypeBlock('Arrival', 'fa-plane-arrival', arrivals);
    if (departures.length) html += meetAssistTypeBlock('Departure', 'fa-plane-departure', departures);
    results.innerHTML = html + paginationHtml(pg, meetAssistState.allRows.length);
  }

  function bindMeetAssistEvents() {
    bindPagination($('rdMeetAssistResults'), meetAssistState, () => renderMeetAssistTable(meetAssistState.allRows));
    const toggle = $('rdMeetAssistToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        meetAssistState.collapsed = !meetAssistState.collapsed;
        const body = $('rdMeetAssistBody');
        const chevron = $('rdMeetAssistChevron');
        if (body) body.classList.toggle('collapsed', meetAssistState.collapsed);
        if (chevron) chevron.classList.toggle('open', !meetAssistState.collapsed);
      });
    }

    meetAssistNameCtl = makeMeetAssistSearchable({
      inputId: 'rdMeetAssistNameInput',
      dropdownId: 'rdMeetAssistNameDropdown',
      clearId: 'rdMeetAssistNameClear',
      wrapSel: '#rdMeetAssistNameWrap',
      stateKey: 'maName',
      allLabel: 'All Names',
      getOptions: () => meetAssistState.filterOptions.ma_names || [],
    });

    const typeSel = $('rdMeetAssistType');
    if (typeSel) {
      typeSel.addEventListener('change', () => {
        meetAssistState.maType = typeSel.value || 'BOTH';
      });
    }

    const assignmentSel = $('rdMeetAssistAssignment');
    if (assignmentSel) {
      assignmentSel.addEventListener('change', () => {
        meetAssistState.assignment = assignmentSel.value;
        syncMeetAssistNameDisabled();
      });
    }

    const pillsWrap = $('rdMeetAssistPills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-ma-sts]');
        if (pill) onMeetAssistPillClick(pill.dataset.maSts);
      });
    }

    const applyBtn = $('rdMeetAssistApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyMeetAssist);
    }
  }

  function refreshMeetAssistOnDateChange() {
    fetchMeetAssistFilters();
    if (meetAssistState.tableVisible) {
      applyMeetAssist();
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     Agent inline section

     Mirrors the Restaurant section (same section chrome, filter row, status
     pills and grouped inline table). Two filters:
       • Agent Name — a plain dropdown; "ALL AGENTS" (value '') keeps every
         agent, each rendered under its own heading.
       • File Status — MULTI-SELECT over Requested / Confirmed / Invoiced /
         Deleted, combining as OR, with "All" as the reset.
     Both combine with the applied date range. Rows are ALWAYS grouped by agent
     — exactly as Restaurant always groups by "City — Restaurant" — so the agent
     name sits above its table instead of becoming a column, and an agent with
     no matching rows produces no group at all.
     ═══════════════════════════════════════════════════════════════════ */

  const agentState = {
    agentName: '',            // '' = ALL AGENTS
    statuses: new Set(['ALL']),
    collapsed: false,
    tableVisible: false,
    total: 0,
    filtered: 0,
    filterOptions: { agent_names: [] },
    page: 1,
    allRows: [],
  };

  /** File Status buckets for the Agent section. These are NOT service statuses:
   *  they come from the server's _file_status_bucket, where 'Deleted' is derived
   *  from the request's deleted-queue flag rather than a stored status value. */
  const AGENT_FILE_STATUS_OPTIONS = [
    { key: 'REQUESTED', label: 'Requested', cls: 'requested' },
    { key: 'CONFIRMED', label: 'Confirmed', cls: 'confirmed' },
    { key: 'INVOICED', label: 'Invoiced', cls: 'invoiced' },
    { key: 'DELETED', label: 'Deleted', cls: 'deleted' },
    { key: 'ALL', label: 'All', cls: 'all' },
  ];

  function initAgentSection() {
    const anchor = document.querySelector('[data-rd-agent-anchor]');
    const template = $('rdAgentTemplate');
    if (!anchor || !template) return;

    const clone = template.content.cloneNode(true);
    anchor.parentNode.insertBefore(clone, anchor);
    anchor.remove();

    renderAgentPills();
    bindAgentEvents();
    fetchAgentFilters();
  }

  function renderAgentPills() {
    const wrap = $('rdAgentPills');
    if (!wrap) return;
    wrap.innerHTML = AGENT_FILE_STATUS_OPTIONS.map((opt) => {
      const on = agentState.statuses.has(opt.key) ? ' on' : '';
      return `<button type="button" class="rd-accom-pill ${opt.cls}${on}" data-agent-sts="${opt.key}">${opt.label}</button>`;
    }).join('');
  }

  function onAgentPillClick(key) {
    if (key === 'ALL') {
      agentState.statuses.clear();
      agentState.statuses.add('ALL');
    } else {
      agentState.statuses.delete('ALL');
      if (agentState.statuses.has(key)) {
        agentState.statuses.delete(key);
      } else {
        agentState.statuses.add(key);
      }
      if (agentState.statuses.size === 0) {
        agentState.statuses.add('ALL');
      }
    }
    renderAgentPills();
  }

  function buildAgentUrl(includeStatuses) {
    let url = `/inbound/run-down/agent-data?date_from=${encodeURIComponent(state.appliedDateFrom)}&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    if (agentState.agentName) url += `&agent=${encodeURIComponent(agentState.agentName)}`;
    if (includeStatuses && !agentState.statuses.has('ALL')) {
      url += `&statuses=${encodeURIComponent([...agentState.statuses].join(','))}`;
    }
    return url;
  }

  async function fetchAgentFilters() {
    const url = buildAgentUrl(false);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) return;
      agentState.total = data.total || 0;
      agentState.filterOptions = data.filters || { agent_names: [] };
      updateAgentDropdown();
      updateAgentCounts();
    } catch (err) {
      console.error('Agent filter fetch error', err);
    }
  }

  function updateAgentDropdown() {
    const sel = $('rdAgentName');
    if (!sel) return;
    const prev = sel.value;
    const names = agentState.filterOptions.agent_names || [];
    sel.innerHTML = '<option value="">ALL AGENTS</option>' +
      names.map((n) => `<option value="${escapeAttr(n)}">${escapeHtml(n)}</option>`).join('');
    // Drop a selection that is no longer offered for the current range.
    if (prev && names.map((n) => n.toLowerCase()).includes(prev.toLowerCase())) {
      sel.value = prev;
    } else {
      sel.value = '';
      agentState.agentName = '';
    }
  }

  function updateAgentCounts() {
    const totalEl = $('rdAgentTotal');
    const showingEl = $('rdAgentShowing');
    if (totalEl) totalEl.textContent = agentState.total;
    if (showingEl) {
      showingEl.textContent = agentState.tableVisible ? `Showing ${agentState.filtered}` : '';
    }
  }

  async function applyAgent() {
    const applyBtn = $('rdAgentApply');
    if (applyBtn) {
      applyBtn.disabled = true;
      applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading…';
    }

    const url = buildAgentUrl(true);
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      agentState.total = data.total || 0;
      agentState.filtered = data.filtered || 0;
      agentState.tableVisible = true;
      agentState.page = 1;
      renderAgentTable(data.agents || []);
      updateAgentCounts();
    } catch (err) {
      console.error('Agent apply error', err);
      const results = $('rdAgentResults');
      if (results) {
        results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load agent data. Please try again.</p></div>`;
      }
      agentState.tableVisible = true;
    } finally {
      if (applyBtn) {
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
      }
    }
  }

  /** Render one Agent record — columns identical to the previous popup table. */
  function agentRow(r) {
    return `<tr>
        <td>${escapeHtml(r.from_date || '—')}</td>
        <td>${escapeHtml(r.to_date || '—')}</td>
        <td><strong>${escapeHtml(r.request_number)}</strong></td>
        <td>${escapeHtml(r.contact_name || '—')}</td>
        <td>${escapeHtml(r.group_name || '—')}</td>
        <td class="num">${r.pax}</td>
        <td>${escapeHtml(r.nationality || '—')}</td>
        <td>${statusBadge(r.file_status)}</td>
        <td class="rd-col-view"><a href="${escapeAttr(r.view_url)}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>`;
  }

  function renderAgentTable(rows) {
    const results = $('rdAgentResults');
    if (!results) return;

    agentState.allRows = rows;
    const pg = paginate(rows, agentState.page);
    agentState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No agent records match the selected filters for this period.</p></div>`;
      return;
    }

    const thead = '<thead><tr>' +
      '<th>From Date</th><th>To Date</th><th>Request ID</th><th>Contact Name</th>' +
      '<th>Group Name</th><th>PAX</th><th>Nationality</th><th>File Status</th><th class="rd-col-view"></th>' +
      '</tr></thead>';

    // Group by Agent, preserving the server-sorted order. Each agent gets a
    // single heading above its rows; the table columns are unchanged.
    const groups = {};
    const order = [];
    rows.forEach((r) => {
      const name = r.agent_name || 'Unassigned Agent';
      if (!groups[name]) { groups[name] = []; order.push(name); }
      groups[name].push(r);
    });

    let body = '';
    order.forEach((name) => {
      body += `<tr><td colspan="9" class="rd-accom-city-header">${escapeHtml(name)}</td></tr>`;
      groups[name].forEach((r) => { body += agentRow(r); });
    });

    results.innerHTML = `<div class="rd-modal-table-wrap"><table class="rd-modal-table">${thead}<tbody>${body}</tbody></table></div>` + paginationHtml(pg, agentState.allRows.length);
  }

  function bindAgentEvents() {
    bindPagination($('rdAgentResults'), agentState, () => renderAgentTable(agentState.allRows));
    const toggle = $('rdAgentToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        agentState.collapsed = !agentState.collapsed;
        const body = $('rdAgentBody');
        const chevron = $('rdAgentChevron');
        if (body) body.classList.toggle('collapsed', agentState.collapsed);
        if (chevron) chevron.classList.toggle('open', !agentState.collapsed);
      });
    }

    const nameSel = $('rdAgentName');
    if (nameSel) {
      nameSel.addEventListener('change', () => { agentState.agentName = nameSel.value; });
    }

    const pillsWrap = $('rdAgentPills');
    if (pillsWrap) {
      pillsWrap.addEventListener('click', (e) => {
        const pill = e.target.closest('[data-agent-sts]');
        if (pill) onAgentPillClick(pill.dataset.agentSts);
      });
    }

    const applyBtn = $('rdAgentApply');
    if (applyBtn) {
      applyBtn.addEventListener('click', applyAgent);
    }
  }

  function refreshAgentOnDateChange() {
    fetchAgentFilters();
    if (agentState.tableVisible) {
      applyAgent();
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     Cut-off section

     The page's last block, and the only section with no filters of its own:
     it is filled by clicking a summary card's cut-off count and lists every
     service of THAT service type whose supplier cut-off deadline falls inside
     the applied date range. One shared table — picking a different service
     replaces its contents rather than stacking a second table.

     Rows come from /run-down/cut-off-data carrying the same view_url /
     section_key / record_id the section tables use, so the View column goes
     through deepLinkUrl() and lands on the exact service item.
     ═══════════════════════════════════════════════════════════════════ */

  // Card key -> the endpoint's service key + the service name shown in the
  // heading. Mirrors RUN_DOWN_CUT_OFF_SERVICES server-side.
  const CUT_OFF_SERVICES = {
    HOTEL: { service: 'accommodation', label: 'Accommodation' },
    TRANSPORT: { service: 'transportation', label: 'Transportation' },
    MEAL: { service: 'restaurant', label: 'Restaurant' },
  };

  const cutOffState = {
    card: '',            // '' until a cut-off count is clicked
    collapsed: false,
    total: 0,
    page: 1,
    allRows: [],
  };

  /** Print header label: the service the table is currently showing. */
  function cutOffPrintLabel() {
    const cfg = CUT_OFF_SERVICES[cutOffState.card];
    return cfg ? `Cut-off — ${cfg.label}` : 'Cut-off';
  }

  /** Heading + total badge always name the service on display, so the table
   *  can never be mistaken for another service's cut-off list. */
  function updateCutOffHeading() {
    const title = $('rdCutOffTitle');
    const total = $('rdCutOffTotal');
    if (title) title.textContent = cutOffPrintLabel();
    if (total) total.textContent = cutOffState.total;
  }

  /** Fill the shared cut-off table with one card's service and scroll to it. */
  async function showCutOffTable(cardKey) {
    const cfg = CUT_OFF_SERVICES[cardKey];
    const section = $('rdCutOffSection');
    const results = $('rdCutOffResults');
    if (!cfg || !section || !results) return;

    cutOffState.card = cardKey;
    cutOffState.total = 0;
    section.hidden = false;
    expandSection(cutOffState, 'rdCutOffBody', 'rdCutOffChevron');
    updateCutOffHeading();
    results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-spinner fa-spin"></i><p>Loading cut-off records…</p></div>`;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    await loadCutOffRows();
  }

  /** (Re)load the rows for the service the table is already showing. */
  async function loadCutOffRows() {
    const cfg = CUT_OFF_SERVICES[cutOffState.card];
    const results = $('rdCutOffResults');
    if (!cfg || !results) return;

    const url = `/inbound/run-down/cut-off-data?service=${encodeURIComponent(cfg.service)}`
      + `&date_from=${encodeURIComponent(state.appliedDateFrom)}`
      + `&date_to=${encodeURIComponent(state.appliedDateTo)}`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');

      cutOffState.total = data.total || 0;
      cutOffState.page = 1;
      renderCutOffTable(data.rows || []);
    } catch (err) {
      console.error('Cut-off load error', err);
      cutOffState.total = 0;
      cutOffState.allRows = [];
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-exclamation-triangle"></i><p>Could not load cut-off records. Please try again.</p></div>`;
    }
    updateCutOffHeading();
  }

  function renderCutOffTable(rows) {
    const results = $('rdCutOffResults');
    if (!results) return;

    // Already sorted by cut-off date ascending server-side; kept as delivered.
    cutOffState.allRows = rows;
    const pg = paginate(rows, cutOffState.page);
    cutOffState.page = pg.page;
    rows = pg.pageRows;

    if (!rows.length) {
      const cfg = CUT_OFF_SERVICES[cutOffState.card];
      const label = cfg ? cfg.label.toLowerCase() : 'service';
      results.innerHTML = `<div class="rd-modal-empty"><i class="fas fa-inbox"></i><p>No ${label} cut-off dates fall inside the selected period.</p></div>`;
      return;
    }

    let html = '<div class="rd-modal-table-wrap"><table class="rd-modal-table"><thead><tr>' +
      '<th>Cut Off Date</th><th>Request</th><th>Name</th><th>Date From</th><th>Date To</th>' +
      '<th class="rd-col-view"></th>' +
      '</tr></thead><tbody>';

    rows.forEach((r) => {
      html += `<tr>
        <td>${escapeHtml(r.cut_off_date_display || '—')}</td>
        <td><strong>${escapeHtml(r.request_number)}</strong></td>
        <td>${escapeHtml(r.name || '—')}</td>
        <td>${escapeHtml(r.date_from_display || '—')}</td>
        <td>${escapeHtml(r.date_to_display || '—')}</td>
        <td class="rd-col-view"><a href="${escapeAttr(deepLinkUrl(r))}" class="rd-view-link" target="_blank" rel="noopener">View</a></td>
      </tr>`;
    });

    html += '</tbody></table></div>';
    results.innerHTML = html + paginationHtml(pg, cutOffState.allRows.length);
  }

  function bindCutOffEvents() {
    bindPagination($('rdCutOffResults'), cutOffState, () => renderCutOffTable(cutOffState.allRows));
    const toggle = $('rdCutOffToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        cutOffState.collapsed = !cutOffState.collapsed;
        const body = $('rdCutOffBody');
        const chevron = $('rdCutOffChevron');
        if (body) body.classList.toggle('collapsed', cutOffState.collapsed);
        if (chevron) chevron.classList.toggle('open', !cutOffState.collapsed);
      });
    }
  }

  function initCutOffSection() {
    // Static markup, not a <template> clone: the section is already in the page,
    // hidden until a cut-off count is clicked.
    bindCutOffEvents();
  }

  /** Date Apply: a cut-off table that is already showing refreshes in place for
   *  the new range, keeping the service it is on. */
  function refreshCutOffOnDateChange() {
    if (cutOffState.card) {
      loadCutOffRows();
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     Summary stat cards

     One card per service section, sitting above the sections themselves.
     The numbers are NOT computed here: each section's own data endpoint
     returns a `stats` block counted from the same in-range dataset that
     feeds that section's table, so a card can never disagree with the
     table below it. Cards therefore refresh for free whenever the global
     date range is applied — every fetchXFilters call repaints its card.

     Clicking a number reuses the section's existing filter state + Apply:
     it resets that section's other filters to All, sets Status to the
     clicked value, re-applies, and scrolls there. Only the clicked
     section is ever touched.
     ═══════════════════════════════════════════════════════════════════ */

  // Card stat key → the status value the section's pills/endpoint already use.
  const STAT_STATUS_KEY = {
    requested: 'REQUESTED',
    confirmed: 'CONFIRMED',
    waiting: 'WAITING_LIST',
    cancelled: 'CANCELLED',
  };

  // The single applied stat across all cards: { card, stat } or null.
  let activeStat = null;

  function expandSection(sectionState, bodyId, chevronId) {
    sectionState.collapsed = false;
    const body = $(bodyId);
    if (body) body.classList.remove('collapsed');
    const chevron = $(chevronId);
    if (chevron) chevron.classList.add('open');
  }

  const STAT_CARDS = {
    HOTEL: {
      state: accomState,
      sectionId: 'rdAccomSection',
      expand: () => expandSection(accomState, 'rdAccomBody', 'rdAccomChevron'),
      renderPills: renderAccomPills,
      refreshFilters: fetchAccomFilters,
      apply: applyAccom,
      resetFilters() {
        accomState.city = '';
        accomState.category = '';
        accomState.hotelName = '';
        const cat = $('rdAccomCategory');
        if (cat) cat.value = '';
        const city = $('rdAccomCity');
        if (city) city.value = '';
        const hotel = $('rdAccomHotelInput');
        if (hotel) {
          hotel.value = '';
          hotel.placeholder = 'All hotels';
        }
      },
    },
    TRANSPORT: {
      state: transportState,
      sectionId: 'rdTransportSection',
      expand: () => expandSection(transportState, 'rdTransportBody', 'rdTransportChevron'),
      renderPills: renderTransportPills,
      refreshFilters: fetchTransportFilters,
      apply: applyTransport,
      resetFilters() {
        transportState.vehicle = '';
        transportState.company = '';
        transportState.assignment = '';
        const vehicle = $('rdTransportVehicle');
        if (vehicle) vehicle.value = '';
        const company = $('rdTransportCompany');
        if (company) company.value = '';
        const assignment = $('rdTransportAssignment');
        if (assignment) assignment.value = '';
        syncTransportCompanyDisabled();
      },
    },
    GUIDE: {
      state: guideState,
      sectionId: 'rdGuideSection',
      expand: () => expandSection(guideState, 'rdGuideBody', 'rdGuideChevron'),
      renderPills: renderGuidePills,
      refreshFilters: fetchGuideFilters,
      apply: applyGuide,
      resetFilters() {
        guideState.language = '';
        guideState.guideName = '';
        guideState.assignment = '';
        const assignment = $('rdGuideAssignment');
        if (assignment) assignment.value = '';
        const lang = $('rdGuideLanguageInput');
        if (lang) {
          lang.value = '';
          lang.placeholder = 'All Languages';
        }
        const name = $('rdGuideNameInput');
        if (name) {
          name.value = '';
          name.placeholder = 'All Guides';
        }
        syncGuideNameDisabled();
        if (guideLangCtl) guideLangCtl.render();
        if (guideNameCtl) guideNameCtl.render();
      },
    },
    MEAL: {
      state: restaurantState,
      sectionId: 'rdRestaurantSection',
      expand: () => expandSection(restaurantState, 'rdRestaurantBody', 'rdRestaurantChevron'),
      renderPills: renderRestaurantPills,
      refreshFilters: fetchRestaurantFilters,
      apply: applyRestaurant,
      resetFilters() {
        restaurantState.city = '';
        restaurantState.restaurantName = '';
        restaurantState.assignment = '';
        const city = $('rdRestaurantCity');
        if (city) city.value = '';
        const assignment = $('rdRestaurantAssignment');
        if (assignment) assignment.value = '';
        const name = $('rdRestaurantNameInput');
        if (name) {
          name.value = '';
          name.placeholder = 'All Restaurants';
        }
        syncRestaurantNameDisabled();
        updateRestaurantNameDropdown();
      },
    },
    GROUND_HANDLER: {
      state: meetAssistState,
      sectionId: 'rdMeetAssistSection',
      expand: () => expandSection(meetAssistState, 'rdMeetAssistBody', 'rdMeetAssistChevron'),
      renderPills: renderMeetAssistPills,
      refreshFilters: fetchMeetAssistFilters,
      apply: applyMeetAssist,
      resetFilters() {
        meetAssistState.maName = '';
        meetAssistState.maType = 'BOTH';   // 'Arrival & Departure' is this filter's All
        meetAssistState.assignment = '';
        const type = $('rdMeetAssistType');
        if (type) type.value = 'BOTH';
        const assignment = $('rdMeetAssistAssignment');
        if (assignment) assignment.value = '';
        const name = $('rdMeetAssistNameInput');
        if (name) {
          name.value = '';
          name.placeholder = 'All Names';
        }
        syncMeetAssistNameDisabled();
        if (meetAssistNameCtl) meetAssistNameCtl.render();
      },
    },
  };

  function renderStatActive() {
    document.querySelectorAll('[data-rd-stat-card]').forEach((card) => {
      const isActiveCard = !!activeStat && card.dataset.rdStatCard === activeStat.card;
      card.classList.toggle('active', isActiveCard);
      card.querySelectorAll('[data-rd-stat]').forEach((item) => {
        const isActiveStat = isActiveCard && item.dataset.rdStat === activeStat.stat;
        item.classList.toggle('active', isActiveStat);
        // A zero stays unclickable — unless it is the applied one, which must
        // remain clickable so the user can always switch it back off.
        item.disabled = Number(item.dataset.rdStatValue || 0) === 0 && !isActiveStat;
      });
    });
  }

  function updateStatCard(cardKey, stats) {
    const card = document.querySelector('[data-rd-stat-card="' + cardKey + '"]');
    if (!card) return;
    const values = stats || {};
    card.querySelectorAll('[data-rd-stat]').forEach((item) => {
      const value = Number(values[item.dataset.rdStat]) || 0;
      item.dataset.rdStatValue = value;
      const numEl = item.querySelector('.rd-stat-num');
      if (numEl) {
        numEl.textContent = value;
        // A live cut-off deadline reads red; a zero keeps the normal colour.
        numEl.classList.toggle('rd-stat-num-alert', item.dataset.rdStat === 'cut_off' && value > 0);
      }
    });
    renderStatActive();
  }

  async function onStatClick(cardKey, statKey) {
    // Cut-off is not a status: it fills its own standalone table at the bottom
    // of the page and leaves every section's filters exactly as they are.
    if (statKey === 'cut_off') {
      await showCutOffTable(cardKey);
      return;
    }

    const cfg = STAT_CARDS[cardKey];
    const statusKey = STAT_STATUS_KEY[statKey];
    if (!cfg || !statusKey) return;

    const isSame = !!activeStat && activeStat.card === cardKey && activeStat.stat === statKey;

    // Every other filter in THIS section goes back to All; the global date
    // range and every other section are left exactly as they are.
    cfg.resetFilters();
    if (isSame) {
      cfg.state.statuses = new Set(['ALL']);
      activeStat = null;
    } else {
      cfg.state.statuses = new Set([statusKey]);
      activeStat = { card: cardKey, stat: statKey };
    }
    cfg.renderPills();
    renderStatActive();

    cfg.expand();
    const section = $(cfg.sectionId);
    if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Refresh the option lists first: a previous cascade may have left this
    // section's dropdowns holding a narrowed set of options.
    await cfg.refreshFilters();
    await cfg.apply();
  }

  function bindStatCards() {
    const wrap = $('rdStatCards');
    if (!wrap) return;
    wrap.addEventListener('click', (e) => {
      const item = e.target.closest('[data-rd-stat]');
      if (!item || item.disabled) return;
      const card = item.closest('[data-rd-stat-card]');
      if (!card) return;
      onStatClick(card.dataset.rdStatCard, item.dataset.rdStat);
    });
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
    bindStatCards();
    updateFieldDisplay('from');
    updateFieldDisplay('to');
    updatePrintMeta();

    // Track modal visibility so date-Apply only refreshes a genuinely open modal.
    const modalEl = $('rdRequestsModal');
    if (modalEl) {
      modalEl.addEventListener('hidden.bs.modal', () => { state.modalOpen = false; });
    }

    // Initialize agent inline section
    initAgentSection();

    // Initialize accommodation inline section
    initAccomSection();

    // Initialize transportation inline section
    initTransportSection();

    // Initialize guide inline section
    initGuideSection();

    // Initialize restaurant inline section
    initRestaurantSection();

    // Initialize Meet & Assist inline section
    initMeetAssistSection();

    // Initialize cut-off section
    initCutOffSection();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
