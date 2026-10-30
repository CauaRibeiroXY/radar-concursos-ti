import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "editais.json")

class ConcursoRadar:
    """
    Motor de Busca, Filtros e Estatísticas de Concursos Públicos de TI
    """
    
    @classmethod
    def load_all(cls) -> List[Dict[str, Any]]:
        if not os.path.exists(DATA_PATH):
            return []
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                editais = json.load(f)
                
            today = date.today()
            # Enriquecer com contagem regressiva de dias
            for e in editais:
                # Dias até o fim das inscrições
                if e.get("inscricoes_fim"):
                    try:
                        dt_fim = datetime.strptime(e["inscricoes_fim"], "%Y-%m-%d").date()
                        delta_insc = (dt_fim - today).days
                        e["dias_fim_inscricoes"] = delta_insc
                    except Exception:
                        e["dias_fim_inscricoes"] = None
                else:
                    e["dias_fim_inscricoes"] = None

                # Dias até a prova
                if e.get("data_prova"):
                    try:
                        dt_prova = datetime.strptime(e["data_prova"], "%Y-%m-%d").date()
                        delta_prova = (dt_prova - today).days
                        e["dias_para_prova"] = delta_prova
                    except Exception:
                        e["dias_para_prova"] = None
                else:
                    e["dias_para_prova"] = None
                    
            return editais
        except Exception as e:
            print(f"[ConcursoRadar] Erro ao carregar dados: {e}")
            return []

    @classmethod
    def filter_editais(
        cls,
        q: str = "",
        min_salary: float = 0.0,
        status: Optional[str] = None,
        banca: Optional[str] = None,
        tech: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        editais = cls.load_all()
        filtered = []
        
        q_clean = q.lower().strip() if q else ""
        tech_clean = tech.lower().strip() if tech else ""
        status_clean = status.lower().strip() if status and status != "todos" else ""
        banca_clean = banca.lower().strip() if banca and banca != "todos" else ""

        for e in editais:
            # Salário
            if e.get("remuneracao", 0) < min_salary:
                continue

            # Status
            if status_clean and status_clean not in e.get("status", "").lower():
                continue

            # Banca
            if banca_clean and banca_clean not in e.get("banca", "").lower():
                continue

            # Stack Tech específico
            if tech_clean:
                stack_lower = [t.lower() for t in e.get("stack", [])]
                if not any(tech_clean in s for s in stack_lower):
                    continue

            # Busca textual geral
            if q_clean:
                searchable = f"{e.get('orgao', '')} {e.get('cargo', '')} {e.get('area', '')} {e.get('localidade', '')} {' '.join(e.get('stack', []))}".lower()
                if q_clean not in searchable:
                    continue

            filtered.append(e)

        return filtered

    @classmethod
    def get_by_id(cls, edital_id: str) -> Optional[Dict[str, Any]]:
        editais = cls.load_all()
        for e in editais:
            if e.get("id") == edital_id:
                return e
        return None

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        editais = cls.load_all()
        if not editais:
            return {
                "total_editais": 0,
                "vagas_totais": 0,
                "maior_salario": 0,
                "media_salarial": 0,
                "inscricoes_abertas": 0
            }

        total = len(editais)
        vagas = sum(e.get("vagas_imediatas", 0) + e.get("vagas_cr", 0) for e in editais)
        salarios = [e.get("remuneracao", 0) for e in editais if e.get("remuneracao")]
        maior = max(salarios) if salarios else 0
        media = (sum(salarios) / len(salarios)) if salarios else 0
        abertas = sum(1 for e in editais if "aberta" in e.get("status", "").lower())

        return {
            "total_editais": total,
            "vagas_totais": vagas,
            "maior_salario": maior,
            "media_salarial": round(media, 2),
            "inscricoes_abertas": abertas
        }
