"""
Embedding Service - Geração e Gestão de Embeddings

Este serviço gera embeddings semânticos para empresas e incentivos,
permitindo busca por similaridade semântica em vez de apenas matching exato.

Vantagens:
- Compreensão semântica das atividades empresariais
- Matching baseado em significado, não apenas palavras-chave
- Redução significativa de custos LLM (menos candidatas para análise)
- Melhor descoberta de matches não óbvios
"""

import openai
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company
from app.services.cost_tracker import CostTracker
import json
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Serviço para geração e gestão de embeddings semânticos.
    
    Usa OpenAI text-embedding-3-small para gerar embeddings de:
    - Descrições de incentivos (título + descrição + objetivos)
    - Atividades empresariais (nome + CAE label + descrição comercial)
    """
    
    def __init__(self, api_key: str, session: Session):
        self.client = openai.OpenAI(api_key=api_key)
        self.session = session
        self.cost_tracker = CostTracker(session)
        self.embedding_model = "text-embedding-3-small"  # Custo-eficiente: $0.00002/1K tokens
        self.embedding_dimensions = 1536  # Dimensões padrão do modelo
        
        # Cache de embeddings para evitar recálculos
        self._embedding_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def generate_incentive_embedding(self, incentive: Incentive) -> Optional[List[float]]:
        """
        Gera embedding semântico para um incentivo.
        
        Combina múltiplas fontes de informação:
        - Título do incentivo
        - Descrição principal
        - Objetivos e setores elegíveis (do ai_description)
        - Atividades suportadas
        
        Args:
            incentive: Incentivo para processar
            
        Returns:
            Lista de floats representando o embedding (1536 dimensões)
        """
        # Cache key baseado no conteúdo do incentivo
        cache_key = f"incentive_{incentive.incentive_id}_{hashlib.md5(str(incentive.title).encode()).hexdigest()}"
        
        if cache_key in self._embedding_cache:
            self._cache_hits += 1
            logger.info(f"💾 Embedding cache HIT for incentive '{incentive.title[:50]}...'")
            return self._embedding_cache[cache_key]
        
        self._cache_misses += 1
        logger.info(f"🔍 Embedding cache MISS for incentive '{incentive.title[:50]}...' - generating new embedding")
        
        # Construir texto rico para embedding
        text_parts = []
        
        # 1. Título (peso alto)
        if incentive.title:
            text_parts.append(f"Título: {incentive.title}")
        
        # 2. Descrição principal (peso alto)
        if incentive.description:
            text_parts.append(f"Descrição: {incentive.description}")
        
        # 3. Informações estruturadas do AI (peso médio)
        ai_desc = incentive.ai_description or {}
        if ai_desc:
            if ai_desc.get('summary'):
                text_parts.append(f"Resumo: {ai_desc['summary']}")
            
            if ai_desc.get('objective'):
                text_parts.append(f"Objetivo: {ai_desc['objective']}")
            
            if ai_desc.get('eligible_sectors'):
                sectors = ', '.join(ai_desc['eligible_sectors'])
                text_parts.append(f"Setores elegíveis: {sectors}")
            
            if ai_desc.get('supported_activities'):
                activities = ', '.join(ai_desc['supported_activities'])
                text_parts.append(f"Atividades suportadas: {activities}")
            
            if ai_desc.get('target_audience'):
                audience = ', '.join(ai_desc['target_audience'])
                text_parts.append(f"Público-alvo: {audience}")
        
        # Combinar todas as partes
        full_text = "\n".join(text_parts)
        
        if not full_text.strip():
            logger.warning(f"Incentive {incentive.incentive_id} has no text content for embedding")
            return None
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=full_text,
                dimensions=self.embedding_dimensions
            )
            
            embedding = response.data[0].embedding
            
            # Track API call cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": 0,  # Embeddings não têm completion tokens
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type="generate_incentive_embedding",
                model_name=self.embedding_model,
                usage_data=usage_data,
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=True
            )
            
            # Cache do resultado
            self._embedding_cache[cache_key] = embedding
            logger.info(f"✅ Generated embedding for incentive '{incentive.title[:50]}...' (cache size: {len(self._embedding_cache)})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for incentive {incentive.incentive_id}: {e}")
            
            # Track failed API call
            self.cost_tracker.track_api_call(
                operation_type="generate_incentive_embedding",
                model_name=self.embedding_model,
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            
            return None
    
    def generate_company_embedding(self, company: Company) -> Optional[List[float]]:
        """
        Gera embedding semântico para uma empresa.
        
        Combina múltiplas fontes de informação:
        - Nome da empresa
        - CAE label (atividade principal)
        - Descrição comercial nativa
        - Website (se disponível)
        
        Args:
            company: Empresa para processar
            
        Returns:
            Lista de floats representando o embedding (1536 dimensões)
        """
        # Cache key baseado no conteúdo da empresa
        cache_key = f"company_{company.company_id}_{hashlib.md5(str(company.company_name).encode()).hexdigest()}"
        
        if cache_key in self._embedding_cache:
            self._cache_hits += 1
            logger.info(f"💾 Embedding cache HIT for company '{company.company_name[:50]}...'")
            return self._embedding_cache[cache_key]
        
        self._cache_misses += 1
        logger.info(f"🔍 Embedding cache MISS for company '{company.company_name[:50]}...' - generating new embedding")
        
        # Construir texto rico para embedding
        text_parts = []
        
        # 1. Nome da empresa (peso alto)
        if company.company_name:
            text_parts.append(f"Empresa: {company.company_name}")
        
        # 2. CAE label - atividade principal (peso alto)
        if company.cae_primary_label:
            text_parts.append(f"Atividade principal: {company.cae_primary_label}")
        
        # 3. Descrição comercial (peso médio)
        if company.trade_description_native:
            text_parts.append(f"Descrição comercial: {company.trade_description_native}")
        
        # 4. Website (peso baixo, mas pode dar contexto)
        if company.website:
            text_parts.append(f"Website: {company.website}")
        
        # Combinar todas as partes
        full_text = "\n".join(text_parts)
        
        if not full_text.strip():
            logger.warning(f"Company {company.company_id} has no text content for embedding")
            return None
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=full_text,
                dimensions=self.embedding_dimensions
            )
            
            embedding = response.data[0].embedding
            
            # Track API call cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": 0,  # Embeddings não têm completion tokens
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type="generate_company_embedding",
                model_name=self.embedding_model,
                usage_data=usage_data,
                incentive_id=None,  # Empresas não têm incentive_id
                cache_hit=False,
                success=True
            )
            
            # Cache do resultado
            self._embedding_cache[cache_key] = embedding
            logger.info(f"✅ Generated embedding for company '{company.company_name[:50]}...' (cache size: {len(self._embedding_cache)})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for company {company.company_id}: {e}")
            
            # Track failed API call
            self.cost_tracker.track_api_call(
                operation_type="generate_company_embedding",
                model_name=self.embedding_model,
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=None,
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcula similaridade coseno entre dois embeddings.
        
        Args:
            embedding1: Primeiro embedding
            embedding2: Segundo embedding
            
        Returns:
            Score de similaridade entre 0 e 1 (1 = idêntico)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        # Converter para numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calcular similaridade coseno
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def find_similar_companies(
        self, 
        incentive: Incentive, 
        all_companies: List[Company], 
        top_k: int = 50
    ) -> List[Tuple[Company, float]]:
        """
        Encontra empresas similares a um incentivo usando busca semântica.
        
        Args:
            incentive: Incentivo de referência
            all_companies: Lista de todas as empresas
            top_k: Número de empresas mais similares a retornar
            
        Returns:
            Lista de tuplas (empresa, score_similaridade) ordenada por score
        """
        logger.info(f"🔍 Finding similar companies for incentive '{incentive.title[:50]}...'")
        
        # Gerar embedding do incentivo
        incentive_embedding = self.generate_incentive_embedding(incentive)
        if not incentive_embedding:
            logger.error(f"Could not generate embedding for incentive {incentive.incentive_id}")
            return []
        
        # Calcular similaridades
        similarities = []
        
        for company in all_companies:
            company_embedding = self.generate_company_embedding(company)
            if company_embedding:
                similarity = self.calculate_similarity(incentive_embedding, company_embedding)
                similarities.append((company, similarity))
        
        # Ordenar por similaridade (maior primeiro)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top K
        top_similarities = similarities[:top_k]
        
        logger.info(f"✅ Found {len(top_similarities)} similar companies")
        if top_similarities:
            logger.info(f"   Top similarity: {top_similarities[0][1]:.3f}")
            logger.info(f"   Bottom similarity: {top_similarities[-1][1]:.3f}")
        
        return top_similarities
    
    def batch_generate_embeddings(
        self, 
        incentives: List[Incentive] = None, 
        companies: List[Company] = None
    ) -> Dict[str, Any]:
        """
        Gera embeddings em lote para múltiplos incentivos e/ou empresas.
        
        Args:
            incentives: Lista de incentivos (opcional)
            companies: Lista de empresas (opcional)
            
        Returns:
            Dict com estatísticas do processamento
        """
        stats = {
            "incentives_processed": 0,
            "companies_processed": 0,
            "incentives_failed": 0,
            "companies_failed": 0,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses
        }
        
        # Processar incentivos
        if incentives:
            logger.info(f"🔄 Batch generating embeddings for {len(incentives)} incentives...")
            for incentive in incentives:
                try:
                    embedding = self.generate_incentive_embedding(incentive)
                    if embedding:
                        stats["incentives_processed"] += 1
                    else:
                        stats["incentives_failed"] += 1
                except Exception as e:
                    logger.error(f"Error processing incentive {incentive.incentive_id}: {e}")
                    stats["incentives_failed"] += 1
        
        # Processar empresas
        if companies:
            logger.info(f"🔄 Batch generating embeddings for {len(companies)} companies...")
            for company in companies:
                try:
                    embedding = self.generate_company_embedding(company)
                    if embedding:
                        stats["companies_processed"] += 1
                    else:
                        stats["companies_failed"] += 1
                except Exception as e:
                    logger.error(f"Error processing company {company.company_id}: {e}")
                    stats["companies_failed"] += 1
        
        logger.info(f"✅ Batch processing completed: {stats}")
        return stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache de embeddings.
        
        Returns:
            Dict com estatísticas do cache
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Calcular economia estimada
        # Cada cache hit economiza ~$0.00002 (custo do embedding)
        estimated_savings = self._cache_hits * 0.00002
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percentage": round(hit_rate, 2),
            "cache_size": len(self._embedding_cache),
            "estimated_savings_usd": round(estimated_savings, 6)
        }
    
    def clear_cache(self) -> int:
        """
        Limpa o cache de embeddings.
        
        Returns:
            Número de entradas removidas
        """
        size = len(self._embedding_cache)
        self._embedding_cache.clear()
        logger.info(f"🗑️ Cleared {size} embeddings from cache")
        return size
