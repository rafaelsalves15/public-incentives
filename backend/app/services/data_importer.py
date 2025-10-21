import pandas as pd
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Incentive, IncentiveMetadata, Company
import logging

logger = logging.getLogger(__name__)


class DataImporter:
    def __init__(self):
        self.session = SessionLocal()
    
    
    def parse_json_field(self, json_str: str) -> Dict[str, Any]:
        """Safely parse JSON string field"""
        if pd.isna(json_str) or json_str == "":
            return {}
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse JSON: {json_str[:100]}...")
            return {}
    
    def parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string with various formats"""
        if pd.isna(date_str) or date_str == "":
            return None
        
        # Try dateutil parser first (handles most formats including +00 timezone)
        try:
            from dateutil import parser
            return parser.parse(str(date_str))
        except (ValueError, TypeError, parser.ParserError):
            pass
        
        # Fallback to common datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse datetime: {date_str}")
        return None
    
    def import_companies(self, csv_path: str) -> int:
        """Import companies from CSV file"""
        logger.info(f"Importing companies from {csv_path}")
        
        df = pd.read_csv(csv_path)
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                company = Company(
                    company_name=row['company_name'],
                    cae_primary_label=row.get('cae_primary_label', ''),
                    trade_description_native=row.get('trade_description_native', ''),
                    website=row.get('website', ''),
                )
                
                self.session.add(company)
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    logger.info(f"Imported {imported_count} companies...")
                    
            except Exception as e:
                logger.error(f"Error importing company {row.get('company_name', 'Unknown')}: {e}")
                continue
        
        self.session.commit()
        logger.info(f"Successfully imported {imported_count} companies")
        return imported_count
    
    def import_incentives(self, csv_path: str) -> int:
        """Import incentives from CSV file"""
        logger.info(f"Importing incentives from {csv_path}")
        
        df = pd.read_csv(csv_path)
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse JSON fields
                document_urls = self.parse_json_field(row.get('document_urls', ''))
                
                # Parse dates
                publication_date = self.parse_datetime(row.get('date_publication'))
                start_date = self.parse_datetime(row.get('date_start'))
                end_date = self.parse_datetime(row.get('date_end'))
                
                # Parse total_budget
                total_budget = None
                try:
                    budget_val = row.get('total_budget')
                    if pd.notna(budget_val) and budget_val != '':
                        total_budget = float(budget_val)
                except (ValueError, TypeError):
                    total_budget = None
                
                # Parse ai_description - deve ser sempre objeto JSON ou None
                ai_description_data = None
                ai_desc_raw = row.get('ai_description', '')
                if pd.notna(ai_desc_raw) and ai_desc_raw != '':
                    # Try to parse as JSON first
                    parsed = self.parse_json_field(ai_desc_raw)
                    # Se retornou dict válido (não vazio), usar
                    # Se for string pura ou parsing falhou, deixar None para AI processar
                    if parsed and isinstance(parsed, dict):
                        ai_description_data = parsed
                    else:
                        # Texto puro - será processado pela AI
                        ai_description_data = None
                
                # 1. Create incentive (APENAS 10 campos do enunciado)
                incentive = Incentive(
                    title=row['title'],
                    description=row.get('description', ''),
                    ai_description=ai_description_data,
                    document_urls=document_urls,
                    publication_date=publication_date,
                    start_date=start_date,
                    end_date=end_date,
                    total_budget=total_budget,
                    source_link=row.get('source_link', ''),
                )
                self.session.add(incentive)
                self.session.flush()  # Para obter incentive_id
                
                # 2. Create metadata (APENAS campos únicos - sem duplicação)
                # Guardamos os 10 campos que NÃO existem na tabela incentives
                raw_csv_data = {
                    # IDs e identificadores
                    'incentive_project_id': str(row.get('incentive_project_id', '')),
                    'project_id': str(row.get('project_id', '')),
                    'incentive_program': str(row.get('incentive_program', '')),
                    
                    # Status e critérios
                    'status': str(row.get('status', '')),
                    'eligibility_criteria': self.parse_json_field(row.get('eligibility_criteria', '')),
                    
                    # all_data (IMPORTANTE - contém calendario, estrutura, etc)
                    'all_data': self.parse_json_field(row.get('all_data', '')),
                    
                    # ai_description ORIGINAL do CSV (texto) - para AI usar como input
                    'ai_description': str(row.get('ai_description', '')),
                    
                    # Documentos GCS
                    'gcs_document_urls': self.parse_json_field(row.get('gcs_document_urls', '')),
                    
                    # Timestamps originais do CSV
                    'created_at': str(row.get('created_at', '')),
                    'updated_at': str(row.get('updated_at', ''))
                }
                # NOTA: Campos como title, description, document_urls, date_publication, 
                # date_start, date_end, total_budget, source_link
                # NÃO são guardados aqui pois já estão na tabela incentives (evitar duplicação)
                # ai_description É guardado aqui pois o texto original serve como INPUT para AI
                
                # Determine if AI processing is needed
                needs_ai = self._check_needs_ai_processing(incentive, row)
                
                metadata = IncentiveMetadata(
                    incentive_id=incentive.incentive_id,
                    raw_csv_data=raw_csv_data,
                    ai_processing_status="pending" if needs_ai else "completed",
                    fields_completed_by_ai=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.session.add(metadata)
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    logger.info(f"Imported {imported_count} incentives...")
                    self.session.commit()  # Commit in batches for better performance
                    
            except Exception as e:
                logger.error(f"Error importing incentive {row.get('title', 'Unknown')}: {e}")
                continue
        
        self.session.commit()
        logger.info(f"Successfully imported {imported_count} incentives")
        return imported_count
    
    def _check_needs_ai_processing(self, incentive: Incentive, row: pd.Series) -> bool:
        """Check if an incentive needs AI processing"""
        needs_ai = False
        
        # Check if ai_description is missing or needs conversion
        ai_desc = row.get('ai_description', '')
        if pd.isna(ai_desc) or ai_desc == '' or not incentive.ai_description:
            needs_ai = True
        
        # Check if critical dates are missing
        if not incentive.publication_date or not incentive.start_date or not incentive.end_date:
            # Try to find in all_data first
            all_data = self.parse_json_field(row.get('all_data', ''))
            if not all_data or 'calendario' not in all_data:
                needs_ai = True
        
        # Check if total_budget is missing
        if not incentive.total_budget:
            # Try to find in all_data first
            all_data = self.parse_json_field(row.get('all_data', ''))
            if not all_data or 'dotacao' not in all_data:
                needs_ai = True
        
        return needs_ai
    
    def import_from_local_files(self, companies_path: str, incentives_path: str) -> Dict[str, int]:
        """Import data from local CSV files"""
        logger.info("Starting data import from local files...")
        
        # Check if files exist
        if not os.path.exists(companies_path):
            raise FileNotFoundError(f"Companies CSV not found: {companies_path}")
        if not os.path.exists(incentives_path):
            raise FileNotFoundError(f"Incentives CSV not found: {incentives_path}")
        
        # Import data
        companies_count = self.import_companies(companies_path)
        incentives_count = self.import_incentives(incentives_path)
        
        return {
            "companies": companies_count,
            "incentives": incentives_count
        }
    
    
    def close(self):
        """Close database session"""
        self.session.close()
