"""
Chatbot API Endpoints

Endpoints para o sistema de chatbot que permite aos utilizadores:
- Enviar mensagens e receber respostas
- Consultar histórico de conversa
- Fazer buscas rápidas
- Obter estatísticas do chatbot
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.chatbot_service import ChatbotService
from app.services.ai_processor import AIProcessor
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging

router = APIRouter(prefix="/chatbot", tags=["chatbot"])
logger = logging.getLogger(__name__)


# Pydantic models para requests/responses
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    success: bool
    response: str
    response_type: str
    data: List[Dict[str, Any]]
    intent: str
    entities: Dict[str, Any]
    timestamp: str


class QuickSearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"


class ChatHistoryResponse(BaseModel):
    messages: List[Dict[str, Any]]
    total_count: int


# Dependency para obter sessão da BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency para obter chatbot service
def get_chatbot_service(db: Session = Depends(get_db)) -> ChatbotService:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    ai_processor = AIProcessor(api_key, db)
    return ChatbotService(ai_processor, db)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Envia mensagem para o chatbot e recebe resposta
    
    Args:
        message: Mensagem do utilizador
        chatbot: Serviço do chatbot
        
    Returns:
        Resposta do chatbot com dados relacionados
    """
    try:
        logger.info(f"Received message from user {message.user_id}: {message.message[:100]}...")
        
        # Processar mensagem
        response = await chatbot.process_message(message.message, message.user_id)
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str,
    limit: int = 20,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Obtém histórico de conversa do utilizador
    
    Args:
        user_id: ID do utilizador
        limit: Número máximo de mensagens a retornar
        
    Returns:
        Histórico de conversa
    """
    try:
        messages = chatbot.get_conversation_history(user_id, limit)
        
        return ChatHistoryResponse(
            messages=messages,
            total_count=len(messages)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=ChatResponse)
async def quick_search(
    search_request: QuickSearchRequest,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Busca rápida sem contexto de conversa
    
    Args:
        search_request: Query de busca
        
    Returns:
        Resultados da busca
    """
    try:
        logger.info(f"Quick search from user {search_request.user_id}: {search_request.query[:100]}...")
        
        # Processar como mensagem normal mas sem contexto
        response = await chatbot.process_message(search_request.query, search_request.user_id)
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in quick search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Limpa histórico de conversa do utilizador
    
    Args:
        user_id: ID do utilizador
        
    Returns:
        Confirmação de limpeza
    """
    try:
        chatbot.clear_context(user_id)
        
        return {
            "success": True,
            "message": f"Chat history cleared for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_chatbot_stats(db: Session = Depends(get_db)):
    """
    Obtém estatísticas do chatbot
    
    Returns:
        Estatísticas de uso e performance
    """
    try:
        from app.db.models import Incentive, Company, IncentiveCompanyMatch
        from sqlalchemy import func
        
        # Estatísticas gerais
        total_incentives = db.query(func.count(Incentive.incentive_id)).scalar()
        total_companies = db.query(func.count(Company.company_id)).scalar()
        total_matches = db.query(func.count(IncentiveCompanyMatch.match_id)).scalar()
        
        # Orçamento total
        total_budget_result = db.query(func.sum(Incentive.total_budget)).scalar()
        total_budget = float(total_budget_result) if total_budget_result else 0
        
        # Estatísticas de custos (se disponível)
        try:
            from app.services.cost_tracker import CostTracker
            cost_tracker = CostTracker(db)
            cost_stats = cost_tracker.get_total_stats()
        except:
            cost_stats = None
        
        return {
            "success": True,
            "data": {
                "total_incentives": total_incentives,
                "total_companies": total_companies,
                "total_matches": total_matches,
                "total_budget": total_budget,
                "avg_budget_per_incentive": total_budget / total_incentives if total_incentives > 0 else 0,
                "cost_stats": cost_stats
            },
            "message": "Chatbot statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help")
async def get_chatbot_help():
    """
    Retorna informações de ajuda sobre como usar o chatbot
    
    Returns:
        Guia de uso do chatbot
    """
    return {
        "success": True,
        "help": {
            "description": "Chatbot especializado em incentivos públicos portugueses",
            "capabilities": [
                "Consultar informações sobre incentivos",
                "Explorar dados sobre empresas",
                "Analisar correspondências entre incentivos e empresas",
                "Obter estatísticas e análises"
            ],
            "example_queries": [
                "Quais incentivos existem para empresas de software?",
                "Mostra-me empresas do setor tecnológico",
                "Que empresas são adequadas para o incentivo X?",
                "Quantos incentivos temos na base de dados?",
                "Qual o orçamento total disponível?"
            ],
            "tips": [
                "Pode mencionar setores específicos (tecnologia, agricultura, etc.)",
                "Pode pedir informações por região (Lisboa, Porto, etc.)",
                "Pode usar IDs específicos de incentivos ou empresas",
                "Pode fazer perguntas sobre orçamentos e datas"
            ]
        }
    }


@router.get("/health")
async def chatbot_health():
    """
    Verifica saúde do serviço de chatbot
    
    Returns:
        Status do serviço
    """
    try:
        # Verificar se API key está configurada
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "status": "unhealthy",
                "message": "OpenAI API key not configured",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
        # Verificar conexão à BD
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except:
            db_status = "unhealthy"
        finally:
            db.close()
        
        overall_status = "healthy" if db_status == "healthy" else "unhealthy"
        
        return {
            "status": overall_status,
            "components": {
                "database": db_status,
                "openai_api": "configured" if api_key else "not_configured"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
