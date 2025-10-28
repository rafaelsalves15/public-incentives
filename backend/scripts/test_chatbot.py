#!/usr/bin/env python3
"""
Teste do Chatbot - Verificação Rápida

Script para testar o chatbot de incentivos de forma rápida.
"""

import asyncio
import logging
import os
from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.chatbot_service import ChatbotService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chatbot():
    """Testa o chatbot com algumas perguntas básicas"""
    
    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY não encontrada no arquivo .env")
        return False
    
    logger.info("🚀 Iniciando teste do chatbot...")
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key, db)
    chatbot = ChatbotService(ai_processor, db)
    
    # Perguntas de teste
    test_questions = [
        "Olá! Como funciona este sistema?",
        "Quantos incentivos temos na base de dados?",
        "Quais incentivos existem para empresas de software?",
        "Mostra-me empresas do setor tecnológico",
        "Qual o orçamento total disponível?"
    ]
    
    logger.info(f"📝 Testando {len(test_questions)} perguntas...")
    
    for i, question in enumerate(test_questions, 1):
        logger.info(f"\n--- Pergunta {i}: {question} ---")
        
        try:
            response = await chatbot.process_message(question, "test_user")
            
            if response["success"]:
                logger.info(f"✅ Resposta: {response['response'][:100]}...")
                logger.info(f"📊 Tipo: {response['response_type']}")
                logger.info(f"🎯 Intenção: {response['intent']}")
                
                if response["data"]:
                    logger.info(f"📋 Dados: {len(response['data'])} itens encontrados")
            else:
                logger.error(f"❌ Erro: {response.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            logger.error(f"❌ Exceção: {e}")
    
    # Estatísticas finais
    logger.info("\n📊 Estatísticas do teste:")
    logger.info(f"💰 Cache hits: {ai_processor._cache_hits}")
    logger.info(f"💸 Cache misses: {ai_processor._cache_misses}")
    
    # Fechar conexão
    db.close()
    
    logger.info("✅ Teste do chatbot concluído!")
    return True

if __name__ == "__main__":
    asyncio.run(test_chatbot())



