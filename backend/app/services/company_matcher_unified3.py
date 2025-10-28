#!/usr/bin/env python3
"""
CompanyMatcherUnified - Sistema de Matching Unificado

Implementa um sistema híbrido que combina análise determinística com refinamento por LLM
para identificar as 5 empresas mais adequadas para cada incentivo.

Arquitetura baseada no AIProcessor:
1. Deterministic Pre-filtering - Filtra empresas por critérios básicos
2. LLM Batch Analysis - Usa analyze_batch_match do AIProcessor para seleção inteligente
3. Validation & Storage - Valida resultados e salva na base de dados
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company, IncentiveCompanyMatch, IncentiveMetadata
from app.services.ai_processor import AIProcessor

logger = logging.getLogger(__name__)


class CompanyMatcherUnified:
    """
    Sistema de matching unificado que usa o AIProcessor para análise inteligente.
    
    Fluxo:
    1. Deterministic Pre-filtering: Filtra empresas por critérios básicos
    2. LLM Batch Analysis: Usa AIProcessor.analyze_batch_match() para seleção inteligente
    3. Validation & Storage: Valida resultados e salva na base de dados
    """
    
    def __init__(self, ai_processor: Optional[AIProcessor] = None):
        """
        Inicializa o matcher.
        
        Args:
            ai_processor: Instância do AIProcessor para chamadas LLM
        """
        self.ai_processor = ai_processor
        self.logger = logging.getLogger(__name__)
    
    def match_incentive_to_companies(
        self, 
        incentive_id: str, 
        company_ids: List[str], 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Encontra as melhores empresas para um incentivo específico.
        
        Args:
            incentive_id: ID do incentivo
            company_ids: Lista de IDs das empresas a considerar
            db: Sessão da base de dados
            
        Returns:
            Lista de matches ordenados por score (melhor primeiro)
        """
        try:
            # Obter incentivo e metadata
            incentive = db.query(Incentive).filter(
                Incentive.incentive_id == incentive_id
            ).first()
            
            if not incentive:
                raise ValueError(f"Incentivo {incentive_id} não encontrado")
            
            metadata = db.query(IncentiveMetadata).filter(
                IncentiveMetadata.incentive_id == incentive_id
            ).first()
            
            if not metadata:
                raise ValueError(f"Metadata para incentivo {incentive_id} não encontrada")
            
            # Obter empresas
            companies = db.query(Company).filter(
                Company.company_id.in_(company_ids)
            ).all()
            
            if not companies:
                raise ValueError("Nenhuma empresa encontrada")
            
            self.logger.info(f"Processando matching para incentivo: {incentive.title}")
            self.logger.info(f"Empresas candidatas: {len(companies)}")
            
            # 1. Deterministic Ranking
            ranked_companies = self._deterministic_pre_filter(incentive, companies)
            
            self.logger.info(f"Empresas após ranking determinístico: {len(ranked_companies)}")
            
            # 2. Selecionar top empresas para LLM (otimização de custos)
            # Enviar apenas as 15 melhores para o LLM escolher as 5 finais
            top_companies_for_llm = ranked_companies[:15]
            self.logger.info(f"Enviando top {len(top_companies_for_llm)} empresas para LLM")
            
            # 3. LLM Batch Analysis (se disponível)
            if self.ai_processor and len(top_companies_for_llm) > 0:
                final_matches = self._llm_batch_analysis(incentive, top_companies_for_llm, metadata.raw_csv_data)
            else:
                # Fallback: usar apenas scoring determinístico
                final_matches = self._deterministic_fallback(ranked_companies)
            
            # 4. Limitar a top 5
            top_5_matches = final_matches[:5]
            
            self.logger.info(f"Matching concluído: {len(top_5_matches)} matches finais")
            
            return top_5_matches
            
        except Exception as e:
            self.logger.error(f"Erro no matching: {str(e)}")
            raise
    
    def _deterministic_pre_filter(self, incentive: Incentive, companies: List[Company]) -> List[Company]:
        """
        Sistema de ranking determinístico que pontua empresas por relevância.
        
        Retorna empresas ordenadas por score determinístico (melhor primeiro).
        O LLM recebe as empresas mais relevantes para fazer a seleção final.
        """
        scored_companies = []
        ai_desc = incentive.ai_description or {}
        
        # Critérios de elegibilidade
        eligible_sectors = ai_desc.get('eligible_sectors', [])
        eligible_cae_codes = ai_desc.get('eligible_cae_codes', [])
        eligible_regions = ai_desc.get('eligible_regions', [])
        company_sizes = ai_desc.get('company_sizes', [])
        
        for company in companies:
            score = 0
            reasons = []
            
            # 1. CAE Code Match (peso muito alto)
            if company.cae_primary_code and eligible_cae_codes:
                company_cae_codes = company.cae_primary_code if isinstance(company.cae_primary_code, list) else [company.cae_primary_code]
                
                for company_cae in company_cae_codes:
                    if str(company_cae) in eligible_cae_codes:
                        score += 100  # Match exato
                        reasons.append(f"CAE code exato: {company_cae}")
                        break
                else:
                    # Verificar se é relacionado (mesmo grupo de 2 dígitos)
                    for company_cae in company_cae_codes:
                        company_cae_group = str(company_cae)[:2] if len(str(company_cae)) >= 2 else ""
                        for eligible_cae in eligible_cae_codes:
                            if str(eligible_cae).startswith(company_cae_group):
                                score += 50  # Match relacionado
                                reasons.append(f"CAE code relacionado: {company_cae}")
                                break
                        if score >= 50:  # Já encontrou match relacionado
                            break
            
            # 2. Setor Match (peso alto)
            if company.cae_primary_label and eligible_sectors:
                company_sector_lower = company.cae_primary_label.lower()
                for sector in eligible_sectors:
                    sector_lower = sector.lower()
                    # Verificar palavras-chave do setor na descrição da empresa
                    if any(keyword in company_sector_lower for keyword in sector_lower.split()):
                        score += 75
                        reasons.append(f"Setor compatível: {sector}")
                        break
            
            # 3. Região Match (peso médio)
            if company.region and eligible_regions:
                company_region_lower = company.region.lower()
                for region in eligible_regions:
                    if region.lower() in company_region_lower or company_region_lower in region.lower():
                        score += 50
                        reasons.append(f"Região elegível: {region}")
                        break
            
            # 4. Tamanho Match (peso médio)
            if company.company_size and company_sizes:
                if company.company_size.lower() in [size.lower() for size in company_sizes]:
                    score += 25
                    reasons.append(f"Tamanho adequado: {company.company_size}")
            
            # 5. Bonus por dados completos
            if company.cae_primary_code:
                score += 10
                reasons.append("CAE code disponível")
            
            if company.region:
                score += 5
                reasons.append("Região disponível")
            
            if company.website:
                score += 5
                reasons.append("Website disponível")
            
            # 6. Penalties
            if not company.is_active:
                score -= 20
                reasons.append("Empresa inativa")
            
            # 7. Score base mínimo para garantir ranking
            if score == 0:
                score = 10  # Score mínimo para empresas sem match
                reasons.append("Sem match específico - score base")
            
            scored_companies.append({
                'company': company,
                'score': score,
                'reasons': reasons
            })
        
        # Ordenar por score (melhor primeiro)
        scored_companies.sort(key=lambda x: x['score'], reverse=True)
        
        # Retornar apenas as empresas (sem scores) ordenadas por relevância
        ranked_companies = [item['company'] for item in scored_companies]
        
        self.logger.info(f"Ranking determinístico: {len(ranked_companies)} empresas pontuadas")
        if scored_companies:
            top_score = scored_companies[0]['score']
            self.logger.info(f"Melhor score: {top_score} ({scored_companies[0]['company'].company_name})")
        
        return ranked_companies
    
    def _llm_batch_analysis(
        self, 
        incentive: Incentive, 
        companies: List[Company], 
        raw_csv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Análise por LLM usando o método analyze_batch_match do AIProcessor.
        
        Este método é otimizado e já inclui validação automática.
        """
        try:
            # Usar o método otimizado do AIProcessor
            results = self.ai_processor.analyze_batch_match(
                incentive=incentive,
                companies=companies,
                raw_csv_data=raw_csv_data,
                select_top_n=5  # Selecionar top 5
            )
            
            # Converter para formato esperado
            final_matches = []
            for i, result in enumerate(results, 1):
                # Encontrar empresa correspondente
                company_id = result.get('company_id')
                company = next((c for c in companies if str(c.company_id) == company_id), None)
                
                if company:
                    final_matches.append({
                        'company': company,
                        'match_score': result.get('match_score', 0.0),
                        'reasons': result.get('reasons', []),
                        'ranking_position': i,
                        'unified_score': result.get('match_score', 0.0) * 100  # Para compatibilidade
                    })
            
            return final_matches
            
        except Exception as e:
            self.logger.error(f"Erro no LLM batch analysis: {str(e)}")
            # Fallback para scoring determinístico
            return self._deterministic_fallback(companies)
    
    def _deterministic_fallback(self, companies: List[Company]) -> List[Dict[str, Any]]:
        """
        Fallback determinístico quando LLM não está disponível.
        
        Usa scoring simples baseado em dados disponíveis.
        """
        scored_companies = []
        
        for company in companies:
            score = 0.5  # Score base
            reasons = []
            
            # Bonus por ter CAE code
            if company.cae_primary_code:
                score += 0.2
                reasons.append(f"CAE code disponível: {company.cae_primary_code}")
            
            # Bonus por ter região
            if company.region:
                score += 0.1
                reasons.append(f"Região: {company.region}")
            
            # Bonus por ter tamanho
            if company.company_size:
                score += 0.1
                reasons.append(f"Tamanho: {company.company_size}")
            
            # Bonus por ter website
            if company.website:
                score += 0.1
                reasons.append("Website disponível")
            
            scored_companies.append({
                'company': company,
                'match_score': min(score, 1.0),  # Normalizar para 0-1
                'reasons': reasons,
                'ranking_position': 0,  # Será definido depois
                'unified_score': score * 100
            })
        
        # Ordenar por score
        scored_companies.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Definir posições
        for i, item in enumerate(scored_companies, 1):
            item['ranking_position'] = i
        
        return scored_companies
    
    def process_incentive_matches(self, db: Session, incentive_id: str) -> Dict[str, Any]:
        """
        Processa matches para um incentivo específico e salva na base de dados.
        
        Segue o padrão do AIProcessor com logging detalhado.
        """
        try:
            # Obter todas as empresas ativas
            companies = db.query(Company).filter(Company.is_active == True).all()
            company_ids = [str(c.company_id) for c in companies]
            
            self.logger.info(f"Iniciando processamento de matches para incentivo {incentive_id}")
            self.logger.info(f"Total de empresas ativas: {len(companies)}")
            
            # Executar matching
            matches = self.match_incentive_to_companies(incentive_id, company_ids, db)
            
            # Limpar matches existentes para este incentivo
            deleted_count = db.query(IncentiveCompanyMatch).filter(
                IncentiveCompanyMatch.incentive_id == incentive_id
            ).delete()
            
            if deleted_count > 0:
                self.logger.info(f"Removidos {deleted_count} matches existentes")
            
            # Salvar novos matches
            saved_matches = []
            for match in matches:
                db_match = IncentiveCompanyMatch(
                    incentive_id=incentive_id,
                    company_id=match['company'].company_id,
                    match_score=match['match_score'],
                    match_reasons=match['reasons'],
                    ranking_position=match['ranking_position']
                )
                db.add(db_match)
                
                saved_matches.append({
                    'company_name': match['company'].company_name,
                    'match_score': match['match_score'],
                    'reasons': match['reasons'],
                    'ranking_position': match['ranking_position']
                })
            
            db.commit()
            
            self.logger.info(f"✅ Salvos {len(saved_matches)} matches para incentivo {incentive_id}")
            
            return {
                'success': True,
                'incentive_id': incentive_id,
                'matches_count': len(saved_matches),
                'matches': saved_matches
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Erro ao processar matches para incentivo {incentive_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_all_incentives(self, db: Session) -> Dict[str, Any]:
        """
        Processa matches para todos os incentivos.
        
        Segue o padrão do AIProcessor com logging detalhado e progresso.
        """
        try:
            # Obter incentivos processados (com AI description)
            incentives = db.query(Incentive).filter(
                Incentive.ai_description.isnot(None)
            ).all()
            
            total_incentives = len(incentives)
            processed_count = 0
            failed_count = 0
            
            self.logger.info(f"Iniciando processamento de matches para {total_incentives} incentivos")
            
            for i, incentive in enumerate(incentives, 1):
                try:
                    self.logger.info(f"Processando {i}/{total_incentives}: {incentive.title[:60]}...")
                    
                    result = self.process_incentive_matches(db, str(incentive.incentive_id))
                    
                    if result['success']:
                        processed_count += 1
                        self.logger.info(f"✅ {result['matches_count']} matches salvos")
                    else:
                        failed_count += 1
                        self.logger.error(f"❌ Falhou: {result['error']}")
                    
                    # Log progresso a cada 10 incentivos
                    if i % 10 == 0:
                        self.logger.info(f"Progresso: {i}/{total_incentives} ({i/total_incentives*100:.1f}%)")
                    
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"❌ Erro no incentivo {incentive.incentive_id}: {str(e)}")
            
            success_rate = (processed_count / total_incentives * 100) if total_incentives > 0 else 0
            
            self.logger.info(f"Processamento concluído: {processed_count} sucessos, {failed_count} falhas")
            self.logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
            
            return {
                'success': True,
                'total_incentives': total_incentives,
                'processed_count': processed_count,
                'failed_count': failed_count,
                'success_rate': success_rate
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento geral: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }