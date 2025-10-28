#!/usr/bin/env python3
"""
Setup Completo do Sistema para Avaliador
==========================================

Este script executa o pipeline completo do sistema:
1. Limpa e recria a base de dados
2. Importa dados dos CSVs
3. INFERE DADOS com AI (incentivos e empresas)
4. Gera embeddings
5. Executa matching
6. Sistema pronto com chatbot disponível

Uso:
    python setup_full_system_for_evaluator.py [num_incentives] [num_companies]
    
Exemplo para demo completa:
    python setup_full_system_for_evaluator.py 50 200

Exemplo para teste rápido:
    python setup_full_system_for_evaluator.py 5 50
"""

import pandas as pd
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import uuid
import sys
import os

# Adicionar path do app
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Incentive, Company, IncentiveMetadata, IncentiveCompanyMatch
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from app.services.hybrid_matching_service import HybridMatchingService
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullSystemSetup:
    """Setup completo do sistema para avaliador"""
    
    def __init__(self, num_incentives: int = 50, num_companies: int = 200):
        self.db = SessionLocal()
        self.num_incentives = num_incentives
        self.num_companies = num_companies
        
        # Carregar variáveis do .env
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
        
        # Estatísticas
        self.stats = {
            'incentives_processed': 0,
            'companies_processed': 0,
            'matches_generated': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("🚀 Full System Setup inicializado")
        logger.info(f"📊 Configurado para: {num_incentives} incentivos + {num_companies} empresas")
    
    def clean_value(self, value):
        """Limpa valores NaN do pandas"""
        if pd.isna(value) or value is None:
            return None
        return value
    
    def load_data_from_csv(self) -> tuple[List[Dict], List[Dict]]:
        """Carrega dados dos CSVs"""
        logger.info("📂 Carregando dados dos CSVs...")
        try:
            incentives_df = pd.read_csv('/data/incentives.csv')
            logger.info(f"📊 Incentivos no CSV: {len(incentives_df)}")
            
            companies_df = pd.read_csv('/data/companies.csv')
            logger.info(f"📊 Empresas no CSV: {len(companies_df)}")
            
            # Amostra baseada em configuração
            sample_incentives = incentives_df.sample(n=min(self.num_incentives, len(incentives_df)), random_state=42)
            sample_companies = companies_df.sample(n=min(self.num_companies, len(companies_df)), random_state=42)
            
            logger.info(f"🎯 Amostra selecionada: {len(sample_incentives)} incentivos, {len(sample_companies)} empresas")
            return sample_incentives.to_dict('records'), sample_companies.to_dict('records')
        except Exception as e:
            logger.error(f"❌ Erro ao carregar CSVs: {e}")
            raise
    
    def create_database_tables(self):
        """Limpa e cria tabelas da base de dados"""
        logger.info("🧹 Limpando e recriando base de dados...")
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
    
    def populate_incentives_with_ai(self, incentives_data: List[Dict]) -> List[str]:
        """Popula incentivos na base de dados com AI description"""
        logger.info("📝 Populando incentivos na base de dados com AI...")
        
        incentive_ids = []
        
        for i, incentive_data in enumerate(incentives_data, 1):
            try:
                # Criar incentivo
                incentive = Incentive(
                    incentive_id=uuid.uuid4(),
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
                    logger.info(f"✅ AI description gerada para incentivo {i}")
                else:
                    logger.warning(f"⚠️ Falha ao gerar AI description para incentivo {i}")
                
                incentive_ids.append(incentive.incentive_id)
                self.stats['incentives_processed'] += 1
                
                # Log de progresso
                if i % 10 == 0:
                    logger.info(f"📊 Progresso: {i}/{len(incentives_data)} incentivos processados")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar incentivo {i}: {e}")
                continue
        
        logger.info(f"✅ {len(incentive_ids)} incentivos processados com AI")
        return incentive_ids
    
    def populate_companies_with_ai(self, companies_data: List[Dict]) -> List[str]:
        """Cria empresas novas com dados AI inferidos"""
        logger.info("🏢 Criando empresas com dados AI inferidos...")
        
        company_ids = []
        
        for i, company_data in enumerate(companies_data, 1):
            try:
                # Criar empresa
                company = Company(
                    company_id=uuid.uuid4(),
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
                logger.info(f"🤖 Inferindo dados para empresa {i}/{len(companies_data)}: {company.company_name[:50]}...")
                
                try:
                    inferred_data = self.ai_processor.infer_company_data(company)
                    if inferred_data:
                        company.cae_primary_code = inferred_data.get('cae_codes', [])
                        company.region = inferred_data.get('region', 'N/A')
                        company.company_size = inferred_data.get('size', 'N/A')
                        self.db.commit()
                        logger.info(f"✅ Dados inferidos para empresa {i}: CAE={len(company.cae_primary_code)}, Região={company.region}, Tamanho={company.company_size}")
                    else:
                        logger.warning(f" Falha ao inferir dados para empresa {i}")
                except Exception as e:
                    logger.error(f"❌ Erro ao inferir dados para empresa {i}: {e}")
                
                company_ids.append(str(company.company_id))
                self.stats['companies_processed'] += 1
                
                # Log de progresso
                if i % 10 == 0:
                    logger.info(f"📊 Progresso: {i}/{len(companies_data)} empresas processadas")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar empresa {i}: {e}")
                continue
        
        logger.info(f"✅ {len(company_ids)} empresas processadas com AI")
        return company_ids
    
    def populate_vector_database(self, incentive_ids: List[str], company_ids: List[str]):
        """Popula base de dados vectorial"""
        logger.info("🧠 Populando base de dados vectorial...")
        logger.info(f"   Empresas a processar: {len(company_ids)}")
        logger.info(f"   Incentivos a processar: {len(incentive_ids)}")
        
        companies_embeddings_created = 0
        incentives_embeddings_created = 0
        
        # Gerar embeddings para empresas
        companies = self.db.query(Company).filter(Company.company_id.in_(company_ids)).all()
        logger.info(f"📊 Gerando embeddings para {len(companies)} empresas...")
        
        for i, company in enumerate(companies, 1):
            try:
                success = self.vector_db.add_company_embedding(company)
                if success:
                    companies_embeddings_created += 1
                    if i % 100 == 0:
                        logger.info(f"   Progresso empresas: {i}/{len(companies)} embeddings criados")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding para empresa {i}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"✅ Empresas: {companies_embeddings_created}/{len(companies)} embeddings criados")
        
        # Gerar embeddings para incentivos
        incentives = self.db.query(Incentive).filter(Incentive.incentive_id.in_(incentive_ids)).all()
        logger.info(f"📊 Gerando embeddings para {len(incentives)} incentivos...")
        
        for i, incentive in enumerate(incentives, 1):
            try:
                success = self.vector_db.add_incentive_embedding(incentive)
                if success:
                    incentives_embeddings_created += 1
                    if i % 10 == 0:
                        logger.info(f"   Progresso incentivos: {i}/{len(incentives)} embeddings criados")
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar embedding para incentivo {i}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"✅ Incentivos: {incentives_embeddings_created}/{len(incentives)} embeddings criados")
        
        # Verificar quantidade real de embeddings no ChromaDB
        try:
            companies_count = self.vector_db.companies_collection.count()
            incentives_count = self.vector_db.incentives_collection.count()
            logger.info(f"📊 VERIFICAÇÃO FINAL:")
            logger.info(f"   Embeddings de empresas no ChromaDB: {companies_count}")
            logger.info(f"   Embeddings de incentivos no ChromaDB: {incentives_count}")
            logger.info(f"   Total: {companies_count + incentives_count}")
        except Exception as e:
            logger.error(f"❌ Erro ao verificar embeddings no ChromaDB: {e}")
        
        logger.info("✅ Base de dados vectorial populada")
    
    def run_hybrid_matching(self, incentive_ids: List[str]):
        """Executa matching híbrido e salva na base de dados"""
        logger.info("🎯 Executando matching híbrido...")
        
        incentives = self.db.query(Incentive).filter(Incentive.incentive_id.in_(incentive_ids)).all()
        
        for i, incentive in enumerate(incentives, 1):
            logger.info(f"🔍 Matching {i}/{len(incentives)}: {incentive.incentive_id}")
            
            try:
                matches = self.hybrid_matcher.find_top_matches(
                    session=self.db, 
                    incentive_id=incentive.incentive_id, 
                    limit=10  # Top 10 matches por incentivo
                )
                
                if matches:
                    logger.info(f"🎯 {len(matches)} matches encontrados para {incentive.title[:50]}...")
                    
                    # 🔧 SALVAR MATCHES NA BASE DE DADOS
                    # Limpar matches existentes para este incentivo
                    self.db.query(IncentiveCompanyMatch).filter(
                        IncentiveCompanyMatch.incentive_id == incentive.incentive_id
                    ).delete()
                    
                    # Salvar novos matches
                    for rank, match in enumerate(matches, 1):
                        # Extrair company_id (pode ser objeto Company ou ID string)
                        company_id = match.get('company_id')
                        if not company_id:
                            company = match.get('company')
                            if company:
                                company_id = company.company_id
                        
                        # ✅ VERIFICAR se empresa existe na BD antes de salvar
                        from app.db.models import Company
                        company_exists = self.db.query(Company).filter(Company.company_id == company_id).first()
                        if not company_exists:
                            continue
                        
                        match_record = IncentiveCompanyMatch(
                            incentive_id=incentive.incentive_id,
                            company_id=company_id,
                            match_score=match.get('total_score', match.get('llm_score', match.get('match_score', 0.0))),
                            match_reasons=match.get('reasons', match.get('match_reasons', [])),
                            ranking_position=rank
                        )
                        self.db.add(match_record)
                    
                    self.db.commit()
                    logger.info(f"✅ Salvos {len(matches)} matches na base de dados")
                    self.stats['matches_generated'] += len(matches)
                else:
                    logger.warning(f"⚠️ Nenhum match encontrado para incentivo {i}")
                
            except Exception as e:
                logger.error(f"❌ Erro no matching para incentivo {i}: {e}")
                self.db.rollback()
                continue
        
        logger.info(f"✅ Matching concluído: {self.stats['matches_generated']} matches salvos na BD")
    
    def print_costs_summary(self):
        """Imprime resumo de custos"""
        logger.info("💰 RESUMO DE CUSTOS:")
        logger.info("=" * 80)
        
        try:
            cost_stats = self.ai_processor.cost_tracker.get_total_stats()
            total_cost = cost_stats['all_time']['total_cost']
            
            logger.info(f"💰 CUSTO TOTAL: ${total_cost:.6f}")
            logger.info("")
            
            # Breakdown por operação
            if 'by_operation' in cost_stats:
                logger.info("📈 BREAKDOWN POR OPERAÇÃO:")
                for op_data in cost_stats['by_operation']:
                    operation = op_data['operation']
                    cost = op_data['cost']
                    logger.info(f"   {operation:<30}: ${cost:.6f}")
            
            logger.info("=" * 80)
        except Exception as e:
            logger.warning(f" Não foi possível obter estatísticas de custos: {e}")
    
    def run_complete_setup(self):
        """Executa setup completo do sistema"""
        logger.info("🚀 INICIANDO SETUP COMPLETO DO SISTEMA")
        logger.info("=" * 80)
        
        self.stats['start_time'] = time.time()
        
        try:
            # 1. Carregar dados
            incentives_data, companies_data = self.load_data_from_csv()
            
            # 2. Criar tabelas
            self.create_database_tables()
            
            # 3. Popular incentivos COM AI
            incentive_ids = self.populate_incentives_with_ai(incentives_data)
            
            # 4. Popular empresas COM dados AI inferidos
            company_ids = self.populate_companies_with_ai(companies_data)
            
            # 5. Popular base vectorial
            self.populate_vector_database(incentive_ids, company_ids)
            
            # 6. Executar matching híbrido
            self.run_hybrid_matching(incentive_ids)
            
        except Exception as e:
            logger.error(f"❌ ERRO NO SETUP: {e}")
            raise
        finally:
            self.stats['end_time'] = time.time()
            self.print_final_summary()
            self.db.close()
    
    def print_final_summary(self):
        """Imprime resumo final"""
        logger.info("")
        logger.info("📊 RESUMO FINAL DO SETUP")
        logger.info("=" * 80)
        
        total_time = self.stats['end_time'] - self.stats['start_time']
        logger.info(f"⏱️ Tempo total: {total_time:.2f}s")
        logger.info(f"📝 Incentivos processados: {self.stats['incentives_processed']}")
        logger.info(f"🏢 Empresas processadas: {self.stats['companies_processed']}")
        logger.info(f"🎯 Matches gerados: {self.stats['matches_generated']}")
        logger.info("")
        
        self.print_costs_summary()
        
        logger.info("")
        logger.info("✅ SISTEMA PRONTO PARA AVALIADOR!")
        logger.info("=" * 80)
        logger.info("🌐 Acesse a interface web: http://localhost:8000/web/")
        logger.info("📚 Documentação da API: http://localhost:8000/docs")
        logger.info("🤖 Chatbot API: http://localhost:8000/chatbot/")
        logger.info("")
        logger.info("💡 O chatbot permite:")
        logger.info("   - Obter informação sobre os incentivos")
        logger.info("   - Consultar dados sobre empresas")
        logger.info("   - Explorar as correspondências entre incentivos e empresas")
        logger.info("=" * 80)

if __name__ == "__main__":
    # Ler argumentos
    num_inc = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    num_comp = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    
    logger.info("")
    logger.info("🚀 SETUP COMPLETO DO SISTEMA PARA AVALIADOR")
    logger.info("=" * 80)
    logger.info(f"📊 Configuração: {num_inc} incentivos + {num_comp} empresas")
    logger.info("=" * 80)
    logger.info("")
    
    setup = FullSystemSetup(num_incentives=num_inc, num_companies=num_comp)
    setup.run_complete_setup()
