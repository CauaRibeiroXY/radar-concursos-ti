import sys
import os

# Suporte UTF-8 no terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.radar import ConcursoRadar
from core.matcher import ProfileMatcherAI

def test_pipeline():
    print("[1] Testando ConcursoRadar.load_all()...")
    editais = ConcursoRadar.load_all()
    assert len(editais) > 0, "Nenhum edital retornado"
    print(f"    Total de editais carregados: {len(editais)}")

    print("[2] Testando ConcursoRadar.filter_editais()...")
    python_editais = ConcursoRadar.filter_editais(tech="Python")
    assert len(python_editais) > 0, "Filtro de Python falhou"
    print(f"    Editais com Python: {len(python_editais)}")

    print("[3] Testando ConcursoRadar.get_stats()...")
    stats = ConcursoRadar.get_stats()
    assert stats["maior_salario"] > 20000, "Maior salário incorreto"
    print(f"    Maior salário: R$ {stats['maior_salario']}")

    print("[4] Testando ProfileMatcherAI.match_candidate()...")
    user_skills = "Sou desenvolvedor Python, trabalho com Docker, PostgreSQL e APIs REST. Tenho interesse em inteligência artificial."
    res = ProfileMatcherAI.match_candidate(user_skills, target_salary=12000.0)
    assert "top_matches" in res, "Chave top_matches não encontrada"
    print(f"    Diagnóstico gerado para: {len(res['top_matches'])} editais recomendados")
    print(f"    Top Match: {res['top_matches'][0]['orgao']} com {res['top_matches'][0]['match_score']}% de aderência")

    print("[OK] Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    test_pipeline()
