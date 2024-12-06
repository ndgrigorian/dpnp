import numpy
import pytest

import dpnp as cupy
from dpnp import random as _distributions
from dpnp.tests.helper import has_support_aspect64, is_win_platform
from dpnp.tests.third_party.cupy import testing

if has_support_aspect64():
    _regular_float_dtypes = (numpy.float64, numpy.float32)
else:
    _regular_float_dtypes = (numpy.float32,)
_float_dtypes = _regular_float_dtypes + (numpy.float16,)
_signed_dtypes = tuple(numpy.dtype(i).type for i in "bhilq")
_unsigned_dtypes = tuple(numpy.dtype(i).type for i in "BHILQ")
_int_dtypes = _signed_dtypes + _unsigned_dtypes


class RandomDistributionsTestCase:
    def check_distribution(self, dist_name, params, dtype=None):
        cp_params = {k: cupy.asarray(params[k]) for k in params}
        np_out = numpy.asarray(
            getattr(numpy.random, dist_name)(size=self.shape, **params), dtype
        )
        dt_kward = {dtype: dtype} if dtype else {}
        cp_out = getattr(_distributions, dist_name)(
            size=self.shape, **dt_kward, **cp_params
        )
        if np_out.ndim > 0:
            assert cp_out.shape == np_out.shape
            if np_out.dtype == numpy.float64 and has_support_aspect64():
                assert cp_out.dtype == np_out.dtype
            else:
                assert cp_out.dtype.kind == np_out.dtype.kind

    def check_generator_distribution(self, dist_name, params, dtype):
        cp_params = {k: cupy.asarray(params[k]) for k in params}
        np_gen = numpy.random.default_rng(0)
        cp_gen = cupy.random.default_rng(0)
        np_out = numpy.asarray(
            getattr(np_gen, dist_name)(size=self.shape, **params)
        )
        cp_out = getattr(cp_gen, dist_name)(size=self.shape, **cp_params)
        assert cp_out.shape == np_out.shape
        assert cp_out.dtype == np_out.dtype


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "a_shape": [(), (3, 2)],
            "b_shape": [(), (3, 2)],
            # "dtype": _float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsBeta(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(_float_dtypes, names=["a_dtype", "b_dtype"])
    def test_beta(self, a_dtype, b_dtype):
        a = numpy.full(self.a_shape, 3, dtype=a_dtype)
        b = numpy.full(self.b_shape, 3, dtype=b_dtype)
        self.check_distribution("beta", {"a": a, "b": b}, self.dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "n_shape": [(), (3, 2)],
            "p_shape": [(), (3, 2)],
            "dtype": _int_dtypes,  # to escape timeout
        }
    )
)
class TestDistributionsBinomial(RandomDistributionsTestCase):

    @testing.for_signed_dtypes("n_dtype")
    @testing.for_float_dtypes("p_dtype")
    def test_binomial(self, n_dtype, p_dtype):
        if numpy.dtype("l") == numpy.int32 and n_dtype == numpy.int64:
            pytest.skip("n must be able to cast to long")
        n = numpy.full(self.n_shape, 5, dtype=n_dtype)
        p = numpy.full(self.p_shape, 0.5, dtype=p_dtype)
        self.check_distribution("binomial", {"n": n, "p": p}, self.dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "df_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsChisquare:

    def check_distribution(self, dist_func, df_dtype):
        df = cupy.full(self.df_shape, 5, dtype=df_dtype)
        out = dist_func(df, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    @testing.for_float_dtypes("df_dtype")
    # @testing.for_float_dtypes("dtype") # dtype is not supported
    def test_chisquare(self, df_dtype):
        self.check_distribution(_distributions.chisquare, df_dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2, 3), (3, 2, 3)],
            "alpha_shape": [(3,)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsDirichlet(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(
        _float_dtypes, names=["alpha_dtype"]  # dtype is not supported
    )
    def test_dirichlet(self, alpha_dtype):
        alpha = numpy.ones(self.alpha_shape, dtype=alpha_dtype)
        self.check_distribution("dirichlet", {"alpha": alpha})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsExponential(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # dtype is not supported
    @testing.for_float_dtypes("scale_dtype")
    def test_exponential(self, scale_dtype):
        scale = numpy.ones(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("exponential", {"scale": scale})


@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsExponentialError(RandomDistributionsTestCase):

    def test_negative_scale(self):
        scale = cupy.array([2, -1, 3], dtype=numpy.float32)
        with pytest.raises(ValueError):
            cupy.random.exponential(scale)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "dfnum_shape": [(), (3, 2)],
            "dfden_shape": [(), (3, 2)],
            # "dtype": _float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsF:

    def check_distribution(self, dist_func, dfnum_dtype, dfden_dtype, dtype):
        dfnum = cupy.ones(self.dfnum_shape, dtype=dfnum_dtype)
        dfden = cupy.ones(self.dfden_shape, dtype=dfden_dtype)
        out = dist_func(dfnum, dfden, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    @testing.for_float_dtypes("dfnum_dtype")
    @testing.for_float_dtypes("dfden_dtype")
    def test_f(self, dfnum_dtype, dfden_dtype):
        self.check_distribution(
            _distributions.f, dfnum_dtype, dfden_dtype, self.dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "shape_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
            # "dtype": _float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsGamma:

    def check_distribution(
        self, dist_func, shape_dtype, scale_dtype, dtype=None
    ):
        shape = cupy.ones(self.shape_shape, dtype=shape_dtype)
        scale = cupy.ones(self.scale_shape, dtype=scale_dtype)
        if dtype is None:
            out = dist_func(shape, scale, self.shape)
        else:
            out = dist_func(shape, scale, self.shape, dtype)
        out_shape = self.shape
        if self.shape is None:
            out_shape = shape.shape if shape.shape != () else scale.shape
        if self.shape is not None:
            assert out_shape == out.shape
            # assert out.dtype == dtype

    @testing.for_dtypes_combination(
        _float_dtypes, names=["shape_dtype", "scale_dtype"]
    )
    def test_gamma_legacy(self, shape_dtype, scale_dtype):
        self.check_distribution(
            _distributions.gamma, shape_dtype, scale_dtype, self.dtype
        )

    @pytest.mark.skip("no support of generator yet")
    @testing.for_dtypes_combination(
        _float_dtypes, names=["shape_dtype", "scale_dtype"]
    )
    def test_gamma_generator(self, shape_dtype, scale_dtype):
        self.check_distribution(
            cupy.random.default_rng().gamma, shape_dtype, scale_dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "p_shape": [(), (3, 2)],
            # "dtype": _int_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsGeometric:

    def check_distribution(self, dist_func, p_dtype, dtype):
        p = 0.5 * cupy.ones(self.p_shape, dtype=p_dtype)
        out = dist_func(p, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    @testing.for_float_dtypes("p_dtype")
    def test_geometric(self, p_dtype):
        self.check_distribution(_distributions.geometric, p_dtype, self.dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "loc_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsGumbel(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["loc_dtype", "scale_dtype"]
    )
    def test_gumbel(self, loc_dtype, scale_dtype):
        loc = numpy.ones(self.loc_shape, dtype=loc_dtype)
        scale = numpy.ones(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("gumbel", {"loc": loc, "scale": scale})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "ngood_shape": [(), (3, 2)],
            "nbad_shape": [(), (3, 2)],
            "nsample_shape": [(), (3, 2)],
            "nsample_dtype": [numpy.int32, numpy.int64],  # to escape timeout
            # "dtype": [numpy.int32, numpy.int64],  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsHyperGeometric:

    def check_distribution(
        self, dist_func, ngood_dtype, nbad_dtype, nsample_dtype, dtype
    ):
        ngood = cupy.ones(self.ngood_shape, dtype=ngood_dtype)
        nbad = cupy.ones(self.nbad_shape, dtype=nbad_dtype)
        nsample = cupy.ones(self.nsample_shape, dtype=nsample_dtype)
        out = dist_func(ngood, nbad, nsample, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    @testing.for_dtypes_combination(
        [numpy.int32, numpy.int64], names=["ngood_dtype", "nbad_dtype"]
    )
    def test_hypergeometric(self, ngood_dtype, nbad_dtype):
        if (
            is_win_platform()
            and numpy.int64 in (self.nsample_dtype, ngood_dtype, nbad_dtype)
            and numpy.lib.NumpyVersion(numpy.__version__) < "2.0.0"
        ):
            pytest.skip("numpy raises TypeError")

        self.check_distribution(
            _distributions.hypergeometric,
            ngood_dtype,
            nbad_dtype,
            self.nsample_dtype,
            self.dtype,
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "loc_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsuLaplace(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["loc_dtype", "scale_dtype"]
    )
    def test_laplace(self, loc_dtype, scale_dtype):
        loc = numpy.ones(self.loc_shape, dtype=loc_dtype)
        scale = numpy.ones(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("laplace", {"loc": loc, "scale": scale})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "loc_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsLogistic(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["loc_dtype", "scale_dtype"]
    )
    def test_logistic(self, loc_dtype, scale_dtype):
        loc = numpy.ones(self.loc_shape, dtype=loc_dtype)
        scale = numpy.ones(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("logistic", {"loc": loc, "scale": scale})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "mean_shape": [(), (3, 2)],
            "sigma_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsLognormal(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["mean_dtype", "sigma_dtype"]
    )
    def test_lognormal(self, mean_dtype, sigma_dtype):
        mean = numpy.ones(self.mean_shape, dtype=mean_dtype)
        sigma = numpy.ones(self.sigma_shape, dtype=sigma_dtype)
        self.check_distribution("lognormal", {"mean": mean, "sigma": sigma})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "p_shape": [()],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsLogseries(RandomDistributionsTestCase):

    # @testing.for_dtypes([numpy.int64, numpy.int32], "dtype") # no dtype supported
    @testing.for_float_dtypes("p_dtype", no_float16=True)
    def test_logseries(self, p_dtype):
        p = numpy.full(self.p_shape, 0.5, dtype=p_dtype)
        self.check_distribution("logseries", {"p": p})

    # @testing.for_dtypes([numpy.int64, numpy.int32], "dtype") # no dtype supported
    @testing.for_float_dtypes("p_dtype", no_float16=True)
    def test_logseries_for_invalid_p(self, p_dtype):
        # with pytest.raises(ValueError): # no exception raised by numpy
        #     cp_params = {"p": cupy.zeros(self.p_shape, dtype=p_dtype)}
        #     _distributions.logseries(size=self.shape, **cp_params)
        with pytest.raises(ValueError):
            cp_params = {"p": cupy.ones(self.p_shape, dtype=p_dtype)}
            _distributions.logseries(size=self.shape, **cp_params)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "d": [2, 4],
        }
    )
)
@pytest.mark.skip("multivariate_normal is not fully supported yet")
class TestDistributionsMultivariateNormal:

    def check_distribution(self, dist_func, mean_dtype, cov_dtype, dtype):
        mean = cupy.zeros(self.d, dtype=mean_dtype)
        cov = cupy.random.normal(size=(self.d, self.d), dtype=cov_dtype)
        cov = cov.T.dot(cov)
        out = dist_func(mean, cov, self.shape, dtype=dtype)
        assert self.shape + (self.d,) == out.shape
        assert out.dtype == dtype

    @testing.for_float_dtypes("dtype", no_float16=True)
    @testing.for_float_dtypes("mean_dtype", no_float16=True)
    @testing.for_float_dtypes("cov_dtype", no_float16=True)
    def test_normal(self, mean_dtype, cov_dtype, dtype):
        self.check_distribution(
            _distributions.multivariate_normal, mean_dtype, cov_dtype, dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "n_shape": [(), (3, 2)],
            "p_shape": [(), (3, 2)],
            # "dtype": _int_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsNegativeBinomial(RandomDistributionsTestCase):

    @testing.for_float_dtypes("n_dtype")
    @testing.for_float_dtypes("p_dtype")
    def test_negative_binomial(self, n_dtype, p_dtype):
        n = numpy.full(self.n_shape, 5, dtype=n_dtype)
        p = numpy.full(self.p_shape, 0.5, dtype=p_dtype)
        self.check_distribution(
            "negative_binomial", {"n": n, "p": p}, self.dtype
        )

    @testing.for_float_dtypes("n_dtype")
    @testing.for_float_dtypes("p_dtype")
    def test_negative_binomial_for_noninteger_n(self, n_dtype, p_dtype):
        n = numpy.full(self.n_shape, 5.5, dtype=n_dtype)
        p = numpy.full(self.p_shape, 0.5, dtype=p_dtype)
        self.check_distribution(
            "negative_binomial", {"n": n, "p": p}, self.dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "df_shape": [(), (3, 2)],
            "nonc_shape": [(), (3, 2)],
            # "dtype": _int_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsNoncentralChisquare(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(
        _regular_float_dtypes, names=["df_dtype", "nonc_dtype"]
    )
    def test_noncentral_chisquare(self, df_dtype, nonc_dtype):
        df = numpy.full(self.df_shape, 1, dtype=df_dtype)
        nonc = numpy.full(self.nonc_shape, 1, dtype=nonc_dtype)
        self.check_distribution(
            "noncentral_chisquare", {"df": df, "nonc": nonc}, self.dtype
        )

    @testing.for_float_dtypes("param_dtype", no_float16=True)
    def test_noncentral_chisquare_for_invalid_params(self, param_dtype):
        df = cupy.full(self.df_shape, -1, dtype=param_dtype)
        nonc = cupy.full(self.nonc_shape, 1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.noncentral_chisquare(df, nonc, size=self.shape)

        df = cupy.full(self.df_shape, 1, dtype=param_dtype)
        nonc = cupy.full(self.nonc_shape, -1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.noncentral_chisquare(df, nonc, size=self.shape)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "dfnum_shape": [(), (3, 2)],
            "dfden_shape": [(), (3, 2)],
            "nonc_shape": [(), (3, 2)],
            # "dtype": _int_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsNoncentralF(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(
        _regular_float_dtypes,
        names=["dfnum_dtype", "dfden_dtype", "nonc_dtype"],
    )
    def test_noncentral_f(self, dfnum_dtype, dfden_dtype, nonc_dtype):
        dfnum = numpy.full(self.dfnum_shape, 1, dtype=dfnum_dtype)
        dfden = numpy.full(self.dfden_shape, 1, dtype=dfden_dtype)
        nonc = numpy.full(self.nonc_shape, 1, dtype=nonc_dtype)
        self.check_distribution(
            "noncentral_f",
            {"dfnum": dfnum, "dfden": dfden, "nonc": nonc},
            self.dtype,
        )

    @testing.for_float_dtypes("param_dtype", no_float16=True)
    def test_noncentral_f_for_invalid_params(self, param_dtype):
        dfnum = numpy.full(self.dfnum_shape, -1, dtype=param_dtype)
        dfden = numpy.full(self.dfden_shape, 1, dtype=param_dtype)
        nonc = numpy.full(self.nonc_shape, 1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.noncentral_f(dfnum, dfden, nonc, size=self.shape)

        dfnum = numpy.full(self.dfnum_shape, 1, dtype=param_dtype)
        dfden = numpy.full(self.dfden_shape, -1, dtype=param_dtype)
        nonc = numpy.full(self.nonc_shape, 1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.noncentral_f(dfnum, dfden, nonc, size=self.shape)

        dfnum = numpy.full(self.dfnum_shape, 1, dtype=param_dtype)
        dfden = numpy.full(self.dfden_shape, 1, dtype=param_dtype)
        nonc = numpy.full(self.nonc_shape, -1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.noncentral_f(dfnum, dfden, nonc, size=self.shape)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "loc_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsNormal(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["loc_dtype", "scale_dtype"]
    )
    def test_normal(self, loc_dtype, scale_dtype):
        loc = numpy.ones(self.loc_shape, dtype=loc_dtype)
        scale = numpy.ones(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("normal", {"loc": loc, "scale": scale})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "a_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsPareto:

    def check_distribution(self, dist_func, a_dtype):
        a = cupy.ones(self.a_shape, dtype=a_dtype)
        out = dist_func(a, self.shape)
        if self.shape is not None:
            assert self.shape == out.shape
        # assert out.dtype == dtype

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_pareto(self, a_dtype):
        self.check_distribution(_distributions.pareto, a_dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "lam_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsPoisson:

    def check_distribution(self, dist_func, lam_dtype, dtype=None):
        lam = cupy.full(self.lam_shape, 5, dtype=lam_dtype)
        if dtype is not None:
            out = dist_func(lam, self.shape, dtype)
            assert out.dtype == dtype
        else:
            out = dist_func(lam, self.shape)
        if self.shape is not None:
            assert self.shape == out.shape
        # else:
        #     assert lam.shape == out.shape

    # @testing.for_int_dtypes("dtype") # no dtype supported
    @testing.for_float_dtypes("lam_dtype")
    def test_poisson_legacy(self, lam_dtype):
        self.check_distribution(_distributions.poisson, lam_dtype)

    @pytest.mark.skip("no support of generator yet")
    @testing.for_float_dtypes("lam_dtype")
    def test_poisson_generator(self, lam_dtype):
        self.check_distribution(cupy.random.default_rng(0).poisson, lam_dtype)


class TestDistributionsPoissonInvalid:

    @pytest.mark.skip("no support of generator yet")
    def test_none_lam_generator(self):
        with pytest.raises(TypeError):
            cupy.random.default_rng(0).poisson(None)

    @pytest.mark.usefixtures("allow_fall_back_on_numpy")
    def test_none_lam_legacy(self):
        with pytest.raises(TypeError):
            _distributions.poisson(None)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "a_shape": [()],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsPower(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_power(self, a_dtype):
        a = numpy.full(self.a_shape, 0.5, dtype=a_dtype)
        self.check_distribution("power", {"a": a})

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_power_for_negative_a(self, a_dtype):
        a = numpy.full(self.a_shape, -0.5, dtype=a_dtype)
        with pytest.raises(ValueError):
            cp_params = {"a": cupy.asarray(a)}
            getattr(_distributions, "power")(size=self.shape, **cp_params)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "scale_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsRayleigh(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("scale_dtype")
    def test_rayleigh(self, scale_dtype):
        scale = numpy.full(self.scale_shape, 3, dtype=scale_dtype)
        self.check_distribution("rayleigh", {"scale": scale})

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("scale_dtype")
    def test_rayleigh_for_zero_scale(self, scale_dtype):
        scale = numpy.zeros(self.scale_shape, dtype=scale_dtype)
        self.check_distribution("rayleigh", {"scale": scale})

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("scale_dtype")
    def test_rayleigh_for_negative_scale(self, scale_dtype):
        scale = numpy.full(self.scale_shape, -0.5, dtype=scale_dtype)
        with pytest.raises(ValueError):
            cp_params = {"scale": cupy.asarray(scale)}
            _distributions.rayleigh(size=self.shape, **cp_params)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
        }
    )
)
class TestDistributionsStandardCauchy(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    def test_standard_cauchy(self):
        self.check_distribution("standard_cauchy", {})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
        }
    )
)
class TestDistributionsStandardExponential(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    def test_standard_exponential(self):
        self.check_distribution("standard_exponential", {})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
            "shape_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsStandardGamma(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("shape_dtype")
    def test_standard_gamma_legacy(self, shape_dtype):
        shape = numpy.ones(self.shape_shape, dtype=shape_dtype)
        self.check_distribution("standard_gamma", {"shape": shape})

    @pytest.mark.skip("no support of generator yet")
    @testing.for_float_dtypes("dtype", no_float16=True)
    @testing.for_float_dtypes("shape_dtype")
    def test_standard_gamma_generator(self, shape_dtype, dtype):
        shape = numpy.ones(self.shape_shape, dtype=shape_dtype)
        self.check_generator_distribution(
            "standard_gamma", {"shape": shape}, dtype
        )


class TestDistributionsStandardGammaInvalid(RandomDistributionsTestCase):

    @pytest.mark.skip("no support of generator yet")
    def test_none_shape_generator(self):
        with pytest.raises(TypeError):
            cupy.random.default_rng(0).standard_gamma(None)

    @pytest.mark.usefixtures("allow_fall_back_on_numpy")
    def test_none_shape_legacy(self):
        with pytest.raises(TypeError):
            _distributions.standard_gamma(None)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2), None],
        }
    )
)
class TestDistributionsStandardNormal(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    def test_standard_normal(self):
        self.check_distribution("standard_normal", {})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "df_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsStandardT:

    def check_distribution(self, dist_func, df_dtype):
        df = cupy.ones(self.df_shape, dtype=df_dtype)
        out = dist_func(df, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("df_dtype")
    def test_standard_t(self, df_dtype):
        self.check_distribution(_distributions.standard_t, df_dtype)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "left_shape": [(), (3, 2)],
            "mode_shape": [(), (3, 2)],
            "right_shape": [(), (3, 2)],
            # "dtype": _regular_float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsTriangular(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(
        _regular_float_dtypes, names=["left_dtype", "mode_dtype", "right_dtype"]
    )
    def test_triangular(self, left_dtype, mode_dtype, right_dtype):
        left = numpy.full(self.left_shape, -1, dtype=left_dtype)
        mode = numpy.full(self.mode_shape, 0, dtype=mode_dtype)
        right = numpy.full(self.right_shape, 2, dtype=right_dtype)
        self.check_distribution(
            "triangular",
            {"left": left, "mode": mode, "right": right},
            self.dtype,
        )

    @testing.for_float_dtypes("param_dtype", no_float16=True)
    def test_triangular_for_invalid_params(self, param_dtype):
        left = cupy.full(self.left_shape, 1, dtype=param_dtype)
        mode = cupy.full(self.mode_shape, 0, dtype=param_dtype)
        right = cupy.full(self.right_shape, 2, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.triangular(left, mode, right, size=self.shape)

        left = cupy.full(self.left_shape, -2, dtype=param_dtype)
        mode = cupy.full(self.mode_shape, 0, dtype=param_dtype)
        right = cupy.full(self.right_shape, -1, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.triangular(left, mode, right, size=self.shape)

        left = cupy.full(self.left_shape, 0, dtype=param_dtype)
        mode = cupy.full(self.mode_shape, 0, dtype=param_dtype)
        right = cupy.full(self.right_shape, 0, dtype=param_dtype)
        with pytest.raises(ValueError):
            _distributions.triangular(left, mode, right, size=self.shape)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "low_shape": [(), (3, 2)],
            "high_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsUniform(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_dtypes_combination(
        _float_dtypes, names=["low_dtype", "high_dtype"]
    )
    def test_uniform(self, low_dtype, high_dtype):
        low = numpy.ones(self.low_shape, dtype=low_dtype)
        high = numpy.ones(self.high_shape, dtype=high_dtype) * 2.0
        self.check_distribution("uniform", {"low": low, "high": high})


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "mu_shape": [(), (3, 2)],
            "kappa_shape": [(), (3, 2)],
            # "dtype": _float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsVonmises:

    def check_distribution(self, dist_func, mu_dtype, kappa_dtype, dtype):
        mu = cupy.ones(self.mu_shape, dtype=mu_dtype)
        kappa = cupy.ones(self.kappa_shape, dtype=kappa_dtype)
        out = dist_func(mu, kappa, self.shape)
        assert self.shape == out.shape
        # assert out.dtype == dtype

    @testing.for_dtypes_combination(
        _float_dtypes, names=["mu_dtype", "kappa_dtype"]
    )
    def test_vonmises(self, mu_dtype, kappa_dtype):
        self.check_distribution(
            _distributions.vonmises, mu_dtype, kappa_dtype, self.dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "mean_shape": [(), (3, 2)],
            "scale_shape": [(), (3, 2)],
            # "dtype": _regular_float_dtypes,  # to escape timeout
            "dtype": [None],  # no dtype supported
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsWald(RandomDistributionsTestCase):

    @testing.for_dtypes_combination(
        _float_dtypes, names=["mean_dtype", "scale_dtype"]
    )
    def test_wald(self, mean_dtype, scale_dtype):
        mean = numpy.full(self.mean_shape, 3, dtype=mean_dtype)
        scale = numpy.full(self.scale_shape, 3, dtype=scale_dtype)
        self.check_distribution(
            "wald", {"mean": mean, "scale": scale}, self.dtype
        )


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "a_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsWeibull(RandomDistributionsTestCase):

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_weibull(self, a_dtype):
        a = numpy.ones(self.a_shape, dtype=a_dtype)
        self.check_distribution("weibull", {"a": a})

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_weibull_for_inf_a(self, a_dtype):
        a = numpy.full(self.a_shape, numpy.inf, dtype=a_dtype)
        self.check_distribution("weibull", {"a": a})

    # @testing.for_float_dtypes("dtype", no_float16=True) # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_weibull_for_negative_a(self, a_dtype):
        a = numpy.full(self.a_shape, -0.5, dtype=a_dtype)
        with pytest.raises(ValueError):
            cp_params = {"a": cupy.asarray(a)}
            getattr(_distributions, "weibull")(size=self.shape, **cp_params)


@testing.parameterize(
    *testing.product(
        {
            "shape": [(4, 3, 2), (3, 2)],
            "a_shape": [(), (3, 2)],
        }
    )
)
@pytest.mark.usefixtures("allow_fall_back_on_numpy")
class TestDistributionsZipf(RandomDistributionsTestCase):

    # @testing.for_dtypes([numpy.int32, numpy.int64], "dtype") # no dtype supported
    @testing.for_float_dtypes("a_dtype")
    def test_zipf(self, a_dtype):
        a = numpy.full(self.a_shape, 2, dtype=a_dtype)
        self.check_distribution("zipf", {"a": a})
