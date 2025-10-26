#!/usr/bin/env python3
"""
Teste Completo de Criação/Atualização da Base de Dados
Importa amostra de CSVs, processa com LLM e verifica campos completos
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.data_importer import DataImporter
from app.db.models import Incentive, Company, IncentiveMetadata, IncentiveCompanyMatch
import logging
import pandas as pd

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_database_creation():
    """Testa criação completa da base de dados com amostra dos CSVs"""
    
    print("🎯 TESTE COMPLETO DE CRIAÇÃO/ATUALIZAÇÃO DA BASE DE DADOS")
    print("=" * 70)
    
    # Configurações do teste
    SAMPLE_INCENTIVES = 5  # Número de incentivos para testar
    SAMPLE_COMPANIES = 20  # Número de empresas para testar
    
    print(f"📊 CONFIGURAÇÃO DO TESTE:")
    print(f"   Incentivos: {SAMPLE_INCENTIVES}")
    print(f"   Empresas: {SAMPLE_COMPANIES}")
    print()
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    data_importer = DataImporter()
    
    try:
        # 1. LIMPAR DADOS EXISTENTES (OPCIONAL)
        print("🧹 LIMPANDO DADOS EXISTENTES...")
        # Limpar na ordem correta para evitar foreign key constraints
        db.query(IncentiveCompanyMatch).delete()
        db.query(IncentiveMetadata).delete()
        db.query(Incentive).delete()
        db.query(Company).delete()
        db.commit()
        print("✅ Dados limpos!")
        print()
        
        # 2. IMPORTAR AMOSTRA DE INCENTIVOS
        print("📋 IMPORTANDO AMOSTRA DE INCENTIVOS...")
        print("-" * 40)
        
        incentives_csv = "/app/../data/incentives.csv"
        if not os.path.exists(incentives_csv):
            print(f"❌ Ficheiro {incentives_csv} não encontrado!")
            print("🔍 Tentando caminho alternativo...")
            incentives_csv = "/app/../data/sample_incentives.csv"
            if not os.path.exists(incentives_csv):
                print(f"❌ Ficheiro {incentives_csv} também não encontrado!")
                return
        
        df_incentives = pd.read_csv(incentives_csv)
        sample_incentives = df_incentives.head(SAMPLE_INCENTIVES)
        
        print(f"Processando {len(sample_incentives)} incentivos...")
        
        for i, row in sample_incentives.iterrows():
            try:
                # Tratar valores NaN
                def clean_value(value):
                    if pd.isna(value) or value == 'NaN':
                        return None
                    return value
                
                # Criar incentivo
                incentive = Incentive(
                    title=row['title'],
                    description=clean_value(row.get('description', '')),
                    document_urls=clean_value(row.get('document_urls', [])) or [],
                    publication_date=data_importer.parse_datetime(row.get('publication_date')),
                    start_date=data_importer.parse_datetime(row.get('start_date')),
                    end_date=data_importer.parse_datetime(row.get('end_date')),
                    total_budget=clean_value(row.get('total_budget')),
                    source_link=clean_value(row.get('source_link', ''))
                )
                
                db.add(incentive)
                db.flush()  # Para obter o ID
                
                # Criar metadata
                raw_data = row.to_dict()
                # Limpar valores NaN do raw_data
                for key, value in raw_data.items():
                    if pd.isna(value) or value == 'NaN':
                        raw_data[key] = None
                
                metadata = IncentiveMetadata(
                    incentive_id=incentive.incentive_id,
                    raw_csv_data=raw_data,
                    ai_processing_status='pending'
                )
                
                db.add(metadata)
                
                print(f"   ✅ {i+1}. {incentive.title[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Erro ao importar incentivo {i+1}: {e}")
                db.rollback()
                continue
        
        db.commit()
        print(f"✅ {len(sample_incentives)} incentivos importados!")
        print()
        
        # 3. PROCESSAR INCENTIVOS COM LLM
        print("🤖 PROCESSANDO INCENTIVOS COM LLM...")
        print("-" * 40)
        
        incentives = db.query(Incentive).all()
        processed_count = 0
        
        for incentive in incentives:
            try:
                metadata = incentive.incentive_metadata
                if not metadata:
                    continue
                
                print(f"Processando: {incentive.title[:50]}...")
                
                # Gerar AI description
                ai_description = ai_processor.generate_ai_description(incentive, metadata.raw_csv_data)
                
                if ai_description:
                    incentive.ai_description = ai_description
                    metadata.ai_processing_status = 'completed'
                    metadata.fields_completed_by_ai = list(ai_description.keys())
                    processed_count += 1
                    print(f"   ✅ AI Description gerada")
                else:
                    metadata.ai_processing_status = 'failed'
                    print(f"   ❌ Falha ao gerar AI Description")
                
            except Exception as e:
                print(f"   ❌ Erro ao processar {incentive.title[:30]}: {e}")
                continue
        
        db.commit()
        print(f"✅ {processed_count}/{len(incentives)} incentivos processados com LLM!")
        print()
        
        # 4. IMPORTAR AMOSTRA DE EMPRESAS
        print("🏢 IMPORTANDO AMOSTRA DE EMPRESAS...")
        print("-" * 40)
        
        companies_csv = "/app/../data/companies.csv"
        if not os.path.exists(companies_csv):
            print(f"❌ Ficheiro {companies_csv} não encontrado!")
            print("🔍 Tentando caminho alternativo...")
            companies_csv = "/app/../data/sample_companies.csv"
            if not os.path.exists(companies_csv):
                print(f"❌ Ficheiro {companies_csv} também não encontrado!")
                return
        
        df_companies = pd.read_csv(companies_csv)
        sample_companies = df_companies.head(SAMPLE_COMPANIES)
        
        print(f"Processando {len(sample_companies)} empresas...")
        
        for i, row in sample_companies.iterrows():
            try:
                company = Company(
                    company_name=row['company_name'],
                    cae_primary_label=row.get('cae_primary_label', ''),
                    trade_description_native=row.get('trade_description_native', ''),
                    website=row.get('website', '')
                )
                
                db.add(company)
                print(f"   ✅ {i+1}. {company.company_name[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Erro ao importar empresa {i+1}: {e}")
                continue
        
        db.commit()
        print(f"✅ {len(sample_companies)} empresas importadas!")
        print()
        
        # 5. PROCESSAR EMPRESAS COM LLM (INFERIR CAMPOS)
        print("🤖 PROCESSANDO EMPRESAS COM LLM...")
        print("-" * 40)
        
        companies = db.query(Company).all()
        processed_companies = 0
        
        for company in companies:
            try:
                print(f"Processando: {company.company_name[:50]}...")
                
                # Inferir dados da empresa usando LLM
                inferred_data = ai_processor.infer_company_data(company)
                
                if inferred_data:
                    company.cae_primary_code = inferred_data.get('cae_codes', [])
                    company.region = inferred_data.get('region', 'N/A')
                    company.company_size = inferred_data.get('size', 'N/A')
                    processed_companies += 1
                    print(f"   ✅ Dados inferidos: CAE={len(company.cae_primary_code)}, Região={company.region}, Tamanho={company.company_size}")
                else:
                    print(f"   ❌ Falha ao inferir dados")
                
            except Exception as e:
                print(f"   ❌ Erro ao processar {company.company_name[:30]}: {e}")
                continue
        
        db.commit()
        print(f"✅ {processed_companies}/{len(companies)} empresas processadas com LLM!")
        print()
        
        # 6. VERIFICAÇÃO FINAL DOS CAMPOS
        print("🔍 VERIFICAÇÃO FINAL DOS CAMPOS:")
        print("-" * 40)
        
        # Verificar incentivos
        incentives_with_ai = db.query(Incentive).filter(Incentive.ai_description.isnot(None)).count()
        total_incentives = db.query(Incentive).count()
        
        print(f"📋 INCENTIVOS:")
        print(f"   Total: {total_incentives}")
        print(f"   Com AI Description: {incentives_with_ai}")
        print(f"   Percentagem: {(incentives_with_ai/total_incentives)*100:.1f}%")
        
        # Verificar empresas
        companies_with_cae = db.query(Company).filter(Company.cae_primary_code.isnot(None)).count()
        companies_with_region = db.query(Company).filter(Company.region.isnot(None)).count()
        companies_with_size = db.query(Company).filter(Company.company_size.isnot(None)).count()
        companies_with_all = db.query(Company).filter(
            Company.cae_primary_code.isnot(None),
            Company.region.isnot(None),
            Company.company_size.isnot(None)
        ).count()
        total_companies = db.query(Company).count()
        
        print(f"🏢 EMPRESAS:")
        print(f"   Total: {total_companies}")
        print(f"   Com CAE codes: {companies_with_cae}")
        print(f"   Com região: {companies_with_region}")
        print(f"   Com tamanho: {companies_with_size}")
        print(f"   Com todos os campos: {companies_with_all}")
        print(f"   Percentagem completa: {(companies_with_all/total_companies)*100:.1f}%")
        
        # 7. MOSTRAR EXEMPLOS
        print("\n📊 EXEMPLOS DOS RESULTADOS:")
        print("-" * 40)
        
        # Exemplo de incentivo
        incentive_example = db.query(Incentive).filter(Incentive.ai_description.isnot(None)).first()
        if incentive_example:
            print(f"📋 INCENTIVO EXEMPLO:")
            print(f"   Título: {incentive_example.title}")
            ai_desc = incentive_example.ai_description
            print(f"   CAE Codes: {ai_desc.get('eligible_cae_codes', [])}")
            print(f"   Setores: {ai_desc.get('eligible_sectors', [])}")
            print(f"   Região: {ai_desc.get('target_region', 'N/A')}")
            print(f"   Tamanho: {ai_desc.get('target_company_size', 'N/A')}")
        
        # Exemplo de empresa
        company_example = db.query(Company).filter(
            Company.cae_primary_code.isnot(None),
            Company.region.isnot(None),
            Company.company_size.isnot(None)
        ).first()
        
        if company_example:
            print(f"\n🏢 EMPRESA EXEMPLO:")
            print(f"   Nome: {company_example.company_name}")
            print(f"   CAE Codes: {company_example.cae_primary_code}")
            print(f"   Região: {company_example.region}")
            print(f"   Tamanho: {company_example.company_size}")
        
        print("\n" + "=" * 70)
        print("🎯 CONCLUSÕES:")
        print("-" * 20)
        
        if incentives_with_ai == total_incentives:
            print("✅ Todos os incentivos têm AI Description completa")
        else:
            print(f"⚠️ {total_incentives - incentives_with_ai} incentivos sem AI Description")
        
        if companies_with_all == total_companies:
            print("✅ Todas as empresas têm campos LLM completos")
        else:
            print(f"⚠️ {total_companies - companies_with_all} empresas sem campos LLM completos")
        
        print(f"\n💰 Custo estimado: ~${(total_incentives + total_companies) * 0.0002:.4f}")
        print(f"⏱️ Tempo estimado: ~{(total_incentives + total_companies) * 2:.0f} segundos")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_complete_database_creation()
