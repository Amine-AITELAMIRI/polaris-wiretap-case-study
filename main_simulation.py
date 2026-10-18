# POLARIS_S8/main_simulation.py
from include import *
from fonctions.fx_construction_z  import z_construction_bsc
from fonctions.fx_construction_mi import H2
from fonctions.fx_metrics import calculer_bilan, afficher_bilan, sauvegarder_bilan
from fonctions import fx_privacy_amp
BILAN_JS = os.path.join(DOSSIER_RACINE, "json/bilan_securite.json")

# Seuil sur Z_eve : les sous-canaux avec Z_eve > ALPHA_WYNER sont opaques pour Eve.
# 0.85 garantit que chaque canal I a une qualité < 15 % pour Eve (Z_Eve > 0.85 ≈ bruit pur).
# Un seuil plus bas (ex. 0.60) inclut des canaux où Eve a encore ~40 % de qualité.
ALPHA_WYNER = 0.85
# Marge de sécurité sur la capacité : plus conservative quand N grand,
# car SCL (L≈4) a besoin de canaux très fiables.
def _safety_margin(N: int) -> float:
    if N <= 1024:
        return 0.85
    if N <= 4096:
        return 0.75
    return 0.70   # N=16384 : validé empiriquement avec SCL NAIVE L=4

def construire_masque_wyner_bsc(N, K, p_bob, p_eve):
    """Masque Wyner pour BSC wiretap — approche argsort-first.

    Étape 1 : sélectionner les K_max = floor(N * C_Bob * margin) meilleurs
              sous-canaux pour Bob (tri sur Z_Bob croissant).
              La marge dépend de N pour garantir BER_Bob ≈ 0% avec SCL NAIVE.
    Étape 2 : parmi ces K_max canaux, classifier en I / R selon Z_Eve :
              I = { Z_Eve(i) > ALPHA_WYNER }  → bits d'information secrets
              R = complémentaire dans K_max   → bits aléatoires (leurre)
    Tous les autres sont gelés (F).

    Retourne
    --------
    frozen_bits        : 0 sur I∪R, 1 sur F
    K_info             : min(K, |I|)
    K_total            : K_max = |I| + |R|
    indices_info_in_u  : positions dans u[0..K_max-1] portant le message
    """
    z_bob = z_construction_bsc(N, p_bob)
    z_eve = z_construction_bsc(N, p_eve)

    # Étape 1 — top K_max canaux pour Bob
    K_max     = int(N * (1.0 - H2(p_bob)) * _safety_margin(N))
    best_bob  = np.argsort(z_bob)[:K_max]
    top_k     = set(int(i) for i in best_bob)

    # Étape 2 — partition Wyner dans ces K_max canaux
    bits_I = {i for i in top_k if z_eve[i] > ALPHA_WYNER}
    bits_R = top_k - bits_I

    if len(bits_I) == 0:
        raise ValueError(
            f"Wyner: |I|=0 — aucun canal sécurisé "
            f"(p_bob={p_bob:.4f}, p_eve={p_eve:.4f}, alpha={ALPHA_WYNER}). "
            f"Essayez d'augmenter p_eve ou de réduire p_bob."
        )

    K_info  = min(K, len(bits_I))
    K_total = K_max   # garanti = |I| + |R|

    sorted_IR         = sorted(top_k)
    indices_info_in_u = np.array([k for k, ch in enumerate(sorted_IR) if ch in bits_I])
    indices_info_in_u = indices_info_in_u[:K_info]

    frozen_bits = np.ones(N, dtype=np.int32)
    for ch in sorted_IR:
        frozen_bits[ch] = 0

    print(f"Wyner: |I|={len(bits_I)}, |R|={len(bits_R)}, K_info={K_info}, "
          f"K_total={K_total}/{N} (taux={K_total/N:.3f}, capa Bob={1-H2(p_bob):.3f})")
    return frozen_bits, K_info, K_total, indices_info_in_u


