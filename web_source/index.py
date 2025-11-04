html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI助教</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #f8f9fa;
            }
            .chat-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .chat-header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }
            .message {
                margin-bottom: 15px;
                padding: 15px;
                border-radius: 10px;
            }
            .user-message {
                background-color: #d4edda;
                text-align: right;
            }
            .ai-message {
                background-color: #e2e3e5;
            }
            .eval-score {
                font-size: 0.9em;
                color: #6c757d;
            }
            .feedback-section {
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .btn-primary {
                background-color: #667eea;
                border: none;
            }
            .btn-primary:hover {
                background-color: #5a6fd8;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h1>AI助教</h1>
                <p>基于RAG技术的智能教学助理</p>
            </div>
            
            <div id="chat-messages" class="mb-4">
                <!-- Messages will be displayed here -->
                <div class="message ai-message">
                    <strong>AI助手:</strong> 您好！我是您的AI助教，专门回答大数据分析课程相关问题。我可以解释概念、总结课程内容、解答练习题等。请提出您的问题吧！
                </div>
            </div>
            
            <div class="input-group mb-3">
                <input type="text" id="query-input" class="form-control" placeholder="请输入您的问题..." onkeypress="handleKeyPress(event)">
                <button class="btn btn-primary" type="button" onclick="sendQuery()">发送</button>
            </div>
            
            <div class="text-center">
                <button class="btn btn-secondary" onclick="clearChat()">清空对话</button>
            </div>
        </div>

        <script>
            let chatHistory = [];
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendQuery();
                }
            }
            
            async function sendQuery() {
                const queryInput = document.getElementById('query-input');
                const query = queryInput.value.trim();
                
                if (!query) return;
                
                // Add user message to chat
                addMessage(query, 'user');
                queryInput.value = '';
                
                try {
                    // Show loading indicator
                    addMessage('AI助手正在思考中...', 'ai', true);
                    
                    // Send query to backend
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query, mode: 'general' })
                    });
                    
                    const data = await response.json();
                    
                    // Remove loading indicator
                    removeLastMessage();
                    
                    if (response.ok) {
                        // Add AI response to chat
                        addMessage(data.response, 'ai', false, data.evaluation);
                        
                        // Add feedback section
                        addFeedbackSection(data.query, data.response);
                    } else {
                        addMessage('抱歉，出现了错误：' + data.detail, 'ai');
                    }
                } catch (error) {
                    removeLastMessage();
                    addMessage('连接错误：' + error.message, 'ai');
                }
            }
            
            function addMessage(text, sender, isLoading = false, evaluation = null) {
                const chatMessages = document.getElementById('chat-messages');
                
                if (sender === 'user') {
                    chatMessages.innerHTML += `
                        <div class="message user-message">
                            <strong>您:</strong> ${text}
                        </div>
                    `;
                } else {
                    if (isLoading) {
                        chatMessages.innerHTML += `
                            <div id="loading-message" class="message ai-message">
                                <strong>AI助手:</strong> ${text}
                            </div>
                        `;
                    } else {
                        let evalHtml = '';
                        if (evaluation) {
                            evalHtml = `
                                <div class="eval-score">
                                    评估 - 相关性: ${evaluation.relevance_score.toFixed(2)}, 
                                    完整性: ${evaluation.completeness_score.toFixed(2)}, 
                                    整体: ${evaluation.overall_score.toFixed(2)}
                                </div>
                            `;
                        }
                        chatMessages.innerHTML += `
                            <div class="message ai-message">
                                <strong>AI助手:</strong> ${text}
                                ${evalHtml}
                            </div>
                        `;
                    }
                }
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function removeLastMessage() {
                const loadingMessage = document.getElementById('loading-message');
                if (loadingMessage) {
                    loadingMessage.remove();
                }
            }
            
            function addFeedbackSection(query, response) {
                const chatMessages = document.getElementById('chat-messages');
                
                // Create unique IDs to avoid conflicts
                const uniqueId = Date.now().toString();
                
                chatMessages.innerHTML += `
                    <div class="feedback-section" id="feedback-${uniqueId}">
                        <p><strong>对本次回答评分：</strong></p>
                        <div class="rating-buttons">
                            <button class="btn btn-sm btn-outline-primary" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleRatingClick(this, 1)">1星</button>
                            <button class="btn btn-sm btn-outline-primary" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleRatingClick(this, 2)">2星</button>
                            <button class="btn btn-sm btn-outline-primary" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleRatingClick(this, 3)">3星</button>
                            <button class="btn btn-sm btn-outline-primary" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleRatingClick(this, 4)">4星</button>
                            <button class="btn btn-sm btn-outline-primary" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleRatingClick(this, 5)">5星</button>
                        </div>
                        <div class="mt-2">
                            <textarea id="feedback-comment-${uniqueId}" class="form-control" rows="2" placeholder="请输入您的反馈意见..."></textarea>
                            <button class="btn btn-sm btn-success mt-1" data-query="${escapeHtml(query)}" data-response="${escapeHtml(response)}" onclick="handleSubmitComment(this, '${uniqueId}')">提交反馈</button>
                        </div>
                    </div>
                `;
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function escapeHtml(text) {
                return text
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }
            
            function handleRatingClick(button, rating) {
                // 只是更新按钮样式，不提交反馈
                const ratingButtons = button.parentElement.querySelectorAll('button');
                ratingButtons.forEach(btn => btn.classList.remove('btn-primary', 'btn-outline-primary'));
                button.classList.add('btn-primary');
                
                // 将评分存储在按钮的data属性中，等待提交
                button.parentElement.parentElement.setAttribute('data-rating', rating);
            }
            
            function handleSubmitComment(button, uniqueId) {
                const feedbackSection = button.closest('.feedback-section');
                const query = button.getAttribute('data-query');
                const response = button.getAttribute('data-response');
                const comment = document.getElementById('feedback-comment-' + uniqueId).value.trim();
                
                // 获取用户选择的评分（如果有的话）
                const rating = feedbackSection.getAttribute('data-rating');
                
                if (!comment && !rating) {
                    alert('请至少输入反馈意见或选择评分');
                    return;
                }
                
                const feedbackResponse = fetch('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        response: response,
                        rating: rating ? parseInt(rating) : null,
                        comment: comment
                    })
                })
                .then(response => {
                    if (response.ok) {
                        alert('感谢您的反馈！');
                        // 重置界面
                        const ratingButtons = feedbackSection.querySelectorAll('.rating-buttons button');
                        ratingButtons.forEach(btn => {
                            btn.classList.remove('btn-primary');
                            btn.classList.add('btn-outline-primary');
                        });
                        document.getElementById('feedback-comment-' + uniqueId).value = '';
                        feedbackSection.removeAttribute('data-rating');
                    } else {
                        alert('反馈提交失败，请重试。');
                    }
                })
                .catch(error => {
                    console.error('Error submitting feedback:', error);
                    alert('反馈提交失败，请重试。');
                });
            }
            
            async function submitFeedback(query, response, rating, comment = '') {
                const feedbackResponse = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        response: response,
                        rating: rating,
                        comment: comment
                    })
                });
                
                if (feedbackResponse.ok) {
                    alert('感谢您的评分！');
                } else {
                    alert('评分提交失败，请重试。');
                }
            }
            
            async function submitFeedbackWithComment(query, response) {
                const comment = document.getElementById('feedback-comment').value.trim();
                if (!comment) {
                    alert('请输入反馈意见');
                    return;
                }
                
                const feedbackResponse = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        response: response,
                        rating: null,
                        comment: comment
                    })
                });
                
                if (feedbackResponse.ok) {
                    alert('感谢您的反馈！');
                    document.getElementById('feedback-comment').value = '';
                } else {
                    alert('反馈提交失败，请重试。');
                }
            }
            
            function clearChat() {
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML = `
                    <div class="message ai-message">
                        <strong>AI助手:</strong> 您好！我是您的AI教学助手，专门回答大数据分析课程相关问题。我可以解释概念、总结课程内容、解答练习题等。请提出您的问题吧！
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    """