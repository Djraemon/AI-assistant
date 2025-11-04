/**
 * AI Teaching Assistant RAG System - Frontend JavaScript
 * Handles chat functionality, API communication, and user interactions
 */

// Configuration
const CONFIG = {
    API_BASE_URL: '/api/rag',
    MAX_MESSAGE_LENGTH: 5000,
    TYPING_DELAY: 300,
    ANIMATION_DURATION: 500
};

// Application State
const AppState = {
    chatHistory: [],
    isLoading: false,
    currentRating: null
};

// DOM Elements
const Elements = {
    chatMessages: null,
    queryInput: null,
    sendButton: null,
    clearButton: null,
    loadingIndicator: null
};

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    bindEvents();
    loadChatHistory();
    focusInput();
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
    Elements.chatMessages = document.getElementById('chat-messages');
    Elements.queryInput = document.getElementById('query-input');
    Elements.sendButton = document.getElementById('send-button');
    Elements.clearButton = document.getElementById('clear-button');

    if (!Elements.chatMessages || !Elements.queryInput) {
        console.error('Required DOM elements not found');
        showError('页面加载失败，请刷新重试');
        return false;
    }

    return true;
}

/**
 * Bind event listeners
 */
function bindEvents() {
    if (Elements.queryInput) {
        Elements.queryInput.addEventListener('keypress', handleKeyPress);
        Elements.queryInput.addEventListener('input', handleInputChange);
    }

    if (Elements.sendButton) {
        Elements.sendButton.addEventListener('click', sendQuery);
    }

    if (Elements.clearButton) {
        Elements.clearButton.addEventListener('click', clearChat);
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter to send message
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        sendQuery();
    }

    // Escape to clear input
    if (event.key === 'Escape') {
        Elements.queryInput.value = '';
        Elements.queryInput.focus();
    }
}

/**
 * Handle input change events
 */
function handleInputChange() {
    const input = Elements.queryInput.value.trim();

    // Update send button state
    if (Elements.sendButton) {
        Elements.sendButton.disabled = !input || AppState.isLoading;
    }

    // Character count warning
    if (input.length > CONFIG.MAX_MESSAGE_LENGTH * 0.8) {
        Elements.queryInput.style.borderColor = '#ffc107';
    } else {
        Elements.queryInput.style.borderColor = '';
    }
}

/**
 * Handle key press events
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuery();
    }
}

/**
 * Send query to the backend API
 */
