"""
Script para validar a importação de dados.
Verifica estrutura das tabelas e dados importados.

CUSTO: $0 (não usa API)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, engine
from app.db.models import Incentive, IncentiveMetadata, Company
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportValidator:
    def __init__(self):
        self.session = SessionLocal()
        self.inspector = inspect(engine)
        self.errors = []
        self.warnings = []
        self.successes = []
    
    def validate_all(self):
        """Run all validation checks"""
        logger.info("="*60)
        logger.info("IMPORT VALIDATION")
        logger.info("="*60)
        
        self.check_tables_exist()
        self.validate_incentives_data()
        self.validate_metadata_data()
        self.validate_companies_data()
        self.validate_relationships()
        self.validate_data_types()
        
        self.print_results()
    
    def check_tables_exist(self):
        """Verify all required tables exist"""
        logger.info("\n[1/6] Checking tables...")
        
        tables = self.inspector.get_table_names()
        required = ['incentives', 'incentives_metadata', 'companies']
        
        for table in required:
            if table in tables:
                self.successes.append(f"✅ Table '{table}' exists")
            else:
                self.errors.append(f"❌ Table '{table}' NOT FOUND")
    
    def validate_incentives_data(self):
        """Validate incentives table data"""
        logger.info("\n[2/6] Validating incentives data...")
        
        count = self.session.query(Incentive).count()
        
        if count == 0:
            self.errors.append("❌ No incentives imported!")
            return
        
        self.successes.append(f"✅ Found {count} incentives")
        
        # Check required fields
        incentive = self.session.query(Incentive).first()
        
        if incentive.title:
            self.successes.append(f"  ✅ Sample title: '{incentive.title[:50]}...'")
        else:
            self.errors.append("  ❌ Title is empty!")
        
        # Check data types
        if incentive.ai_description:
            if isinstance(incentive.ai_description, dict):
                self.successes.append(f"  ✅ ai_description is JSON (dict)")
            else:
                self.warnings.append(f"  ⚠️  ai_description is {type(incentive.ai_description)}, expected dict")
        
        if incentive.document_urls:
            if isinstance(incentive.document_urls, (list, dict)):
                self.successes.append(f"  ✅ document_urls is JSON")
            else:
                self.warnings.append(f"  ⚠️  document_urls type: {type(incentive.document_urls)}")
        
        # Count fields that need AI
        needs_ai = self.session.query(Incentive).filter(
            Incentive.ai_description.is_(None)
        ).count()
        
        self.successes.append(f"  ✅ Incentives needing ai_description: {needs_ai}")
        
        # Count with dates
        with_dates = self.session.query(Incentive).filter(
            Incentive.start_date.isnot(None)
        ).count()
        
        self.successes.append(f"  ✅ Incentives with dates: {with_dates}/{count}")
    
    def validate_metadata_data(self):
        """Validate metadata table data"""
        logger.info("\n[3/6] Validating metadata...")
        
        count = self.session.query(IncentiveMetadata).count()
        incentives_count = self.session.query(Incentive).count()
        
        if count == 0:
            self.errors.append("❌ No metadata imported!")
            return
        
        self.successes.append(f"✅ Found {count} metadata records")
        
        # Check 1:1 relationship
        if count == incentives_count:
            self.successes.append(f"  ✅ 1:1 relationship OK ({count} incentives = {count} metadata)")
        else:
            self.errors.append(f"  ❌ Relationship broken: {incentives_count} incentives vs {count} metadata")
        
        # Check raw_csv_data
        metadata = self.session.query(IncentiveMetadata).first()
        
        if metadata.raw_csv_data:
            if isinstance(metadata.raw_csv_data, dict):
                self.successes.append(f"  ✅ raw_csv_data is JSON (dict)")
                
                # Check it has expected fields
                expected_fields = ['incentive_project_id', 'project_id', 'incentive_program', 
                                 'status', 'all_data']
                found_fields = [f for f in expected_fields if f in metadata.raw_csv_data]
                
                self.successes.append(f"  ✅ raw_csv_data has {len(found_fields)}/{len(expected_fields)} expected fields")
                
                # Check it's NOT duplicated (should have ~9 fields, not 18+)
                num_fields = len(metadata.raw_csv_data.keys())
                if num_fields <= 12:
                    self.successes.append(f"  ✅ No duplication detected ({num_fields} fields)")
                else:
                    self.warnings.append(f"  ⚠️  Possible duplication ({num_fields} fields, expected ~9)")
            else:
                self.errors.append(f"  ❌ raw_csv_data is {type(metadata.raw_csv_data)}, expected dict")
        else:
            self.errors.append("  ❌ raw_csv_data is empty!")
        
        # Check processing status
        pending = self.session.query(IncentiveMetadata).filter(
            IncentiveMetadata.ai_processing_status == "pending"
        ).count()
        
        completed = self.session.query(IncentiveMetadata).filter(
            IncentiveMetadata.ai_processing_status == "completed"
        ).count()
        
        self.successes.append(f"  ✅ Status: {pending} pending, {completed} completed")
    
    def validate_companies_data(self):
        """Validate companies table data"""
        logger.info("\n[4/6] Validating companies...")
        
        count = self.session.query(Company).count()
        
        if count == 0:
            self.warnings.append("⚠️  No companies imported")
            return
        
        self.successes.append(f"✅ Found {count} companies")
        
        company = self.session.query(Company).first()
        
        if company.company_name:
            self.successes.append(f"  ✅ Sample: '{company.company_name[:50]}...'")
        
        # Check new fields
        if hasattr(company, 'cae_primary_code'):
            self.successes.append(f"  ✅ cae_primary_code field exists")
        else:
            self.warnings.append(f"  ⚠️  cae_primary_code field missing (need migration?)")
        
        if hasattr(company, 'updated_at'):
            self.successes.append(f"  ✅ updated_at field exists")
        else:
            self.warnings.append(f"  ⚠️  updated_at field missing (need migration?)")
    
    def validate_relationships(self):
        """Validate foreign key relationships"""
        logger.info("\n[5/6] Validating relationships...")
        
        # Test JOIN
        try:
            result = self.session.query(Incentive, IncentiveMetadata)\
                .join(IncentiveMetadata)\
                .first()
            
            if result:
                incentive, metadata = result
                self.successes.append(f"✅ JOIN works: incentive '{incentive.title[:30]}...' has metadata")
            else:
                self.warnings.append("⚠️  JOIN returned no results")
        except Exception as e:
            self.errors.append(f"❌ JOIN failed: {e}")
        
        # Check orphans
        orphan_metadata = self.session.query(IncentiveMetadata)\
            .outerjoin(Incentive)\
            .filter(Incentive.incentive_id.is_(None))\
            .count()
        
        if orphan_metadata == 0:
            self.successes.append("  ✅ No orphan metadata (all linked to incentives)")
        else:
            self.errors.append(f"  ❌ Found {orphan_metadata} orphan metadata records!")
    
    def validate_data_types(self):
        """Validate data types are correct"""
        logger.info("\n[6/6] Validating data types...")
        
        incentive = self.session.query(Incentive).first()
        
        # Check JSON fields
        if incentive.ai_description is not None:
            if isinstance(incentive.ai_description, dict):
                self.successes.append("  ✅ ai_description is dict (JSON)")
            else:
                self.errors.append(f"  ❌ ai_description is {type(incentive.ai_description)}")
        
        if incentive.document_urls is not None:
            if isinstance(incentive.document_urls, (list, dict)):
                self.successes.append("  ✅ document_urls is JSON")
            else:
                self.errors.append(f"  ❌ document_urls is {type(incentive.document_urls)}")
        
        # Check datetime fields
        if incentive.start_date is not None:
            from datetime import datetime
            if isinstance(incentive.start_date, datetime):
                self.successes.append("  ✅ start_date is datetime")
            else:
                self.errors.append(f"  ❌ start_date is {type(incentive.start_date)}")
        
        # Check numeric fields
        if incentive.total_budget is not None:
            from decimal import Decimal
            if isinstance(incentive.total_budget, (Decimal, float, int)):
                self.successes.append("  ✅ total_budget is numeric")
            else:
                self.errors.append(f"  ❌ total_budget is {type(incentive.total_budget)}")
    
    def print_results(self):
        """Print validation results"""
        logger.info("\n" + "="*60)
        logger.info("VALIDATION RESULTS")
        logger.info("="*60)
        
        print("\n✅ SUCCESSES:")
        for success in self.successes:
            print(f"  {success}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n" + "="*60)
        print(f"SUMMARY: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("="*60)
        
        if self.errors:
            print("\n❌ VALIDATION FAILED - Fix errors before proceeding")
            return False
        elif self.warnings:
            print("\n⚠️  VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print("\n✅ VALIDATION PASSED - All checks successful!")
            return True


if __name__ == "__main__":
    validator = ImportValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


