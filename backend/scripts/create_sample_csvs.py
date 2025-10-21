"""
Script para criar CSVs de sample pequenos para testes.
Extrai 10-20 linhas dos CSVs completos.

CUSTO: $0 (não usa API)
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_sample_csvs(num_samples: int = 20):
    """
    Cria CSVs de sample a partir dos ficheiros completos.
    
    Args:
        num_samples: Número de linhas a extrair (default: 20)
    """
    
    # Paths
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    incentives_path = os.path.join(data_dir, 'incentives.csv')
    companies_path = os.path.join(data_dir, 'companies.csv')
    
    sample_incentives_path = os.path.join(data_dir, 'sample_incentives.csv')
    sample_companies_path = os.path.join(data_dir, 'sample_companies.csv')
    
    print(f"📂 Data directory: {data_dir}")
    print(f"📄 Reading from: {incentives_path}")
    print(f"📄 Reading from: {companies_path}")
    
    # Check if files exist
    if not os.path.exists(incentives_path):
        print(f"❌ ERROR: {incentives_path} not found!")
        print(f"   Please ensure incentives.csv is in {data_dir}")
        return False
    
    if not os.path.exists(companies_path):
        print(f"❌ ERROR: {companies_path} not found!")
        print(f"   Please ensure companies.csv is in {data_dir}")
        return False
    
    try:
        # Read incentives
        print(f"\n📊 Reading incentives.csv...")
        df_incentives = pd.read_csv(incentives_path)
        total_incentives = len(df_incentives)
        print(f"   Total incentives: {total_incentives}")
        
        # Read companies
        print(f"📊 Reading companies.csv...")
        df_companies = pd.read_csv(companies_path)
        total_companies = len(df_companies)
        print(f"   Total companies: {total_companies}")
        
        # Create samples with variety
        print(f"\n🎲 Creating samples with {num_samples} entries each...")
        
        # Sample incentives - get variety (some with ai_description, some without)
        # Try to get a mix
        sample_incentives = df_incentives.sample(n=min(num_samples, total_incentives), random_state=42)
        
        # Sample companies
        sample_companies = df_companies.sample(n=min(num_samples, total_companies), random_state=42)
        
        # Save samples
        print(f"\n💾 Saving sample files...")
        sample_incentives.to_csv(sample_incentives_path, index=False)
        print(f"   ✅ Created: {sample_incentives_path}")
        print(f"      Rows: {len(sample_incentives)}")
        
        sample_companies.to_csv(sample_companies_path, index=False)
        print(f"   ✅ Created: {sample_companies_path}")
        print(f"      Rows: {len(sample_companies)}")
        
        # Analysis of sample
        print(f"\n📋 Sample Analysis:")
        print(f"   Incentives with ai_description: {sample_incentives['ai_description'].notna().sum()}")
        print(f"   Incentives without ai_description: {sample_incentives['ai_description'].isna().sum()}")
        print(f"   Incentives with dates: {sample_incentives['date_start'].notna().sum()}")
        print(f"   Incentives with budget: {sample_incentives['total_budget'].notna().sum()}")
        
        print(f"\n✅ Sample CSVs created successfully!")
        print(f"\n📝 Next steps:")
        print(f"   1. Apply migrations: cd backend && alembic upgrade head")
        print(f"   2. Import samples: curl -X POST 'http://localhost:8000/data/import?incentives_file=sample_incentives.csv&companies_file=sample_companies.csv'")
        print(f"   3. Validate import: python scripts/validate_import.py")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create sample CSV files for testing')
    parser.add_argument('--num-samples', type=int, default=20, 
                       help='Number of samples to extract (default: 20)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("CREATE SAMPLE CSVs FOR TESTING")
    print("="*60)
    print(f"Sample size: {args.num_samples} entries")
    print(f"Cost: $0 (no API calls)")
    print("="*60)
    
    success = create_sample_csvs(args.num_samples)
    
    sys.exit(0 if success else 1)


