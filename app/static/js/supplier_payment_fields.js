(function () {
    const WRAP_OVERRIDES = {
        new_hotel: {
            bankNameWrap: 'bankNameFieldWrap',
            bankAccountWrap: 'bankAccountFieldWrap',
            cliqWrap: 'cliqFieldWrap',
        },
    };

    const SUPPLIER_PREFIXES = [
        'new_hotel',
        'new_transport',
        'new_guide',
        'new_restaurant',
        'new_ma_rep',
        'new_airline',
        'new_arrival_supplier',
        'new_departure_supplier',
    ];

    function getWrapIds(prefix) {
        if (WRAP_OVERRIDES[prefix]) {
            return WRAP_OVERRIDES[prefix];
        }
        return {
            bankNameWrap: `${prefix}_bank_name_wrap`,
            bankAccountWrap: `${prefix}_bank_account_wrap`,
            cliqWrap: `${prefix}_cliq_wrap`,
        };
    }

    function syncSupplierPaymentMethodFields(prefix) {
        const methodSelect = document.getElementById(`${prefix}_payment_method`);
        if (!methodSelect) return;

        const ids = getWrapIds(prefix);
        const bankNameWrap = document.getElementById(ids.bankNameWrap);
        const bankAccountWrap = document.getElementById(ids.bankAccountWrap);
        const cliqWrap = document.getElementById(ids.cliqWrap);
        const method = methodSelect.value;

        if (bankNameWrap) bankNameWrap.style.display = method === 'Bank' ? '' : 'none';
        if (bankAccountWrap) bankAccountWrap.style.display = method === 'Bank' ? '' : 'none';
        if (cliqWrap) cliqWrap.style.display = method === 'Cliq' ? '' : 'none';
    }

    function bindSupplierPaymentMethodFields(prefix) {
        const methodSelect = document.getElementById(`${prefix}_payment_method`);
        if (!methodSelect) return;

        if (methodSelect.dataset.paymentSyncBound !== '1') {
            methodSelect.dataset.paymentSyncBound = '1';
            methodSelect.addEventListener('change', function () {
                syncSupplierPaymentMethodFields(prefix);
            });
        }
        syncSupplierPaymentMethodFields(prefix);
    }

    function getSupplierPaymentFinancialFields(prefix) {
        const paymentTerms = (document.getElementById(`${prefix}_payment_terms`)?.value || '').trim();
        const paymentMethod = (document.getElementById(`${prefix}_payment_method`)?.value || '').trim();
        const bankName = (document.getElementById(`${prefix}_bank_name`)?.value || '').trim();
        const bankAccount = (document.getElementById(`${prefix}_bank_account`)?.value || '').trim();
        const cliqAlias = (document.getElementById(`${prefix}_cliq_alias`)?.value || '').trim();

        if (document.getElementById(`${prefix}_payment_method`)) {
            return {
                payment_terms: paymentTerms,
                payment_method: paymentMethod,
                bank_name: paymentMethod === 'Cliq' ? 'Cliq' : (paymentMethod === 'Bank' ? bankName : ''),
                bank_account: paymentMethod === 'Cliq' ? cliqAlias : (paymentMethod === 'Bank' ? bankAccount : ''),
                cliq_alias: cliqAlias,
            };
        }

        return {
            payment_terms: paymentTerms,
            bank_name: paymentTerms === 'Cliq' ? 'Cliq' : bankName,
            bank_account: paymentTerms === 'Cliq' ? cliqAlias : bankAccount,
            cliq_alias: cliqAlias,
        };
    }

    window.syncSupplierPaymentMethodFields = syncSupplierPaymentMethodFields;
    window.syncAccommodationPaymentMethodFields = function () {
        syncSupplierPaymentMethodFields('new_hotel');
    };
    window.bindSupplierPaymentMethodFields = bindSupplierPaymentMethodFields;
    window.getSupplierPaymentFinancialFields = getSupplierPaymentFinancialFields;
    window.getSupplierDialogFinancialFields = getSupplierPaymentFinancialFields;

    function initAllSupplierPaymentFields() {
        SUPPLIER_PREFIXES.forEach(bindSupplierPaymentMethodFields);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllSupplierPaymentFields);
    } else {
        initAllSupplierPaymentFields();
    }
})();
