import aff3ct
import streampu as spu

def test_encoder_polar():
    encoder = aff3ct.factory.Encoder_polar()
    encoder.K = 4
    encoder.N_cw = 8
    encoder.systematic = True
    encoder.B = spu.int16

    enc = encoder.build([1,1,1,0,1,0,0,0])
    u = [1,0,0,0]
    c = enc(spu.int16(u))

if __name__ == "__main__":
    test_encoder_polar()
