#!/usr/bin/env python3
"""
Teste End-to-End Corrigido - 1 Incentivo + 50 Empresas
======================================================

Teste idêntico ao end-to-end completo, mas com:
- Apenas 1 incentivo
- Apenas 50 empresas  
- COM preenchimento dos campos das empresas via AI
- Para testar se os scores unificados funcionam
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

class CorrectedEndToEndTester:
    """Testador end-to-end corrigido"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.cost_limit = 2.0  # $2 limite
        self.current_cost = 0.0
        
        # Serviços
        import os
        # Carregar variáveis do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
        self.ai_processor = AIProcessor(api_key=api_key, session=self.db)
        self.embedding_service = EmbeddingService(api_key, self.db)
        self.vector_db = VectorDatabaseService(self.embedding_service)
        self.hybrid_matcher = HybridMatchingService(
            self.ai_processor,
            self.embedding_service, 
            self.vector_db
        )
        self.unified_scorer = UnifiedScorer(self.ai_processor)
        
        # Estatísticas
        self.stats = {
            'incentives_processed': 0,
            'companies_processed': 0,
            'matches_generated': 0,
            'total_cost': 0.0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("🚀 Corrected End-to-End Tester inicializado")
        logger.info(f"💰 Limite de custos: ${self.cost_limit}")
    
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
            logger.error(f"🚨 LIMITE DE CUSTOS ATINGIDO: ${self.current_cost:.3f}")
            return False
        
        # Atualizar custo atual
        current_stats = self.ai_processor.cost_tracker.get_total_stats()
        self.current_cost = current_stats['all_time']['total_cost']
        logger.info(f"💰 Custo atual: ${self.current_cost:.6f} | Restante: ${self.cost_limit - self.current_cost:.3f}")
        return True
    
    def load_data_from_csv(self) -> tuple[List[Dict], List[Dict]]:
        """Carrega dados dos CSVs com amostras pequenas"""
        logger.info("📂 Carregando dados dos CSVs...")
        try:
            incentives_df = pd.read_csv('/data/incentives.csv')
            logger.info(f"📊 Incentivos carregados: {len(incentives_df)}")
            
            companies_df = pd.read_csv('/data/companies.csv')
            logger.info(f"📊 Empresas carregadas: {len(companies_df)}")
            
            # Amostras pequenas para teste
            sample_incentives = incentives_df.sample(n=min(1, len(incentives_df)), random_state=42)
            sample_companies = companies_df.sample(n=min(50, len(companies_df)), random_state=42)
            
            logger.info(f"🎯 Amostra selecionada: {len(sample_incentives)} incentivos, {len(sample_companies)} empresas")
            return sample_incentives.to_dict('records'), sample_companies.to_dict('records')
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSVs: {e}")
            raise
    
    def create_database_tables(self):
        """Limpa e cria tabelas da base de dados"""
        logger.info("🧹 Limpando base de dados...")
        try:
            from app.db.models import Base
            from app.db.database import engine
            
            # Limpar todas as tabelas
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ Base de dados limpa")
            
            # Criar tabelas novamente
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
                
                ai_description = self.ai_processor.generate_ai_description(incentive, {})
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
        """Cria empresas novas com dados AI inferidos"""
        logger.info("🏢 Criando empresas com dados AI inferidos...")
        
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
                
                # 🔧 CORREÇÃO: Inferir dados da empresa usando LLM
                if not self.check_cost_limit():
                    logger.warning(f"⚠️ Parando na população de empresas devido ao limite de custos")
                    break
                
                try:
                    inferred_data = self.ai_processor.infer_company_data(company)
                    if inferred_data:
                        company.cae_primary_code = inferred_data.get('cae_codes', [])
                        company.region = inferred_data.get('region', 'N/A')
                        company.company_size = inferred_data.get('size', 'N/A')
                        self.db.commit()  # Commit imediatamente após inferir dados
                        logger.info(f"✅ Dados inferidos para empresa {i}: CAE={len(company.cae_primary_code)}, Região={company.region}, Tamanho={company.company_size}")
                    else:
                        logger.warning(f"⚠️ Falha ao inferir dados para empresa {i}")
                except Exception as e:
                    logger.error(f"❌ Erro ao inferir dados para empresa {i}: {e}")
                
                company_ids.append(str(company.company_id))
                self.stats['companies_processed'] += 1
                
                # Log de progresso
                if i % 10 == 0:
                    logger.info(f"📊 Empresas processadas: {i}/{len(companies_data)}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar empresa {i}: {e}")
                continue
        
        logger.info(f"✅ Empresas processadas: {len(company_ids)}")
        return company_ids
    
    def populate_vector_database(self, incentive_ids: List[str], company_ids: List[str]):
        """Popula base de dados vectorial"""
        logger.info("🧠 Populando base de dados vectorial...")
        
        # Gerar embeddings para empresas
        companies = self.db.query(Company).filter(Company.company_id.in_(company_ids)).all()
        for i, company in enumerate(companies, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando embeddings de empresas devido ao limite de custos")
                break
            
            try:
                success = self.vector_db.add_company_embedding(company)
                if success:
                    logger.info(f"✅ Added company embedding: {company.company_name[:50]}...")
                else:
                    logger.warning(f"⚠️ Falha ao adicionar embedding para empresa {i}")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding para empresa {i}: {e}")
        
        # Gerar embeddings para incentivos
        incentives = self.db.query(Incentive).filter(Incentive.incentive_id.in_(incentive_ids)).all()
        for i, incentive in enumerate(incentives, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando embeddings de incentivos devido ao limite de custos")
                break
            
            try:
                success = self.vector_db.add_incentive_embedding(incentive)
                if success:
                    logger.info(f"✅ Added incentive embedding: {incentive.title[:50]}...")
                else:
                    logger.warning(f"⚠️ Falha ao adicionar embedding para incentivo {i}")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding para incentivo {i}: {e}")
        
        logger.info("✅ Base de dados vectorial populada")
    
    def test_unified_scoring(self, incentive_id: str, company_ids: List[str]):
        """Testa especificamente o scoring unificado"""
        logger.info("📊 TESTANDO SCORING UNIFICADO...")
        
        incentive = self.db.query(Incentive).filter(Incentive.incentive_id == incentive_id).first()
        if not incentive:
            logger.error(f"❌ Incentivo {incentive_id} não encontrado")
            return
        
        # Usar apenas as empresas que acabámos de criar
        companies = self.db.query(Company).filter(Company.company_id.in_(company_ids)).all()
        logger.info(f"🔍 Testando scoring para {len(companies)} empresas (apenas as criadas)")
        
        # Testar scoring unificado
        scored_companies = []
        for company in companies:
            score_data = self.unified_scorer.score_company(incentive, company)
            scored_companies.append({
                'company': company,
                'score': score_data['score'],
                'details': score_data['details']
            })
        
        # Ordenar por score
        scored_companies.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"📊 RESULTADOS DO SCORING UNIFICADO:")
        logger.info(f"   Total empresas: {len(scored_companies)}")
        logger.info(f"   Top score: {scored_companies[0]['score']}")
        logger.info(f"   Bottom score: {scored_companies[-1]['score']}")
        
        # Mostrar top 5
        logger.info(f"🏆 TOP 5 EMPRESAS:")
        for i, item in enumerate(scored_companies[:5], 1):
            company = item['company']
            score = item['score']
            details = item['details']
            
            logger.info(f"   {i}. {company.company_name[:50]}...")
            logger.info(f"      Score: {score}")
            logger.info(f"      CAE: {company.cae_primary_code}")
            logger.info(f"      Região: {company.region}")
            logger.info(f"      Tamanho: {company.company_size}")
            logger.info(f"      Detalhes: {details}")
            logger.info("")
    
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
                matches = self.hybrid_matcher.find_top_matches(session=self.db, incentive_id=incentive.incentive_id, limit=5)
                
                if matches:
                    logger.info(f"📋 INCENTIVO: {incentive.title[:80]}...")
                    logger.info(f"🎯 Top {len(matches)} matches encontrados:")
                    
                    for j, match in enumerate(matches, 1):
                        company_name = match['company_name']
                        total_score = match['total_score']
                        semantic_score = match['semantic_similarity']
                        unified_score = match['unified_score']
                        llm_score = match['llm_score']
                        
                        logger.info(f"   {j}. {company_name[:50]}...")
                        logger.info(f"      🧠 Semântica: {semantic_score:.3f}")
                        logger.info(f"      📊 Unificado: {unified_score}")
                        logger.info(f"      🤖 LLM: {llm_score:.3f}")
                        logger.info(f"      🎯 Total: {total_score:.3f}")
                        logger.info(f"      🏷️ CAE: {match['cae_primary_label']}")
                    
                    logger.info("─" * 80)
                    self.stats['matches_generated'] += len(matches)
                else:
                    logger.warning(f"⚠️ Nenhum match encontrado para incentivo {i}")
                
            except Exception as e:
                logger.error(f"❌ Erro no matching para incentivo {i}: {e}")
                continue
    
    def run_corrected_test(self):
        """Executa teste corrigido"""
        logger.info("🚀 INICIANDO TESTE CORRIGIDO END-TO-END")
        logger.info("=" * 80)
        
        self.stats['start_time'] = time.time()
        
        try:
            # 1. Carregar dados
            incentives_data, companies_data = self.load_data_from_csv()
            
            # 2. Criar tabelas
            self.create_database_tables()
            
            # 3. Popular incentivos
            incentive_ids = self.populate_incentives(incentives_data)
            
            # 4. Popular empresas COM dados inferidos
            company_ids = self.populate_companies(companies_data)
            
            # 5. Popular base vectorial
            self.populate_vector_database(incentive_ids, company_ids)
            
            # 6. 🔧 TESTE ESPECÍFICO: Scoring unificado
            if incentive_ids and company_ids:
                self.test_unified_scoring(incentive_ids[0], company_ids)
            
            # 7. Executar matching híbrido
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
        logger.info("📊 RESUMO FINAL DO TESTE CORRIGIDO")
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
        logger.info(f"   Total: ${total_cost:.6f}")
        logger.info(f"   Limite: ${self.cost_limit:.3f}")
        logger.info(f"   Economia: ${self.cost_limit - total_cost:.3f}")
        logger.info("")
        
        # Breakdown por operação
        logger.info("📈 BREAKDOWN POR OPERAÇÃO:")
        for op_data in final_stats['by_operation']:
            operation = op_data['operation']
            cost = op_data['cost']
            logger.info(f"   {operation:<30}: ${cost:.6f}")
        logger.info("=" * 80)
        logger.info("✅ TESTE CORRIGIDO CONCLUÍDO!")

if __name__ == "__main__":
    tester = CorrectedEndToEndTester()
    tester.run_corrected_test()
