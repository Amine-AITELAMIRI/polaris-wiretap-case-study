"""
test_parametres.py — Sweep paramétrique du système Wyner polar wiretap

Pour chaque configuration (N, p_bob, p_eve) :
  - Construction du masque Wyner (argsort + partition MI)
  - Simulation BER sur N_FRAMES trames
  - Affichage des métriques BER et d'information mutuelle

Usage :
    python tests/test_parametres.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import aff3ct
import streampu as spu

from fonctions.fx_construction_z  import z_construction_bsc
from fonctions.fx_construction_mi import H2, mi_construction_bsc

# ─────────────────────────────────────────────────────────────────
#  Configurations à tester  (N, p_bob, p_eve)
# ─────────────────────────────────────────────────────────────────
CONFIGS = [
    (512,  0.05, 0.15),
    (512,  0.05, 0.25),
    (512,  0.05, 0.35),
    (512,  0.10, 0.30),
    (1024, 0.05, 0.25),
]

N_FRAMES = 50    # trames par configuration (réduit pour la vitesse du sweep)
SCL_L    = 8
ALPHA    = 0.60  # seuil Z_eve : canaux I sont opaques pour Eve

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

def decode(llrs, frozen_bits, L):
    _, u_hat = aff3ct.polar.decode_siho(
        llrs, frozen_bits,
        decoder_type='SCL', L=L, implem='NAIVE'
    )
    return np.array(u_hat)[0].astype(np.int8)

# ─────────────────────────────────────────────────────────────────
#  Construction du masque Wyner pour une configuration donnée
# ─────────────────────────────────────────────────────────────────
def construire_wyner(N, p_bob, p_eve):
    z_bob = z_construction_bsc(N, p_bob)
    z_eve = z_construction_bsc(N, p_eve)
    mi_bob = mi_construction_bsc(N, p_bob)
    mi_eve = mi_construction_bsc(N, p_eve)

    K_max        = int(N * (1.0 - H2(p_bob)) * 0.85)
    best_for_bob = np.argsort(z_bob)[:K_max]
    top_k        = set(int(i) for i in best_for_bob)

    bits_I = {i for i in top_k if z_eve[i] > ALPHA}
    bits_R = top_k - bits_I
    K_info  = len(bits_I)
    K_total = K_max

    sorted_IR         = sorted(top_k)
    indices_info_in_u = np.array([k for k, ch in enumerate(sorted_IR) if ch in bits_I])

    frozen_bits = np.ones(N, dtype=np.int32)
    for ch in sorted_IR:
        frozen_bits[ch] = 0

    # Métriques MI
    mi_bob_I = np.array([mi_bob[i] for i in bits_I])
    mi_eve_I = np.array([mi_eve[i] for i in bits_I])
    Cs_theo  = float(np.sum(mi_bob_I - mi_eve_I)) / N

    return frozen_bits, K_info, K_total, indices_info_in_u, Cs_theo, len(bits_I), len(bits_R)

# ─────────────────────────────────────────────────────────────────
#  Simulation d'une configuration
# ─────────────────────────────────────────────────────────────────
def simuler(N, p_bob, p_eve, n_frames):
    frozen_bits, K_info, K_total, indices_info_in_u, Cs_theo, nI, nR = \
        construire_wyner(N, p_bob, p_eve)

    if K_info == 0:
        return None

    bob_errors, eve_errors, total_bits = 0, 0, 0

    for _ in range(n_frames):
        message = np.random.randint(0, 2, K_info, dtype=np.int8)
        u       = np.random.randint(0, 2, K_total, dtype=np.int8)
        u[indices_info_in_u] = message

        x   = encode(u, frozen_bits)
        s   = bpsk(x)

        y_bob   = canal_bsc(s, p_bob)
        llr_bob = llr_bsc(y_bob, p_bob)
        u_bob   = decode(llr_bob, frozen_bits, SCL_L)
        msg_bob = u_bob[indices_info_in_u]

        y_eve   = canal_bsc(s, p_eve)
        llr_eve = llr_bsc(y_eve, p_eve)
        u_eve   = decode(llr_eve, frozen_bits, SCL_L)
        msg_eve = u_eve[indices_info_in_u]

        bob_errors += int(np.sum(message != msg_bob))
        eve_errors += int(np.sum(message != msg_eve))
        total_bits += K_info

    ber_bob = bob_errors / total_bits
    ber_eve = eve_errors / total_bits
    return ber_bob, ber_eve, K_info, K_total, Cs_theo, nI, nR

# ─────────────────────────────────────────────────────────────────
#  Sweep principal
# ─────────────────────────────────────────────────────────────────
print(f"\n{'='*75}")
print(f"  POLARIS — Sweep paramétrique Wyner wiretap polar")
print(f"  {N_FRAMES} trames par config, SCL L={SCL_L}, alpha={ALPHA}")
print(f"{'='*75}")
print(f"{'N':>5}  {'p_bob':>5}  {'p_eve':>5}  "
      f"{'|I|':>4}  {'K_tot':>5}  "
      f"{'BER Bob':>8}  {'BER Eve':>8}  {'Ratio':>6}  "
      f"{'Cs théo':>8}  {'Cs prat':>8}")
print(f"{'-'*75}")

for (N, p_bob, p_eve) in CONFIGS:
    res = simuler(N, p_bob, p_eve, N_FRAMES)
    if res is None:
        print(f"{N:>5}  {p_bob:>5.2f}  {p_eve:>5.2f}  — |I|=0, config invalide")
        continue

    ber_bob, ber_eve, K_info, K_total, Cs_theo, nI, nR = res
    ratio   = ber_eve / (ber_bob + 1e-9)
    Cs_prat = K_info / N

    print(f"{N:>5}  {p_bob:>5.2f}  {p_eve:>5.2f}  "
          f"{nI:>4}  {K_total:>5}  "
          f"{ber_bob:>8.4f}  {ber_eve:>8.4f}  {ratio:>6.1f}x  "
          f"{Cs_theo:>8.4f}  {Cs_prat:>8.4f}")

print(f"{'='*75}\n")
print("Légende :")
print("  |I|     : nombre de canaux d'information sécurisés (bits message/trame)")
print("  K_tot   : total canaux actifs = |I| + |R| = 85 % capacité Bob")
print("  Cs théo : taux de confidentialité théorique = Σ_{i∈I}(MI_Bob[i]-MI_Eve[i]) / N")
print("  Cs prat : taux pratique = K_info / N")
print()