async function sendQuery() {
    const query = Elements.queryInput.value.trim();

    // Validation
    if (!query) {
        showWarning('请输入您的问题');
        return;
    }

    if (query.length > CONFIG.MAX_MESSAGE_LENGTH) {
        showError(`问题过长，请控制在${CONFIG.MAX_MESSAGE_LENGTH}字符以内`);
        return;
    }

    if (AppState.isLoading) {
        showWarning('正在处理上一个问题，请稍候');
        return;
    }

    // Add user message to chat
    addMessage(query, 'user');
    Elements.queryInput.value = '';

    // Show loading state
    setLoadingState(true);
    addMessage('AI助手正在思考中...', 'ai', true);

    try {
        // Send request to backend
        const response = await fetch(`${CONFIG.API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                query: query,
                mode: 'general',
                timestamp: new Date().toISOString()
            })
        });

        const data = await response.json();

        // Remove loading indicator
        removeLastMessage();

        if (response.ok) {
            // Add AI response
            addMessage(data.response, 'ai', false, data.evaluation);

            // Add feedback section
            addFeedbackSection(data.query, data.response);

            // Update state
            AppState.chatHistory.push({
                query: data.query,
                response: data.response,
                evaluation: data.evaluation,
                timestamp: new Date().toISOString()
            });

            saveChatHistory();

        } else {
            const errorMessage = data.detail || data.message || '服务器错误';
            addMessage(`抱歉，出现了错误：${errorMessage}`, 'ai', false, null, 'error');
            console.error('API Error:', data);
        }

    } catch (error) {
        removeLastMessage();

        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            addMessage('无法连接到服务器，请检查网络连接后重试', 'ai', false, null, 'error');
        } else {
            addMessage(`连接错误：${error.message}`, 'ai', false, null, 'error');
        }

        console.error('Network Error:', error);
    } finally {
        setLoadingState(false);
        focusInput();
    }
}

/**
 * Set loading state
 */
function setLoadingState(loading) {
    AppState.isLoading = loading;

    if (Elements.sendButton) {
        Elements.sendButton.disabled = loading;
        Elements.sendButton.innerHTML = loading ?
            '发送中 <span class="loading-indicator"></span>' : '发送';
    }

    if (Elements.queryInput) {
        Elements.queryInput.disabled = loading;
    }
}

/**
 * Add message to chat
 */
function addMessage(text, sender, isLoading = false, evaluation = null, type = 'normal') {
    if (!Elements.chatMessages) return;

    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.id = messageId;

    let content = '';

    if (sender === 'user') {
        content = `
            <strong>您:</strong>
            <div class="message-text">${escapeHtml(text)}</div>
        `;
    } else {
        let evalHtml = '';
        let iconHtml = '';

        if (isLoading) {
            iconHtml = '<span class="loading-indicator"></span>';
        } else if (type === 'error') {
            iconHtml = '<span style="color: var(--danger-color);">⚠️</span>';
        } else {
            iconHtml = '<span style="color: var(--primary-color);">🤖</span>';
        }

        if (evaluation && !isLoading) {
            evalHtml = createEvaluationHtml(evaluation);
        }

        content = `
            <strong>AI助手 ${iconHtml}:</strong>
            <div class="message-text">${formatMessage(text)}</div>
            ${evalHtml}
        `;
    }

    messageDiv.innerHTML = content;
    Elements.chatMessages.appendChild(messageDiv);

    // Smooth scroll to bottom
    smoothScrollToBottom();

    // Fade in animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';

    requestAnimationFrame(() => {
        messageDiv.style.transition = `all ${CONFIG.ANIMATION_DURATION}ms ease-out`;
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    });
}

/**
 * Create evaluation HTML
 */
function createEvaluationHtml(evaluation) {
    if (!evaluation) return '';

    const scores = [
        { label: '相关性', value: evaluation.relevance_score },
        { label: '完整性', value: evaluation.completeness_score },
        { label: '整体', value: evaluation.overall_score }
    ];

    const scoreHtml = scores.map(score => {
        const percentage = Math.round(score.value * 100);
        const color = percentage >= 80 ? 'success' : percentage >= 60 ? 'warning' : 'danger';

        return `
            <div style="margin-bottom: 0.5rem;">
                <small class="text-muted">${score.label}:</small>
                <div class="progress" style="height: 8px; margin-bottom: 0.25rem;">
                    <div class="progress-bar bg-${color}" style="width: ${percentage}%"></div>
                </div>
                <small>${score.value.toFixed(2)}</small>
            </div>
        `;
    }).join('');

    return `
        <div class="eval-score">
            <strong>📊 回答质量评估:</strong>
            <div style="margin-top: 0.5rem;">
                ${scoreHtml}
            </div>
        </div>
    `;
}

/**
 * Add feedback section
 */
function addFeedbackSection(query, response) {
    if (!Elements.chatMessages) return;

    console.log('🎯 添加反馈区域:', { query: query.substring(0, 50) + '...', response: response.substring(0, 50) + '...' });

    const uniqueId = `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const feedbackHtml = `
        <div class="feedback-section" id="${uniqueId}" style="border: 2px solid #667eea; background-color: #f0f8ff; margin-top: 1rem; padding: 1.5rem; border-radius: 8px;">
            <p style="margin-bottom: 1rem; color: #333; font-weight: bold;">
                <strong>📝 对本次回答进行评价:</strong>
                <small style="color: #666; margin-left: 10px;">(您的反馈能帮助我们改进系统)</small>
            </p>

            <div class="rating-buttons" style="margin-bottom: 1rem;">
                ${[1, 2, 3, 4, 5].map(rating => `
                    <button class="btn btn-sm btn-outline-primary"
                            data-rating="${rating}"
                            onclick="handleRatingClick('${uniqueId}', ${rating})"
                            title="${rating}星"
                            style="margin: 0 2px;">
                        ${rating}星
                    </button>
                `).join('')}
            </div>

            <div class="mt-2">
                <textarea id="feedback-comment-${uniqueId}"
                          class="form-control"
                          rows="3"
                          placeholder="请输入您的反馈意见（可选）..."
                          maxlength="1000"
                          style="width: 100%; margin-bottom: 0.5rem;"></textarea>

                <div>
                    <button class="btn btn-sm btn-success"
                            onclick="handleSubmitFeedback('${uniqueId}', '${escapeHtml(query)}', '${escapeHtml(response)}')"
                            style="margin-right: 8px;">
                        ✅ 提交反馈
                    </button>
                    <button class="btn btn-sm btn-secondary"
                            onclick="skipFeedback('${uniqueId}')">
                        ⏭️ 跳过
                    </button>
                </div>
            </div>
        </div>
    `;

    const feedbackDiv = document.createElement('div');
    feedbackDiv.innerHTML = feedbackHtml;
    Elements.chatMessages.appendChild(feedbackDiv);

    console.log('✅ 反馈区域已添加到页面，ID:', uniqueId);
    smoothScrollToBottom();
}

/**
 * Handle rating click
 */
function handleRatingClick(feedbackId, rating) {
    const feedbackSection = document.getElementById(feedbackId);
    if (!feedbackSection) return;

    // Update button styles
    const ratingButtons = feedbackSection.querySelectorAll('.rating-buttons button');
    ratingButtons.forEach((btn, index) => {
        btn.classList.remove('btn-primary', 'btn-outline-primary');
        if (index < rating) {
            btn.classList.add('btn-primary');
        } else {
            btn.classList.add('btn-outline-primary');
        }
    });

    // Store rating
    feedbackSection.setAttribute('data-rating', rating);
    AppState.currentRating = rating;
}

/**
 * Handle feedback submission
 */
async function handleSubmitFeedback(feedbackId, query, response) {
    console.log('🚀 开始提交反馈:', { feedbackId, rating: feedbackSection?.getAttribute('data-rating'), commentLength: comment?.length });

    const feedbackSection = document.getElementById(feedbackId);
    if (!feedbackSection) {
        console.error('❌ 反馈区域不存在:', feedbackId);
        return;
    }

    const comment = document.getElementById(`feedback-comment-${feedbackId}`).value.trim();
    const rating = feedbackSection.getAttribute('data-rating');

    console.log('📊 反馈数据:', { rating, comment: comment.substring(0, 50) + '...', queryLength: query.length });

    // Validation
    if (!comment && !rating) {
        showWarning('请至少选择评分或输入反馈意见');
        return;
    }

    // Disable submit button
    const submitButton = feedbackSection.querySelector('.btn-success');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '提交中 <span class="loading-indicator"></span>';

    try {
        console.log('📡 发送反馈请求到:', `${CONFIG.API_BASE_URL}/feedback`);

        const response = await fetch(`${CONFIG.API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                query: unescapeHtml(query),
                response: unescapeHtml(response),
                rating: rating ? parseInt(rating) : null,
                comment: comment,
                timestamp: new Date().toISOString()
            })
        });

        if (response.ok) {
            showSuccess('感谢您的反馈！');

            // Remove feedback section
            feedbackSection.style.transition = 'opacity 0.5s';
            feedbackSection.style.opacity = '0';
            setTimeout(() => feedbackSection.remove(), 500);

        } else {
            const errorData = await response.json();
            showError(`反馈提交失败：${errorData.detail || '请重试'}`);
        }

    } catch (error) {
        console.error('Feedback submission error:', error);
        showError('网络错误，请重试');
    } finally {
        // Restore button
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

/**
 * Skip feedback
 */
function skipFeedback(feedbackId) {
    const feedbackSection = document.getElementById(feedbackId);
    if (feedbackSection) {
        feedbackSection.style.transition = 'opacity 0.3s';
        feedbackSection.style.opacity = '0';
        setTimeout(() => feedbackSection.remove(), 300);
    }
}

/**
 * Remove last message
 */
function removeLastMessage() {
    const messages = Elements.chatMessages.querySelectorAll('.message');
    if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        lastMessage.style.transition = 'opacity 0.3s';
        lastMessage.style.opacity = '0';
        setTimeout(() => lastMessage.remove(), 300);
    }
}

/**
 * Clear chat
 */
function clearChat() {
    if (!Elements.chatMessages) return;

    if (AppState.chatHistory.length > 1) {
        if (!confirm('确定要清空所有对话记录吗？')) {
            return;
        }
    }

    // Clear messages
    Elements.chatMessages.innerHTML = `
        <div class="message ai-message">
            <strong>AI助手 🤖:</strong>
            <div class="message-text">
                您好！我是您的AI教学助手，专门回答大数据分析课程相关问题。
                我可以解释概念、总结课程内容、解答练习题等。请提出您的问题吧！
            </div>
        </div>
    `;

    // Clear state
    AppState.chatHistory = [];
    AppState.currentRating = null;

    // Clear storage
    localStorage.removeItem('chatHistory');

    focusInput();
    showSuccess('对话已清空');
}

/**
 * Format message text
 */
function formatMessage(text) {
    // Convert line breaks to HTML
    text = text.replace(/\n/g, '<br>');

    // Convert markdown-style emphasis
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert code blocks
    text = text.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');

    return escapeHtml(text).replace(/&lt;(\/?(strong|em|code|pre|br))&gt;/g, '<$1>');
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Unescape HTML
 */
function unescapeHtml(text) {
    const div = document.createElement('div');
    div.innerHTML = text;
    return div.textContent || div.innerText || '';
}

/**
 * Smooth scroll to bottom
 */
function smoothScrollToBottom() {
    if (!Elements.chatMessages) return;

    setTimeout(() => {
        Elements.chatMessages.scrollTo({
            top: Elements.chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }, CONFIG.TYPING_DELAY);
}

/**
 * Focus input field
 */
function focusInput() {
    if (Elements.queryInput) {
        Elements.queryInput.focus();
    }
}

/**
 * Save chat history to localStorage
 */
function saveChatHistory() {
    try {
        localStorage.setItem('chatHistory', JSON.stringify(AppState.chatHistory));
    } catch (error) {
        console.warn('Failed to save chat history:', error);
    }
}

/**
 * Load chat history from localStorage
 */
function loadChatHistory() {
    try {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            AppState.chatHistory = JSON.parse(saved);

            // Restore messages (limit to last 10 for performance)
            const recentHistory = AppState.chatHistory.slice(-10);
            recentHistory.forEach(item => {
                addMessage(item.query, 'user');
                addMessage(item.response, 'ai', false, item.evaluation);
            });
        }
    } catch (error) {
        console.warn('Failed to load chat history:', error);
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show warning message
 */
function showWarning(message) {
    showToast(message, 'warning');
}

/**
 * Show error message
 */
function showError(message) {
    showToast(message, 'danger');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.transition = 'opacity 0.5s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

// Export functions for global access
window.handleRatingClick = handleRatingClick;
window.handleSubmitFeedback = handleSubmitFeedback;
window.skipFeedback = skipFeedback;