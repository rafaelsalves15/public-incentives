#!/usr/bin/env python3
"""
Teste Otimizado de Custos - Sistema Híbrido
===========================================

Teste focado em otimização de custos para escala:
- 500 incentivos + 250k empresas
- Limite: €20 total
- Estratégias de otimização implementadas
"""

import pandas as pd
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import random
import uuid
import numpy as np

# Imports do sistema
from app.db.database import SessionLocal
from app.db.models import Incentive, Company, IncentiveMetadata
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from app.services.hybrid_matching_service import HybridMatchingService
from app.services.unified_scorer import UnifiedScorer

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CostOptimizedTester:
    """Testador otimizado para custos"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.cost_limit = 20.0  # €20 limite total
        self.current_cost = 0.0
        
        # Serviços
        self.ai_processor = AIProcessor(api_key="sk-proj-123", session=self.db)
        self.embedding_service = EmbeddingService(self.ai_processor.cost_tracker)
        self.vector_db = VectorDatabaseService(self.embedding_service)
        self.hybrid_matcher = HybridMatchingService(
            self.embedding_service, 
            self.vector_db, 
            self.ai_processor
        )
        
        # Estatísticas
        self.stats = {
            'incentives_processed': 0,
            'companies_processed': 0,
            'matches_generated': 0,
            'total_cost': 0.0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("🚀 Cost Optimized Tester inicializado")
        logger.info(f"💰 Limite de custos: €{self.cost_limit}")
    
    def clean_value(self, value):
        """Limpa valores NaN do pandas"""
        if pd.isna(value) or value is None:
            return None
        return value
    
    def check_cost_limit(self) -> bool:
        """Verifica se ainda estamos dentro do limite de custos"""
        current_stats = self.ai_processor.cost_tracker.get_total_stats()
        self.current_cost = current_stats['all_time']['total_cost']
        
        if self.current_cost >= self.cost_limit:
            logger.error(f"🚨 LIMITE DE CUSTOS ATINGIDO: €{self.current_cost:.3f}")
            return False
        
        logger.info(f"💰 Custo atual: €{self.current_cost:.3f} | Restante: €{self.cost_limit - self.current_cost:.3f}")
        return True
    
    def load_data_from_csv(self) -> tuple[List[Dict], List[Dict]]:
        """Carrega dados dos CSVs com amostras menores para teste"""
        logger.info("📂 Carregando dados dos CSVs...")
        try:
            incentives_df = pd.read_csv('/data/incentives.csv')
            logger.info(f"📊 Incentivos carregados: {len(incentives_df)}")
            
            companies_df = pd.read_csv('/data/companies.csv')
            logger.info(f"📊 Empresas carregadas: {len(companies_df)}")
            
            # Amostras MUITO menores para teste de custos
            sample_incentives = incentives_df.sample(n=min(5, len(incentives_df)), random_state=42)
            sample_companies = companies_df.sample(n=min(50, len(companies_df)), random_state=42)
            
            logger.info(f"🎯 Amostra selecionada: {len(sample_incentives)} incentivos, {len(sample_companies)} empresas")
            return sample_incentives.to_dict('records'), sample_companies.to_dict('records')
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSVs: {e}")
            raise
    
    def create_database_tables(self):
        """Cria tabelas da base de dados"""
        logger.info("🗄️ Criando tabelas da base de dados...")
        try:
            from app.db.models import Base
            from app.db.database import engine
            
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def populate_incentives(self, incentives_data: List[Dict]) -> List[str]:
        """Popula incentivos na base de dados"""
        logger.info("📝 Populando incentivos na base de dados...")
        
        incentive_ids = []
        
        for i, incentive_data in enumerate(incentives_data, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando na população de incentivos devido ao limite de custos")
                break
            
            try:
                # Criar incentivo (usando apenas campos que existem no modelo)
                incentive = Incentive(
                    incentive_id=uuid.uuid4(),  # Gerar UUID válido
                    title=self.clean_value(incentive_data.get('title', '')) or '',
                    description=self.clean_value(incentive_data.get('description', '')) or '',
                    ai_description=None,  # Será preenchido pelo AI
                    document_urls=self.clean_value(incentive_data.get('document_urls', [])) or [],
                    publication_date=self.clean_value(incentive_data.get('date_publication')),
                    start_date=self.clean_value(incentive_data.get('date_start')),
                    end_date=self.clean_value(incentive_data.get('date_end')),
                    total_budget=self.clean_value(incentive_data.get('total_budget')),
                    source_link=self.clean_value(incentive_data.get('source_link', '')) or ''
                )
                
                self.db.add(incentive)
                self.db.commit()
                
                # Gerar AI description
                if not self.check_cost_limit():
                    logger.warning(f"⚠️ Parando na população de incentivos devido ao limite de custos")
                    break
                
                ai_description = self.ai_processor.generate_structured_ai_description(incentive)
                if ai_description:
                    incentive.ai_description = ai_description
                    self.db.commit()
                    logger.info(f"✅ AI description gerada para incentivo {i}")
                else:
                    logger.warning(f"⚠️ Falha ao gerar AI description para incentivo {i}")
                
                incentive_ids.append(incentive.incentive_id)
                self.stats['incentives_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar incentivo {i}: {e}")
                continue
        
        logger.info(f"✅ Incentivos processados: {len(incentive_ids)}")
        return incentive_ids
    
    def populate_companies(self, companies_data: List[Dict]) -> List[str]:
        """Popula empresas na base de dados COM dados inferidos"""
        logger.info("🏢 Populando empresas na base de dados...")
        
        company_ids = []
        
        for i, company_data in enumerate(companies_data, 1):
            try:
                # Criar empresa (usando apenas campos que existem no modelo)
                company = Company(
                    company_id=uuid.uuid4(),  # Gerar UUID válido
                    company_name=self.clean_value(company_data.get('company_name', '')) or '',
                    cae_primary_label=self.clean_value(company_data.get('cae_primary_label', '')) or '',
                    cae_primary_code=[],  # Será preenchido pelo AI
                    trade_description_native=self.clean_value(company_data.get('trade_description_native', '')) or '',
                    website=self.clean_value(company_data.get('website', '')) or '',
                    company_size='',  # Será preenchido pelo AI
                    region='',  # Será preenchido pelo AI
                    is_active=True
                )
                
                self.db.add(company)
                
                # Inferir dados da empresa usando LLM (OTIMIZADO)
                if not self.check_cost_limit():
                    logger.warning(f"⚠️ Parando na população de empresas devido ao limite de custos")
                    break
                
                try:
                    inferred_data = self.ai_processor.infer_company_data(company)
                    if inferred_data:
                        company.cae_primary_code = inferred_data.get('cae_codes', [])
                        company.region = inferred_data.get('region', 'N/A')
                        company.company_size = inferred_data.get('size', 'N/A')
                        logger.info(f"✅ Dados inferidos para empresa {i}: CAE={len(company.cae_primary_code)}, Região={company.region}, Tamanho={company.company_size}")
                    else:
                        logger.warning(f"⚠️ Falha ao inferir dados para empresa {i}")
                except Exception as e:
                    logger.error(f"❌ Erro ao inferir dados para empresa {i}: {e}")
                
                if i % 10 == 0:  # Commit mais frequente para teste pequeno
                    self.db.commit()
                    logger.info(f"📊 Empresas processadas: {i}/{len(companies_data)}")
                
                company_ids.append(str(company.company_id))
                self.stats['companies_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar empresa {i}: {e}")
                continue
        
        self.db.commit()
        logger.info(f"✅ Empresas processadas: {len(company_ids)}")
        return company_ids
    
    def populate_vector_database(self, incentive_ids: List[str], company_ids: List[str]):
        """Popula base de dados vectorial"""
        logger.info("🧠 Populando base de dados vectorial...")
        
        # Gerar embeddings para empresas (OTIMIZADO - apenas algumas)
        companies = self.db.query(Company).filter(Company.company_id.in_(company_ids[:10])).all()  # Apenas 10 empresas
        for i, company in enumerate(companies, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando embeddings de empresas devido ao limite de custos")
                break
            
            try:
                embedding = self.embedding_service.generate_company_embedding(company)
                if embedding:
                    self.vector_db.add_company_embedding(company, embedding)
                    logger.info(f"✅ Added company embedding: {company.company_name[:50]}...")
                else:
                    logger.warning(f"⚠️ Falha ao gerar embedding para empresa {i}")
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding para empresa {i}: {e}")
        
        # Gerar embeddings para incentivos
        incentives = self.db.query(Incentive).filter(Incentive.incentive_id.in_(incentive_ids)).all()
        for i, incentive in enumerate(incentives, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando embeddings de incentivos devido ao limite de custos")
                break
            
            try:
                embedding = self.embedding_service.generate_incentive_embedding(incentive)
                if embedding:
                    self.vector_db.add_incentive_embedding(incentive, embedding)
                    logger.info(f"✅ Added incentive embedding: {incentive.title[:50]}...")
                else:
                    logger.warning(f"⚠️ Falha ao gerar embedding para incentivo {i}")
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding para incentivo {i}: {e}")
        
        logger.info("✅ Base de dados vectorial populada")
    
    def run_hybrid_matching(self, incentive_ids: List[str]):
        """Executa matching híbrido"""
        logger.info("🎯 Executando matching híbrido...")
        
        incentives = self.db.query(Incentive).filter(Incentive.incentive_id.in_(incentive_ids)).all()
        
        for i, incentive in enumerate(incentives, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando matching devido ao limite de custos")
                break
            
            logger.info(f"🔍 Matching {i}/{len(incentives)}: {incentive.incentive_id}")
            logger.info(f"🎯 Finding top 5 matches for incentive {incentive.incentive_id}")
            
            try:
                matches = self.hybrid_matcher.find_top_matches(incentive, limit=5)
                
                if matches:
                    logger.info(f"📋 INCENTIVO: {incentive.title[:80]}...")
                    logger.info(f"🎯 Top {len(matches)} matches encontrados:")
                    
                    for j, match in enumerate(matches, 1):
                        company = match['company']
                        total_score = match['total_score']
                        semantic_score = match['semantic_score']
                        unified_score = match['unified_score']
                        llm_score = match['llm_score']
                        
                        logger.info(f"   {j}. {company.company_name[:50]}...")
                        logger.info(f"      🧠 Semântica: {semantic_score:.3f}")
                        logger.info(f"      📊 Unificado: {unified_score}")
                        logger.info(f"      🤖 LLM: {llm_score:.3f}")
                        logger.info(f"      🎯 Total: {total_score:.3f}")
                        logger.info(f"      🏷️ CAE: {company.cae_primary_label}")
                    
                    logger.info("─" * 80)
                    self.stats['matches_generated'] += len(matches)
                else:
                    logger.warning(f"⚠️ Nenhum match encontrado para incentivo {i}")
                
            except Exception as e:
                logger.error(f"❌ Erro no matching para incentivo {i}: {e}")
                continue
    
    def run_cost_optimized_test(self):
        """Executa teste otimizado para custos"""
        logger.info("🚀 INICIANDO TESTE OTIMIZADO DE CUSTOS")
        logger.info("=" * 80)
        
        self.stats['start_time'] = time.time()
        
        try:
            # 1. Carregar dados
            incentives_data, companies_data = self.load_data_from_csv()
            
            # 2. Criar tabelas
            self.create_database_tables()
            
            # 3. Popular incentivos
            incentive_ids = self.populate_incentives(incentives_data)
            
            # 4. Popular empresas
            company_ids = self.populate_companies(companies_data)
            
            # 5. Popular base vectorial
            self.populate_vector_database(incentive_ids, company_ids)
            
            # 6. Executar matching híbrido
            self.run_hybrid_matching(incentive_ids)
            
        except Exception as e:
            logger.error(f"❌ ERRO NO TESTE: {e}")
            raise
        finally:
            self.stats['end_time'] = time.time()
            self.print_final_summary()
            self.db.close()
    
    def print_final_summary(self):
        """Imprime resumo final"""
        logger.info("📊 RESUMO FINAL DO TESTE OTIMIZADO")
        logger.info("=" * 80)
        
        total_time = self.stats['end_time'] - self.stats['start_time']
        logger.info(f"⏱️ Tempo total: {total_time:.2f}s")
        logger.info(f"📝 Incentivos processados: {self.stats['incentives_processed']}")
        logger.info(f"🏢 Empresas processadas: {self.stats['companies_processed']}")
        logger.info(f"🎯 Matches gerados: {self.stats['matches_generated']}")
        logger.info("")
        
        # Custos finais
        final_stats = self.ai_processor.cost_tracker.get_total_stats()
        total_cost = final_stats['all_time']['total_cost']
        
        logger.info("💰 CUSTOS:")
        logger.info(f"   Total: €{total_cost:.3f}")
        logger.info(f"   Limite: €{self.cost_limit:.3f}")
        logger.info(f"   Economia: €{self.cost_limit - total_cost:.3f}")
        logger.info("")
        
        # Breakdown por operação
        logger.info("📈 BREAKDOWN POR OPERAÇÃO:")
        for operation, cost in final_stats['all_time']['costs_by_operation'].items():
            logger.info(f"   {operation:<30}: €{cost:.6f}")
        logger.info("")
        
        # Projeção para escala
        logger.info("🔮 PROJEÇÃO PARA ESCALA COMPLETA:")
        logger.info(f"   500 incentivos: €{total_cost * (500/self.stats['incentives_processed']):.2f}")
        logger.info(f"   250k empresas: €{total_cost * (250000/self.stats['companies_processed']):.2f}")
        logger.info(f"   Total estimado: €{total_cost * (500/self.stats['incentives_processed']) + total_cost * (250000/self.stats['companies_processed']):.2f}")
        logger.info("=" * 80)
        logger.info("✅ TESTE OTIMIZADO CONCLUÍDO!")

if __name__ == "__main__":
    tester = CostOptimizedTester()
    tester.run_cost_optimized_test()
