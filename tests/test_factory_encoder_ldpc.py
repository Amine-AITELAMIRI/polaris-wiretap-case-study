from aff3ct import factory as fct
from aff3ct import sparse_matrix as spm

import streampu as spu

factory = fct.Encoder_LDPC()
help(factory)
factory.K = 4
factory.N_cw = 7
factory.type = 'LDPC'
