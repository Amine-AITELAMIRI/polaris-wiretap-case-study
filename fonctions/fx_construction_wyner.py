import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from .fx_construction_z import z_construction_bsc


# ─────────────────────────────────────────────────────────────────
#  2. PARTITION DES SOUS-CANAUX  I / R / F
# ─────────────────────────────────────────────────────────────────

def partition(z_bob: np.ndarray, z_eve: np.ndarray,
              beta: float, alpha: float):
    """
    Partitionne les N sous-canaux en trois ensembles.

    Critères
    --------
    beta  : seuil Bob  — canal "bon" pour Bob si Z_bob[i] < beta
    alpha : seuil Eve  — canal "mauvais" pour Eve si Z_eve[i] > alpha

    Retourne
    --------
    bits_I : bons pour Bob ET mauvais pour Eve  → portent l'information
    bits_R : bons pour Bob ET bons pour Eve     → portent des bits aléatoires
    bits_F : mauvais pour Bob                   → bits gelés (= 0)
    """
    if len(z_bob) != len(z_eve):
        raise ValueError("z_bob et z_eve doivent avoir la même longueur.")
    if not (0.0 <= beta <= 1.0):
        raise ValueError(f"beta doit être dans [0,1], reçu {beta}.")
    if not (0.0 <= alpha <= 1.0):
        raise ValueError(f"alpha doit être dans [0,1], reçu {alpha}.")

    N        = len(z_bob)
    good_bob = set(np.where(z_bob < beta)[0])
    bad_eve  = set(np.where(z_eve > alpha)[0])

    bits_I = good_bob & bad_eve          # sûrs ET fiables
    bits_R = good_bob - bad_eve          # fiables mais visibles d'Eve
    bits_F = set(range(N)) - good_bob    # mauvais pour Bob

    return bits_I, bits_R, bits_F


# ─────────────────────────────────────────────────────────────────
#  3. RECHERCHE OPTIMALE DE alpha ET beta
# ─────────────────────────────────────────────────────────────────

def optimiser_seuils(z_bob: np.ndarray, z_eve: np.ndarray,
                     n_points: int = 200,
                     beta_min: float = 0.01,
                     beta_max: float = 0.50,
                     alpha_min: float = 0.50,
                     alpha_max: float = 0.99):
    """
    Cherche les valeurs de beta et alpha qui maximisent |I|.

    Contraintes physiques imposées :
      - beta  ∈ ]0,   0.5]  → Bob doit être fiable (Z petit = bon)
      - alpha ∈ [0.5, 1[   → Eve doit être vraiment bloquée (Z grand = mauvais)

    Retourne
    --------
    best_beta, best_alpha : seuils optimaux
    best_I                : taille maximale de I
    results               : grille 2D de |I| pour heatmap
    betas, alphas         : axes de la grille
    """
    if len(z_bob) != len(z_eve):
        raise ValueError("z_bob et z_eve doivent avoir la même longueur.")
    if n_points < 2:
        raise ValueError("n_points doit être >= 2.")
    if not (0.0 <= beta_min < beta_max <= 1.0):
        raise ValueError("Intervalle beta invalide.")
    if not (0.0 <= alpha_min < alpha_max <= 1.0):
        raise ValueError("Intervalle alpha invalide.")

    betas  = np.linspace(beta_min, beta_max, n_points)
    alphas = np.linspace(alpha_min, alpha_max, n_points)

    best_I, best_alpha, best_beta = 0, 0.5, 0.5
    results = np.zeros((len(betas), len(alphas)))

    for i, beta in enumerate(betas):
        for j, alpha in enumerate(alphas):
            I, _, _ = partition(z_bob, z_eve, beta, alpha)
            results[i, j] = len(I)
            if len(I) > best_I:
                best_I     = len(I)
                best_alpha = alpha
                best_beta  = beta

    return best_beta, best_alpha, best_I, results, betas, alphas


# ─────────────────────────────────────────────────────────────────
#  4. VISUALISATION
# ─────────────────────────────────────────────────────────────────

