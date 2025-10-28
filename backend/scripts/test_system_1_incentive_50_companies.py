#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema está funcionando
com 1 incentivo e 50 empresas
"""

import sys
import os
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.db.models import Incentive, Company
from sqlalchemy.orm import Session
import time

def test_system():
    """Testa o sistema com 1 incentivo e 50 empresas"""
    print("🔍 Testando sistema com 1 incentivo e 50 empresas...")
    
    # Obter sessão da base de dados
    db = SessionLocal()
    
    try:
        # Verificar se existem incentivos e empresas na base de dados
        incentive_count = db.query(Incentive).count()
        company_count = db.query(Company).count()
        
        print(f"📊 Base de dados:")
        print(f"   - Incentivos: {incentive_count}")
        print(f"   - Empresas: {company_count}")
        
        if incentive_count == 0:
            print("❌ Não existem incentivos na base de dados!")
            return False
            
        if company_count == 0:
            print("❌ Não existem empresas na base de dados!")
            return False
        
        # Obter o primeiro incentivo
        incentive = db.query(Incentive).first()
        print(f"🎯 Incentivo selecionado: {incentive.title}")
        
        # Obter as primeiras 50 empresas
        companies = db.query(Company).limit(50).all()
        print(f"🏢 Empresas selecionadas: {len(companies)}")
        
        # Inicializar o matcher
        print("⚙️ Inicializando CompanyMatcherUnified...")
        matcher = CompanyMatcherUnified()
        
        # Testar matching
        print("🔄 Executando matching...")
        start_time = time.time()
        
        matches = matcher.match_incentive_to_companies(
            incentive_id=incentive.id,
            company_ids=[c.id for c in companies],
            db=db
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Matching concluído em {duration:.2f} segundos")
        print(f"📈 Matches encontrados: {len(matches)}")
        
        if matches:
            print("\n🏆 Top 5 matches:")
            for i, match in enumerate(matches[:5], 1):
                company = next(c for c in companies if c.id == match.company_id)
                print(f"   {i}. {company.name} - Score: {match.score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_system()
    if success:
        print("\n🎉 Sistema funcionando corretamente!")
    else:
        print("\n💥 Sistema com problemas!")
        sys.exit(1)
