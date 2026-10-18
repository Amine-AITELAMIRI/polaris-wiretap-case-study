# server.py - Serveur central POLARIS
from flask import Flask, request, jsonify
from include import *
import sys

server = Flask(__name__)

# ── État global
TIMEOUT_DECONNECT = 180 # 3 min sans nouvelle on deconnecte de force
TIMEOUT_POLL = 30

state = {
    "alice":     {"online": False, "ready": False, "last_seen": 0},
    "bob":       {"online": False, "ready": False, "last_seen": 0},
    "eve":       {"online": False, "ready": False, "last_seen": 0},
    "version":   0,
}

changed = threading.Condition()

def changement(now):
    """Incrémente version"""
    refresh_online(now)
    state["version"] += 1
    changed.notify_all()

def refresh_online(now):
    """Actualise le statut online de chaque rôle."""
    for r in ROLES:
        if (now - state[r]["last_seen"]) > TIMEOUT_DECONNECT:
            if state[r]["online"] == True:
                state[r]["online"] = False
                state[r]["ready"] = False   #déconnexion => plus prêt

def snapshot():
    """Dictionnaire de l'état actuel complet."""

    config, _ = fx_json.lire_param()
    meta_data = fx_json.lire_meta_data()
    n_err, errs  = fx_json.lire_erreurs()

    return {
        "alice":     dict(state["alice"]),
        "bob":       dict(state["bob"]),
        "eve":       dict(state["eve"]),
        "config":    config or {},
        "meta_data": meta_data or {},
        "errors":    {"count": n_err, "list": errs},
        "version":   state["version"]
    }


# ── /api/sync 

@server.route("/api/sync", methods=["GET", "POST"])
def sync():
    """
    POST  {role, online?, ready?, config?, meta_data?,error?,clear_errors?}
    GET   ?version=N&role=R
    """

    now = time.time()

    # ── POST 
    if request.method == "POST":
        data = request.json or {}
        role = data.get("role")

        if role not in ROLES:
            return jsonify(ok=False, error="Rôle inconnu"), 400

        with changed:
            state[role]["last_seen"] = now

            if "online" in data:
                state[role]["online"] = bool(data["online"])

            if "ready" in data:
                state[role]["ready"] = bool(data["ready"])

            if "config" in data:
                conf = data["config"]
                try:
                    fx_json.ecrire_param(
                        nom          = "INTERFACE_SESSION",
                        mode_securise= conf.get("mode") == "WIRETAP",
                        simulation   = conf.get("conn_mode") == "HORS LIGNE",
                        N            = int(conf.get("N",        DEFAUT_VAR["N"])),
                        K            = int(conf.get("K",        DEFAUT_VAR["K"])),
                        type_canal   = conf.get("type_canal",   DEFAUT_VAR["type_canal"]),
                        snr_bob      = float(conf.get("snr_bob",DEFAUT_VAR["snr_bob"])),
                        snr_eve      = float(conf.get("snr_eve",DEFAUT_VAR["snr_eve"])),
                        p_bob        = float(conf.get("p_bob",  DEFAUT_VAR["p_bob"])),
                        p_eve        = float(conf.get("p_eve",  DEFAUT_VAR["p_eve"])),
                        amplification_confidentialite=bool(
                            conf.get(
                                "amplification_confidentialite",
                                DEFAUT_VAR.get("amplification_confidentialite", False),
                            )
                        ),
                    )
                except Exception as e:
                    return jsonify(ok=False, error=f"Erreur écriture config : {e}"), 500

            if "meta_data" in data:
                try:
                    fx_json.ecrire_meta_data(data["meta_data"])
                except Exception as e:
                    return jsonify(ok=False, error=f"Erreur écriture meta_data : {e}"), 500

            if "error" in data:
                try:
                    fx_json.ajouter_erreur(f"{role}:{data['error'].get('nom', '?')}",data["error"].get("message", "*"))
                except Exception as e:
                    return jsonify(ok=False, error=f"Erreur log : {e}"), 500

            if "clear_errors" in data:
                try:
                    fx_json.effacer_erreurs()
                except Exception as e:
                    return jsonify(ok=False, error=f"Erreur effacement : {e}"), 500

            #Pour la prise en compte des changements 
            changement(now)

        return jsonify(ok=True)

    # ── GET 
    version = request.args.get("version", -1, type=int)

    with changed:

        if state["version"] == version:
            changed.wait(timeout=TIMEOUT_POLL)

        res = snapshot()

    return jsonify(**res)


# ── /api/simulation 

@server.route("/api/simulation", methods=["GET", "POST"])
def simulation():
    """
    POST {bits}: lance main_simulation.py.
    GET  ?role=bob|eve : Bob/Eve lisent leur résultat.
    """
    if request.method == "POST":
        data = request.json or {}
        bits = data.get("bits")

        if not bits:
            return jsonify(ok=False, error="Pas de message"), 400

        try:
            fx_json.ecrire_message(bits)
            result = subprocess.run([sys.executable, "main_simulation.py"],capture_output=True, text=True, timeout=180,cwd=DOSSIER_RACINE)

            if result.returncode != 0:
                return jsonify(ok=False, error=result.stderr or result.stdout), 500
            with changed:
                changement(time.time())

            return jsonify(ok=True)

        except subprocess.TimeoutExpired:
            return jsonify(ok=False, error="Timeout simulation"), 500
        except Exception as e:
            return jsonify(ok=False, error=f"Erreur Simulation : {e}"), 500

    # GET
    role = request.args.get("role")
    if role not in ("bob", "eve"):
        return jsonify(ok=False, error="Rôle invalide"), 400

    js_file = RX_BOB_JS if role == "bob" else RX_EVE_JS
    time_msg, bits_recus, err = fx_json.lire_message(js_file)

    if err:
        return jsonify(ok=False, error=err), 404

    return jsonify(ok=True, role=role, time=time_msg, bits=bits_recus)

@server.route('/api/security-stats', methods=['GET'])
def get_security_stats():
    # Chemin vers ton fichier de stats
    path = os.path.join(DOSSIER_RACINE, "json", "bilan_securite.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Fichier non trouvé"}), 404

if __name__ == "__main__":
    print("\n  POLARIS — Serveur central — http://0.0.0.0:5000\n")
    server.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
