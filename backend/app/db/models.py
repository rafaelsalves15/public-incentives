from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, JSON, Boolean, func, Float
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
    # Nota: não pode ser "metadata" pois é palavra reservada do SQLAlchemy
    incentive_metadata = relationship("IncentiveMetadata", back_populates="incentive", uselist=False, cascade="all, delete-orphan")


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
    fields_completed_by_ai = Column(JSON)  # Lista de campos preenchidos por IA
    ai_processing_error = Column(Text)  # Mensagem de erro se falhar
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship com incentive (1:1)
    incentive = relationship("Incentive", back_populates="incentive_metadata")


class Company(Base):
    """
    Tabela de empresas do CSV original.
    
    Campos do CSV (4 disponíveis):
    - company_name, cae_primary_label, trade_description_native, website
    
    Campo futuro (NULL):
    - company_size: Requer API externa (eInforma/Racius) - maior impacto no matching
    """
    __tablename__ = "companies"
    
    # Primary key
    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ✅ Campos do CSV (disponíveis e suficientes)
    company_name = Column(String(500), nullable=False)
    cae_primary_label = Column(String(500))  # Ex: "Software development" - usado para matching
    cae_primary_code = Column(JSON)          # Ex: ["62010", "62020"] - múltiplos códigos inferidos por LLM
    trade_description_native = Column(Text)  # Descrição atividade em PT
    website = Column(String(500))
    
    # ⚠️ Campos inferidos via LLM (NULL - requer dados externos)
    company_size = Column(String(50))  # micro/small/medium/large - +20% precisão se adicionado
    region = Column(String(100))       # Região NUTS II de Portugal
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# STUB para Fase 2 - apenas para evitar erros de importação
class IncentiveCompanyMatch(Base):
    """
    Tabela de matches entre incentivos e empresas (FASE 2).
    
    Armazena as Top 5 empresas para cada incentivo, com:
    - Score LLM (0.0-1.0)
    - Razões do match
    - Posição no ranking (1-5)
    """
    __tablename__ = "incentive_company_matches"
    
    match_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incentive_id = Column(UUID(as_uuid=True), ForeignKey("incentives.incentive_id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False)
    
    # Match quality (from LLM)
    match_score = Column(Float)  # 0.0-1.0
    match_reasons = Column(JSON)  # ["razão1", "razão2", ...]
    ranking_position = Column(Integer)  # 1, 2, 3, 4, 5
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    incentive = relationship("Incentive", foreign_keys=[incentive_id])
    company = relationship("Company", foreign_keys=[company_id])


class AICostTracking(Base):
    """
    Tabela para rastrear custos de chamadas à OpenAI API.
    Registra tokens usados, custos e tipo de operação.
    """
    __tablename__ = "ai_cost_tracking"
    
    tracking_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Referência ao incentivo processado (se aplicável)
    incentive_id = Column(UUID(as_uuid=True), ForeignKey("incentives.incentive_id"), nullable=True)
    
    # Tipo de operação AI
    operation_type = Column(String(100), nullable=False)  # 'ai_description', 'extract_dates', 'extract_budget'
    
    # Tokens e modelo
    model_name = Column(String(100), nullable=False)  # 'gpt-4o-mini', etc.
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    
    # Custos (em USD)
    input_cost = Column(Numeric(10, 6), nullable=False)  # Custo dos tokens de input
    output_cost = Column(Numeric(10, 6), nullable=False)  # Custo dos tokens de output
    total_cost = Column(Numeric(10, 6), nullable=False)  # Custo total desta chamada
    
    # Metadata
    cache_hit = Column(Boolean, default=False)  # Se foi cache hit (custo = 0)
    success = Column(Boolean, default=True)  # Se a chamada teve sucesso
    error_message = Column(Text)  # Mensagem de erro (se aplicável)
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    incentive = relationship("Incentive", foreign_keys=[incentive_id])
