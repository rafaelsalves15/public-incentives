"""
Frontend Web Interface

Interface web simples para o chatbot de incentivos que funciona dentro do container Docker.
Usa HTML/CSS/JavaScript vanilla para máxima compatibilidade.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter(prefix="/web", tags=["web-interface"])

# Montar arquivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
if os.path.exists(static_dir):
    router.mount("/static", StaticFiles(directory=static_dir), name="static")


@router.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """
    Interface principal do chatbot
    """
    html_content = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot de Incentivos Públicos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .chat-header h1 {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 0.9rem;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8fafc;
        }

        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }

        .message.user .message-content {
            background: #4f46e5;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.bot .message-content {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 4px;
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            margin: 0 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.8rem;
        }

        .message.user .message-avatar {
            background: #4f46e5;
            color: white;
            order: 1;
        }

        .message.bot .message-avatar {
            background: #10b981;
            color: white;
        }

        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
        }

        .chat-input-form {
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: #4f46e5;
        }

        .send-button {
            padding: 12px 20px;
            background: #4f46e5;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }

        .send-button:hover {
            background: #4338ca;
        }

        .send-button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            margin-bottom: 15px;
            max-width: 70%;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: #9ca3af;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }

        .data-display {
            margin-top: 10px;
            padding: 10px;
            background: #f3f4f6;
            border-radius: 8px;
            font-size: 0.9rem;
        }

        .data-item {
            margin-bottom: 5px;
            padding: 5px 0;
            border-bottom: 1px solid #e5e7eb;
        }

        .data-item:last-child {
            border-bottom: none;
        }

        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .quick-action {
            padding: 8px 16px;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .quick-action:hover {
            background: #4f46e5;
            color: white;
        }

        .error-message {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .success-message {
            background: #f0fdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        @media (max-width: 768px) {
            .chat-container {
                width: 95%;
                height: 90vh;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 Chatbot de Incentivos</h1>
            <p>Especialista em incentivos públicos portugueses</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    Olá! Sou o assistente especializado em incentivos públicos portugueses. 
                    Como posso ajudá-lo hoje?
                    <div class="quick-actions">
                        <div class="quick-action" onclick="sendQuickMessage('Quais incentivos existem para empresas de software?')">
                            Incentivos para Software
                        </div>
                        <div class="quick-action" onclick="sendQuickMessage('Mostra-me empresas do setor tecnológico')">
                            Empresas Tecnológicas
                        </div>
                        <div class="quick-action" onclick="sendQuickMessage('Quantos incentivos temos na base de dados?')">
                            Estatísticas
                        </div>
                        <div class="quick-action" onclick="sendQuickMessage('Qual o orçamento total disponível?')">
                            Orçamento Total
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="messageInput" 
                    placeholder="Digite sua pergunta sobre incentivos..."
                    autocomplete="off"
                >
                <button type="submit" class="send-button" id="sendButton">
                    Enviar
                </button>
            </form>
        </div>
    </div>

    <script>
        const API_BASE = '/chatbot';
        let isLoading = false;

        // Elementos DOM
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const chatForm = document.getElementById('chatForm');
        const typingIndicator = document.getElementById('typingIndicator');

        // Event listeners
        chatForm.addEventListener('submit', handleSubmit);
        messageInput.addEventListener('keypress', handleKeyPress);

        function handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
            }
        }

        function handleSubmit(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message && !isLoading) {
                sendMessage(message);
                messageInput.value = '';
            }
        }

        function sendQuickMessage(message) {
            if (!isLoading) {
                sendMessage(message);
            }
        }

        async function sendMessage(message) {
            if (isLoading) return;
            
            isLoading = true;
            sendButton.disabled = true;
            
            // Adicionar mensagem do usuário
            addMessage('user', message);
            
            // Mostrar indicador de digitação
            showTypingIndicator();
            
            try {
                const response = await fetch(`${API_BASE}/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        user_id: 'web_user'
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('bot', data.response, data.data, data.intent);
                } else {
                    addMessage('bot', 'Desculpe, ocorreu um erro ao processar sua mensagem.', null, 'error');
                }
                
            } catch (error) {
                console.error('Error:', error);
                addMessage('bot', 'Desculpe, ocorreu um erro de conexão. Tente novamente.', null, 'error');
            } finally {
                hideTypingIndicator();
                isLoading = false;
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        function addMessage(sender, content, data = null, intent = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = sender === 'user' ? '👤' : '🤖';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            // Adicionar dados relacionados se existirem
            if (data && data.length > 0) {
                const dataDiv = document.createElement('div');
                dataDiv.className = 'data-display';
                
                if (intent === 'incentive_query' || intent === 'incentives_list') {
                    dataDiv.innerHTML = '<strong>📋 Incentivos encontrados:</strong>';
                    data.forEach(item => {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'data-item';
                        itemDiv.innerHTML = `
                            <strong>${item.title}</strong><br>
                            ${item.description ? item.description.substring(0, 100) + '...' : ''}<br>
                            ${item.total_budget ? `💰 Orçamento: €${item.total_budget.toLocaleString()}` : ''}
                        `;
                        dataDiv.appendChild(itemDiv);
                    });
                } else if (intent === 'company_query' || intent === 'companies_list') {
                    dataDiv.innerHTML = '<strong>🏢 Empresas encontradas:</strong>';
                    data.forEach(item => {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'data-item';
                        itemDiv.innerHTML = `
                            <strong>${item.company_name}</strong><br>
                            ${item.cae_primary_label || ''}<br>
                            ${item.website ? `🌐 ${item.website}` : ''}
                        `;
                        dataDiv.appendChild(itemDiv);
                    });
                } else if (intent === 'analytics') {
                    dataDiv.innerHTML = `
                        <strong>📊 Estatísticas:</strong><br>
                        📋 Incentivos: ${data.total_incentives}<br>
                        🏢 Empresas: ${data.total_companies}<br>
                        🔗 Correspondências: ${data.total_matches}<br>
                        💰 Orçamento Total: €${data.total_budget.toLocaleString()}
                    `;
                }
                
                contentDiv.appendChild(dataDiv);
            }
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTypingIndicator() {
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTypingIndicator() {
            typingIndicator.style.display = 'none';
        }

        // Focar no input quando a página carrega
        window.addEventListener('load', () => {
            messageInput.focus();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)
