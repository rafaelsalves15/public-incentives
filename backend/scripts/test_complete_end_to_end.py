#!/usr/bin/env python3
"""
TESTE COMPLETO END-TO-END DO SISTEMA HÍBRIDO

Este script executa um teste completo do sistema:
1. Carrega 20 incentivos e 1000 empresas dos CSVs
2. Popula base de dados com ajuda de LLMs
3. Executa matching híbrido (embeddings + unified score + LLM)
4. Mostra top 5 empresas para cada incentivo
5. Monitoriza custos em tempo real (limite $2.00)

REQUISITOS:
- Executar dentro do Docker
- Usar data/incentives.csv e data/companies.csv
- Limite de custos: $2.00 USD
- Output detalhado para cada incentivo
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal, engine
from app.db.models import Base, Incentive, IncentiveMetadata, Company
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from app.services.hybrid_matching_service import HybridMatchingService
from app.services.unified_scorer import UnifiedScorer
import pandas as pd
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import random
import uuid
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndToEndTester:
    """Testador completo do sistema híbrido"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.cost_limit = 2.00  # Limite de $2.00 USD
        self.current_cost = 0.0
        
        # Inicializar serviços
        self.ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=self.db)
        self.embedding_service = EmbeddingService(api_key=os.getenv('OPENAI_API_KEY'), session=self.db)
        self.vector_db_service = VectorDatabaseService(self.embedding_service)
        self.hybrid_service = HybridMatchingService(
            self.ai_processor, 
            self.embedding_service, 
            self.vector_db_service
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
        
        logger.info("🚀 End-to-End Tester inicializado")
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
            logger.warning(f"⚠️ LIMITE DE CUSTOS ATINGIDO: ${self.current_cost:.6f} >= ${self.cost_limit}")
            return False
        
        remaining = self.cost_limit - self.current_cost
        logger.info(f"💰 Custo atual: ${self.current_cost:.6f} | Restante: ${remaining:.6f}")
        return True
    
    def load_data_from_csv(self) -> tuple[List[Dict], List[Dict]]:
        """Carrega dados dos CSVs"""
        logger.info("📂 Carregando dados dos CSVs...")
        
        try:
            # Carregar incentivos
            incentives_df = pd.read_csv('/data/incentives.csv')
            logger.info(f"📊 Incentivos carregados: {len(incentives_df)}")
            
            # Carregar empresas
            companies_df = pd.read_csv('/data/companies.csv')
            logger.info(f"📊 Empresas carregadas: {len(companies_df)}")
            
            # Selecionar amostras
            sample_incentives = incentives_df.sample(n=min(20, len(incentives_df)), random_state=42)
            sample_companies = companies_df.sample(n=min(1000, len(companies_df)), random_state=42)
            
            logger.info(f"🎯 Amostra selecionada: {len(sample_incentives)} incentivos, {len(sample_companies)} empresas")
            
            return sample_incentives.to_dict('records'), sample_companies.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSVs: {e}")
            raise
    
    def create_database_tables(self):
        """Cria tabelas da base de dados"""
        logger.info("🗄️ Criando tabelas da base de dados...")
        
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def populate_incentives(self, incentives_data: List[Dict]) -> List[str]:
        """Popula incentivos na base de dados com AI descriptions"""
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
                logger.info(f"🤖 Gerando AI description para incentivo {i}/{len(incentives_data)}: {incentive.title[:50]}...")
                
                ai_description = self.ai_processor.generate_ai_description(incentive, incentive_data)
                if ai_description:
                    incentive.ai_description = ai_description
                    self.db.commit()
                    logger.info(f"✅ AI description gerada para: {incentive.title[:50]}...")
                else:
                    logger.warning(f"⚠️ Falha ao gerar AI description para: {incentive.title[:50]}...")
                
                incentive_ids.append(str(incentive.incentive_id))
                self.stats['incentives_processed'] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar incentivo {i}: {e}")
                continue
        
        logger.info(f"✅ Incentivos processados: {len(incentive_ids)}")
        return incentive_ids
    
    def populate_companies(self, companies_data: List[Dict]) -> List[str]:
        """Popula empresas na base de dados"""
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
                
                # Inferir dados da empresa usando LLM
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
                
                if i % 100 == 0:  # Commit a cada 100 empresas
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
    
    def populate_vector_database(self):
        """Popula base de dados vectorial com embeddings"""
        logger.info("🧠 Populando base de dados vectorial...")
        
        # Resetar estatísticas de sessão
        self.ai_processor.cost_tracker.reset_session_stats()
        
        # Processar empresas
        companies = self.db.query(Company).limit(1000).all()
        logger.info(f"📊 Processando {len(companies)} empresas para embeddings...")
        
        for i, company in enumerate(companies, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando na população vectorial devido ao limite de custos")
                break
            
            try:
                success = self.vector_db_service.add_company_embedding(company)
                if success and i % 50 == 0:
                    logger.info(f"📊 Embeddings de empresas: {i}/{len(companies)}")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding da empresa {i}: {e}")
        
        # Processar incentivos
        incentives = self.db.query(Incentive).limit(20).all()
        logger.info(f"📊 Processando {len(incentives)} incentivos para embeddings...")
        
        for i, incentive in enumerate(incentives, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando na população vectorial devido ao limite de custos")
                break
            
            try:
                success = self.vector_db_service.add_incentive_embedding(incentive)
                if success:
                    logger.info(f"📊 Embeddings de incentivos: {i}/{len(incentives)}")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding do incentivo {i}: {e}")
        
        logger.info("✅ Base de dados vectorial populada")
    
    def run_hybrid_matching(self, incentive_ids: List[str]) -> Dict[str, List[Dict]]:
        """Executa matching híbrido para todos os incentivos"""
        logger.info("🎯 Executando matching híbrido...")
        
        results = {}
        
        for i, incentive_id in enumerate(incentive_ids, 1):
            if not self.check_cost_limit():
                logger.warning(f"⚠️ Parando no matching devido ao limite de custos")
                break
            
            try:
                logger.info(f"🔍 Matching {i}/{len(incentive_ids)}: {incentive_id}")
                
                # Resetar estatísticas de sessão para cada incentivo
                self.ai_processor.cost_tracker.reset_session_stats()
                
                # Executar matching híbrido
                matches = self.hybrid_service.find_top_matches(
                    session=self.db,
                    incentive_id=incentive_id,
                    limit=5,
                    use_hybrid=True
                )
                
                results[incentive_id] = matches
                self.stats['matches_generated'] += len(matches)
                
                # Mostrar resultados para este incentivo
                incentive = self.db.query(Incentive).filter(Incentive.incentive_id == incentive_id).first()
                if incentive:
                    logger.info(f"📋 INCENTIVO: {incentive.title[:60]}...")
                    logger.info(f"🎯 Top {len(matches)} matches encontrados:")
                    
                    for j, match in enumerate(matches, 1):
                        logger.info(f"  {j}. {match['company_name'][:50]}...")
                        logger.info(f"     🧠 Semântica: {match['semantic_similarity']:.3f}")
                        logger.info(f"     📊 Unificado: {match['unified_score']}")
                        logger.info(f"     🤖 LLM: {match['llm_score']:.3f}")
                        logger.info(f"     🎯 Total: {match['total_score']:.3f}")
                        logger.info(f"     🏷️ CAE: {match.get('cae_primary_label', 'N/A')}")
                
                logger.info("─" * 80)
                
            except Exception as e:
                logger.error(f"❌ Erro no matching do incentivo {incentive_id}: {e}")
                continue
        
        return results
    
    def print_final_summary(self, results: Dict[str, List[Dict]]):
        """Imprime resumo final do teste"""
        logger.info("📊 RESUMO FINAL DO TESTE END-TO-END")
        logger.info("=" * 80)
        
        # Estatísticas gerais
        final_stats = self.ai_processor.cost_tracker.get_total_stats()
        
        logger.info(f"⏱️ Tempo total: {self.stats['end_time'] - self.stats['start_time']:.2f}s")
        logger.info(f"📝 Incentivos processados: {self.stats['incentives_processed']}")
        logger.info(f"🏢 Empresas processadas: {self.stats['companies_processed']}")
        logger.info(f"🎯 Matches gerados: {self.stats['matches_generated']}")
        
        logger.info(f"\n💰 CUSTOS:")
        logger.info(f"   Total: ${final_stats['all_time']['total_cost']:.6f}")
        logger.info(f"   Limite: ${self.cost_limit:.6f}")
        logger.info(f"   Economia: ${self.cost_limit - final_stats['all_time']['total_cost']:.6f}")
        
        logger.info(f"\n📈 BREAKDOWN POR OPERAÇÃO:")
        for op in final_stats['by_operation']:
            logger.info(f"   {op['operation']:25}: ${op['cost']:.6f} ({op['calls']} chamadas)")
        
        # Resumo por incentivo
        logger.info(f"\n🎯 RESUMO POR INCENTIVO:")
        for incentive_id, matches in results.items():
            incentive = self.db.query(Incentive).filter(Incentive.incentive_id == incentive_id).first()
            if incentive:
                avg_score = sum(m['total_score'] for m in matches) / len(matches) if matches else 0
                logger.info(f"   {incentive.title[:50]}...")
                logger.info(f"     Matches: {len(matches)} | Score médio: {avg_score:.3f}")
        
        logger.info("=" * 80)
    
    def run_complete_test(self):
        """Executa o teste completo end-to-end"""
        logger.info("🚀 INICIANDO TESTE COMPLETO END-TO-END")
        logger.info("=" * 80)
        
        self.stats['start_time'] = time.time()
        
        try:
            # 1. Carregar dados
            incentives_data, companies_data = self.load_data_from_csv()
            
            # 2. Criar base de dados
            self.create_database_tables()
            
            # 3. Popular incentivos
            incentive_ids = self.populate_incentives(incentives_data)
            
            # 4. Popular empresas
            company_ids = self.populate_companies(companies_data)
            
            # 5. Popular base vectorial
            self.populate_vector_database()
            
            # 6. Executar matching híbrido
            results = self.run_hybrid_matching(incentive_ids)
            
            # 7. Resumo final
            self.stats['end_time'] = time.time()
            self.print_final_summary(results)
            
            logger.info("✅ TESTE COMPLETO CONCLUÍDO COM SUCESSO!")
            
        except Exception as e:
            logger.error(f"❌ ERRO NO TESTE: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.db.close()

def main():
    """Função principal"""
    tester = EndToEndTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()
