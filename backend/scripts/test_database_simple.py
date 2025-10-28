#!/usr/bin/env python3
"""
Script de teste simples para verificar se a base de dados está funcionando
"""

import sys
import os
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Incentive, Company
import time

def test_database():
    """Testa se a base de dados está funcionando"""
    print("🔍 Testando conexão com a base de dados...")
    
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
        print(f"🎯 Primeiro incentivo: {incentive.title}")
        
        # Obter as primeiras 10 empresas
        companies = db.query(Company).limit(10).all()
        print(f"🏢 Primeiras 10 empresas:")
        for i, company in enumerate(companies, 1):
            print(f"   {i}. {company.company_name}")
        
        print("✅ Base de dados funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database()
    if success:
        print("\n🎉 Sistema básico funcionando!")
    else:
        print("\n💥 Sistema com problemas!")
        sys.exit(1)
