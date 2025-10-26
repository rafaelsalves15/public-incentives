"""
Vector Database Service - Gestão de Base de Dados Vectorial

Este serviço implementa uma base de dados vectorial usando ChromaDB para armazenar
e pesquisar embeddings de empresas e incentivos de forma eficiente.

Vantagens do ChromaDB:
- Armazenamento local (sem custos de API externa)
- Busca rápida por similaridade coseno
- Persistência automática dos dados
- Interface simples e eficiente
"""

import chromadb
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company
from app.services.embedding_service import EmbeddingService
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorDatabaseService:
    """
    Serviço para gestão da base de dados vectorial usando ChromaDB.
    
    Organiza embeddings em duas coleções:
    - 'incentives': Embeddings de incentivos
    - 'companies': Embeddings de empresas
    
    Permite busca rápida por similaridade semântica.
    """
    
    def __init__(self, embedding_service: EmbeddingService, persist_directory: str = None):
        """
        Inicializa o serviço de base de dados vectorial.
        
        Args:
            embedding_service: Serviço para geração de embeddings
            persist_directory: Diretório para persistir dados (padrão: ./chroma_db)
        """
        self.embedding_service = embedding_service
        
        # Configurar diretório de persistência
        if persist_directory is None:
            persist_directory = os.path.join(os.getcwd(), "chroma_db")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # Coleções
        self.incentives_collection = self.client.get_or_create_collection(
            name="incentives",
            metadata={"description": "Embeddings de incentivos públicos"}
        )
        
        self.companies_collection = self.client.get_or_create_collection(
            name="companies", 
            metadata={"description": "Embeddings de empresas"}
        )
        
        logger.info(f"✅ Vector database initialized at {self.persist_directory}")
        logger.info(f"📊 Incentives collection: {self.incentives_collection.count()} embeddings")
        logger.info(f"📊 Companies collection: {self.companies_collection.count()} embeddings")
    
    def add_incentive_embedding(self, incentive: Incentive) -> bool:
        """
        Adiciona embedding de um incentivo à base de dados vectorial.
        
        Args:
            incentive: Incentivo para processar
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            # Gerar embedding
            embedding = self.embedding_service.generate_incentive_embedding(incentive)
            if not embedding:
                logger.error(f"Could not generate embedding for incentive {incentive.incentive_id}")
                return False
            
            # Preparar metadados
            ai_desc = incentive.ai_description or {}
            metadata = {
                "incentive_id": str(incentive.incentive_id),
                "title": incentive.title[:500],  # ChromaDB tem limite de 500 chars
                "description": incentive.description[:1000] if incentive.description else "",
                "summary": ai_desc.get('summary', '')[:500],
                "eligible_sectors": json.dumps(ai_desc.get('eligible_sectors', [])),
                "eligible_cae_codes": json.dumps(ai_desc.get('eligible_cae_codes', [])),
                "target_audience": json.dumps(ai_desc.get('target_audience', [])),
                "total_budget": float(incentive.total_budget) if incentive.total_budget else 0.0,
                "created_at": str(incentive.created_at) if hasattr(incentive, 'created_at') else ""
            }
            
            # Adicionar à coleção
            self.incentives_collection.add(
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[str(incentive.incentive_id)]
            )
            
            logger.info(f"✅ Added incentive embedding: {incentive.title[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding incentive embedding {incentive.incentive_id}: {e}")
            return False
    
    def add_company_embedding(self, company: Company) -> bool:
        """
        Adiciona embedding de uma empresa à base de dados vectorial.
        
        Args:
            company: Empresa para processar
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            # Gerar embedding
            embedding = self.embedding_service.generate_company_embedding(company)
            if not embedding:
                logger.error(f"Could not generate embedding for company {company.company_id}")
                return False
            
            # Preparar metadados
            metadata = {
                "company_id": str(company.company_id),
                "company_name": company.company_name[:500],
                "cae_primary_label": company.cae_primary_label[:500] if company.cae_primary_label else "",
                "cae_primary_code": json.dumps(company.cae_primary_code) if company.cae_primary_code else "[]",
                "trade_description": company.trade_description_native[:1000] if company.trade_description_native else "",
                "website": company.website[:500] if company.website else "",
                "company_size": company.company_size or "",
                "region": company.region or "",
                "is_active": company.is_active if hasattr(company, 'is_active') else True,
                "created_at": str(company.created_at) if hasattr(company, 'created_at') else ""
            }
            
            # Adicionar à coleção
            self.companies_collection.add(
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[str(company.company_id)]
            )
            
            logger.info(f"✅ Added company embedding: {company.company_name[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding company embedding {company.company_id}: {e}")
            return False
    
    def search_similar_companies(
        self, 
        incentive: Incentive, 
        top_k: int = 50,
        min_similarity: float = 0.0
    ) -> List[Tuple[Company, float, Dict[str, Any]]]:
        """
        Busca empresas similares a um incentivo usando busca vectorial.
        
        Args:
            incentive: Incentivo de referência
            top_k: Número de empresas mais similares a retornar
            min_similarity: Similaridade mínima (0.0 a 1.0)
            
        Returns:
            Lista de tuplas (empresa, score_similaridade, metadados)
        """
        try:
            # Gerar embedding do incentivo
            incentive_embedding = self.embedding_service.generate_incentive_embedding(incentive)
            if not incentive_embedding:
                logger.error(f"Could not generate embedding for incentive {incentive.incentive_id}")
                return []
            
            # Buscar na base de dados vectorial
            results = self.companies_collection.query(
                query_embeddings=[incentive_embedding],
                n_results=top_k,
                include=["metadatas", "embeddings"]  # Incluir embeddings para calcular similaridade coseno
            )
            
            # Processar resultados
            similar_companies = []
            
            if results['ids'] and results['ids'][0]:
                for i, company_id in enumerate(results['ids'][0]):
                    # Calcular similaridade coseno manualmente
                    company_embedding = results['embeddings'][0][i]
                    # Converter numpy array para list se necessário
                    if hasattr(company_embedding, 'tolist'):
                        company_embedding = company_embedding.tolist()
                    
                    similarity = self.embedding_service.calculate_similarity(
                        incentive_embedding, 
                        company_embedding
                    )
                    
                    # Filtrar por similaridade mínima
                    if similarity >= min_similarity:
                        metadata = results['metadatas'][0][i]
                        
                        # Criar objeto Company simplificado para compatibilidade
                        company = Company()
                        company.company_id = company_id
                        company.company_name = metadata.get('company_name', '')
                        company.cae_primary_label = metadata.get('cae_primary_label', '')
                        company.cae_primary_code = json.loads(metadata.get('cae_primary_code', '[]'))
                        company.trade_description_native = metadata.get('trade_description', '')
                        company.website = metadata.get('website', '')
                        company.company_size = metadata.get('company_size', '')
                        company.region = metadata.get('region', '')
                        
                        similar_companies.append((company, similarity, metadata))
            
            logger.info(f"🔍 Found {len(similar_companies)} similar companies (min_similarity: {min_similarity})")
            if similar_companies:
                logger.info(f"   Top similarity: {similar_companies[0][1]:.3f}")
                logger.info(f"   Bottom similarity: {similar_companies[-1][1]:.3f}")
            
            return similar_companies
            
        except Exception as e:
            logger.error(f"Error searching similar companies for incentive {incentive.incentive_id}: {e}")
            return []
    
    def search_similar_incentives(
        self, 
        company: Company, 
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[Tuple[Incentive, float, Dict[str, Any]]]:
        """
        Busca incentivos similares a uma empresa usando busca vectorial.
        
        Args:
            company: Empresa de referência
            top_k: Número de incentivos mais similares a retornar
            min_similarity: Similaridade mínima (0.0 a 1.0)
            
        Returns:
            Lista de tuplas (incentivo, score_similaridade, metadados)
        """
        try:
            # Gerar embedding da empresa
            company_embedding = self.embedding_service.generate_company_embedding(company)
            if not company_embedding:
                logger.error(f"Could not generate embedding for company {company.company_id}")
                return []
            
            # Buscar na base de dados vectorial
            results = self.incentives_collection.query(
                query_embeddings=[company_embedding],
                n_results=top_k,
                include=["metadatas", "distances"]
            )
            
            # Processar resultados
            similar_incentives = []
            
            if results['ids'] and results['ids'][0]:
                for i, incentive_id in enumerate(results['ids'][0]):
                    # Calcular similaridade
                    distance = results['distances'][0][i]
                    similarity = 1.0 - distance
                    
                    # Filtrar por similaridade mínima
                    if similarity >= min_similarity:
                        metadata = results['metadatas'][0][i]
                        
                        # Criar objeto Incentive simplificado para compatibilidade
                        incentive = Incentive()
                        incentive.incentive_id = incentive_id
                        incentive.title = metadata.get('title', '')
                        incentive.description = metadata.get('description', '')
                        incentive.total_budget = metadata.get('total_budget', 0.0)
                        
                        # Reconstruir ai_description
                        ai_description = {
                            'summary': metadata.get('summary', ''),
                            'eligible_sectors': json.loads(metadata.get('eligible_sectors', '[]')),
                            'eligible_cae_codes': json.loads(metadata.get('eligible_cae_codes', '[]')),
                            'target_audience': json.loads(metadata.get('target_audience', '[]'))
                        }
                        incentive.ai_description = ai_description
                        
                        similar_incentives.append((incentive, similarity, metadata))
            
            logger.info(f"🔍 Found {len(similar_incentives)} similar incentives (min_similarity: {min_similarity})")
            if similar_incentives:
                logger.info(f"   Top similarity: {similar_incentives[0][1]:.3f}")
                logger.info(f"   Bottom similarity: {similar_incentives[-1][1]:.3f}")
            
            return similar_incentives
            
        except Exception as e:
            logger.error(f"Error searching similar incentives for company {company.company_id}: {e}")
            return []
    
    def batch_populate_database(
        self, 
        session: Session, 
        incentive_ids: List[str] = None,
        company_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Popula a base de dados vectorial com embeddings em lote.
        
        Args:
            session: Sessão da base de dados
            incentive_ids: Lista de IDs de incentivos (opcional, None = todos)
            company_ids: Lista de IDs de empresas (opcional, None = todas)
            
        Returns:
            Dict com estatísticas do processamento
        """
        stats = {
            "incentives_processed": 0,
            "incentives_failed": 0,
            "companies_processed": 0,
            "companies_failed": 0,
            "total_embeddings": 0
        }
        
        # Processar incentivos
        if incentive_ids is not None:
            incentives = session.query(Incentive).filter(
                Incentive.incentive_id.in_(incentive_ids)
            ).all()
        else:
            incentives = session.query(Incentive).all()
        
        logger.info(f"🔄 Processing {len(incentives)} incentives...")
        for incentive in incentives:
            try:
                success = self.add_incentive_embedding(incentive)
                if success:
                    stats["incentives_processed"] += 1
                else:
                    stats["incentives_failed"] += 1
            except Exception as e:
                logger.error(f"Error processing incentive {incentive.incentive_id}: {e}")
                stats["incentives_failed"] += 1
        
        # Processar empresas
        if company_ids is not None:
            companies = session.query(Company).filter(
                Company.company_id.in_(company_ids)
            ).all()
        else:
            companies = session.query(Company).all()
        
        logger.info(f"🔄 Processing {len(companies)} companies...")
        for company in companies:
            try:
                success = self.add_company_embedding(company)
                if success:
                    stats["companies_processed"] += 1
                else:
                    stats["companies_failed"] += 1
            except Exception as e:
                logger.error(f"Error processing company {company.company_id}: {e}")
                stats["companies_failed"] += 1
        
        stats["total_embeddings"] = stats["incentives_processed"] + stats["companies_processed"]
        
        logger.info(f"✅ Batch population completed: {stats}")
        return stats
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de dados vectorial.
        
        Returns:
            Dict com estatísticas das coleções
        """
        return {
            "incentives_count": self.incentives_collection.count(),
            "companies_count": self.companies_collection.count(),
            "total_embeddings": self.incentives_collection.count() + self.companies_collection.count(),
            "persist_directory": str(self.persist_directory),
            "embedding_cache_stats": self.embedding_service.get_cache_stats()
        }
    
    def clear_database(self) -> Dict[str, int]:
        """
        Limpa toda a base de dados vectorial.
        
        Returns:
            Dict com número de embeddings removidos
        """
        incentives_count = self.incentives_collection.count()
        companies_count = self.companies_collection.count()
        
        # Limpar coleções
        self.client.delete_collection("incentives")
        self.client.delete_collection("companies")
        
        # Recriar coleções vazias
        self.incentives_collection = self.client.create_collection(
            name="incentives",
            metadata={"description": "Embeddings de incentivos públicos"}
        )
        
        self.companies_collection = self.client.create_collection(
            name="companies",
            metadata={"description": "Embeddings de empresas"}
        )
        
        logger.info(f"🗑️ Cleared vector database: {incentives_count} incentives, {companies_count} companies")
        
        return {
            "incentives_removed": incentives_count,
            "companies_removed": companies_count,
            "total_removed": incentives_count + companies_count
        }
