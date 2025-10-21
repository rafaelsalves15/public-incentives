"""
Nova estrutura de modelos seguindo exatamente o enunciado.

3 tabelas:
1. incentives - Campos principais (10) conforme enunciado
2. incentives_metadata - Dados adicionais e metadata IA
3. companies - Dados de empresas
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


class Incentive(Base):
    """
    Tabela principal de incentivos.
    Contém EXATAMENTE os 10 campos especificados no enunciado.
    """
    __tablename__ = "incentives"
    
    # Campos conforme enunciado (10 campos)
    incentive_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    ai_description = Column(JSON)  # Descrição estruturada em JSON gerada por IA
    document_urls = Column(JSON)  # Links para documentos associados
    publication_date = Column(DateTime)  # Data de publicação
    start_date = Column(DateTime)  # Data de início
    end_date = Column(DateTime)  # Data de fim
    total_budget = Column(Numeric(15, 2))  # Orçamento total
    source_link = Column(String(1000))  # Link para página oficial
    
    # Relationship com metadata (1:1)
    metadata = relationship("IncentiveMetadata", back_populates="incentive", uselist=False, cascade="all, delete-orphan")


class IncentiveMetadata(Base):
    """
    Tabela de metadata e dados adicionais.
    Contém dados completos do CSV e informação de processamento IA.
    Relação 1:1 com Incentive.
    """
    __tablename__ = "incentives_metadata"
    
    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incentive_id = Column(UUID(as_uuid=True), ForeignKey("incentives.incentive_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Dados completos do CSV (21 campos originais)
    raw_csv_data = Column(JSON, nullable=False)
    
    # Metadata de processamento IA
    ai_processing_status = Column(String(50), default="pending")  # pending/processing/completed/failed
    ai_processing_date = Column(DateTime)
    fields_completed_by_ai = Column(JSON, default=list)  # Lista de campos preenchidos por IA
    ai_processing_error = Column(Text)  # Mensagem de erro se falhar
    
    # Timestamps
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")
    
    # Relationship com incentive (1:1)
    incentive = relationship("Incentive", back_populates="metadata")


class Company(Base):
    """
    Tabela de empresas.
    Schema livre conforme utilidade para o sistema.
    
    Campos do CSV:
    - company_name, cae_primary_code, cae_primary_label, 
      trade_description_native, website
    
    Campos derivados (para facilitar matching):
    - activity_sector (derivado do CAE)
    - company_size (micro/small/medium/large)
    """
    __tablename__ = "companies"
    
    # Primary key
    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Campos do CSV
    company_name = Column(String(500), nullable=False)
    cae_primary_code = Column(String(10))  # Código CAE (ex: "62010")
    cae_primary_label = Column(String(500))  # Descrição do CAE
    trade_description_native = Column(Text)  # Descrição da atividade comercial
    website = Column(String(500))
    
    # Campos derivados (para facilitar matching na Fase 2)
    activity_sector = Column(String(200))  # Setor derivado do CAE (ex: "Tecnologia")
    company_size = Column(String(50))  # micro, small, medium, large
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")


# Nota: IncentiveCompanyMatch será criado na Fase 2 (Matching)
# Por agora, focamos apenas em ter dados limpos nas 3 tabelas acima

