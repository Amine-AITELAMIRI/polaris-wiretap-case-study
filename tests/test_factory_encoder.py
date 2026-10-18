import aff3ct
import streampu as spu

def test_encoder():
    encoder = aff3ct.factory.Encoder()
    encoder.K = 4
    encoder.N_cw = 8
    encoder.type = 'AZCW'
    encoder.systematic = True
    encoder.B = spu.int8

    enc = encoder.build()
    print(enc)

if __name__ == "__main__":
    test_encoder()
