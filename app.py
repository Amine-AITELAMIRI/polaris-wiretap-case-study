# app.py - Interface POLARIS 
from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from include import *
import requests
import socket
import qrcode
import sys
from io import BytesIO
from gallery_paths import resolve_gallery_image

PORT = 5001

app = Flask(
    __name__,
    template_folder=os.path.join(DOSSIER_RACINE, "interface", "templates"),
    static_folder=os.path.join(DOSSIER_RACINE, "interface", "static"),
)
app.secret_key = os.urandom(24)
app.config["SESSION_COOKIE_NAME"] = f"polaris_{PORT}"

SERVER_URL = "http://localhost:5000"
TIMEOUT = 35

# --- Fonction pour trouver IP locale
def generate_qrcode():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Dire au système de résoudre la route réseau par défaut.
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    
    url = f"http://{ip}:{PORT}"
    print(f"\n  PROJET POLARIS — {url}\n")

    qr = qrcode.make(url)
    qr.save(f"qrcode_app{PORT}.png")

# ── NOUVEAU : Calculs Physiques (Carte Tactique) ──────────────────────────────
D_MAX_CARTE = 100.0  # distance max de la carte en mètres

def distance_to_params(distance_m):
    """p = 0.5*(d/D_MAX)^2 : varie de 0 (d=0) à 0.5 (d=D_MAX), loi en 1/d^2."""
    d = max(float(distance_m), 0.1)
    d = min(d, D_MAX_CARTE)
    p = 0.5 * (d / D_MAX_CARTE) ** 2
    snr_db = 20.0 - 20.0 * math.log10(d)
    return round(snr_db, 2), round(p, 4)

# ── Fonctions communication server
def server_get(path, **kwargs):
    try:
        res = requests.get(f"{SERVER_URL}{path}", timeout=kwargs.pop("timeout", TIMEOUT), **kwargs)
        return res.json()
    except Exception:
        return None

def server_post(path, **kwargs):
    try:
        res = requests.post(f"{SERVER_URL}{path}", timeout=kwargs.pop("timeout", TIMEOUT), **kwargs)
        return res.json()
    except Exception:
        return None

def report_error(nom, message,version):
    server_post("/api/sync", params={
        "version": version,                    
        "role":    session.get("role", "inconnu"),
        "error": {"nom": nom, "message": message}
    })

# ------Etat local
state = {
    "alice": {"online": False, "ready": False},
    "bob": {"online": False, "ready": False},
    "eve": {"online": False, "ready": False},
    "config": {},
    "meta_data": {},
    "errors": {"count": 0, "list": []},
    "version": -1,
}
state_lock = threading.Lock()
state_changed = threading.Condition(state_lock)

def get_state():
    with state_lock:
        return dict(state)

def state_loop():
    """Thread de long poll : Etat local."""
    version = state.get("version", -1)
    while True:
        try:
            data = server_get("/api/sync",params={"version": version},timeout=TIMEOUT)
            version = data.get("version", version)
            with state_changed:
                state.update(data)
                state_changed.notify_all()
        except Exception:
            print("Erreur synchro server")
            time.sleep(3)

#------Authentification 

@app.route("/", methods=["GET", "POST"])
def login():

    state = get_state()
    if session.get("role"):
        return redirect(url_for("terminal"))
    
    roles_online = {}
    for r in ROLES:
        roles_online[r] = (state.get(r) or {}).get("online", False)

    if request.method == "POST":
        role = request.form.get("role")
        if role in ROLES:
            if roles_online.get(role):
                return render_template("login.html", error=f"Le rôle {role.upper()} est déjà connecté.", roles_online=roles_online)

            session["role"] = role
            session["configured"] = False
            session["simulation"] = False
            # --- Envoi du role au server
            server_post("/api/sync", json={"role": role, "online": True, "ready": False})
            return redirect(url_for("terminal"))
        
    return render_template("login.html",roles_online=roles_online)

@app.route("/logout")
def logout():
    role = session.get("role")
    if role:
        server_post("/api/sync", json={"role": role, "online": False, "ready": False})
    session.clear()

    return redirect(url_for("login"))

@app.route("/api/roles")
def api_roles():
    """Retourne juste le statut online de chaque rôle."""
    client_version = int(request.args.get("version", -1))

    with state_changed:
        if state.get("version", -1) == client_version:
            state_changed.wait(timeout=20)
            
    return jsonify({
        "alice": (state.get("alice") or {}).get("online", False),
        "bob":   (state.get("bob")   or {}).get("online", False),
        "eve":   (state.get("eve")   or {}).get("online", False),
        "version": state.get("version", -1)
    })

# ── Terminal