def run_transmission(message_padded, frozen_bits, K, type_canal, param_bob, param_eve,
                     indices_info_in_u=None, K_total=None,
                     pa_k_secure=None, pa_seed=fx_privacy_amp.PA_SEED_DEFAUT):
    """Lance la transmission trame par trame.

    pa_k_secure : si fourni, active l'amplification de confidentialité.
                  K_secure bits de message → K bits dans les positions I.
    pa_seed     : graine publique pour la matrice PA (identique chez Bob).
    """
    print("Début de la transmission")

    pa_active  = (pa_k_secure is not None) and (indices_info_in_u is not None)
    chunk_size = pa_k_secure if pa_active else K   # taille de trame message

    i=0
    bob_all,eve_all = [],[]
    t0=time.time()
    while i < len(message_padded):
        trame = message_padded[i:i + chunk_size]  # K_secure (ou K_info) bits
        print("(While) i =",i)
        # --- EMETTEUR ---
        t1=time.time()
        if indices_info_in_u is not None:        # mode Wyner
            u = np.random.randint(0, 2, K_total, dtype=np.int8)
            if pa_active:
                # PA : K_secure bits → K_info bits avant placement dans I
                u_pa = fx_privacy_amp.pa_encode(trame, K, pa_seed)
                u[indices_info_in_u] = u_pa
            else:
                u[indices_info_in_u] = trame
        else:
            u = trame
        message_encode,frozen_bits=fx_emetteur.encoder(u,frozen_bits)
        t2=time.time()
        print("Encoder",(t2-t1))

        message_module=fx_emetteur.moduler_bpsk(message_encode)
        t3=time.time()
        print("Moduler",t3-t2)


        # --- CANAL
        signal_bob, signal_eve = fx_canal.canal(message_module,type_canal,param_bob,param_eve)
        t4=time.time()
        print("Canal",t4-t3)

        # --- RECEPTEUR
        llrs_bob, llrs_eve=fx_recepteur.demoduler_bpsk(signal_bob,signal_eve,type_canal,param_bob,param_eve)
        t5=time.time()
        print("Demoduler",t5-t4)

        message_recu_bob=fx_recepteur.decoder(llrs_bob, frozen_bits)
        message_recu_eve=fx_recepteur.decoder(llrs_eve, frozen_bits)
        t6=time.time()
        print("Decoder",t6-t5)

        if indices_info_in_u is not None:        # mode Wyner : extraire uniquement les bits I
            bits_bob_I = message_recu_bob[indices_info_in_u]
            bits_eve_I = message_recu_eve[indices_info_in_u]
            if pa_active:
                # PA : K_info bits reçus → K_secure bits message
                bits_bob_I = fx_privacy_amp.pa_decode(bits_bob_I, chunk_size, pa_seed)
                bits_eve_I = fx_privacy_amp.pa_decode(bits_eve_I, chunk_size, pa_seed)
            bob_all.append(bits_bob_I)
            eve_all.append(bits_eve_I)
        else:
            bob_all.append(message_recu_bob)
            eve_all.append(message_recu_eve)
        t7=time.time()
        print("Append",t7-t6)


        i += chunk_size

    # Concaténation
    message_recu_bob = np.concatenate(bob_all)
    message_recu_eve = np.concatenate(eve_all)

    print("Fin de la transmission")

    return message_recu_bob,message_recu_eve

