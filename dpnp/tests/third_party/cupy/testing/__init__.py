from dpnp.tests.third_party.cupy.testing._array import (
    assert_allclose,
    assert_array_almost_equal,
    assert_array_almost_equal_nulp,
    assert_array_equal,
    assert_array_less,
    assert_array_list_equal,
    assert_array_max_ulp,
)
from dpnp.tests.third_party.cupy.testing._attr import multi_gpu, slow

# from dpnp.tests.third_party.cupy.testing._helper import shaped_sparse_random
from dpnp.tests.third_party.cupy.testing._helper import (
    AssertFunctionIsCalled,
    NumpyAliasBasicTestBase,
    NumpyAliasValuesTestBase,
    assert_warns,
    generate_matrix,
    installed,
    numpy_satisfies,
    shaped_arange,
    shaped_random,
    shaped_reverse_arange,
    with_requires,
)
from dpnp.tests.third_party.cupy.testing._loops import (
    for_all_dtypes,
    for_all_dtypes_combination,
    for_castings,
    for_CF_orders,
    for_complex_dtypes,
    for_contiguous_axes,
    for_dtypes,
    for_dtypes_combination,
    for_float_dtypes,
    for_int_dtypes,
    for_int_dtypes_combination,
    for_orders,
    for_signed_dtypes,
    for_signed_dtypes_combination,
    for_unsigned_dtypes,
    for_unsigned_dtypes_combination,
    numpy_cupy_allclose,
    numpy_cupy_array_almost_equal,
    numpy_cupy_array_almost_equal_nulp,
    numpy_cupy_array_equal,
    numpy_cupy_array_less,
    numpy_cupy_array_list_equal,
    numpy_cupy_array_max_ulp,
    numpy_cupy_equal,
    numpy_cupy_raises,
)
from dpnp.tests.third_party.cupy.testing._parameterized import (
    parameterize,
    product,
    product_dict,
)
from dpnp.tests.third_party.cupy.testing._random import (
    fix_random,
    generate_seed,
)