@app.route("/terminal")
def terminal():
    if "role" not in session:
        return redirect(url_for("login"))
    state  = get_state()
    params = state.get("config") or {}

    return render_template("terminal.html",
        role       = session["role"],
        configured = session.get("configured", False),
        defaut     = DEFAUT_VAR,
        params     = params
    )

# ── Sync

@app.route("/api/sync")
def sync():
    """Long poll — le navigateur appelle cette route, app.py attend server.py."""
    if not session.get("role"):
        return jsonify(ok=False), 401

    client_version = int(request.args.get("version", -1))

    with state_changed:
        # Si le client est à jour, on met cette requête HTTP en pause
        if state.get("version", -1) == client_version:
            state_changed.wait(timeout=20)
        
        # On renvoie l'état complet
        return jsonify(**state)

# ── Alice : configuration

@app.route("/configure", methods=["POST"])
def configure():
    if session.get("role") != "alice":
        return jsonify(ok=False, error="Non autorisé"), 403
    f = request.form

    # Distances fournies par la carte tactique (en mètres)
    # SNR et p sont TOUJOURS dérivés des distances — jamais saisis manuellement
    try:
        dist_ab = float(f.get("dist_ab", 10))
        dist_ae = float(f.get("dist_ae", 20))
    except (ValueError, TypeError):
        dist_ab, dist_ae = 10.0, 20.0

    snr_bob, p_bob = distance_to_params(dist_ab)
    snr_eve, p_eve = distance_to_params(dist_ae)

    res = server_post("/api/sync", json={
        "role": "alice",
        "config": {
            "mode":       f.get("mode","WIRETAP"),
            "conn_mode":  f.get("conn_mode"),
            "N":          f.get("N"),
            "K":          f.get("K"),
            "type_canal": f.get("type_canal"),
            "snr_bob":    snr_bob,
            "snr_eve":    snr_eve,
            "p_bob":      p_bob,
            "p_eve":      p_eve,
        }
    })

    if res and res.get("ok"):
        session["configured"] = True
        session["simulation"] = (f.get("conn_mode") == "HORS LIGNE")
        return jsonify(ok=True)
    else:
        return jsonify(ok=False, error="Erreur serveur"), 500


# ── Alice : envoi

@app.route("/send", methods=["POST"])
def send():
    if session.get("role") != "alice":
        return jsonify(ok=False, error="Non autorisé"), 403
    if not session.get("configured"):
        return jsonify(ok=False, error="Canal non initialisé."), 403

    message = request.form.get("message", "")
    image_filename = request.form.get("image_filename", "")

    if image_filename:
        type_msg = "IMAGE"
        print("\n Image: ",image_filename,"OK ?\n")
    else:
        type_msg = fx_interface.determiner_type_message(message, None)

    try:
        if type_msg == "IMAGE":
            try:
                chemin_image = resolve_gallery_image(
                    os.path.join(app.static_folder, "gallery"), image_filename
                )
            except ValueError:
                return jsonify(ok=False, error="Image de galerie invalide"), 400
            
            with open(chemin_image, "rb") as image_stream:
                img_np, dim = fx_interface.image_to_numpy(image_stream)
                message_bits = fx_interface.numpy_to_bits(img_np)

        elif type_msg == "BINAIRE":
            message_bits = message.strip().replace(" ", "")
            dim = [0,0,0]

        elif type_msg == "TEXTE":
            if not message.strip():
                return jsonify(ok=False, error="Message vide.")
            message_bits = fx_interface.text_to_bits(message)
            dim = [0,0,0]
        
        res = server_post("/api/sync", json={
            "role":  "alice",
            "ready": False,
            "meta_data": {
                "type":     type_msg,
                "longueur": len(message_bits),
                "dim_img":  list(dim),
            }
        })
        if not res or not res.get("ok"):
            return jsonify(ok=False, error="Erreur envoi métadonnées"), 500
        with state_lock:
            is_simu = state.get("config", {}).get("simulation", False)

        # ── Simulation
        if is_simu:
            server_post("/api/sync", json={"role": "alice", "ready": True})

            res = server_post("/api/simulation",json={"bits": message_bits}, timeout=130)

            server_post("/api/sync", json={"role": "alice", "ready": False})

            if not res or not res.get("ok"):
                return jsonify(ok=False, error=res.get("error", "Erreur simulation")), 500
            return jsonify(ok=True, type=type_msg)

        # ── Radio
        else:

            result = subprocess.run([sys.executable, "configuration_emetteur.py"],capture_output=True, text=True, timeout=TIMEOUT, cwd=DOSSIER_RACINE)
            if result.returncode != 0:
                return jsonify(ok=False, error="Erreur config émetteur"), 500
            
            server_post("/api/sync", json={"role": "alice", "ready": True})

            with state_changed:
                state_changed.wait(timeout=1)

                if state.get("bob").get("ready"):
                    result = subprocess.run([sys.executable, "radio_send.py"],capture_output=True, text=True, timeout=60, cwd=DOSSIER_RACINE)
                    server_post("/api/sync", json={"role": "alice", "ready": False})

                    if result.returncode != 0:
                        return jsonify(ok=False, error="Erreur émission"), 500
                    return jsonify(ok=True, type=type_msg)

            server_post("/api/sync", json={"role": "alice", "ready": False})
            return jsonify(ok=False, error="Bob n'est pas prêt (timeout 30s).")

    except subprocess.TimeoutExpired as e:
        report_error("send", str(e),state["version"])
        return jsonify(ok=False, error="Timeout"), 500
    except Exception as e:
        report_error("send", str(e),state["version"])
        return jsonify(ok=False, error=f"Erreur envoi message : {e}"), 500


