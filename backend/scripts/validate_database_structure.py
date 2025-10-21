"""
Validation script for 3-table database structure.

This script validates:
1. Table schemas match specifications
2. Relationships are correctly defined
3. Indexes are in place
4. Data integrity constraints work
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.db.database import engine, SessionLocal
from app.db.models import Incentive, IncentiveMetadata, Company
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseValidator:
    def __init__(self):
        self.session = SessionLocal()
        self.inspector = inspect(engine)
        self.errors = []
        self.warnings = []
        self.successes = []
    
    def validate_all(self):
        """Run all validation checks"""
        logger.info("=" * 60)
        logger.info("DATABASE STRUCTURE VALIDATION")
        logger.info("=" * 60)
        
        self.validate_tables_exist()
        self.validate_incentives_schema()
        self.validate_metadata_schema()
        self.validate_companies_schema()
        self.validate_relationships()
        self.validate_indexes()
        self.validate_data_integrity()
        
        self.print_results()
    
    def validate_tables_exist(self):
        """Check that all required tables exist"""
        logger.info("\n[1/7] Checking table existence...")
        
        tables = self.inspector.get_table_names()
        required_tables = ['incentives', 'incentives_metadata', 'companies']
        
        for table in required_tables:
            if table in tables:
                self.successes.append(f"✅ Table '{table}' exists")
            else:
                self.errors.append(f"❌ Table '{table}' NOT FOUND")
    
    def validate_incentives_schema(self):
        """Validate incentives table has EXACTLY 10 fields"""
        logger.info("\n[2/7] Validating 'incentives' schema...")
        
        columns = self.inspector.get_columns('incentives')
        column_names = [col['name'] for col in columns]
        
        # MUST have exactly 10 columns (as per enunciado)
        expected_columns = [
            'incentive_id',
            'title',
            'description',
            'ai_description',
            'document_urls',
            'publication_date',
            'start_date',
            'end_date',
            'total_budget',
            'source_link'
        ]
        
        if len(column_names) == 10:
            self.successes.append(f"✅ 'incentives' has EXACTLY 10 columns (as required)")
        else:
            self.errors.append(f"❌ 'incentives' has {len(column_names)} columns, expected 10")
        
        for col in expected_columns:
            if col in column_names:
                self.successes.append(f"  ✅ Column '{col}' exists")
            else:
                self.errors.append(f"  ❌ Column '{col}' NOT FOUND")
        
        # Should NOT have metadata columns
        forbidden_columns = [
            'raw_csv_data',
            'ai_processing_status',
            'ai_processing_date',
            'fields_completed_by_ai',
            'ai_processing_error',
            'created_at',
            'updated_at'
        ]
        
        for col in forbidden_columns:
            if col in column_names:
                self.errors.append(f"  ❌ Forbidden column '{col}' found in 'incentives'")
            else:
                self.successes.append(f"  ✅ Column '{col}' correctly NOT in 'incentives'")
    
    def validate_metadata_schema(self):
        """Validate incentives_metadata table schema"""
        logger.info("\n[3/7] Validating 'incentives_metadata' schema...")
        
        columns = self.inspector.get_columns('incentives_metadata')
        column_names = [col['name'] for col in columns]
        
        expected_columns = [
            'metadata_id',
            'incentive_id',
            'raw_csv_data',
            'ai_processing_status',
            'ai_processing_date',
            'fields_completed_by_ai',
            'ai_processing_error',
            'created_at',
            'updated_at'
        ]
        
        if len(column_names) == 9:
            self.successes.append(f"✅ 'incentives_metadata' has 9 columns (as designed)")
        else:
            self.warnings.append(f"⚠️  'incentives_metadata' has {len(column_names)} columns, expected 9")
        
        for col in expected_columns:
            if col in column_names:
                self.successes.append(f"  ✅ Column '{col}' exists")
            else:
                self.errors.append(f"  ❌ Column '{col}' NOT FOUND")
        
        # Check raw_csv_data is JSON type
        raw_csv_col = next((c for c in columns if c['name'] == 'raw_csv_data'), None)
        if raw_csv_col:
            col_type = str(raw_csv_col['type']).upper()
            if 'JSON' in col_type:
                self.successes.append(f"  ✅ 'raw_csv_data' is JSON type")
            else:
                self.errors.append(f"  ❌ 'raw_csv_data' is {col_type}, expected JSON")
    
    def validate_companies_schema(self):
        """Validate companies table schema"""
        logger.info("\n[4/7] Validating 'companies' schema...")
        
        columns = self.inspector.get_columns('companies')
        column_names = [col['name'] for col in columns]
        
        required_columns = [
            'company_id',
            'company_name',
            'cae_primary_code',  # NEW
            'cae_primary_label',
            'trade_description_native',
            'website',
            'activity_sector',
            'company_size',
            'is_active',
            'created_at',
            'updated_at'  # NEW
        ]
        
        if len(column_names) == 11:
            self.successes.append(f"✅ 'companies' has 11 columns (as designed)")
        else:
            self.warnings.append(f"⚠️  'companies' has {len(column_names)} columns, expected 11")
        
        for col in required_columns:
            if col in column_names:
                self.successes.append(f"  ✅ Column '{col}' exists")
            else:
                self.errors.append(f"  ❌ Column '{col}' NOT FOUND")
    
    def validate_relationships(self):
        """Validate foreign keys and relationships"""
        logger.info("\n[5/7] Validating relationships...")
        
        # Check FK from incentives_metadata to incentives
        fks = self.inspector.get_foreign_keys('incentives_metadata')
        
        metadata_fk = next((fk for fk in fks if fk['referred_table'] == 'incentives'), None)
        if metadata_fk:
            self.successes.append(f"✅ FK from 'incentives_metadata' to 'incentives' exists")
            
            # Check CASCADE delete
            if 'CASCADE' in metadata_fk.get('options', {}).get('ondelete', '').upper():
                self.successes.append(f"  ✅ CASCADE DELETE configured")
            else:
                self.warnings.append(f"  ⚠️  CASCADE DELETE not found (check manually)")
        else:
            self.errors.append(f"❌ FK from 'incentives_metadata' to 'incentives' NOT FOUND")
    
    def validate_indexes(self):
        """Validate indexes are in place"""
        logger.info("\n[6/7] Validating indexes...")
        
        # Get indexes for each table
        incentives_indexes = self.inspector.get_indexes('incentives')
        metadata_indexes = self.inspector.get_indexes('incentives_metadata')
        companies_indexes = self.inspector.get_indexes('companies')
        
        # Check primary keys (should have indexes automatically)
        self.successes.append(f"✅ 'incentives' has {len(incentives_indexes)} index(es)")
        self.successes.append(f"✅ 'incentives_metadata' has {len(metadata_indexes)} index(es)")
        self.successes.append(f"✅ 'companies' has {len(companies_indexes)} index(es)")
        
        # Check specific indexes
        metadata_index_names = [idx['name'] for idx in metadata_indexes]
        
        expected_indexes = ['idx_metadata_incentive', 'idx_metadata_status']
        for idx_name in expected_indexes:
            if any(idx_name in name for name in metadata_index_names):
                self.successes.append(f"  ✅ Index '{idx_name}' exists")
            else:
                self.warnings.append(f"  ⚠️  Index '{idx_name}' not found")
        
        companies_index_names = [idx['name'] for idx in companies_indexes]
        company_expected = ['idx_companies_cae', 'idx_companies_name', 'idx_companies_sector', 'idx_companies_size']
        
        for idx_name in company_expected:
            if any(idx_name in name for name in companies_index_names):
                self.successes.append(f"  ✅ Index '{idx_name}' exists")
            else:
                self.warnings.append(f"  ⚠️  Index '{idx_name}' not found (should be created)")
    
    def validate_data_integrity(self):
        """Validate data integrity with sample operations"""
        logger.info("\n[7/7] Validating data integrity...")
        
        try:
            # Count records
            incentives_count = self.session.query(Incentive).count()
            metadata_count = self.session.query(IncentiveMetadata).count()
            companies_count = self.session.query(Company).count()
            
            self.successes.append(f"✅ Found {incentives_count} incentives")
            self.successes.append(f"✅ Found {metadata_count} metadata records")
            self.successes.append(f"✅ Found {companies_count} companies")
            
            # Check 1:1 relationship
            if incentives_count == metadata_count:
                self.successes.append(f"✅ 1:1 relationship validated (same count)")
            elif incentives_count == 0:
                self.warnings.append(f"⚠️  No data imported yet (counts are 0)")
            else:
                self.errors.append(f"❌ 1:1 relationship BROKEN: {incentives_count} incentives vs {metadata_count} metadata")
            
            # Test JOIN query
            result = self.session.query(Incentive, IncentiveMetadata)\
                .join(IncentiveMetadata)\
                .first()
            
            if result or incentives_count == 0:
                self.successes.append(f"✅ JOIN between 'incentives' and 'metadata' works")
            else:
                self.errors.append(f"❌ JOIN between 'incentives' and 'metadata' FAILED")
            
        except Exception as e:
            self.errors.append(f"❌ Data integrity check failed: {e}")
    
    def print_results(self):
        """Print validation results"""
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 60)
        
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
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.errors)} errors")
        print("=" * 60)
        
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
    validator = DatabaseValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)

