#!/usr/bin/env python3
"""
Teste Completo do Sistema - Chatbot + Interface Web

Script para testar todo o sistema incluindo:
1. Backend API
2. Chatbot Service
3. Interface Web
"""

import requests
import time
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_health():
    """Testa se a API está funcionando"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API está funcionando")
            return True
        else:
            logger.error(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com API: {e}")
        return False

def test_chatbot_endpoints():
    """Testa os endpoints do chatbot"""
    base_url = "http://localhost:8000/chatbot"
    
    # Teste de saúde do chatbot
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Chatbot health check OK")
        else:
            logger.error(f"❌ Chatbot health check falhou: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro no chatbot health check: {e}")
        return False
    
    # Teste de ajuda
    try:
        response = requests.get(f"{base_url}/help", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Endpoint de ajuda OK")
        else:
            logger.error(f"❌ Endpoint de ajuda falhou: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro no endpoint de ajuda: {e}")
    
    # Teste de estatísticas
    try:
        response = requests.get(f"{base_url}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Estatísticas: {data['data']['total_incentives']} incentivos, {data['data']['total_companies']} empresas")
        else:
            logger.error(f"❌ Endpoint de estatísticas falhou: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro no endpoint de estatísticas: {e}")
    
    return True

def test_chatbot_messages():
    """Testa envio de mensagens para o chatbot"""
    base_url = "http://localhost:8000/chatbot"
    
    test_messages = [
        "Olá! Como funciona este sistema?",
        "Quantos incentivos temos na base de dados?",
        "Quais incentivos existem para empresas de software?"
    ]
    
    logger.info(f"📝 Testando {len(test_messages)} mensagens...")
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n--- Teste {i}: {message} ---")
        
        try:
            response = requests.post(
                f"{base_url}/message",
                json={"message": message, "user_id": "test_user"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"✅ Resposta: {data['response'][:100]}...")
                    logger.info(f"📊 Tipo: {data['response_type']}")
                    logger.info(f"🎯 Intenção: {data['intent']}")
                    
                    if data["data"]:
                        logger.info(f"📋 Dados: {len(data['data'])} itens encontrados")
                else:
                    logger.error(f"❌ Erro na resposta: {data.get('error', 'Erro desconhecido')}")
            else:
                logger.error(f"❌ Status HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Exceção: {e}")
        
        # Pausa entre mensagens
        time.sleep(1)

def test_web_interface():
    """Testa se a interface web está acessível"""
    try:
        response = requests.get("http://localhost:8000/web/", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Interface web está acessível")
            return True
        else:
            logger.error(f"❌ Interface web retornou status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao acessar interface web: {e}")
        return False

def main():
    """Executa todos os testes"""
    logger.info("🚀 Iniciando teste completo do sistema...")
    
    # Aguardar API estar pronta
    logger.info("⏳ Aguardando API estar pronta...")
    for i in range(30):  # 30 tentativas, 5 segundos cada
        if test_api_health():
            break
        logger.info(f"Tentativa {i+1}/30 - Aguardando...")
        time.sleep(5)
    else:
        logger.error("❌ API não ficou pronta em 150 segundos")
        return False
    
    # Testes
    logger.info("\n📋 Executando testes...")
    
    # 1. Teste de endpoints do chatbot
    logger.info("\n1️⃣ Testando endpoints do chatbot...")
    test_chatbot_endpoints()
    
    # 2. Teste de mensagens
    logger.info("\n2️⃣ Testando mensagens do chatbot...")
    test_chatbot_messages()
    
    # 3. Teste da interface web
    logger.info("\n3️⃣ Testando interface web...")
    test_web_interface()
    
    logger.info("\n✅ Teste completo concluído!")
    logger.info("\n🌐 Acesse a interface web em: http://localhost:8000/web/")
    logger.info("📚 Documentação da API em: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
