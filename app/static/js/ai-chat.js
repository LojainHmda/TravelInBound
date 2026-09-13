/**
 * Operations assistant widget -- Phase 1.
 *
 * Talks to /api/assistant. Renders the model's prose, then renders the tool
 * results as real tables from the returned data rather than trusting the prose
 * to have repeated the numbers correctly.
 *
 * Reuses the existing .ai-chat-* classes in css/ai-chat.css.
 */
(function () {
    'use strict';

    var ENDPOINT = '/api/assistant';
    var CONTEXT_ENDPOINT = '/api/assistant/context';
    var CUSTOMER_ENDPOINT = '/api/assistant/customer';

    // Kept short on purpose: long labels wrap to several rows and crowd the
    // message area out of a 300-350px widget.
    var SUGGESTIONS = [
        { label: 'Today', text: 'Run down for today' },
        { label: 'This week', text: 'Run down for this week' },
        { label: 'Accommodation', text: 'Show accommodation requests' },
        { label: 'Find customer', text: 'Find customer ', keepOpen: true }
    ];

    // Stable per-tab id so logged turns can be stitched back into one
    // conversation. sessionStorage so a reload keeps the thread; wrapped
    // because it throws outright in some embedded/blocked-storage contexts.
    var sessionKey = (function () {
        var key;
        try {
            key = sessionStorage.getItem('assistantSessionKey');
            if (!key) {
                key = 's-' + Date.now().toString(36) + '-' +
                    Math.random().toString(36).slice(2, 10);
                sessionStorage.setItem('assistantSessionKey', key);
            }
        } catch (e) {
            key = 's-' + Date.now().toString(36);
        }
        return key;
    })();

    var history = [];
    var selectedCustomer = null;
    var busy = false;
    var els = {};

    function esc(value) {
        return String(value === null || value === undefined ? '' : value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function ddmmyyyy(iso) {
        if (!iso) { return ''; }
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
        return m ? (m[3] + '/' + m[2] + '/' + m[1]) : iso;
    }

    // Deliberately tiny: bold, code and line breaks only. The assistant is
    // told to keep replies short, and a full markdown parser here would be a
    // large XSS surface for very little gain.
    function miniMarkdown(text) {
        return esc(text)
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    function csrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function build() {
        var fab = document.createElement('button');
        fab.className = 'ai-chat-fab';
        fab.type = 'button';
        fab.setAttribute('aria-label', 'Open assistant');
        fab.innerHTML = '<i class="fas fa-comment-dots"></i>';

        var widget = document.createElement('div');
        // The stylesheet keeps .ai-chat-widget at display:none and reveals it
        // with .show -- toggling [hidden] here would never make it visible.
        widget.className = 'ai-chat-widget';
        widget.innerHTML =
            '<div class="ai-chat-header">' +
                '<div class="ai-chat-title"><i class="fas fa-robot"></i> Assistant</div>' +
                '<button type="button" class="ai-chat-close" aria-label="Close">&times;</button>' +
            '</div>' +
            '<div class="ai-chat-messages" role="log" aria-live="polite"></div>' +
            '<div class="ai-chat-input-container">' +
                '<div class="chat-suggestions"></div>' +
                '<div class="ai-chat-input-group">' +
                    '<input type="text" class="ai-chat-input" placeholder="Ask about tours, files or the run down...">' +
                    '<button type="button" class="ai-chat-send" aria-label="Send">' +
                        '<i class="fas fa-paper-plane"></i></button>' +
                '</div>' +
            '</div>';

        document.body.appendChild(fab);
        document.body.appendChild(widget);

        els.fab = fab;
        els.widget = widget;
        els.messages = widget.querySelector('.ai-chat-messages');
        els.input = widget.querySelector('.ai-chat-input');
        els.send = widget.querySelector('.ai-chat-send');
        els.suggestions = widget.querySelector('.chat-suggestions');

        fab.addEventListener('click', toggle);
        widget.querySelector('.ai-chat-close').addEventListener('click', toggle);
        els.send.addEventListener('click', submit);
        els.input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
        });

        renderSuggestions();
    }

    function renderSuggestions() {
        els.suggestions.innerHTML = '';
        SUGGESTIONS.forEach(function (item) {
            var chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'chat-suggestion';
            chip.textContent = item.label;
            chip.addEventListener('click', function () {
                els.input.value = item.text;
                els.input.focus();
                if (!item.keepOpen) { submit(); }
            });
            els.suggestions.appendChild(chip);
        });
    }

    function toggle() {
        var opening = !els.widget.classList.contains('show');
        els.widget.classList.toggle('show', opening);
        els.fab.classList.toggle('active', opening);
        if (opening) {
            els.input.focus();
            if (!els.messages.childElementCount) {
                addMessage('assistant',
                    'Ask me for a run down, a customer\'s tours, or a drill-down ' +
                    'into any service category.');
            }
            loadContext();
        }
    }

    function addMessage(role, html) {
        var wrap = document.createElement('div');
        wrap.className = 'chat-message ' + (role === 'user' ? 'user' : 'assistant');

        var avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user'
            ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = html;

        wrap.appendChild(avatar);
        wrap.appendChild(bubble);
        els.messages.appendChild(wrap);
        els.messages.scrollTop = els.messages.scrollHeight;
        return bubble;
    }

    function showTyping() {
        var wrap = document.createElement('div');
        wrap.className = 'chat-message assistant typing-indicator';
        wrap.innerHTML = '<div class="message-avatar"><i class="fas fa-robot"></i></div>' +
            '<div class="message-bubble"><span class="typing-dot"></span>' +
            '<span class="typing-dot"></span><span class="typing-dot"></span></div>';
        els.messages.appendChild(wrap);
        els.messages.scrollTop = els.messages.scrollHeight;
        return wrap;
    }

    /* ---------------------------------------------------------------- */
    /* Structured renderers -- numbers come from data, never from prose  */
    /* ---------------------------------------------------------------- */

    function renderSummary(d) {
        var html = '<div class="booking-card">';
        html += '<div class="booking-card-header">Run Down &mdash; ' +
            esc(d.period.label) + ' (' + ddmmyyyy(d.period.date_from) +
            ' &ndash; ' + ddmmyyyy(d.period.date_to) + ')</div>';

        if (d.urgent) {
            html += '<div class="booking-card-detail" style="color:#b42318;font-weight:600">' +
                '<i class="fas fa-triangle-exclamation"></i> Cut-off attention needed: ' +
                d.flagged.map(function (f) {
                    return esc(f.label) + ' (' + f.cut_off + ')';
                }).join(', ') + '</div>';
        }

        html += '<table style="width:100%;border-collapse:collapse;font-size:12px">' +
            '<thead><tr>' +
            ['Category', 'Req', 'Conf', 'Wait', 'Canc', 'Cut-off'].map(function (h) {
                return '<th style="text-align:left;padding:4px;border-bottom:1px solid #ddd">' + h + '</th>';
            }).join('') + '</tr></thead><tbody>';

        d.categories.forEach(function (c) {
            // REQ-3.5: zero-activity categories are shown, not dropped.
            var dim = c.has_activity ? '' : 'opacity:.55;';
            var cut = !c.cut_off_applicable
                ? '<span title="Cut-off does not apply to this category">n/a</span>'
                : (c.cut_off > 0
                    ? '<strong style="color:#b42318">' + c.cut_off + '</strong>'
                    : '0');
            html += '<tr style="' + dim + '">' +
                '<td style="padding:4px">' + esc(c.label) +
                    (c.has_activity ? '' : ' <em style="font-size:11px">no activity</em>') + '</td>' +
                '<td style="padding:4px">' + c.requested + '</td>' +
                '<td style="padding:4px">' + c.confirmed + '</td>' +
                '<td style="padding:4px">' + c.waiting + '</td>' +
                '<td style="padding:4px">' + c.cancelled + '</td>' +
                '<td style="padding:4px">' + cut + '</td></tr>';
        });

        return html + '</tbody></table></div>';
    }

    function renderDrilldown(d) {
        var html = '<div class="booking-card">';
        html += '<div class="booking-card-header">' + esc(d.label) + ' &mdash; ' +
            esc(d.status_filter) + ' &mdash; ' + esc(d.period.label) + '</div>';

        var bits = [];
        if (d.city) { bits.push('City: ' + esc(d.city)); }
        if (d.name_filter) { bits.push('Name: ' + esc(d.name_filter)); }
        bits.push('Grouped by ' + esc(d.grouped_by));
        bits.push(d.matched + ' of ' + d.total_in_range + ' in range');
        html += '<div class="booking-card-detail">' + bits.join(' &middot; ') + '</div>';

        if (!d.groups.length) {
            return html + '<div class="booking-card-detail"><em>No matching rows.</em></div></div>';
        }

        d.groups.forEach(function (g) {
            html += '<div class="service-item"><strong>' + esc(g.label) +
                '</strong> (' + g.count + ')';
            html += '<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:4px">' +
                '<thead><tr>' +
                ['File', 'Date', 'Name', 'Pax', 'Status', 'File Status'].map(function (h) {
                    return '<th style="text-align:left;padding:3px;border-bottom:1px solid #ddd">' + h + '</th>';
                }).join('') + '</tr></thead><tbody>';
            g.rows.forEach(function (r) {
                // REQ-4.5: Status and File Status stay in separate columns.
                html += '<tr>' +
                    '<td style="padding:3px">' + esc(r.request_number) + '</td>' +
                    '<td style="padding:3px">' + ddmmyyyy(r.date) + '</td>' +
                    '<td style="padding:3px">' + esc(r.name) + '</td>' +
                    '<td style="padding:3px">' + esc(r.pax) + '</td>' +
                    '<td style="padding:3px">' + esc(r.status) + '</td>' +
                    '<td style="padding:3px">' + esc(r.file_status) + '</td></tr>';
            });
            html += '</tbody></table></div>';
        });

        return html + '</div>';
    }

    function renderCustomers(d) {
        if (!d.customers.length) {
            return '<div class="booking-card"><div class="booking-card-detail">' +
                'No customer matches &ldquo;' + esc(d.query) + '&rdquo;.</div></div>';
        }
        var html = '<div class="booking-card"><div class="booking-card-header">' +
            d.count + ' customer' + (d.count === 1 ? '' : 's') + ' matching &ldquo;' +
            esc(d.query) + '&rdquo;</div>';
        d.customers.forEach(function (c) {
            html += '<button type="button" class="service-item js-pick-customer" ' +
                'data-customer-id="' + esc(c.id) + '" data-customer-name="' + esc(c.name) + '" ' +
                'style="display:block;width:100%;text-align:left;cursor:pointer;border:0;background:none">' +
                '<strong>' + esc(c.name) + '</strong>' +
                (c.company_name ? ' &middot; ' + esc(c.company_name) : '') +
                (c.email ? '<br><small>' + esc(c.email) + '</small>' : '') +
                '</button>';
        });
        return html + '</div>';
    }

    function renderTours(d) {
        if (!d.tours.length) {
            return '<div class="booking-card"><div class="booking-card-detail">' +
                'No inbound tours for &ldquo;' + esc(d.customer_name) + '&rdquo;.</div></div>';
        }

        var html = '<div class="booking-card"><div class="booking-card-header">' +
            d.count + ' inbound tour' + (d.count === 1 ? '' : 's') + ' for ' +
            esc(d.customer_name) +
            (d.truncated ? ' (showing ' + d.returned + ')' : '') + '</div>';

        var bits = [];
        if (d.span && d.span.date_from) {
            bits.push('Travelling ' + ddmmyyyy(d.span.date_from) +
                ' &ndash; ' + ddmmyyyy(d.span.date_to));
        }
        bits.push('Grouped by ' + esc(d.grouped_by || 'status'));
        html += '<div class="booking-card-detail">' + bits.join(' &middot; ') + '</div>';

        // Same shape as a Run Down drill-down: a headed section per group,
        // each with its own row table.
        (d.groups || []).forEach(function (g) {
            html += '<div class="service-item"><strong>' + esc(g.label) +
                '</strong> (' + g.count + ')';
            html += '<table><thead><tr>' +
                ['File', 'Dates', 'Days', 'Pax'].map(function (h) {
                    return '<th style="text-align:left;padding:3px;border-bottom:1px solid #ddd">' +
                        h + '</th>';
                }).join('') + '</tr></thead><tbody>';
            g.rows.forEach(function (r) {
                html += '<tr>' +
                    '<td style="padding:3px"><a href="' + esc(r.url) + '">' +
                        esc(r.request_number) + '</a></td>' +
                    '<td style="padding:3px">' + ddmmyyyy(r.from_date) + ' &ndash; ' +
                        ddmmyyyy(r.to_date) + '</td>' +
                    '<td style="padding:3px">' + esc(r.no_of_days) + '</td>' +
                    '<td style="padding:3px">' + esc(r.pax) + '</td></tr>';
            });
            html += '</tbody></table></div>';
        });

        if (d.list_url) {
            html += '<a class="chat-suggestion" style="display:inline-block;' +
                'margin-top:6px" href="' + esc(d.list_url) + '">' +
                'Open the file list</a>';
        }
        return html + '</div>';
    }

    var RENDERERS = {
        run_down_summary: renderSummary,
        run_down_drilldown: renderDrilldown,
        search_customers: renderCustomers,
        find_inbound_tours: renderTours
    };

    function renderResults(bubble, toolResults) {
        (toolResults || []).forEach(function (item) {
            var result = item.result || {};
            var render = RENDERERS[item.tool];
            if (!render) { return; }
            if (!result.ok) {
                var box = document.createElement('div');
                box.className = 'booking-card-detail';
                box.style.color = '#b42318';
                box.textContent = result.error || 'That lookup failed.';
                if (result.hint) { box.textContent += ' ' + result.hint; }
                bubble.appendChild(box);
                return;
            }
            var holder = document.createElement('div');
            holder.innerHTML = render(result);
            bubble.appendChild(holder);
        });
    }

    function addNavigation(bubble, url) {
        if (!url) { return; }
        var link = document.createElement('a');
        link.href = url;
        link.className = 'chat-suggestion';
        link.style.display = 'inline-block';
        link.style.marginTop = '6px';
        // Name the destination -- "Open this page" is wrong when the reply was
        // about tours and the link goes to the Run Down.
        var where = url.indexOf('/run-down') > -1 ? 'Run Down' : 'the file list';
        link.innerHTML = '<i class="fas fa-arrow-up-right-from-square"></i> Open ' + where;
        bubble.appendChild(link);
    }

    /* ---------------------------------------------------------------- */

    function loadContext() {
        fetch(CONTEXT_ENDPOINT, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) { selectedCustomer = d.selected_customer || null; })
            .catch(function () { /* context is a nicety, not required */ });
    }

    function pickCustomer(id, name) {
        fetch(CUSTOMER_ENDPOINT, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: JSON.stringify({ customer: { id: id, name: name } })
        }).then(function (r) { return r.json(); }).then(function (d) {
            selectedCustomer = d.selected_customer || null;
            addMessage('assistant', 'Selected <strong>' + esc(name) +
                '</strong>. Ask about their tours, or say "show their inbound tours".');
        }).catch(function () {
            addMessage('assistant', 'Could not select that customer.');
        });
    }

    function submit() {
        var text = (els.input.value || '').trim();
        if (!text || busy) { return; }

        busy = true;
        els.suggestions.style.display = 'none';
        els.input.value = '';
        els.send.disabled = true;
        addMessage('user', esc(text));
        var typing = showTyping();

        fetch(ENDPOINT, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: JSON.stringify({
                message: text,
                history: history.slice(-8),
                session_key: sessionKey
            })
        }).then(function (r) {
            return r.json().then(function (body) { return { status: r.status, body: body }; });
        }).then(function (res) {
            typing.remove();
            var d = res.body || {};
            var bubble = addMessage('assistant', miniMarkdown(
                d.reply || d.error || 'No answer came back.'));
            renderResults(bubble, d.tool_results);
            addNavigation(bubble, d.navigate_url);
            if (d.selected_customer !== undefined) {
                selectedCustomer = d.selected_customer;
            }
            history.push({ role: 'user', content: text });
            if (d.reply) { history.push({ role: 'assistant', content: d.reply }); }
            els.messages.scrollTop = els.messages.scrollHeight;
        }).catch(function (err) {
            typing.remove();
            addMessage('assistant', 'Could not reach the assistant: ' + esc(err.message));
        }).then(function () {
            busy = false;
            els.send.disabled = false;
            els.input.focus();
        });
    }

    function init() {
        build();
        els.messages.addEventListener('click', function (e) {
            var btn = e.target.closest('.js-pick-customer');
            if (btn) {
                pickCustomer(btn.getAttribute('data-customer-id'),
                             btn.getAttribute('data-customer-name'));
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
