import streampu as spu
import aff3ct

def test_crcs(dtype=spu.int32):
    u = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0]

    crc_std = aff3ct.crc.build(16, "0xF7", 8, dtype, aff3ct.crc.implem.STD)
    c = crc_std.build(dtype(u))
    c = c.numpy

    crc_fast = aff3ct.crc.build(16, "0xF7", 8, dtype, aff3ct.crc.implem.FAST)
    c0 = crc_fast.build(dtype(u))
    c0 = c0.numpy

    assert (c == c0).all()

    crc_inter = aff3ct.crc.build(16, "0xF7", 8, dtype, aff3ct.crc.implem.INTER)
    c1 = crc_inter.build(dtype(u))
    c1 = c1.numpy
    assert (c == c1).all()

    # c2 = aff3ct.crc.encode(dtype(u), "0xF7")
    # c2 = c2.numpy
    # assert (c == c2).all()

if __name__ == "__main__":
    test_crcs(spu.int8)
    test_crcs(spu.int16)
    test_crcs(spu.int32)
    test_crcs(spu.int64)