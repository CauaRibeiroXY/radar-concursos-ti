import os
import json
import re
from typing import List, Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from core.radar import ConcursoRadar

class ProfileMatcherAI:
    """
    Agente de Inteligência Artificial para Diagnóstico de Perfil em Concursos de TI
    Calcula afinidade técnica, aponta gaps no edital e traça estratégia de aprovação.
    """

    SYSTEM_PROMPT = """Você é o principal estrategista de aprovação em Concursos Públicos de Tecnologia da Informação do Brasil.
Sua missão é analisar o perfil/currículo técnico do candidato e cruzar com os editais de TI abertos e previstos.

Você DEVE responder ESTRITAMENTE em formato JSON com o seguinte schema:
{
  "profile_summary": "Diagnóstico do nível e perfil do candidato (ex: Desenvolvedor Backend / Cientista de Dados)",
  "top_matches": [
    {
      "edital_id": "id-do-edital",
      "orgao": "Nome do Órgão",
      "match_score": 85,
      "why_match": "Justificativa direta em 1 a 2 frases",
      "matching_skills": ["Skill 1", "Skill 2"],
      "missing_skills_to_study": ["Conteúdo a estudar 1", "Conteúdo 2"]
    }
  ],
  "strategic_study_plan": "Orientação tática de estudos detalhada em tópicos prioritários baseada nas datas das provas e no custo de aprendizagem.",
  "quick_win_tip": "Uma dica acionável de curto prazo para ganhar pontos rápidos nas provas de banca (Cebraspe/FGV/FCC)."
}
"""

    @classmethod
    def match_candidate(cls, user_profile: str, target_salary: float = 0.0) -> Dict[str, Any]:
        editais = ConcursoRadar.load_all()
        if not editais:
            return {"error": "Nenhum edital cadastrado no sistema"}

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and genai:
            try:
                client = genai.Client(api_key=api_key)
                
                editais_context = "\n".join([
                    f"- [{e['id']}] {e['orgao']} ({e['cargo']}) | Remuneração: R$ {e['remuneracao']} | Banca: {e['banca']} | Prova: {e['data_prova']} | Stack: {', '.join(e['stack'])}"
                    for e in editais
                ])
                
                prompt = f"""
Perfil e Habilidades do Candidato:
\"\"\"{user_profile}\"\"\"

Pretensão Salarial Mínima: R$ {target_salary or 0}

Editais de TI catalogados no Radar:
{editais_context}

Gere o diagnóstico completo de aderência e plano de estudos:
"""
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=cls.SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                print(f"[ProfileMatcherAI] Falha no Gemini, acionando motor analítico local: {e}")

        # Fallback Heurístico Local Robusto
        return cls._local_heuristic_matcher(user_profile, editais, target_salary)

    @classmethod
    def _local_heuristic_matcher(cls, user_profile: str, editais: List[Dict[str, Any]], target_salary: float) -> Dict[str, Any]:
        profile_lower = user_profile.lower()
        scored_matches = []

        for e in editais:
            # Pular se salário for menor que a pretensão mínima
            if target_salary and e.get("remuneracao", 0) < target_salary:
                continue

            stack = e.get("stack", [])
            matching = []
            missing = []

            for tech in stack:
                # Busca flexível por regex / substring
                tech_words = re.findall(r"\w+", tech.lower())
                found = any(w in profile_lower for w in tech_words if len(w) > 2)
                if found:
                    matching.append(tech)
                else:
                    missing.append(tech)

            total_techs = max(len(stack), 1)
            raw_ratio = len(matching) / total_techs
            
            # Bonificar se o candidato cita especificamente a área
            bonus = 0.15 if any(term in profile_lower for term in ["desenvolvedor", "engenheiro", "dados", "backend", "software", "nuvem", "ti"]) else 0.0
            
            final_score = int(min(round((raw_ratio + bonus) * 100), 98))
            # Garantir nota mínima realista
            final_score = max(final_score, 35)

            why = f"Você já cobre {len(matching)} de {len(stack)} requisitos centrais do edital do {e['sigla']}."
            if final_score >= 75:
                why += " Excelente alinhamento com sua bagagem prática atual!"
            elif final_score >= 50:
                why += " Boa base técnica, necessitando apenas focar nos tópicos de governança e regulação."
            else:
                why += " Exigirá um ciclo focado nos gaps técnicos antes da data da prova."

            scored_matches.append({
                "edital_id": e["id"],
                "orgao": e["orgao"],
                "cargo": e["cargo"],
                "remuneracao": e["remuneracao"],
                "data_prova": e.get("data_prova"),
                "match_score": final_score,
                "why_match": why,
                "matching_skills": matching,
                "missing_skills_to_study": missing
            })

        scored_matches.sort(key=lambda x: (x["match_score"], x["remuneracao"]), reverse=True)
        top = scored_matches[:4]

        # Consolidar tópicos mais frequentes que faltam
        missing_freq = {}
        for item in top:
            for m in item["missing_skills_to_study"]:
                missing_freq[m] = missing_freq.get(m, 0) + 1

        priority_topics = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        priority_str = ", ".join([p[0] for p in priority_topics]) if priority_topics else "Governança de TI e LGPD"

        return {
            "profile_summary": "Perfil Tecnológico Mapeado: Forte aderência a cargos de Engenharia de Software, Desenvolvimento e Ciência de Dados.",
            "top_matches": top,
            "strategic_study_plan": (
                f"1. Foco Imediato de Estudos: Priorize {priority_str}, que são cobrados em múltiplos editais de alto salário.\n"
                "2. Aproveitamento de Disciplinas Comuns: Como você já domina parte considerável da stack prática de programação e banco de dados, dedique 70% da sua carga horária às matérias regulatórias e discursivas da banca.\n"
                "3. Resolução Diária de Questões: Resolva ao menos 30 questões comentadas por dia focando especificamente no estilo da banca organizadora (Cebraspe ou Cesgranrio)."
            ),
            "quick_win_tip": "Em concursos federais de TI (como Bacen e BNDES), as questões de Governança (COBIT/ITIL) e LGPD costumam ser conceituais e literais. Dominar esses 2 temas garante pontos fáceis e decisivos em relação aos concorrentes que só estudam código."
        }
