#!/usr/bin/env python3
"""
Importar Amostra de Dados

Importa apenas N incentiv os e M empresas dos CSVs para testes rápidos.

Uso:
    python import_sample_data.py [num_incentives] [num_companies]
    
Exemplo:
    python import_sample_data.py 10 1000
"""

import sys
import os

# Adicionar path do app
sys.path.insert(0, '/app')

import pandas as pd
from app.db.database import SessionLocal
from app.db.models import Incentive, Company, IncentiveMetadata, IncentiveCompanyMatch
from app.services.data_importer import DataImporter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_sample_data(num_incentives: int = 10, num_companies: int = 1000):
    """Importa amostra de dados para testes"""
    
    db = SessionLocal()
    
    try:
        # Limpar BD existente
        logger.info("🧹 Limpando dados existentes...")
        db.query(IncentiveCompanyMatch).delete()
        db.query(IncentiveMetadata).delete()
        db.query(Incentive).delete()
        db.query(Company).delete()
        db.commit()
        logger.info("✅ BD limpa")
        
        # Importar incentivos
        logger.info(f"📥 Importando {num_incentives} incentiv os...")
        df_inc = pd.read_csv('/data/incentives.csv')
        sample_inc = df_inc.head(num_incentives)
        
        for _, row in sample_inc.iterrows():
            incentive = Incentive(
                title=row.get('title', ''),
                description=row.get('description', ''),
                ai_description=row.get('ai_description'),
                document_urls=row.get('document_urls'),
                publication_date=pd.to_datetime(row.get('date_publication')) if pd.notna(row.get('date_publication')) else None,
                start_date=pd.to_datetime(row.get('date_start')) if pd.notna(row.get('date_start')) else None,
                end_date=pd.to_datetime(row.get('date_end')) if pd.notna(row.get('date_end')) else None,
                total_budget=float(row.get('total_budget', 0)) if pd.notna(row.get('total_budget')) else None,
                source_link=row.get('source_link', '')
            )
            db.add(incentive)
            
            # Criar metadata
            metadata = IncentiveMetadata(
                incentive=incentive,
                raw_csv_data=row.to_dict(),
                ai_processing_status='pending'
            )
            db.add(metadata)
            
        db.commit()
        logger.info(f"✅ {len(sample_inc)} incentiv os importados")
        
        # Importar empresas
        logger.info(f"📥 Importando {num_companies} empresas...")
        df_comp = pd.read_csv('/data/companies.csv')
        sample_comp = df_comp.head(num_companies)
        
        for _, row in sample_comp.iterrows():
            company = Company(
                company_name=row.get('company_name', ''),
                cae_primary_label=row.get('cae_primary_label', ''),
                trade_description_native=row.get('trade_description_native', ''),
                website=row.get('website', ''),
                cae_primary_code=row.get('cae_primary_code')
            )
            db.add(company)
            
        db.commit()
        logger.info(f"✅ {len(sample_comp)} empresas importadas")
        
        # Estatísticas
        total_inc = db.query(Incentive).count()
        total_comp = db.query(Company).count()
        
        logger.info(f"\n🎉 Total importado:")
        logger.info(f"   • {total_inc} incentiv os")
        logger.info(f"   • {total_comp} empresas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar dados: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Ler argumentos
    num_inc = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    num_comp = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    logger.info(f"🚀 Importando amostra: {num_inc} incentiv os + {num_comp} empresas")
    
    success = import_sample_data(num_inc, num_comp)
    
    if success:
        logger.info("\n✅ Importação concluída!")
    else:
        logger.error("\n❌ Importação falhou!")
        sys.exit(1)
