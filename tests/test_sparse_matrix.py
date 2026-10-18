from aff3ct import sparse_matrix as spm
import numpy as np
# import matplotlib.pyplot as plt


def test_sparse_matrix():
    H1 = spm.eye(5,2)
    print(H1)

    H2 = spm.eye(5,0)
    print(H2)

    H1 += H2
    print(H1)

    print(H1[:,3])
    print(H1[3,:])

    H3 = H1[:,3] @ H1[3,:]
    print(H3)

    # H4, _, _ = spm.read("tests/data/AR4JA_4096_8192.qc")
    # H5, _, _ = spm.read("tests/data/DEBUG_6_3.alist")
    pass

if __name__ == "__main__":
    test_sparse_matrix()