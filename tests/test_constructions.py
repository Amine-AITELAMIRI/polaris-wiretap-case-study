"""Tests simples de construction polaire (version courte projet)."""

import os
import sys
import math

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fonctions.fx_construction_mi import H2, H2_inv, mi_construction_bsc
from fonctions.fx_construction_z import z_construction_bsc
from fonctions.fx_construction_wyner import partition, optimiser_seuils
from fonctions.fx_construction_fBits_mask import generer_masque

TOL = 1e-9


def test_h2_basique():
    assert H2(0.0) == 0.0
    assert H2(1.0) == 0.0
    assert abs(H2(0.5) - 1.0) < TOL
    assert abs(H2(H2_inv(0.7)) - 0.7) < 1e-8


def test_mi_construction_basique():
    N, p = 128, 0.1
    mi = mi_construction_bsc(N, p)
    assert len(mi) == N
    assert np.all(mi >= 0.0) and np.all(mi <= 1.0)
    assert abs(mi.sum() - N * (1.0 - H2(p))) < 1e-6


def test_z_construction_basique():
    N, p = 128, 0.1
    z = z_construction_bsc(N, p)
    assert len(z) == N
    assert np.all(z >= 0.0) and np.all(z <= 1.0)
    assert abs(z_construction_bsc(1, p)[0] - 2.0 * np.sqrt(p * (1.0 - p))) < TOL


def test_masque_contient_k_bits_info():
    N, K, p = 128, 64, 0.1
    mask = generer_masque(N, K, p, methode="MI")
    assert np.sum(mask == 0) == K
    assert np.sum(mask == 1) == N - K


def test_partition_et_optimiseur():
    N = 128
    z_bob = z_construction_bsc(N, 0.05)
    z_eve = z_construction_bsc(N, 0.25)

    i_set, r_set, f_set = partition(z_bob, z_eve, beta=0.3, alpha=0.7)
    assert i_set | r_set | f_set == set(range(N))
    assert len(i_set & r_set) == 0 and len(i_set & f_set) == 0 and len(r_set & f_set) == 0

    beta, alpha, best_i, _, _, _ = optimiser_seuils(z_bob, z_eve, n_points=25)
    assert 0.0 < beta <= 0.5
    assert 0.5 <= alpha < 1.0
    assert best_i > 0


def test_entrees_invalides():
    with pytest.raises(ValueError):
        mi_construction_bsc(3, 0.1)
    with pytest.raises(ValueError):
        z_construction_bsc(3, 0.1)
    with pytest.raises(ValueError):
        generer_masque(64, 80, 0.1, methode="MI")


def snr_db_to_bsc_p(snr_db: float) -> float:
    """Convertit un SNR (dB) en crossover BSC équivalent."""
    x = math.sqrt(2.0 * (10.0 ** (snr_db / 10.0)))
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def analyse_bits_utiles_vs_delta(
    snr_bob_db: float = 6.0,
    deltas_db=(1.0, 2.0, 3.0, 4.0, 5.0),
    n_values=(1024, 4096, 16384),
    n_points: int = 50,
):
    """Petit tableau pour le rendu projet (bits utiles selon Delta et N)."""
    print("\nPOLARIS - Resultats bits utiles")
    print(f"Hypothese: SNR Bob={snr_bob_db:.1f} dB, Eve=Bob-Delta")
    print("Delta(dB)   N      |I|_opt    |I|/N")

    for delta in deltas_db:
        p_bob = snr_db_to_bsc_p(snr_bob_db)
        p_eve = snr_db_to_bsc_p(snr_bob_db - float(delta))

        for N in n_values:
            z_bob = z_construction_bsc(int(N), p_bob)
            z_eve = z_construction_bsc(int(N), p_eve)
            _, _, i_bits, _, _, _ = optimiser_seuils(z_bob, z_eve, n_points=n_points)

            print(f"{float(delta):>8.1f}  {int(N):>6d}   {int(i_bits):>7d}   {float(i_bits)/int(N):>7.4f}")


if __name__ == "__main__":
    if "--secrecy-report" in sys.argv:
        analyse_bits_utiles_vs_delta()
    else:
        print("Use pytest for tests, or run with --secrecy-report")
