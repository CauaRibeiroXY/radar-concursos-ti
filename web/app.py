import os
import sys
import json
from flask import Flask, render_template, request, jsonify

# Suporte UTF-8 no terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Path setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from core.radar import ConcursoRadar
from core.matcher import ProfileMatcherAI

app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, "templates"))
app.secret_key = "radar_concursos_ti_secret_key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/editais", methods=["GET"])
def get_editais():
    q = request.args.get("q", "")
    min_sal = float(request.args.get("min_salary", 0.0))
    status = request.args.get("status", "todos")
    banca = request.args.get("banca", "todos")
    tech = request.args.get("tech", "")

    results = ConcursoRadar.filter_editais(
        q=q,
        min_salary=min_sal,
        status=status,
        banca=banca,
        tech=tech
    )
    return jsonify(results)

@app.route("/api/edital/<edital_id>", methods=["GET"])
def get_edital(edital_id):
    edital = ConcursoRadar.get_by_id(edital_id)
    if not edital:
        return jsonify({"error": "Edital não encontrado"}), 404
    return jsonify(edital)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    stats = ConcursoRadar.get_stats()
    return jsonify(stats)

@app.route("/api/match_profile", methods=["POST"])
def match_profile():
    data = request.json or {}
    profile = data.get("profile", "").strip()
    target_salary = float(data.get("target_salary", 0.0))

    if not profile:
        return jsonify({"error": "Descreva suas habilidades ou perfil técnico"}), 400

    diagnosis = ProfileMatcherAI.match_candidate(profile, target_salary)
    return jsonify(diagnosis)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5060))
    print(f"[*] Radar de Concursos de TI ativo em http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
