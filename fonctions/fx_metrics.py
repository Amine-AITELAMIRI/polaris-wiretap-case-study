"""
fx_metrics.py — Métriques de sécurité du canal wiretap de Wyner
================================================================
Fournit :
  - IM théorique de chaque canal (BSC)
  - Capacité secrète  Cs = C_Bob − C_Eve
  - IM empirique I(U ; V) calculée sur les bits simulés
  - TEB (taux d'erreur binaire)
  - Bilan complet affiché et/ou sauvegardé en JSON
"""

import numpy as np
import json
import os
from scipy.optimize import brentq

def _H2(p: float) -> float:
    p = float(np.clip(p, 1e-12, 1.0 - 1e-12))
    return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)

def mi_theorique_bsc(p: float) -> float:
    
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p doit être dans [0, 1], reçu {p}.")
    return float(np.clip(1.0 - _H2(p), 0.0, 1.0))


def capacite_secrete_bsc(p_bob: float, p_eve: float) -> dict:
   
    C_bob = mi_theorique_bsc(p_bob)
    C_eve = mi_theorique_bsc(p_eve)
    Cs    = max(0.0, C_bob - C_eve)

    return {
        "C_bob": round(C_bob, 6),
        "C_eve": round(C_eve, 6),
        "Cs":    round(Cs,    6),
        "p_bob": p_bob,
        "p_eve": p_eve,
    }

def mi_empirique_binaire(bits_envoyes: np.ndarray,
                         bits_recus: np.ndarray) -> float:
    
    bits_envoyes = np.asarray(bits_envoyes, dtype=np.int8).flatten()
    bits_recus   = np.asarray(bits_recus,   dtype=np.int8).flatten()

    N = len(bits_envoyes)
    if N == 0:
        return 0.0
    if N != len(bits_recus):
        raise ValueError("bits_envoyes et bits_recus doivent avoir la même longueur.")

    # Distribution jointe sur {(0,0),(0,1),(1,0),(1,1)}
    joint = np.zeros((2, 2), dtype=np.float64)
    for u, v in zip(bits_envoyes, bits_recus):
        joint[int(u), int(v)] += 1
    joint /= N                               # normalisation → probabilités

    p_u = joint.sum(axis=1)                  # marginales P(U)
    p_v = joint.sum(axis=0)                  # marginales P(V)

    mi = 0.0
    for u in range(2):
        for v in range(2):
            p_uv = joint[u, v]
            if p_uv > 0 and p_u[u] > 0 and p_v[v] > 0:
                mi += p_uv * np.log2(p_uv / (p_u[u] * p_v[v]))

    return float(np.clip(mi, 0.0, 1.0))


def teb(bits_envoyes: np.ndarray, bits_recus: np.ndarray) -> float:
    """Retourne le TEB en pourcentage (0–100)."""
    bits_envoyes = np.asarray(bits_envoyes, dtype=np.int8).flatten()
    bits_recus   = np.asarray(bits_recus,   dtype=np.int8).flatten()
    N = len(bits_envoyes)
    if N == 0:
        return 0.0
    return float(np.sum(np.abs(bits_envoyes - bits_recus)) * 100.0 / N)

