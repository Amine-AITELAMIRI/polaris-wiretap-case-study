# Results and reproduction notes

The table in the [case study](../README.md) is transcribed from Section 5.1, Table 5.1 of the team's final POLARIS report (ENSEIRB-MATMECA, Semester 8, 2025–26).

## What the reported numbers mean

- **Channel model:** independent simulated BSC links, with $p_{Bob}=0.05$ and $p_{Eve}=0.25$.
- **Selection:** select $K_{max}=\lfloor0.85N(1-H_2(p_{Bob}))\rfloor$ subchannels with the lowest Bob Bhattacharyya parameter, then assign positions with $Z_{Eve}>0.60$ to the information set **I**. Remaining selected positions are randomized (**R**); all others are frozen (**F**).
- **BER:** total errors in decoded **I** message bits divided by total transmitted **I** message bits, over 200 random frames. Bob and Eve use successive-cancellation-list decoding in the reported $N=512$ and $N=1024$ setups (list size 8); $N=128$ uses list size 1.
- **MI:** the mean synthetic-subchannel MI on **I** computed by `fonctions/fx_construction_mi.py`. It is a construction metric, distinct from empirical mutual information between a complete secret message and Eve's observations.

The reported N=1024 run has 385 information bits per frame (77,000 over 200 frames). The published BER values are rounded, so exact error counts cannot be reconstructed from the table. The test scripts use unseeded random frames; rerunning them can produce different BER values. The main application also uses different current defaults (`ALPHA_WYNER=0.85`, a size-dependent capacity margin, and different decoder settings). Do not treat the reported table as a fresh measurement of those defaults or as a validated radio link.

## Available rerun entry points

After following the [setup steps](../README.md#run-the-software-simulation), with `aff3ct` (pyAFF3CT) and `streampu` available in the same Python environment, run from the repository root:

```bash
python tests/test_wiretap_ber.py   # N=512, 200 frames, SCL L=8
python tests/test_parametres.py    # five configurations, 50 frames each
```

These are the team's existing scripts. Neither reproduces the report's exact N=1024, 200-frame BER row without changing its configuration, and no dependency lockfile or original random seed is present. The deterministic set size and MI values can be checked against the construction modules for N=1024, p values above, and alpha 0.60; that cross-check gives $|I|=385$, Bob MI 0.971892, and Eve MI 0.027174 (rounded to the report's 0.9719 and 0.0272). The reported BER values have not been exactly reproduced in this repository.

The results support a Bob/Eve gap for the stated **simulated degraded BSC**. They do not establish secrecy against arbitrary eavesdroppers, a real RF channel, or the optional privacy-amplification mode.
