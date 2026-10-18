"""
test_wiretap_ber.py — Validation statistique du système Wyner polar wiretap

Mesure le BER de Bob et d'Eve sur N_FRAMES trames indépendantes et compare.
Bob doit avoir un BER proche de 0, Eve un BER proche de 0.5.

Usage :
    python tests/test_wiretap_ber.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import aff3ct
import streampu as spu

from fonctions.fx_construction_z  import z_construction_bsc
from fonctions.fx_construction_mi import H2, mi_construction_bsc

# ─────────────────────────────────────────────────────────────────
#  Paramètres du test
# ─────────────────────────────────────────────────────────────────
N        = 512     # taille du code polaire
P_BOB    = 0.05    # probabilité d'erreur canal Bob  (meilleur)
P_EVE    = 0.25    # probabilité d'erreur canal Eve  (pire)
N_FRAMES = 200     # nombre de trames à simuler
SCL_L    = 8       # taille de la liste SCL
ALPHA    = 0.60    # seuil Z_eve : canaux avec Z_eve > ALPHA sont opaques pour Eve

# ─────────────────────────────────────────────────────────────────
#  Helpers canal et codec
# ─────────────────────────────────────────────────────────────────
def bpsk(bits):
    return (1.0 - 2.0 * bits).astype(np.float32)

def canal_bsc(signal, p):
    bruit = np.random.choice([1, -1], len(signal), p=[1-p, p])
    return (signal * bruit).astype(np.float32)

def llr_bsc(signal, p):
    return (signal * np.log((1-p)/p)).astype(np.float32)

def encode(u, frozen_bits):
    u_spu = spu.int8(u)
    x_spu = aff3ct.polar.encode(u_spu, frozen_bits)
    return np.array(x_spu).flatten().astype(np.int8)

def decode(llrs, frozen_bits):
    _, u_hat = aff3ct.polar.decode_siho(
        llrs, frozen_bits,
        decoder_type='SCL', L=SCL_L, implem='NAIVE'
    )
    return np.array(u_hat)[0].astype(np.int8)   # meilleur candidat SCL

# ─────────────────────────────────────────────────────────────────
#  Construction du masque Wyner — approche directe (argsort)
#
#  1. Prendre les K_max meilleurs canaux pour Bob (Z_bob minimal)
#     → code polaire standard pour Bob, taux bien en dessous de la capacité
#  2. Parmi ces K_max canaux, classifier en I / R selon Z_eve :
#       I = {Z_eve > ALPHA} : opaques pour Eve → bits d'information
#       R = {Z_eve ≤ ALPHA} : accessibles à Eve → bits aléatoires (redondance)
# ─────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  POLARIS — Test BER Wyner wiretap polar")
print(f"  N={N}, p_bob={P_BOB}, p_eve={P_EVE}, {N_FRAMES} trames, SCL L={SCL_L}")
print(f"{'='*55}\n")

print("Construction Wyner en cours...")
z_bob = z_construction_bsc(N, P_BOB)
z_eve = z_construction_bsc(N, P_EVE)

K_max = int(N * (1.0 - H2(P_BOB)) * 0.85)   # 85 % de la capacité de Bob

# Étape 1 : meilleurs K_max sous-canaux pour Bob
best_for_bob = np.argsort(z_bob)[:K_max]     # indices triés par Z_bob croissant
top_k        = set(int(i) for i in best_for_bob)

# Étape 2 : partition Wyner dans ces K_max canaux
bits_I = {i for i in top_k if z_eve[i] > ALPHA}
bits_R = top_k - bits_I
K_info  = len(bits_I)
K_total = K_max   # garanti par construction

sorted_IR         = sorted(top_k)
indices_info_in_u = np.array([k for k, ch in enumerate(sorted_IR) if ch in bits_I])

frozen_bits = np.ones(N, dtype=np.int32)
for ch in sorted_IR:
    frozen_bits[ch] = 0

# ─── Métriques d'information mutuelle ────────────────────────────
mi_bob = mi_construction_bsc(N, P_BOB)
mi_eve = mi_construction_bsc(N, P_EVE)

mi_bob_I  = np.array([mi_bob[i] for i in bits_I])
mi_eve_I  = np.array([mi_eve[i] for i in bits_I])

# Taux de confidentialité théorique : contribution des canaux I sur N
Cs_theo = float(np.sum(mi_bob_I - mi_eve_I)) / N
# Taux pratique : K_info bits secrets par N symboles canal
Cs_prat = K_info / N

print(f"  K_max={K_max} (taux={K_max/N:.3f}, capa Bob={1-H2(P_BOB):.3f})")
print(f"  |I|={len(bits_I)}, |R|={len(bits_R)}, |F|={N - K_total}")
print(f"  K_info={K_info} bits/trame, K_total={K_total}")
print()
print(f"  — Information mutuelle (canaux I) —")
print(f"    MI_Bob moy = {mi_bob_I.mean():.4f}  (idéal : 1.000)")
print(f"    MI_Eve moy = {mi_eve_I.mean():.4f}  (idéal : 0.000)")
print(f"    Cs théorique = {Cs_theo:.4f} bits/canal")
print(f"    Cs pratique  = {Cs_prat:.4f} bits/canal  (K_info/N)")

if K_info == 0:
    print("ERREUR : |I|=0, aucun canal sécurisé. Vérifiez que p_bob < p_eve ou réduisez ALPHA.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
#  Vérification sanity : canal sans bruit (doit donner BER = 0)
# ─────────────────────────────────────────────────────────────────
print("Vérification noiseless (3 trames)...")
for _ in range(3):
    u_test   = np.random.randint(0, 2, K_total, dtype=np.int8)
    x_test   = encode(u_test, frozen_bits)
    s_test   = bpsk(x_test)
    llr_test = llr_bsc(s_test, 1e-6)       # canal quasi-parfait
    u_dec    = decode(llr_test, frozen_bits)
    assert np.array_equal(u_test, u_dec), \
        f"Sanity FAILED: {np.sum(u_test != u_dec)} erreurs sur {K_total} bits"
print("  → OK (0 erreur sur canal parfait)\n")

# ─────────────────────────────────────────────────────────────────
#  Simulation sur N_FRAMES trames
# ─────────────────────────────────────────────────────────────────
bob_errors, eve_errors = 0, 0
total_bits = 0

for frame in range(N_FRAMES):
    # Message aléatoire de K_info bits
    message = np.random.randint(0, 2, K_info, dtype=np.int8)

    # Vecteur u : message sur I, aléatoire sur R
    u = np.random.randint(0, 2, K_total, dtype=np.int8)
    u[indices_info_in_u] = message

    # Encodage → BPSK
    x = encode(u, frozen_bits)
    s = bpsk(x)

    # Canal Bob (p_bob) → décodage → extraction I
    y_bob   = canal_bsc(s, P_BOB)
    llr_bob = llr_bsc(y_bob, P_BOB)
    u_bob   = decode(llr_bob, frozen_bits)
    msg_bob = u_bob[indices_info_in_u]

    # Canal Eve (p_eve) → décodage → extraction I
    y_eve   = canal_bsc(s, P_EVE)
    llr_eve = llr_bsc(y_eve, P_EVE)
    u_eve   = decode(llr_eve, frozen_bits)
    msg_eve = u_eve[indices_info_in_u]

    bob_errors += int(np.sum(message != msg_bob))
    eve_errors += int(np.sum(message != msg_eve))
    total_bits += K_info

    if (frame + 1) % 50 == 0:
        print(f"  trame {frame+1:>3}/{N_FRAMES}  — "
              f"BER Bob={bob_errors/((frame+1)*K_info):.4f}  "
              f"BER Eve={eve_errors/((frame+1)*K_info):.4f}")

# ─────────────────────────────────────────────────────────────────
#  Résultats finaux
# ─────────────────────────────────────────────────────────────────
ber_bob = bob_errors / total_bits
ber_eve = eve_errors / total_bits

print(f"\n{'='*55}")
print(f"  Résultats finaux  ({N_FRAMES} trames × {K_info} bits = {total_bits} bits)")
print(f"{'='*55}")
print(f"  BER Bob : {ber_bob:.4f}  ({bob_errors} erreurs / {total_bits} bits)")
print(f"  BER Eve : {ber_eve:.4f}  ({eve_errors} erreurs / {total_bits} bits)")
print(f"  Ratio   : Eve/Bob = {ber_eve/(ber_bob+1e-9):.1f}x")
print(f"{'='*55}")

if ber_bob < 0.05 and ber_eve > 0.20:
    print("  ✓ Gap de sécurité confirmé : Bob décode, Eve est bloquée.")
elif ber_bob < ber_eve:
    print("  ~ Gap visible mais faible — essayer avec N plus grand ou p_eve plus élevé.")
else:
    print("  ✗ Pas de gap — vérifier les paramètres du canal.")
print()
