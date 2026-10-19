/*
 * Customer form behaviour, shared by the New/Edit Customer page and the request
 * page's Quick Add Customer popup (markup: templates/customer/_form_fields.html).
 *
 * - Customer Type "Direct" shows First/Last Name instead of Agent Name/Contact Person.
 * - Payment Terms "Cliq" shows the Cliq field instead of the bank fields.
 * - Payment Terms "Other" asks for a new term and saves it for everyone.
 *
 * Forms marked data-customer-form are set up on page load, except those also
 * marked data-customer-form-lazy (the popup), which call init() when opened.
 */
(function () {
  const DIRECT = 'Direct';

  function field(root, name) {
    return root.querySelector(`[name="${name}"]`);
  }

  function show(root, part, visible) {
    const el = root.querySelector(`[data-cf="${part}"]`);
    if (el) el.style.display = visible ? '' : 'none';
  }

  function syncNameFields(root) {
    const isDirect = (field(root, 'customer_type') || {}).value === DIRECT;
    show(root, 'account-names', !isDirect);
    show(root, 'person-names', isDirect);
    // Only the visible pair is required; a hidden required field would block saving.
    const agentName = field(root, 'agent_name');
    const firstName = field(root, 'first_name');
    if (agentName) agentName.required = !isDirect;
    if (firstName) firstName.required = isDirect;
  }

  function syncFinanceFields(root) {
    const pt = String((field(root, 'payment_terms') || {}).value || '').trim();
    const isCliq = pt === 'Cliq';
    show(root, 'bank-fields', !isCliq);
    show(root, 'cliq-field', isCliq);
  }

  function ensurePaymentTermOption(selectEl, value) {
    const val = String(value || '').trim();
    if (!selectEl || !val) return false;
    const exists = Array.from(selectEl.options).some(opt => (opt.value || '').toLowerCase() === val.toLowerCase());
    if (exists) return false;
    const option = document.createElement('option');
    option.value = val;
    option.textContent = val;
    const otherOption = Array.from(selectEl.options).find(opt => opt.value === 'Other');
    if (otherOption) selectEl.insertBefore(option, otherOption);
    else selectEl.appendChild(option);
    return true;
  }

  function openCustomPromptModal(root, message, onSubmit) {
    const existingOverlay = document.getElementById('customer-payment-prompt-overlay');
    if (existingOverlay) existingOverlay.remove();
    const overlay = document.createElement('div');
    overlay.id = 'customer-payment-prompt-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:99999;';
    const dialog = document.createElement('div');
    dialog.style.cssText = 'background:white;border-radius:12px;padding:24px;min-width:360px;max-width:460px;box-shadow:0 20px 60px rgba(0,0,0,0.3);';
    dialog.innerHTML = `
      <div style="font-size:14px;font-weight:600;color:#1e293b;margin-bottom:12px;">${message}</div>
      <input type="text" id="customer-payment-prompt-input" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;outline:none;box-sizing:border-box;" placeholder="Type value..." autofocus>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
        <button type="button" id="customer-payment-prompt-cancel" style="padding:6px 16px;border:1px solid #cbd5e1;border-radius:6px;background:#f8fafc;color:#475569;font-size:12px;cursor:pointer;">Cancel</button>
        <button type="button" id="customer-payment-prompt-ok" style="padding:6px 16px;border:none;border-radius:6px;background:#3b82f6;color:white;font-size:12px;cursor:pointer;font-weight:500;">Add</button>
      </div>
    `;
    overlay.appendChild(dialog);
    // Inside a Bootstrap modal the prompt must live in the modal, or the modal's
    // focus trap pulls focus away from the prompt's input.
    (root.closest('.modal') || document.body).appendChild(overlay);
    const input = document.getElementById('customer-payment-prompt-input');
    const okBtn = document.getElementById('customer-payment-prompt-ok');
    const cancelBtn = document.getElementById('customer-payment-prompt-cancel');
    const submit = () => {
      const value = (input?.value || '').trim();
      overlay.remove();
      onSubmit(value);
    };
    const cancel = () => overlay.remove();
    okBtn?.addEventListener('click', submit);
    cancelBtn?.addEventListener('click', cancel);
    input?.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        submit();
      }
      if (e.key === 'Escape') {
        e.stopPropagation();
        cancel();
      }
    });
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) cancel();
    });
    setTimeout(() => input?.focus(), 50);
  }

  async function persistCustomerPaymentTerm(value) {
    const v = String(value || '').trim();
    if (!v) return false;
    try {
      const resp = await fetch('/inbound/api/supplier-option-values/global', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'customer_payment_terms', value: v })
      });
      const data = await resp.json();
      return !!(resp.ok && data && data.success);
    } catch (_) {
      return false;
    }
  }

  async function loadCustomPaymentTerms(selectEl) {
    try {
      const resp = await fetch('/inbound/api/supplier-option-values/global?key=customer_payment_terms');
      const data = await resp.json();
      if (data && data.success && Array.isArray(data.values)) {
        data.values.forEach(v => ensurePaymentTermOption(selectEl, v));
      }
    } catch (_) {}
  }

  function bind(root) {
    const typeSel = field(root, 'customer_type');
    if (typeSel) typeSel.addEventListener('change', () => syncNameFields(root));

    const sel = field(root, 'payment_terms');
    if (!sel) return;
    loadCustomPaymentTerms(sel);
    sel.addEventListener('change', function () {
      if (sel.value !== 'Other') {
        syncFinanceFields(root);
        return;
      }
      openCustomPromptModal(root, 'Enter new payment term:', async function (customValue) {
        const val = String(customValue || '').trim();
        if (!val) {
          sel.value = '';
          syncFinanceFields(root);
          return;
        }
        ensurePaymentTermOption(sel, val);
        sel.value = val;
        const ok = await persistCustomerPaymentTerm(val);
        if (!ok) {
          console.warn('Could not save payment term globally.');
        }
        syncFinanceFields(root);
      });
    });
  }

  function init(root) {
    if (!root) return;
    if (root.dataset.customerFormBound !== '1') {
      root.dataset.customerFormBound = '1';
      bind(root);
    }
    syncNameFields(root);
    syncFinanceFields(root);
  }

  function clearErrors(root) {
    root.querySelectorAll('[data-field-error]').forEach(el => { el.textContent = ''; });
  }

  // Puts each server error under its field; returns the ones with no field to sit under.
  function showErrors(root, errors) {
    const unplaced = [];
    Object.entries(errors || {}).forEach(([name, messages]) => {
      const text = [].concat(messages).join(' ');
      const slot = root.querySelector(`[data-field-error="${name}"]`);
      if (slot) slot.textContent = text;
      else unplaced.push(text);
    });
    return unplaced;
  }

  window.CustomerFormFields = { init, clearErrors, showErrors };

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-customer-form]:not([data-customer-form-lazy])').forEach(init);
  });
})();
