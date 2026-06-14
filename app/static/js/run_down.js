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

    if (title) title.textContent = `${m.serviceLabel} — ${m.supplierName}`;
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

  function bindEvents() {
    const dateApplyBtn = $('rdDateApply');
    if (dateApplyBtn) dateApplyBtn.addEventListener('click', applyDateRange);

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
      if (!e.target.closest('.rd-supplier-wrap')) {
        closeAllDropdowns(null);
      }
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
    updatePrintMeta();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