def run_simulation():


    print("Effacage des anciennes erreurs")
    fx_json.effacer_erreurs()

    print("Chargement des paramètres")
    params, err = fx_json.lire_param()
    if err:
        fx_json.ajouter_erreur("main_simulation", err)
        err=None

    if params["simulation"] == True:
        print("-----------------Démarrage de la simulation-----------------")
        

        N = params["N"]
        K = params["K"]

        type_canal = params["parametres_simulation"]["type_canal"]

        if type_canal == "BSC":
            param_bob = params["parametres_simulation"]["canal_bsc"]["p_bob"]
            param_eve = params["parametres_simulation"]["canal_bsc"]["p_eve"]

        elif type_canal == "AWGN":
            param_bob = params["parametres_simulation"]["canal_awgn"]["snr_bob"]
            param_eve = params["parametres_simulation"]["canal_awgn"]["snr_eve"]

        else:
            fx_json.ajouter_erreur("main_simulation", "Type de canal inconnu.")
            return

        print("Lecture du message")
        time_message, donnees, err = fx_json.lire_message(TX_JS)
        if err:
            fx_json.ajouter_erreur("main_simulation", err)
        if donnees is None:
            fx_json.ajouter_erreur("main_simulation", "Message source vide, simulation arrêtée.")
            return

        message_envoye = fx_interface.bits_to_numpy(donnees)

        mode_securise = bool(params.get("mode_securise", False))
        use_pa = bool(params.get("amplification_confidentialite", False))

        print("Calcul du masque polaire")
        K_secure_pa = None                       # PA désactivée par défaut
        if mode_securise and type_canal == "BSC":
            try:
                frozen_bits, K_info, K_total, indices_info_in_u = \
                    construire_masque_wyner_bsc(N, K, param_bob, param_eve)
            except ValueError as e:
                # p_bob ≥ p_eve ou |I|=0 : pas de capacité secrète Wyner exploitable.
                # On continue avec un masque polaire classique (Bob) : Bob et Eve
                # décodent le même mot si leurs canaux sont identiques (démo « pire cas »).
                print(f"Wyner indisponible ({e})")
                print("→ Bascule masque polaire classique (pas de partition I/R/F).")
                frozen_bits = fx_emetteur.generer_masque_polaire(
                    K, N, type_canal, param_bob)
                K_info, K_total, indices_info_in_u = K, None, None
            else:
                if use_pa:
                    K_secure_pa = fx_privacy_amp.compute_k_secure(
                        K_info, param_bob, param_eve)
                    print(f"PA activée : K_info={K_info} → K_secure={K_secure_pa} "
                          f"(Cs/C_bob={K_secure_pa/K_info:.2f})")
                else:
                    print("PA désactivée (amplification_confidentialite=false dans param.json).")
        else:                                    # AWGN ou mode standard : masque Bob seul
            frozen_bits = fx_emetteur.generer_masque_polaire(K, N, type_canal, param_bob)
            K_info, K_total, indices_info_in_u = K, None, None

        print("Padding du message")
        L_avant_padd = len(message_envoye)
        chunk_size   = K_secure_pa if K_secure_pa is not None else K_info
        pad_len = (chunk_size - (L_avant_padd % chunk_size)) % chunk_size
        if pad_len > 0:
            message_padded = np.concatenate([message_envoye, np.zeros(pad_len, dtype=np.int8)])
        else:
            message_padded = message_envoye

        L_apres_padd = len(message_padded)
        print("Taille: ",L_avant_padd,"->",L_apres_padd)

        # Envoi du message (à bob et eve)
        message_recu_bob, message_recu_eve = run_transmission(
            message_padded, frozen_bits, K_info, type_canal, param_bob, param_eve,
            indices_info_in_u=indices_info_in_u, K_total=K_total,
            pa_k_secure=K_secure_pa)


        print("Suppression du padding")
        message_recu_bob, message_recu_eve = message_recu_bob[:L_avant_padd], message_recu_eve[:L_avant_padd]
        if type_canal == "BSC":
            print("Calcul du bilan de sécurité")
            C_bob = 1.0 - H2(param_bob)
            C_eve = 1.0 - H2(param_eve)
            Cs    = max(0.0, C_bob - C_eve)
            pa_info = None
            if K_secure_pa is not None:
                pa_info = {
                    "K_info":       K_info,
                    "K_secure":     K_secure_pa,
                    "ratio_cs_cbob": round(Cs / C_bob if C_bob > 1e-9 else 0.0, 4),
                    "seed":         fx_privacy_amp.PA_SEED_DEFAUT,
                }
            bilan = calculer_bilan(message_envoye, message_recu_bob, message_recu_eve,
                                   param_bob, param_eve, pa_info=pa_info)
            afficher_bilan(bilan)
            sauvegarder_bilan(bilan, BILAN_JS)
        print("Sauvegarde du message")
        donnees_bob = fx_interface.numpy_to_bits(message_recu_bob)
        donnees_eve = fx_interface.numpy_to_bits(message_recu_eve)
        fx_json.ecrire_message(donnees_bob,RX_BOB_JS)
        fx_json.ecrire_message(donnees_eve,RX_EVE_JS)

        print("-----------------Fin de la simulation-----------------")

    else:
        err="Mauvais choix de progamme: simulation."
        fx_json.ajouter_erreur("run_main()", err)
        err=None

if __name__ == "__main__":
    run_simulation()
