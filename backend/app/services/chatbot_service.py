"""
Chatbot Service - Sistema de Chat Inteligente para Incentivos

Este serviço implementa um chatbot que permite aos utilizadores:
- Consultar informações sobre incentivos
- Explorar dados sobre empresas  
- Analisar correspondências entre incentivos e empresas
- Obter respostas contextualizadas usando LLM + RAG
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.db.models import Incentive, Company, IncentiveCompanyMatch, IncentiveMetadata
from app.services.ai_processor import AIProcessor
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatbotContext:
    """Gestor de contexto da conversa"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_entities = {}  # Entidades mencionadas
        self.user_preferences = {}  # Preferências do utilizador
        self.session_data = {}
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Adiciona mensagem ao histórico"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        
    def get_recent_context(self, limit: int = 5) -> List[Dict]:
        """Retorna contexto recente da conversa"""
        return self.conversation_history[-limit:] if self.conversation_history else []
        
    def update_entities(self, entities: Dict[str, Any]):
        """Atualiza entidades mencionadas"""
        self.current_entities.update(entities)


class QueryRouter:
    """Router para diferentes tipos de consultas"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analisa a intenção da mensagem"""
        message_lower = message.lower()
        
        # Verificar primeiro se é uma pergunta de contagem/estatísticas
        if re.search(r"\b(quantos|quantas|total|contar|número|estatística|resumo|orçamento.*total|quantidade)\b", message_lower):
            # Se menciona empresas/incentivos também, dá prioridade a analytics
            if re.search(r"\b(empresa|incentivo|empresas|incentivos)\b", message_lower):
                return {
                    "primary_intent": "analytics_query",
                    "intent_scores": {"analytics_query": 3},
                    "confidence": 1.0
                }
        
        # Padrões para diferentes tipos de consultas
        patterns = {
            "incentive_query": [
                r"incentivo", r"subsídio", r"apoio", r"financiamento",
                r"que incentivos", r"mostra.*incentivo", r"lista.*incentivo"
            ],
            "company_query": [
                r"empresa", r"companhia", r"que empresas", r"mostra.*empresa",
                r"lista.*empresa", r"empresas.*setor"
            ],
            "match_query": [
                r"match", r"correspondência", r"adequada", r"adequado",
                r"empresa.*incentivo", r"incentivo.*empresa", r"recomenda",
                r"melhores.*empresas.*incentivo", r"empresas.*para.*incentivo",
                r"quais.*empresas.*para", r"empresas.*adequadas.*incentivo"
            ],
            "analytics_query": [
                r"quantos", r"total", r"estatística", r"resumo",
                r"orçamento.*total", r"quantidade"
            ],
            "specific_query": [
                r"incentivo.*[a-z0-9-]+", r"empresa.*[a-z0-9-]+",
                r"id.*[a-z0-9-]+", r"uuid.*[a-z0-9-]+"
            ]
        }
        
        intent_scores = {}
        for intent, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                if re.search(pattern, message_lower):
                    score += 1
            intent_scores[intent] = score
            
        # Determinar intenção principal
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "general_query"
        
        return {
            "primary_intent": primary_intent,
            "intent_scores": intent_scores,
            "confidence": max(intent_scores.values()) / len(pattern_list) if intent_scores else 0
        }
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extrai entidades da mensagem"""
        entities = {}
        
        # Extrair IDs/UUIDs
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuids = re.findall(uuid_pattern, message, re.IGNORECASE)
        if uuids:
            entities["uuids"] = uuids
            
        # Extrair números (orçamentos, quantidades)
        number_pattern = r'\b\d+(?:\.\d+)?(?:k|m|mil|milhão)?\b'
        numbers = re.findall(number_pattern, message.lower())
        if numbers:
            entities["numbers"] = numbers
            
        # Extrair setores/atividades
        sectors = ["tecnologia", "software", "agricultura", "turismo", "indústria", "serviços"]
        found_sectors = [s for s in sectors if s in message.lower()]
        if found_sectors:
            entities["sectors"] = found_sectors
            
        # Extrair regiões
        regions = ["lisboa", "porto", "coimbra", "aveiro", "braga", "faro"]
        found_regions = [r for r in regions if r in message.lower()]
        if found_regions:
            entities["regions"] = found_regions
            
        return entities


class ChatbotService:
    """Serviço principal do chatbot"""
    
    def __init__(self, ai_processor: AIProcessor, db_session: Session):
        self.ai_processor = ai_processor
        self.db = db_session
        self.context_manager = ChatbotContext()
        self.query_router = QueryRouter(db_session)
        
    async def process_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Processa mensagem do utilizador e retorna resposta
        
        Args:
            message: Mensagem do utilizador
            user_id: ID do utilizador (para contexto)
            
        Returns:
            Dict com resposta, tipo de resposta e dados relacionados
        """
        try:
            logger.info(f"Processing message: {message[:100]}...")
            
            # 1. Analisar intenção e extrair entidades
            intent_analysis = self.query_router.analyze_intent(message)
            entities = self.query_router.extract_entities(message)
            
            # 2. Atualizar contexto
            self.context_manager.add_message("user", message, {
                "intent": intent_analysis,
                "entities": entities
            })
            
            # 3. Processar baseado na intenção
            response_data = await self._handle_intent(intent_analysis, entities, message)
            
            # 4. Gerar resposta contextualizada com LLM
            final_response = await self._generate_contextual_response(
                message, response_data, intent_analysis
            )
            
            # 5. Adicionar resposta ao contexto
            self.context_manager.add_message("assistant", final_response["text"], {
                "intent": intent_analysis["primary_intent"],
                "data": response_data
            })
            
            # Converter data para lista se necessário (analytics retorna dict)
            data = response_data.get("data", [])
            if isinstance(data, dict):
                data = [data]  # Converter dict para lista com um elemento
            
            return {
                "success": True,
                "response": final_response["text"],
                "response_type": response_data.get("type", "text"),
                "data": data,
                "intent": intent_analysis["primary_intent"],
                "entities": entities,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "response": "Desculpe, ocorreu um erro ao processar a sua mensagem. Pode reformular a pergunta?",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_intent(self, intent_analysis: Dict, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consulta baseado na intenção"""
        intent = intent_analysis["primary_intent"]
        
        if intent == "incentive_query":
            return await self._handle_incentive_query(entities, message)
        elif intent == "company_query":
            return await self._handle_company_query(entities, message)
        elif intent == "match_query":
            return await self._handle_match_query(entities, message)
        elif intent == "analytics_query":
            return await self._handle_analytics_query(entities, message)
        elif intent == "specific_query":
            return await self._handle_specific_query(entities, message)
        else:
            return await self._handle_general_query(message)
    
    async def _handle_incentive_query(self, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consultas sobre incentivos"""
        query = self.db.query(Incentive)
        
        # Aplicar filtros baseados em entidades
        if "sectors" in entities:
            # Buscar por setores na descrição ou ai_description
            sector_filters = []
            for sector in entities["sectors"]:
                sector_filters.append(
                    or_(
                        Incentive.description.ilike(f"%{sector}%"),
                        Incentive.ai_description.op('->>')('sectors').ilike(f"%{sector}%")
                    )
                )
            query = query.filter(or_(*sector_filters))
        
        if "numbers" in entities:
            # Filtrar por orçamento se mencionado
            for number in entities["numbers"]:
                try:
                    budget = float(number.replace("k", "000").replace("m", "000000"))
                    query = query.filter(Incentive.total_budget >= budget)
                except:
                    pass
        
        # Limitar resultados
        incentives = query.limit(10).all()
        
        return {
            "type": "incentives_list",
            "data": [
                {
                    "incentive_id": str(inc.incentive_id),
                    "title": inc.title,
                    "description": inc.description,
                    "total_budget": float(inc.total_budget) if inc.total_budget else None,
                    "start_date": inc.start_date.isoformat() if inc.start_date else None,
                    "end_date": inc.end_date.isoformat() if inc.end_date else None
                }
                for inc in incentives
            ],
            "count": len(incentives)
        }
    
    async def _handle_company_query(self, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consultas sobre empresas"""
        query = self.db.query(Company)
        
        # Aplicar filtros
        if "sectors" in entities:
            sector_filters = []
            for sector in entities["sectors"]:
                sector_filters.append(
                    or_(
                        Company.cae_primary_label.ilike(f"%{sector}%"),
                        Company.trade_description_native.ilike(f"%{sector}%")
                    )
                )
            query = query.filter(or_(*sector_filters))
        
        companies = query.limit(10).all()
        
        return {
            "type": "companies_list",
            "data": [
                {
                    "company_id": str(comp.company_id),
                    "company_name": comp.company_name,
                    "cae_primary_label": comp.cae_primary_label,
                    "trade_description_native": comp.trade_description_native,
                    "website": comp.website
                }
                for comp in companies
            ],
            "count": len(companies)
        }
    
    async def _handle_match_query(self, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consultas sobre correspondências"""
        # Tentar encontrar incentivo por título na mensagem
        logger.info(f"Processing match query: {message}")
        
        # Buscar matches usando título do incentivo
        # Se tem UUIDs específicos, buscar matches específicos
        if "uuids" in entities:
            logger.info(f"Busca de matches para UUID: {entities['uuids']}")
            uuid = entities["uuids"][0]
            
            # Verificar se é incentivo ou empresa
            incentive = self.db.query(Incentive).filter(Incentive.incentive_id == uuid).first()
            if incentive:
                matches = self.db.query(IncentiveCompanyMatch).filter(
                    IncentiveCompanyMatch.incentive_id == uuid
                ).order_by(IncentiveCompanyMatch.ranking_position).limit(5).all()
                
                return {
                    "type": "incentive_matches",
                    "data": [
                        {
                            "company_name": match.company.company_name,
                            "match_score": float(match.match_score),
                            "reasons": match.match_reasons or [],
                            "ranking_position": match.ranking_position
                        }
                        for match in matches
                    ],
                    "incentive_title": incentive.title
                }
            
            company = self.db.query(Company).filter(Company.company_id == uuid).first()
            if company:
                matches = self.db.query(IncentiveCompanyMatch).filter(
                    IncentiveCompanyMatch.company_id == uuid
                ).order_by(IncentiveCompanyMatch.match_score.desc()).limit(5).all()
                
                return {
                    "type": "company_matches",
                    "data": [
                        {
                            "incentive_title": match.incentive.title,
                            "match_score": float(match.match_score),
                            "reasons": match.match_reasons or [],
                            "total_budget": float(match.incentive.total_budget) if match.incentive.total_budget else None
                        }
                        for match in matches
                    ],
                    "company_name": company.company_name
                }
        
        # ✅ NOVO: Buscar incentivo mencionado na mensagem usando busca textual inteligente
        message_lower = message.lower()
        
        # 1. Tentar buscar por palavras-chave específicas conhecidas
        keywords = []
        if "infraestrutura portuária" in message_lower or "portuár" in message_lower:
            keywords = ["infraestrutura", "portuária", "porto"]
        elif "cuidados de saúde" in message_lower or ("saúde" in message_lower and "empresas" in message_lower):
            keywords = ["saúde", "cuidados"]
        elif "educação" in message_lower or "ensino" in message_lower:
            keywords = ["educação", "ensino"]
        
        # 2. Se não tem keywords específicas, tentar buscar por termos mencionados na mensagem
        if not keywords:
            # Extrair palavras significativas da mensagem (remover stop words)
            stop_words = ["o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos", "em", 
                         "para", "com", "sem", "por", "sobre", "até", "entre", "qual", "quais", "este", "esta", 
                         "isso", "que", "para", "melhores", "matches", "empresas", "empresa", "incentivo", 
                         "mais", "melhor", "top", "para", "para", "este", "que", "são", "está", "estão"]
            
            message_words = message_lower.split()
            message_words = [w for w in message_words if w not in stop_words and len(w) > 3]
            
            # Pegar primeiras palavras relevantes
            if message_words:
                keywords = message_words[:3]  # Top 3 palavras relevantes
        
        # 3. Buscar incentivo na base de dados
        if keywords:
            logger.info(f"🔍 Procurando incentivo por keywords: {keywords}")
            
            query = self.db.query(Incentive)
            
            # Criar filtros OR para as keywords
            filters = []
            for keyword in keywords:
                filters.append(Incentive.title.ilike(f"%{keyword}%"))
                filters.append(Incentive.description.ilike(f"%{keyword}%"))
                # Também buscar em ai_description se existir
                if hasattr(Incentive, 'ai_description'):
                    filters.append(Incentive.ai_description.op('->>')('summary').ilike(f"%{keyword}%"))
            
            query = query.filter(or_(*filters))
            
            incentive = query.first()  # Pegar primeiro match
            
            if incentive:
                logger.info(f"✅ Incentivo encontrado: {incentive.title}")
                matches = self.db.query(IncentiveCompanyMatch).filter(
                    IncentiveCompanyMatch.incentive_id == incentive.incentive_id
                ).order_by(IncentiveCompanyMatch.ranking_position).limit(5).all()
                
                if matches:
                    return {
                        "type": "incentive_matches",
                        "data": [
                            {
                                "company_name": match.company.company_name,
                                "match_score": float(match.match_score),
                                "reasons": match.match_reasons or [],
                                "ranking_position": match.ranking_position
                            }
                            for match in matches
                        ],
                        "incentive_title": incentive.title
                    }
                else:
                    logger.warning(f"⚠️ Incentivo encontrado mas sem matches: {incentive.title}")
                    return {
                        "type": "no_matches",
                        "data": {},
                        "message": f"O incentivo '{incentive.title}' foi encontrado mas ainda não tem matches calculados na base de dados."
                    }
        
        # 4. Se ainda não encontrou, listar alguns incentivos disponíveis para o utilizador escolher
        logger.info("⚠️ Nenhum incentivo específico encontrado, retornando incentivos recentes")
        # Ordenar por data de publicação ou data de início (quando disponível)
        recent_incentives = self.db.query(Incentive).order_by(
            Incentive.publication_date.desc(),
            Incentive.start_date.desc()
        ).limit(5).all()
        
        return {
            "type": "incentives_list",
            "data": [
                {
                    "incentive_id": str(inc.incentive_id),
                    "title": inc.title,
                    "description": inc.description[:200] + "..." if inc.description and len(inc.description) > 200 else inc.description
                }
                for inc in recent_incentives
            ],
            "message": f"Encontrei {len(recent_incentives)} incentivos recentes. Pode ser mais específico sobre qual incentivo procura?"
        }
    
    async def _handle_analytics_query(self, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consultas analíticas"""
        # Estatísticas gerais
        total_incentives = self.db.query(func.count(Incentive.incentive_id)).scalar()
        total_companies = self.db.query(func.count(Company.company_id)).scalar()
        total_matches = self.db.query(func.count(IncentiveCompanyMatch.match_id)).scalar()
        
        # Orçamento total
        total_budget_result = self.db.query(func.sum(Incentive.total_budget)).scalar()
        total_budget = float(total_budget_result) if total_budget_result else 0
        
        return {
            "type": "analytics",
            "data": {
                "total_incentives": total_incentives,
                "total_companies": total_companies,
                "total_matches": total_matches,
                "total_budget": total_budget,
                "avg_budget_per_incentive": total_budget / total_incentives if total_incentives > 0 else 0
            }
        }
    
    async def _handle_specific_query(self, entities: Dict, message: str) -> Dict[str, Any]:
        """Processa consultas específicas por ID"""
        if "uuids" not in entities:
            return {"type": "error", "message": "ID não encontrado na mensagem"}
        
        uuid = entities["uuids"][0]
        
        # Buscar incentivo
        incentive = self.db.query(Incentive).filter(Incentive.incentive_id == uuid).first()
        if incentive:
            return {
                "type": "incentive_detail",
                "data": {
                    "incentive_id": str(incentive.incentive_id),
                    "title": incentive.title,
                    "description": incentive.description,
                    "ai_description": incentive.ai_description,
                    "total_budget": float(incentive.total_budget) if incentive.total_budget else None,
                    "start_date": incentive.start_date.isoformat() if incentive.start_date else None,
                    "end_date": incentive.end_date.isoformat() if incentive.end_date else None,
                    "source_link": incentive.source_link
                }
            }
        
        # Buscar empresa
        company = self.db.query(Company).filter(Company.company_id == uuid).first()
        if company:
            return {
                "type": "company_detail",
                "data": {
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                    "cae_primary_label": company.cae_primary_label,
                    "trade_description_native": company.trade_description_native,
                    "website": company.website,
                    "company_size": company.company_size,
                    "region": company.region
                }
            }
        
        return {"type": "error", "message": "ID não encontrado"}
    
    async def _handle_general_query(self, message: str) -> Dict[str, Any]:
        """Processa consultas gerais"""
        return {
            "type": "general",
            "message": "Como posso ajudá-lo? Pode perguntar sobre incentivos, empresas ou correspondências entre eles."
        }
    
    async def _generate_contextual_response(self, message: str, response_data: Dict, intent_analysis: Dict) -> Dict[str, str]:
        """Gera resposta contextualizada usando LLM"""
        try:
            # Construir contexto para o LLM
            context_parts = []
            
            # Adicionar dados relevantes
            if response_data.get("type") == "incentives_list":
                context_parts.append(f"Dados encontrados: {len(response_data['data'])} incentivos")
                for inc in response_data["data"][:3]:  # Primeiros 3
                    context_parts.append(f"- {inc['title']}: {inc['description'][:100]}...")
            
            elif response_data.get("type") == "companies_list":
                context_parts.append(f"Dados encontrados: {len(response_data['data'])} empresas")
                for comp in response_data["data"][:3]:  # Primeiros 3
                    context_parts.append(f"- {comp['company_name']}: {comp['cae_primary_label']}")
            
            elif response_data.get("type") == "analytics":
                data = response_data["data"]
                context_parts.append(f"Estatísticas: {data['total_incentives']} incentivos, {data['total_companies']} empresas, orçamento total: €{data['total_budget']:,.0f}")
            
            elif response_data.get("type") == "incentive_matches":
                # ✅ NOVO: Tratar matches de incentivos
                data = response_data["data"]
                incentive_title = response_data.get("incentive_title", "incentivo")
                context_parts.append(f"Melhores empresas para o incentivo: {incentive_title}")
                for i, match in enumerate(data[:5], 1):
                    company_name = match.get('company_name', 'N/A')
                    score = match.get('match_score', 0)
                    reasons = match.get('reasons', [])
                    context_parts.append(f"{i}. {company_name} (Score: {score:.2f})")
                    if reasons:
                        context_parts.append(f"   Razões: {', '.join(reasons[:2])}")
            
            elif response_data.get("type") == "company_matches":
                # Tratar matches de empresas
                data = response_data["data"]
                company_name = response_data.get("company_name", "empresa")
                context_parts.append(f"Incentivos adequados para: {company_name}")
                for i, match in enumerate(data[:5], 1):
                    incentive_title = match.get('incentive_title', 'N/A')
                    score = match.get('match_score', 0)
                    context_parts.append(f"{i}. {incentive_title} (Score: {score:.2f})")
            
            elif response_data.get("type") == "no_matches":
                # Tratar caso em que incentivo foi encontrado mas não tem matches
                message = response_data.get("message", "Incentivo encontrado mas sem matches.")
                context_parts.append(message)
            
            elif response_data.get("type") == "incentives_list":
                # Tratar lista de incentivos
                data = response_data["data"]
                context_parts.append(f"Incentivos disponíveis:")
                for i, inc in enumerate(data[:5], 1):
                    title = inc.get('title', 'N/A')
                    description = inc.get('description', 'Sem descrição')[:100]
                    context_parts.append(f"{i}. {title}: {description}...")
            
            # Construir prompt
            context_text = "\n".join(context_parts) if context_parts else "Nenhum dado específico encontrado."
            
            prompt = f"""
Você é um assistente especializado em incentivos públicos portugueses. Responda de forma útil e amigável.

Pergunta do utilizador: {message}

Dados disponíveis:
{context_text}

Responda de forma natural e útil, incorporando os dados relevantes quando apropriado. Seja conciso mas informativo.
"""
            
            # Usar AI processor para gerar resposta
            response = await self.ai_processor.generate_text_response(prompt, max_tokens=500)
            
            return {"text": response}
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            # Fallback para resposta simples
            if response_data.get("type") == "incentives_list":
                count = len(response_data['data']) if isinstance(response_data.get('data'), list) else 1
                return {"text": f"Encontrei {count} incentivos que correspondem à sua pesquisa."}
            elif response_data.get("type") == "companies_list":
                return {"text": f"Encontrei {len(response_data['data'])} empresas que correspondem à sua pesquisa."}
            elif response_data.get("type") == "incentive_matches":
                count = len(response_data['data']) if isinstance(response_data.get('data'), list) else 0
                return {"text": f"Encontrei {count} empresas adequadas para este incentivo."}
            elif response_data.get("type") == "no_matches":
                return {"text": response_data.get("message", "Incentivo encontrado mas ainda não tem matches calculados.")}
            else:
                return {"text": "Aqui estão os dados que encontrei para a sua consulta."}
    
    def get_conversation_history(self, user_id: str = "default", limit: int = 10) -> List[Dict]:
        """Retorna histórico de conversa"""
        return self.context_manager.get_recent_context(limit)
    
    def clear_context(self, user_id: str = "default"):
        """Limpa contexto da conversa"""
        self.context_manager = ChatbotContext()
