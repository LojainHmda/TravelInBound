/**
 * AI Chat Widget for Travel Booking Platform
 * Provides intelligent booking assistance using OpenAI
 */

class AIChat {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.createChatWidget();
        this.bindEvents();
        this.addWelcomeMessage();
    }

    createChatWidget() {
        // Create AI chat button
        const chatFab = document.createElement('button');
        chatFab.className = 'ai-chat-fab';
        chatFab.id = 'aiChatFab';
        chatFab.innerHTML = `
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
        `;

        // Create chat widget
        const chatWidget = document.createElement('div');
        chatWidget.className = 'ai-chat-widget';
        chatWidget.id = 'aiChatWidget';
        chatWidget.innerHTML = `
            <div class="ai-chat-header">
                <div class="ai-chat-title">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                    AI Travel Assistant
                </div>
                <button class="ai-chat-close" id="aiChatClose">×</button>
            </div>
            
            <div class="ai-chat-messages" id="aiChatMessages">
                <!-- Messages will be added here dynamically -->
            </div>
            
            <div class="ai-chat-input-container">
                <div class="ai-chat-input-group">
                    <textarea 
                        class="ai-chat-input" 
                        id="aiChatInput" 
                        placeholder="Ask me about bookings, customers, or travel details..."
                        rows="1"
                    ></textarea>
                    <button class="ai-chat-send" id="aiChatSend">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(chatFab);
        document.body.appendChild(chatWidget);

        this.chatFab = chatFab;
        this.chatWidget = chatWidget;
        this.messagesContainer = document.getElementById('aiChatMessages');
        this.inputField = document.getElementById('aiChatInput');
        this.sendButton = document.getElementById('aiChatSend');
    }

    bindEvents() {
        // Toggle chat widget
        this.chatFab.addEventListener('click', () => {
            this.toggle();
        });

        document.getElementById('aiChatClose').addEventListener('click', () => {
            this.close();
        });

        // Send message events
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.inputField.addEventListener('input', () => {
            this.inputField.style.height = 'auto';
            this.inputField.style.height = Math.min(this.inputField.scrollHeight, 80) + 'px';
        });

        // Close chat when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.ai-chat-widget') && 
                !e.target.closest('.ai-chat-fab') && 
                this.isOpen) {
                // Don't auto-close the chat to avoid interrupting conversations
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        this.chatWidget.classList.add('show');
        this.chatFab.classList.add('active');
        this.inputField.focus();
    }

    close() {
        this.isOpen = false;
        this.chatWidget.classList.remove('show');
        this.chatFab.classList.remove('active');
    }

    addWelcomeMessage() {
        const welcomeMessage = {
            type: 'ai',
            content: 'Hi! I\'m your AI travel assistant. I can help you find booking information, check customer details, and answer questions about your travel platform. Try asking me something like:',
            timestamp: new Date()
        };

        this.addMessage(welcomeMessage);

        // Add suggestions
        setTimeout(() => {
            this.addSuggestions([
                'Find booking IR-12345',
                'Show me recent bookings',
                'Search for John Smith',
                'What bookings are pending?',
                'Show me today\'s confirmations'
            ]);
        }, 500);
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.type}`;

        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${message.type}`;
        avatar.innerHTML = message.type === 'user' ? 'U' : 'AI';

        const bubble = document.createElement('div');
        bubble.className = `message-bubble ${message.type}`;
        
        // Handle booking data in AI responses
        if (message.bookingData && message.bookingData.bookings) {
            bubble.innerHTML = this.formatAIResponse(message.content, message.bookingData);
        } else {
            bubble.innerHTML = this.formatMessageContent(message.content);
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        if (message.type === 'user') {
            messageDiv.appendChild(bubble);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(bubble);
        }

        bubble.appendChild(time);
        this.messagesContainer.appendChild(messageDiv);
    }

    formatAIResponse(content, bookingData) {
        let html = this.formatMessageContent(content);

        // Add customer cards if available
        if (bookingData.customers && bookingData.customers.length > 0) {
            html += '<div style="margin-top: 10px;">';
            bookingData.customers.forEach(customer => {
                html += this.createCustomerCard(customer);
            });
            html += '</div>';
        }

        // Add booking cards if available
        if (bookingData.bookings && bookingData.bookings.length > 0) {
            html += '<div style="margin-top: 10px;">';
            bookingData.bookings.forEach(booking => {
                html += this.createBookingCard(booking);
            });
            html += '</div>';
        }

        // Add action results if available
        if (bookingData.actions_performed && bookingData.actions_performed.length > 0) {
            html += this.createActionResults(bookingData);
        }

        return html;
    }

    createCustomerCard(customer) {
        return `
            <div class="booking-card" onclick="window.open('/customer/${customer.id}', '_blank')">
                <div class="booking-card-header">
                    👤 ${customer.name}
                </div>
                <div class="booking-card-detail">
                    📧 Email: ${customer.email || 'Not provided'}
                </div>
                <div class="booking-card-detail">
                    📞 Phone: ${customer.phone || 'Not provided'}
                </div>
                ${customer.company ? `
                    <div class="booking-card-detail">
                        🏢 Company: ${customer.company}
                    </div>
                ` : ''}
                <div class="booking-card-detail">
                    🌍 Country: ${customer.country || 'Not specified'}
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 6px;">
                    Click to view customer details
                </div>
            </div>
        `;
    }

    createBookingCard(booking) {
        return `
            <div class="booking-card" onclick="window.open('/booking/${booking.id}', '_blank')">
                <div class="booking-card-header">
                    📋 ${booking.reference_number} - ${booking.status}
                </div>
                <div class="booking-card-detail">
                    👤 Customer: ${booking.customer_name}
                </div>
                <div class="booking-card-detail">
                    💰 Amount: $${booking.total_amount.toFixed(2)}
                </div>
                ${booking.service_items.length > 0 ? `
                    <div class="booking-card-detail">
                        🛫 Services: ${booking.service_items.length} item(s)
                    </div>
                ` : ''}
                <div style="font-size: 11px; color: #666; margin-top: 6px;">
                    Click to view details
                </div>
                <div style="margin-top: 8px;">
                    <button onclick="event.stopPropagation(); aiChat.generateInvoice(${booking.id})" 
                            class="btn btn-sm btn-primary me-2">
                        📄 Generate Invoice
                    </button>
                    <button onclick="event.stopPropagation(); aiChat.sendWhatsApp(${booking.id})" 
                            class="btn btn-sm btn-success">
                        💬 Send WhatsApp
                    </button>
                </div>
            </div>
        `;
    }

    createActionResults(bookingData) {
        let html = '<div style="margin-top: 15px; padding: 12px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #28a745;">';
        
        html += '<div style="font-weight: 600; color: #155724; margin-bottom: 8px;">✅ Actions Completed:</div>';
        
        bookingData.actions_performed.forEach(action => {
            html += `<div style="color: #155724; font-size: 13px;">• ${action}</div>`;
        });

        // Show invoice details if available
        if (bookingData.action_results?.invoice?.success) {
            html += `
                <div style="margin-top: 10px; padding: 8px; background: white; border-radius: 6px;">
                    <strong>📄 Invoice Generated:</strong><br>
                    <small>${bookingData.action_results.invoice.message}</small><br>
                    <a href="${bookingData.action_results.invoice.download_url}" target="_blank" 
                       style="color: #007bff; text-decoration: none;">
                        📥 Download Invoice
                    </a>
                </div>
            `;
        }

        // Show WhatsApp preview if available
        if (bookingData.action_results?.whatsapp?.success) {
            html += `
                <div style="margin-top: 10px; padding: 8px; background: white; border-radius: 6px;">
                    <strong>💬 WhatsApp Message Preview:</strong><br>
                    <div style="font-family: monospace; font-size: 12px; background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 4px; white-space: pre-line;">${bookingData.action_results.whatsapp.message_preview}</div>
                    <small style="color: #666;">Sent to: ${bookingData.action_results.whatsapp.recipient}</small>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    formatMessageContent(content) {
        // Convert line breaks to HTML
        return content.replace(/\n/g, '<br>');
    }

    addSuggestions(suggestions) {
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'chat-suggestions';

        suggestions.forEach(suggestion => {
            const suggestionButton = document.createElement('button');
            suggestionButton.className = 'chat-suggestion';
            suggestionButton.textContent = suggestion;
            suggestionButton.onclick = () => {
                this.inputField.value = suggestion;
                this.sendMessage();
                suggestionsDiv.remove();
            };
            suggestionsDiv.appendChild(suggestionButton);
        });

        this.messagesContainer.appendChild(suggestionsDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message ai';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-avatar ai">AI</div>
            <div class="message-bubble ai">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage({
            type: 'user',
            content: message,
            timestamp: new Date()
        });

        // Clear input
        this.inputField.value = '';
        this.inputField.style.height = 'auto';

        // Disable send button
        this.sendButton.disabled = true;
        this.showTypingIndicator();

        try {
            // Capture current screen context
            const screenContext = window.screenContext ? window.screenContext.getContextForAI() : {};
            
            // Decide whether to use contextual or regular chat
            const useContextual = this.shouldUseContextualChat(message, screenContext);
            
            const endpoint = useContextual ? '/api/chat/contextual' : '/api/chat';
            const requestBody = {
                message: message,
                timestamp: new Date().toISOString()
            };
            
            if (useContextual) {
                requestBody.screen_context = screenContext;
            }

            // Send to AI chat API
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success) {
                // Add AI response
                this.addMessage({
                    type: 'ai',
                    content: data.response,
                    bookingData: data.booking_data,
                    screenUpdates: data.screen_updates,
                    nextSteps: data.next_steps,
                    timestamp: new Date()
                });

                // Handle screen updates if any
                if (data.screen_updates) {
                    this.handleScreenUpdates(data.screen_updates);
                }
            } else {
                throw new Error(data.error || 'AI chat service error');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage({
                type: 'ai',
                content: 'I apologize, but I\'m having trouble right now. Please try again later or contact support if the problem persists.',
                timestamp: new Date()
            });
        } finally {
            this.hideTypingIndicator();
            this.sendButton.disabled = false;
            this.inputField.focus();
        }
    }

    shouldUseContextualChat(message, screenContext) {
        // Use contextual chat for screen-aware queries
        const contextualKeywords = [
            'this', 'current', 'update', 'change', 'edit', 'modify', 
            'here', 'show me', 'what is', 'explain this',
            'on this page', 'in this table', 'selected',
            'first', 'last', 'top', 'bottom'
        ];
        
        const hasContextKeywords = contextualKeywords.some(keyword => 
            message.toLowerCase().includes(keyword)
        );
        
        const hasScreenData = screenContext && (
            screenContext.visible_data || 
            screenContext.table_data || 
            screenContext.current_data
        );
        
        return hasContextKeywords && hasScreenData;
    }

    handleScreenUpdates(screenUpdates) {
        // Handle different types of screen updates
        if (screenUpdates.redirect_url) {
            setTimeout(() => {
                window.location.href = screenUpdates.redirect_url;
            }, 1500);
        }
        
        if (screenUpdates.highlight_element) {
            this.highlightElement(screenUpdates.highlight_element);
        }
        
        if (screenUpdates.suggested_values && screenUpdates.field) {
            this.showFieldSuggestions(screenUpdates.field, screenUpdates.suggested_values);
        }
    }

    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.style.transition = 'all 0.3s ease';
            element.style.boxShadow = '0 0 10px #007bff';
            element.style.border = '2px solid #007bff';
            
            setTimeout(() => {
                element.style.boxShadow = '';
                element.style.border = '';
            }, 3000);
        }
    }

    showFieldSuggestions(field, suggestions) {
        // Create suggestion popup near the field
        const fieldElement = document.querySelector(`[name="${field}"], #${field}`);
        if (fieldElement && suggestions.length > 0) {
            const popup = document.createElement('div');
            popup.className = 'ai-suggestions-popup';
            popup.innerHTML = `
                <div style="background: white; border: 1px solid #ddd; border-radius: 6px; padding: 10px; position: absolute; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <div style="font-weight: bold; margin-bottom: 8px;">AI Suggestions:</div>
                    ${suggestions.map(suggestion => `
                        <div style="padding: 4px 8px; cursor: pointer; border-radius: 3px;" 
                             onmouseover="this.style.background='#f0f8ff'" 
                             onmouseout="this.style.background=''"
                             onclick="document.querySelector('[name=\\'${field}\\']').value='${suggestion}'; this.parentElement.parentElement.remove();">
                            ${suggestion}
                        </div>
                    `).join('')}
                </div>
            `;
            
            fieldElement.parentNode.appendChild(popup);
            
            // Remove popup after 10 seconds
            setTimeout(() => {
                if (popup.parentNode) {
                    popup.parentNode.removeChild(popup);
                }
            }, 10000);
        }
    }

    async generateInvoice(bookingId) {
        try {
            const response = await fetch(`/api/chat/booking/${bookingId}`, {
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage({
                    type: 'ai',
                    content: '📄 Invoice generated successfully! You can download it from the booking details.',
                    timestamp: new Date()
                });
            }
        } catch (error) {
            this.addMessage({
                type: 'ai',
                content: 'Sorry, I had trouble generating the invoice. Please try again.',
                timestamp: new Date()
            });
        }
    }

    async sendWhatsApp(bookingId) {
        try {
            this.addMessage({
                type: 'user',
                content: `Send WhatsApp for booking ${bookingId}`,
                timestamp: new Date()
            });

            this.showTypingIndicator();

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: `Generate WhatsApp message for booking ${bookingId}`,
                    timestamp: new Date().toISOString()
                })
            });

            const data = await response.json();
            
            this.hideTypingIndicator();

            if (data.success) {
                this.addMessage({
                    type: 'ai',
                    content: data.response,
                    bookingData: data.booking_data,
                    timestamp: new Date()
                });
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage({
                type: 'ai',
                content: 'Sorry, I had trouble sending the WhatsApp message. Please try again.',
                timestamp: new Date()
            });
        }
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
}

// Initialize AI Chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiChat = new AIChat();
});