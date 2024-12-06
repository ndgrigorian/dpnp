import unittest

import pytest

from dpnp import random
from dpnp.tests.third_party.cupy import testing


@pytest.mark.skip("random.get_random_state() is not supported yet")
class TestResetSeed(unittest.TestCase):

    @testing.for_float_dtypes(no_float16=True)
    def test_reset_seed(self, dtype):
        rs = random.get_random_state()
        rs.seed(0)
        l1 = rs.rand(10, dtype=dtype)

        rs = random.get_random_state()
        rs.seed(0)
        l2 = rs.rand(10, dtype=dtype)

        testing.assert_array_equal(l1, l2)