def calculer_bilan(bits_envoyes: np.ndarray,
                   bits_bob: np.ndarray,
                   bits_eve: np.ndarray,
                   p_bob: float,
                   p_eve: float,
                   pa_info: dict = None) -> dict:
    
    # ── Métriques théoriques ──────────────────────────────────────
    cap = capacite_secrete_bsc(p_bob, p_eve)

    # ── Métriques empiriques ──────────────────────────────────────
    teb_bob = teb(bits_envoyes, bits_bob)
    teb_eve = teb(bits_envoyes, bits_eve)

    mi_bob     = mi_empirique_binaire(bits_envoyes, bits_bob)  # I(Source ; Bob)
    mi_eve     = mi_empirique_binaire(bits_envoyes, bits_eve)  # I(Source ; Eve)
    mi_bob_eve = mi_empirique_binaire(bits_bob, bits_eve)      # I(Bob ; Eve)

    avantage_bob = max(0.0, mi_bob - mi_eve)

    bilan = {
        "theorique": {
            "p_bob":       cap["p_bob"],
            "p_eve":       cap["p_eve"],
            "C_bob":       cap["C_bob"],
            "C_eve":       cap["C_eve"],
            "Cs_capacite": cap["Cs"],
        },
        "empirique": {
            "teb_bob_pct":   round(teb_bob,     4),
            "teb_eve_pct":   round(teb_eve,     4),
            "mi_source_bob": round(mi_bob,      6),
            "mi_source_eve": round(mi_eve,      6),
            "mi_bob_eve":    round(mi_bob_eve,  6),
            "avantage_bob":  round(avantage_bob,6),
        }
    }
    if pa_info is not None:
        bilan["amplification_confidentialite"] = pa_info
    return bilan


def afficher_bilan(bilan: dict):
    """Affiche le bilan de sécurité de façon lisible dans la console."""
    th = bilan["theorique"]
    em = bilan["empirique"]
    sep = "=" * 60

    print(f"\n{sep}")
    print(f"  BILAN DE SÉCURITÉ — Canal BSC")
    print(sep)
    print(f"  p_bob = {th['p_bob']}   |   p_eve = {th['p_eve']}")

    print(f"\n  ── Capacités théoriques ──────────────────────────")
    print(f"  C_Bob          = {th['C_bob']:.4f} bit/usage")
    print(f"  C_eve          = {th['C_eve']:.4f} bit/usage")
    print(f"  Cs (secrète)   = {th['Cs_capacite']:.4f} bit/usage", end="")
    if th["Cs_capacite"] > 0:
        print("  ✓ Transmission sécurisée possible")
    else:
        print("  ✗ Aucune capacité secrète !")

    print(f"\n  ── Résultats empiriques ──────────────────────────")
    print(f"  TEB Bob         = {em['teb_bob_pct']:.3f} %")
    print(f"  TEB Eve         = {em['teb_eve_pct']:.3f} %")
    print(f"\n  I(Source ; Bob) = {em['mi_source_bob']:.4f} bit")
    print(f"  I(Source ; Eve) = {em['mi_source_eve']:.4f} bit")
    print(f"  I(Bob ; Eve)    = {em['mi_bob_eve']:.4f} bit  ← corrélation entre récepteurs")
    print(f"\n  Avantage Bob    = {em['avantage_bob']:.4f} bit", end="")
    if em["avantage_bob"] > 0.05:
        print("  ✓ Bob est significativement avantagé")
    elif em["avantage_bob"] > 0:
        print("  ~ Avantage faible")
    else:
        print("  ✗ Aucun avantage détecté (Eve aussi bien informée que Bob)")

    pa = bilan.get("amplification_confidentialite")
    if pa:
        print(f"\n  ── Amplification de confidentialité ──────────────")
        print(f"  K_info          = {pa['K_info']} bits/trame  (positions I)")
        print(f"  K_secure        = {pa['K_secure']} bits/trame  (après compression)")
        print(f"  Taux sécurisé   = {pa['K_secure']/pa['K_info']:.2f}  (Cs/C_bob ≈ {pa['ratio_cs_cbob']:.2f})")
        print(f"  Graine PA       = {pa['seed']}  (publique, partagée Alice–Bob)")

    print(sep + "\n")


def sauvegarder_bilan(bilan: dict, fichier: str):
    """Sauvegarde le bilan dans un fichier JSON."""
    os.makedirs(os.path.dirname(fichier), exist_ok=True)
    with open(fichier, "w") as f:
        json.dump(bilan, f, indent=4, ensure_ascii=False)
    print(f"  Bilan sauvegardé → {fichier}")