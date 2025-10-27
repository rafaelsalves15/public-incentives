"""
Cost Tracker para chamadas OpenAI API.
Rastreia tokens, custos e estatísticas de uso.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from app.db.models import AICostTracking

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Rastreia custos de chamadas à OpenAI API.
    
    Preços GPT-4o-mini (atualizado em Oct 2024):
    - Input: $0.150 / 1M tokens
    - Output: $0.600 / 1M tokens
    """
    
    # Preços por modelo (USD por 1M tokens)
    MODEL_PRICING = {
        "gpt-4o-mini": {
            "input": 0.150,   # $0.150 / 1M tokens
            "output": 0.600   # $0.600 / 1M tokens
        },
        "gpt-4o": {
            "input": 2.50,    # $2.50 / 1M tokens
            "output": 10.00   # $10.00 / 1M tokens
        },
        "text-embedding-3-small": {
            "input": 0.02,    # $0.02 / 1M tokens
            "output": 0.0     # Embeddings não têm output tokens
        }
    }
    
    def __init__(self, session: Session):
        self.session = session
        self._in_memory_stats = {
            "total_requests": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self._current_incentive = None
        self._current_incentive_cost = 0.0
    
    def track_api_call(
        self,
        operation_type: str,
        model_name: str,
        usage_data: Dict[str, int],
        incentive_id: Optional[str] = None,
        cache_hit: bool = False,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra uma chamada à API e calcula o custo.
        
        Args:
            operation_type: Tipo de operação ('ai_description', 'extract_dates', 'extract_budget')
            model_name: Nome do modelo usado
            usage_data: Dict com 'prompt_tokens', 'completion_tokens', 'total_tokens'
            incentive_id: UUID do incentivo processado (opcional)
            cache_hit: Se foi um cache hit (custo = 0)
            success: Se a chamada teve sucesso
            error_message: Mensagem de erro (se aplicável)
        
        Returns:
            Dict com estatísticas do custo
        """
        
        # Extrair tokens do usage_data
        input_tokens = usage_data.get('prompt_tokens', 0)
        output_tokens = usage_data.get('completion_tokens', 0)
        total_tokens = usage_data.get('total_tokens', input_tokens + output_tokens)
        
        # Calcular custos
        if cache_hit:
            # Cache hit = custo zero
            input_cost = 0.0
            output_cost = 0.0
            total_cost = 0.0
        else:
            # Obter preços do modelo
            pricing = self.MODEL_PRICING.get(model_name, self.MODEL_PRICING["gpt-4o-mini"])
            
            # Calcular custo (preço por 1M tokens)
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            total_cost = input_cost + output_cost
        
        # Criar registro na BD
        tracking_record = AICostTracking(
            incentive_id=incentive_id,
            operation_type=operation_type,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=Decimal(str(round(input_cost, 6))),
            output_cost=Decimal(str(round(output_cost, 6))),
            total_cost=Decimal(str(round(total_cost, 6))),
            cache_hit=cache_hit,
            success=success,
            error_message=error_message
        )
        
        self.session.add(tracking_record)
        self.session.commit()
        
        # Atualizar estatísticas em memória
        self._in_memory_stats["total_requests"] += 1
        self._in_memory_stats["total_cost"] += total_cost
        self._current_incentive_cost += total_cost
        if cache_hit:
            self._in_memory_stats["cache_hits"] += 1
        else:
            self._in_memory_stats["cache_misses"] += 1
        
        # Visual output no terminal
        self._print_operation_cost(operation_type, input_tokens, output_tokens, total_cost, cache_hit)
        
        return {
            "operation_type": operation_type,
            "model_name": model_name,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            "cost": {
                "input": input_cost,
                "output": output_cost,
                "total": total_cost,
                "formatted": f"${total_cost:.6f}"
            },
            "cache_hit": cache_hit,
            "success": success
        }
    
    def track_cost(
        self,
        operation_type: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        input_cost: float,
        output_cost: float,
        total_cost: float,
        cache_hit: bool = False,
        success: bool = True,
        error_message: Optional[str] = None,
        incentive_id: Optional[str] = None
    ) -> None:
        """
        Alias para track_api_call para compatibilidade.
        """
        usage_data = {
            'prompt_tokens': input_tokens,
            'completion_tokens': output_tokens,
            'total_tokens': total_tokens
        }
        self.track_api_call(
            operation_type=operation_type,
            model_name=model_name,
            usage_data=usage_data,
            incentive_id=incentive_id,
            cache_hit=cache_hit,
            success=success,
            error_message=error_message
        )
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da sessão atual (em memória).
        """
        return {
            "session": self._in_memory_stats,
            "average_cost_per_request": (
                self._in_memory_stats["total_cost"] / self._in_memory_stats["total_requests"]
                if self._in_memory_stats["total_requests"] > 0
                else 0.0
            )
        }
    
    def get_total_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas totais da BD (todos os tempos).
        """
        from sqlalchemy import func
        
        # Query agregada
        result = self.session.query(
            func.count(AICostTracking.tracking_id).label('total_calls'),
            func.sum(AICostTracking.total_cost).label('total_cost'),
            func.sum(AICostTracking.input_tokens).label('total_input_tokens'),
            func.sum(AICostTracking.output_tokens).label('total_output_tokens'),
            func.sum(AICostTracking.total_tokens).label('total_tokens'),
            func.count(func.nullif(AICostTracking.cache_hit, False)).label('cache_hits')
        ).first()
        
        total_calls = result.total_calls or 0
        total_cost = float(result.total_cost or 0.0)
        cache_hits = result.cache_hits or 0
        
        # Query por tipo de operação
        by_operation = self.session.query(
            AICostTracking.operation_type,
            func.count(AICostTracking.tracking_id).label('calls'),
            func.sum(AICostTracking.total_cost).label('cost'),
            func.sum(AICostTracking.total_tokens).label('tokens')
        ).group_by(AICostTracking.operation_type).all()
        
        operations_breakdown = [
            {
                "operation": op.operation_type,
                "calls": op.calls,
                "cost": float(op.cost or 0.0),
                "tokens": int(op.tokens or 0),
                "avg_cost_per_call": float(op.cost or 0.0) / op.calls if op.calls > 0 else 0.0
            }
            for op in by_operation
        ]
        
        return {
            "all_time": {
                "total_calls": total_calls,
                "total_cost": total_cost,
                "total_cost_formatted": f"${total_cost:.6f}",
                "total_tokens": {
                    "input": int(result.total_input_tokens or 0),
                    "output": int(result.total_output_tokens or 0),
                    "total": int(result.total_tokens or 0)
                },
                "cache_stats": {
                    "hits": cache_hits,
                    "misses": total_calls - cache_hits,
                    "hit_rate": (cache_hits / total_calls * 100) if total_calls > 0 else 0.0
                },
                "average_cost_per_call": total_cost / total_calls if total_calls > 0 else 0.0
            },
            "by_operation": operations_breakdown
        }
    
    def reset_session_stats(self):
        """Reseta estatísticas em memória."""
        self._in_memory_stats = {
            "total_requests": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    # ============================================================================
    # VISUAL DISPLAY METHODS
    # ============================================================================
    
    def start_incentive(self, incentive_title: str, index: int, total: int):
        """Inicia o tracking visual de um incentivo."""
        self._current_incentive = incentive_title
        self._current_incentive_cost = 0.0
        
        print()
        print("=" * 90)
        print(f"📝 Processing Incentive [{index}/{total}]: {incentive_title[:60]}...")
        print("=" * 90)
    
    def _print_operation_cost(self, operation_type: str, input_tokens: int, output_tokens: int, cost: float, cache_hit: bool):
        """Imprime o custo de uma operação no terminal."""
        icon = "💾" if cache_hit else "💰"
        status = "CACHE HIT!" if cache_hit else f"{input_tokens}→{output_tokens} tokens"
        cost_str = "$0.000000" if cache_hit else f"${cost:.6f}"
        
        operation_label = {
            "ai_description": "AI Description ",
            "extract_dates": "Extract Dates  ",
            "extract_budget": "Extract Budget ",
            "generate_incentive_embedding": "Incentive Embed ",
            "generate_company_embedding": "Company Embed  ",
            "batch_company_match": "Batch Match   "
        }.get(operation_type, operation_type)
        
        print(f"  {icon} {operation_label}: {cost_str:12} ({status})")
    
    def end_incentive(self):
        """Finaliza o tracking visual de um incentivo."""
        running_total = self._in_memory_stats["total_cost"]
        incentive_cost = self._current_incentive_cost
        
        print(f"  ─────────────────────────────────────────────")
        print(f"  ✅ Incentive Total: ${incentive_cost:.6f}")
        print(f"  📊 Running Total:   ${running_total:.6f}")
        print()
    
    def print_batch_summary(self, total_incentives: int, duration_seconds: float):
        """Imprime um resumo visual completo do processamento em batch."""
        stats = self._in_memory_stats
        total_cost = stats["total_cost"]
        total_calls = stats["total_requests"]
        cache_hits = stats["cache_hits"]
        cache_misses = stats["cache_misses"]
        cache_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0
        avg_cost = total_cost / total_incentives if total_incentives > 0 else 0
        
        print()
        print("━" * 90)
        print("📊 BATCH PROCESSING SUMMARY")
        print("━" * 90)
        print(f"  Total Incentives Processed: {total_incentives}")
        print(f"  Processing Time:            {duration_seconds:.2f}s ({duration_seconds/total_incentives:.2f}s per incentive)")
        print()
        print(f"  💰 COST BREAKDOWN:")
        print(f"     Total API Calls:         {total_calls}")
        print(f"     Cache Hits:              {cache_hits} ({cache_rate:.1f}%)")
        print(f"     Cache Misses:            {cache_misses}")
        print()
        print(f"     Total Cost:              ${total_cost:.6f}")
        print(f"     Average per Incentive:   ${avg_cost:.6f}")
        print(f"     Cost Saved (cache):      ${self._calculate_cache_savings():.6f}")
        print("━" * 90)
        
        # Alert se custo alto
        if total_cost > 0.10:
            print(f"  ⚠️  WARNING: Total cost (${total_cost:.6f}) exceeds $0.10!")
            print("━" * 90)
    
    def _calculate_cache_savings(self) -> float:
        """Calcula quanto foi economizado com cache hits."""
        # Assumir custo médio de $0.0005 por chamada que foi cached
        avg_cost_per_call = 0.0005
        return self._in_memory_stats["cache_hits"] * avg_cost_per_call
    
    def print_progress(self, current: int, total: int):
        """Imprime barra de progresso visual."""
        percent = (current / total) * 100
        filled = int(percent / 2)  # 50 chars max
        bar = "█" * filled + "░" * (50 - filled)
        print(f"\r  Progress: [{bar}] {percent:.1f}% ({current}/{total})", end="", flush=True)

