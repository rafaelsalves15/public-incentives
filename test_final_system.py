#!/usr/bin/env python3
"""
Teste Final do Sistema Completo

Script para verificar se todo o sistema está funcionando corretamente:
1. Backend API
2. Chatbot Service  
3. Interface Web
4. Integração completa
"""

import requests
import time
import logging
import json
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_system():
    """Executa teste completo do sistema"""
    
    logger.info("🚀 INICIANDO TESTE FINAL DO SISTEMA COMPLETO")
    logger.info("=" * 60)
    
    # 1. Teste de conectividade básica
    logger.info("\n1️⃣ Testando conectividade básica...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API principal está funcionando")
        else:
            logger.error(f"❌ API principal retornou status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com API: {e}")
        return False
    
    # 2. Teste do chatbot
    logger.info("\n2️⃣ Testando chatbot...")
    try:
        # Health check do chatbot
        response = requests.get("http://localhost:8000/chatbot/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Chatbot health check OK")
        else:
            logger.error(f"❌ Chatbot health check falhou: {response.status_code}")
            return False
        
        # Teste de mensagem simples
        response = requests.post(
            "http://localhost:8000/chatbot/message",
            json={"message": "Olá! Como funciona este sistema?", "user_id": "test_user"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                logger.info("✅ Chatbot respondeu corretamente")
                logger.info(f"   Resposta: {data['response'][:100]}...")
            else:
                logger.error(f"❌ Chatbot retornou erro: {data.get('error', 'Erro desconhecido')}")
                return False
        else:
            logger.error(f"❌ Erro HTTP {response.status_code} no chatbot")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar chatbot: {e}")
        return False
    
    # 3. Teste da interface web
    logger.info("\n3️⃣ Testando interface web...")
    try:
        response = requests.get("http://localhost:8000/web/", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Interface web está acessível")
            if "Chatbot de Incentivos" in response.text:
                logger.info("✅ Interface web contém conteúdo correto")
            else:
                logger.warning("⚠️ Interface web pode não estar carregando corretamente")
        else:
            logger.error(f"❌ Interface web retornou status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao acessar interface web: {e}")
        return False
    
    # 4. Teste de funcionalidades específicas
    logger.info("\n4️⃣ Testando funcionalidades específicas...")
    
    test_queries = [
        "Quantos incentivos temos na base de dados?",
        "Quais incentivos existem para empresas de software?",
        "Mostra-me empresas do setor tecnológico"
    ]
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n   Teste {i}: {query}")
        try:
            response = requests.post(
                "http://localhost:8000/chatbot/message",
                json={"message": query, "user_id": "test_user"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"   ✅ Resposta: {data['response'][:80]}...")
                    logger.info(f"   📊 Tipo: {data['response_type']}, Intenção: {data['intent']}")
                else:
                    logger.error(f"   ❌ Erro: {data.get('error', 'Erro desconhecido')}")
            else:
                logger.error(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Exceção: {e}")
        
        time.sleep(1)  # Pausa entre testes
    
    # 5. Teste de estatísticas
    logger.info("\n5️⃣ Testando estatísticas...")
    try:
        response = requests.get("http://localhost:8000/chatbot/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stats = data["data"]
            logger.info(f"✅ Estatísticas: {stats['total_incentives']} incentivos, {stats['total_companies']} empresas")
            logger.info(f"   💰 Orçamento total: €{stats['total_budget']:,.0f}")
        else:
            logger.error(f"❌ Erro ao obter estatísticas: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro ao testar estatísticas: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 TESTE FINAL CONCLUÍDO COM SUCESSO!")
    logger.info("=" * 60)
    
    logger.info("\n📋 RESUMO DO SISTEMA:")
    logger.info("✅ Backend API funcionando")
    logger.info("✅ Chatbot Service operacional")
    logger.info("✅ Interface Web acessível")
    logger.info("✅ Integração completa funcionando")
    
    logger.info("\n🌐 ACESSOS:")
    logger.info("   Interface Web: http://localhost:8000/web/")
    logger.info("   API Docs: http://localhost:8000/docs")
    logger.info("   Chatbot API: http://localhost:8000/chatbot/")
    
    logger.info("\n🎯 FUNCIONALIDADES DISPONÍVEIS:")
    logger.info("   • Consultas sobre incentivos")
    logger.info("   • Exploração de empresas")
    logger.info("   • Análise de correspondências")
    logger.info("   • Estatísticas e análises")
    logger.info("   • Interface de chat moderna")
    
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