def plot_analyse(z_bob, z_eve, best_beta, best_alpha,
                 results, betas, alphas,
                 N, p_bob, p_eve):
    """
    Produit deux figures :
      Fig 1 — distributions Z triées + heatmap
      Fig 2 — partition I/R/F par indice de sous-canal
    """
    I_opt, R_opt, F_opt = partition(z_bob, z_eve, best_beta, best_alpha)
    best_I = len(I_opt)
    idx    = np.arange(N)

    # ── Figure 1 ──────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(
        f"POLARIS — N={N},  p_bob={p_bob},  p_eve={p_eve}",
        fontsize=14, fontweight='bold', color='#003566'
    )

    # Gauche : Z triés + seuils
    ax = axes[0]
    ax.plot(idx, np.sort(z_bob), color='#0096C7', lw=2, label=f'Bob  (p={p_bob})')
    ax.plot(idx, np.sort(z_eve), color='#F4A261', lw=2, label=f'Eve  (p={p_eve})')
    ax.axhline(best_beta,  color='#0096C7', ls='--', lw=1.5,
               label=f'β = {best_beta:.3f}  (seuil Bob)')
    ax.axhline(best_alpha, color='#F4A261', ls='--', lw=1.5,
               label=f'α = {best_alpha:.3f}  (seuil Eve)')
    ax.fill_betweenx([best_beta, best_alpha], 0, N,
                     alpha=0.12, color='#2DC653', label='Gap de sécurité')
    ax.set_xlabel("Sous-canal (trié par Z croissant)")
    ax.set_ylabel("Z Bhattacharyya")
    ax.set_title("Distributions Z_bob et Z_eve (triées)")
    ax.legend(fontsize=10)
    ax.set_ylim(-0.02, 1.05)
    ax.grid(alpha=0.3)

    # Droite : heatmap |I|(alpha, beta)
    ax2 = axes[1]
    im  = ax2.imshow(results, origin='lower', aspect='auto',
                     extent=[alphas[0], alphas[-1], betas[0], betas[-1]],
                     cmap='RdYlGn', vmin=0, vmax=results.max())
    ax2.scatter([best_alpha], [best_beta], color='#003566', s=200,
                zorder=5, marker='*',
                label=f'Optimum\nα={best_alpha:.3f}, β={best_beta:.3f}\n|I|={best_I}')
    ax2.set_xlabel("α  (seuil Eve,  Z_eve > α)")
    ax2.set_ylabel("β  (seuil Bob,  Z_bob < β)")
    ax2.set_title(f"|I| selon α et β  (max = {best_I})")
    ax2.legend(loc='upper right', fontsize=10)
    plt.colorbar(im, ax=ax2, label="|I| bits d'information sécurisés")

    plt.tight_layout()
    plt.savefig("polaris_bhattacharyya.png", dpi=150, bbox_inches='tight')
    plt.show()

    # ── Figure 2 ──────────────────────────────────────────────────
    fig2, ax3 = plt.subplots(figsize=(16, 4))
    ax3.bar(idx, z_bob, color='#0096C7', alpha=0.4, width=1, label='Z_bob')
    ax3.bar(idx, z_eve, color='#F4A261', alpha=0.25, width=1, label='Z_eve')

    for i in I_opt:
        ax3.axvspan(i - 0.5, i + 0.5, alpha=0.55, color='#2DC653', zorder=0)
    for i in R_opt:
        ax3.axvspan(i - 0.5, i + 0.5, alpha=0.3,  color='#F4A261', zorder=0)

    ax3.axhline(best_beta,  color='#0096C7', ls='--', lw=1.5,
                label=f'β={best_beta:.3f}')
    ax3.axhline(best_alpha, color='#F4A261', ls='--', lw=1.5,
                label=f'α={best_alpha:.3f}')

    pI = mpatches.Patch(color='#2DC653', alpha=0.6,
                        label=f'I — info sécurisée  ({len(I_opt)} bits)')
    pR = mpatches.Patch(color='#F4A261', alpha=0.5,
                        label=f'R — aléatoire        ({len(R_opt)} bits)')
    pF = mpatches.Patch(color='#ADB5BD', alpha=0.5,
                        label=f'F — gelé             ({len(F_opt)} bits)')

    ax3.legend(handles=[pI, pR, pF], fontsize=10)
    ax3.set_xlabel("Indice du sous-canal")
    ax3.set_ylabel("Z Bhattacharyya")
    ax3.set_title(f"Partition I / R / F  —  β={best_beta:.3f},  α={best_alpha:.3f}")
    ax3.set_ylim(-0.02, 1.08)
    ax3.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("polaris_partition.png", dpi=150, bbox_inches='tight')
    plt.show()

    return I_opt, R_opt, F_opt


# ─────────────────────────────────────────────────────────────────
#  5. PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Paramètres à ajuster ──────────────────────────────────────
    N     = 256    # taille du code (puissance de 2)
    p_bob = 0.05   # BER du canal Bob  (plus petit = meilleur)
    p_eve = 0.25   # BER du canal Eve  (plus grand = plus bruité)

    # ── Calcul des Z ──────────────────────────────────────────────
    z_bob = z_construction_bsc(N, p_bob)
    z_eve = z_construction_bsc(N, p_eve)

    # ── Recherche des seuils optimaux ─────────────────────────────
    best_beta, best_alpha, best_I, results, betas, alphas = \
        optimiser_seuils(z_bob, z_eve, n_points=200)

    print("=" * 50)
    print(f"  N       = {N}")
    print(f"  p_bob   = {p_bob}  |  p_eve = {p_eve}")
    print(f"  β opt.  = {best_beta:.3f}   (seuil Bob, Z_bob < β)")
    print(f"  α opt.  = {best_alpha:.3f}   (seuil Eve, Z_eve > α)")
    print(f"  |I|     = {best_I}   bits d'information sécurisés")
    print("=" * 50)

    # ── Partition finale ──────────────────────────────────────────
    I_opt, R_opt, F_opt = plot_analyse(
        z_bob, z_eve, best_beta, best_alpha,
        results, betas, alphas, N, p_bob, p_eve
    )

    print(f"\n  |I| = {len(I_opt)}  |R| = {len(R_opt)}  |F| = {len(F_opt)}")
    print(f"  Indices I (info sécurisée) : {sorted(I_opt)[:10]} ...")
    print(f"  Indices R (aléatoires)     : {sorted(R_opt)[:10]} ...")
