import heterocl as hcl
import numpy as np

def test_gather128():
    hcl.init()
    def kernel():
        a32 = hcl.compute((4,), lambda i: i+50, "a1", dtype='uint32')
        v = hcl.scalar(0, "x", dtype='uint128')
        factor = 128//32
        def shift_copy(i):
            v.v = 0
            for j in range(factor): # j = 0, 1, 2, 3
                a = a32[i*factor + j] # a = a32[0], a32[1], a32[2], a32[3]
                v.v = (v.v << 32) | a
        hcl.mutate((1,), shift_copy)
        res = hcl.compute((4,), lambda i : 0, "res", dtype='uint32')
        res[0] = (v.v >>  0) & 0xFFFFFFFF # should be a32[3]
        res[1] = (v.v >> 32) & 0xFFFFFFFF # should be a32[2]
        res[2] = (v.v >> 64) & 0xFFFFFFFF # should be a32[1]
        res[3] = (v.v >> 96) & 0xFFFFFFFF # should be a32[0]
        return res

    s = hcl.create_schedule([], kernel)
    hcl_res = hcl.asarray(np.zeros((4,), dtype=np.uint32), dtype=hcl.UInt(32))
    f = hcl.build(s)
    f(hcl_res)
    golden = np.array([53, 52, 51, 50], dtype=np.uint32)
    assert np.allclose(hcl_res.asnumpy(), golden)