#!/usr/bin/env python3
"""
Script de teste económico para sistema de matching.

Este script testa o sistema de matching com custos mínimos:
- Usa apenas scoring determinístico (sem LLM)
- Testa com sample pequeno
- Foca em validação funcional
"""

import sys
import os
import time
from datetime import datetime

# Adicionar o path da aplicação
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.db.models import Incentive, Company, IncentiveCompanyMatch
from sqlalchemy.orm import Session


def print_header():
    """Imprime cabeçalho do script"""
    print("=" * 80)
    print("💰 TESTE ECONÓMICO DE MATCHING")
    print("=" * 80)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Modo: Apenas scoring determinístico (sem LLM)")
    print("💡 Custo: $0.00")
    print()


def test_deterministic_matching(db: Session):
    """Testa matching apenas com scoring determinístico"""
    print_header()
    
    # Obter primeiro incentivo
    incentive = db.query(Incentive).first()
    if not incentive:
        print("❌ Nenhum incentivo encontrado na base de dados!")
        return False
    
    print(f"🎯 Testando com incentivo: {incentive.title}")
    
    # Obter empresas (limitado para teste rápido)
    companies = db.query(Company).limit(10).all()
    if not companies:
        print("❌ Nenhuma empresa encontrada na base de dados!")
        return False
    
    print(f"🏢 Empresas candidatas: {len(companies)}")
    print()
    
    # Inicializar matcher SEM AI processor (modo determinístico)
    matcher = CompanyMatcherUnified(ai_processor=None)
    
    # Executar matching
    print("🔄 Executando matching determinístico...")
    start_time = time.time()
    
    try:
        company_ids = [str(c.company_id) for c in companies]
        matches = matcher.match_incentive_to_companies(
            str(incentive.incentive_id), 
            company_ids, 
            db
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Matching concluído em {duration:.2f} segundos")
        print(f"📊 Matches encontrados: {len(matches)}")
        print()
        
        # Mostrar resultados
        print("🏆 RESULTADOS DO MATCHING:")
        print("-" * 60)
        
        for i, match in enumerate(matches, 1):
            company = match['company']
            score = match['match_score']
            reasons = match['reasons']
            
            print(f"{i}. {company.company_name}")
            print(f"   CAE: {company.cae_primary_code}")
            print(f"   Setor: {company.cae_primary_label}")
            print(f"   Região: {company.region}")
            print(f"   Score: {score:.3f}")
            print(f"   Razões: {', '.join(reasons[:2])}")
            print()
        
        # Estatísticas
        print("📊 ESTATÍSTICAS:")
        print("-" * 30)
        
        if matches:
            scores = [m['match_score'] for m in matches]
            print(f"Score médio: {sum(scores) / len(scores):.3f}")
            print(f"Score máximo: {max(scores):.3f}")
            print(f"Score mínimo: {min(scores):.3f}")
        
        # Verificar se há empresas com CAE codes
        companies_with_cae = sum(1 for c in companies if c.cae_primary_code)
        print(f"Empresas com CAE code: {companies_with_cae}/{len(companies)}")
        
        # Verificar se há empresas com região
        companies_with_region = sum(1 for c in companies if c.region)
        print(f"Empresas com região: {companies_with_region}/{len(companies)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_quality(db: Session):
    """Testa qualidade dos dados"""
    print("\n" + "=" * 60)
    print("🔍 ANÁLISE DE QUALIDADE DOS DADOS")
    print("=" * 60)
    
    # Incentivos
    total_incentives = db.query(Incentive).count()
    incentives_with_ai_desc = db.query(Incentive).filter(
        Incentive.ai_description.isnot(None)
    ).count()
    
    print(f"📋 Incentivos:")
    print(f"   Total: {total_incentives}")
    print(f"   Com AI description: {incentives_with_ai_desc}")
    print(f"   Taxa de processamento: {(incentives_with_ai_desc / total_incentives * 100):.1f}%")
    
    # Empresas
    total_companies = db.query(Company).count()
    companies_with_cae = db.query(Company).filter(
        Company.cae_primary_code.isnot(None)
    ).count()
    companies_with_region = db.query(Company).filter(
        Company.region.isnot(None)
    ).count()
    
    print(f"\n🏢 Empresas:")
    print(f"   Total: {total_companies}")
    print(f"   Com CAE code: {companies_with_cae}")
    print(f"   Com região: {companies_with_region}")
    print(f"   Taxa CAE: {(companies_with_cae / total_companies * 100):.1f}%")
    print(f"   Taxa região: {(companies_with_region / total_companies * 100):.1f}%")
    
    # Matches existentes
    total_matches = db.query(IncentiveCompanyMatch).count()
    print(f"\n🎯 Matches:")
    print(f"   Total: {total_matches}")
    
    return True


def main():
    """Função principal"""
    print("🧪 TESTE ECONÓMICO DE MATCHING")
    print("   Este teste usa apenas scoring determinístico (custo: $0)")
    print()
    
    # Obter sessão da base de dados
    db = SessionLocal()
    
    try:
        # Verificar se há dados na base de dados
        total_incentives = db.query(Incentive).count()
        total_companies = db.query(Company).count()
        
        if total_incentives == 0:
            print("❌ Nenhum incentivo encontrado na base de dados!")
            print("   Execute primeiro: make setup-sample")
            return False
        
        if total_companies == 0:
            print("❌ Nenhuma empresa encontrada na base de dados!")
            print("   Execute primeiro: make setup-sample")
            return False
        
        # Executar testes
        success1 = test_deterministic_matching(db)
        success2 = test_data_quality(db)
        
        print("\n" + "=" * 80)
        if success1 and success2:
            print("🎉 TESTE ECONÓMICO CONCLUÍDO COM SUCESSO!")
            print("✅ Sistema de matching funcionando corretamente")
            print("💰 Custo total: $0.00")
        else:
            print("❌ TESTE ECONÓMICO FALHOU!")
            print("   Verifique os erros acima")
        
        return success1 and success2
        
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
