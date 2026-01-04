let models = [];
let selectedModels = new Set();

// 配置 marked.js
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
});

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        models = await response.json();
        renderModelSelector();
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

function renderModelSelector() {
    const selector = document.getElementById('model-selector');
    selector.innerHTML = models.map(model => `
        <label class="model-option">
            <input type="checkbox" value="${model.id}" data-id="${model.id}">
            <div class="model-label">
                <span class="radio-dot"></span>
                <span>${model.display_name}</span>
            </div>
        </label>
    `).join('');

    selector.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const id = checkbox.dataset.id;
            if (checkbox.checked) {
                if (selectedModels.size < 5) {
                    selectedModels.add(id);
                } else {
                    checkbox.checked = false;
                }
            } else {
                selectedModels.delete(id);
            }
        });
    });
}

function createResponseCards() {
    const container = document.getElementById('responses');
    container.innerHTML = '';

    const modelMap = {};
    models.forEach(m => modelMap[m.id] = m.display_name);

    selectedModels.forEach(modelId => {
        const card = document.createElement('div');
        card.className = 'response-card';
        card.innerHTML = `
            <div class="response-header">
                <span class="model-name">${modelMap[modelId] || modelId}</span>
                <span class="status" id="status-${modelId}">生成中</span>
            </div>
            <div class="response-content markdown-body loading" id="response-${modelId}">等待响应...</div>
        `;
        container.appendChild(card);
    });
}

function renderMarkdown(element, content) {
    element.innerHTML = marked.parse(content);
}

async function sendMessage() {
    const systemPrompt = document.getElementById('system-prompt').value;
    const userPrompt = document.getElementById('user-prompt').value;

    if (!userPrompt.trim()) {
        alert('请输入用户提示词');
        return;
    }

    if (selectedModels.size === 0) {
        alert('请选择至少一个模型');
        return;
    }

    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;

    createResponseCards();

    const responses = {};
    selectedModels.forEach(id => responses[id] = '');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_prompt: systemPrompt,
                user_prompt: userPrompt,
                models: Array.from(selectedModels)
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    if (!dataStr) continue;

                    try {
                        const data = JSON.parse(dataStr);
                        const contentEl = document.getElementById(`response-${data.model}`);
                        const statusEl = document.getElementById(`status-${data.model}`);

                        if (contentEl) {
                            contentEl.classList.remove('loading');
                            if (data.error) {
                                contentEl.classList.add('error');
                                contentEl.textContent = `错误: ${data.error}`;
                                if (statusEl) {
                                    statusEl.textContent = '失败';
                                    statusEl.classList.add('error');
                                }
                            } else if (data.content) {
                                responses[data.model] += data.content;
                                renderMarkdown(contentEl, responses[data.model]);
                            }
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                } else if (line.startsWith('event: done')) {
                    // Mark all as done
                    selectedModels.forEach(modelId => {
                        const statusEl = document.getElementById(`status-${modelId}`);
                        if (statusEl && !statusEl.classList.contains('error')) {
                            statusEl.textContent = '完成';
                            statusEl.classList.add('done');
                        }
                    });
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        sendBtn.disabled = false;
    }
}

document.getElementById('send-btn').addEventListener('click', sendMessage);

// Allow Ctrl+Enter to send
document.getElementById('user-prompt').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        sendMessage();
    }
});

loadModels();