# ── Bob / Eve : lecture RX ────────────────────────────────────────────────────

@app.route("/rx")
def rx():
    role = session.get("role")
    if not role:
        return jsonify(ok=False), 401
    with state_lock:
        is_simu = state.get("config", {}).get("simulation", False)

    target  = request.args.get("target", role)
    # ── Mode radio 
    if not is_simu:
        with state_changed:
            if not state.get("alice", {}).get("ready"):
                state_changed.wait(timeout=TIMEOUT)

            if state.get("alice", {}).get("ready"):
                meta_data = state.get("meta_data") or {}

                # Configurer le récepteur
                result = subprocess.run([sys.executable, "configuration_recepteur.py"],capture_output=True, text=True, timeout=TIMEOUT, cwd=DOSSIER_RACINE)
                if result.returncode != 0:
                    report_error("rx", "Erreur configuration récepteur",state["version"])
                    return jsonify(ok=False, error="Erreur config récepteur"), 500

                try:
                    proc = subprocess.Popen([sys.executable, "recevoir.py"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=DOSSIER_RACINE)

                    server_post("/api/sync", json={"role": role, "ready": True})
                    stdout, stderr = proc.communicate()

                except subprocess.TimeoutExpired:
                    proc.kill()
                    server_post("/api/sync", json={"role": role, "ready": False})
                    return jsonify({"ok": False, "error": "Timeout réception radio"}), 500

                finally:
                    # Attendre la fin de la réception
                    server_post("/api/sync", json={"role": role, "ready": False})

                if proc.returncode != 0:
                    return jsonify(ok=False, error="Erreur réception radio"), 500

                return format_result(time.time(),stdout, target, meta_data)

        return jsonify(ok=False, error="Alice n'a pas émis (timeout).")

    # ── Mode simulation
    else :
        # Lire le résultat sur le serveur
        res = server_get("/api/simulation", params={"role": target})
        if not res or not res.get("ok"):
            return jsonify(ok=True, ready=False)

        meta_data = state.get("meta_data", {})
        time_msg = res.get("time")
        bits = res.get("bits","")
        return format_result(time_msg,bits, target, meta_data)

def format_result(time_msg,bits, target, meta_data):
    type_msg = meta_data.get("type",DEFAUT_VAR["MSG_TYPE"])
    dim = meta_data.get("dim_img")
    data = {"ok": True, "ready": True, "time": time_msg, "type": type_msg}

    if type_msg == "IMAGE":
        try:
            bits_np = fx_interface.bits_to_numpy(bits)
            img = fx_interface.numpy_to_image(bits_np,dim)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            img_b64 = base64.b64encode(buffer.read()).decode()
            data["image"] = True
            data["content"] = img_b64
        except Exception as e:
            data["image_error"] = True

    elif type_msg == "TEXTE":
        data["content"] = fx_interface.bits_to_text(bits)
    elif type_msg =="BINAIRE" or type_msg=="INCONNU":
        data["content"] = bits

    if target == "bob":
        data["error_count"] = get_state().get("errors", {}).get("count", 0)

    return jsonify(**data)

@app.route('/api/security-stats')
def security_stats_relay():
    # On demande les stats au serveur central
    res = requests.get(f"{SERVER_URL}/api/security-stats")
    return jsonify(res.json())

# ── Erreurs 

@app.route("/errors/clear", methods=["POST"])
def clear_errors():
    """Efface toutes les erreurs."""
    res = server_post("/api/sync", json={"role": session.get("role", "inconnu"),"clear_errors": True})
    return jsonify(**(res or {"ok": False}))

if __name__ == "__main__":

    init = server_get("/api/sync")
    if init is None:
        print(f"Serveur indisponible ({SERVER_URL}) — lancez server.py d'abord.")
        exit(1)

    else:
        print(f"Connecté au Serveur ({SERVER_URL}) !")

        with state_lock:
            state.update(init)

        threading.Thread(target=state_loop, daemon=True).start()

        generate_qrcode()
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
