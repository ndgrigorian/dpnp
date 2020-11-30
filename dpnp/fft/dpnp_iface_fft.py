# cython: language_level=3
# distutils: language = c++
# -*- coding: utf-8 -*-
# *****************************************************************************
# Copyright (c) 2016-2020, Intel Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
# *****************************************************************************

"""
Interface of the Discrete Fourier Transform part of the DPNP

Notes
-----
This module is a face or public interface file for the library
it contains:
 - Interface functions
 - documentation for the functions
 - The functions parameters check

"""


import dpnp
import numpy

from dpnp.dparray import dparray
from dpnp.dpnp_utils import *
from dpnp.fft.dpnp_algo_fft import *


__all__ = [
    "fft",
    "fft2",
    "fftn"
]


def fft(x1, n=None, axis=-1, norm=None):
    """
    Compute the one-dimensional discrete Fourier Transform.

    Limitations
    -----------
    Parameter ``norm`` is unsupported.
    Parameter ``x1`` supports `dpnp.int32`, `dpnp.int64`, `dpnp.float32`, `dpnp.float64` and
    `dpnp.complex128` datatypes only.

    For full documentation refer to :obj:`numpy.fft.fft`.

    """

    is_x1_dparray = isinstance(x1, dparray)

    if (not use_origin_backend(x1) and is_x1_dparray):
        if axis is None:
            axis_param = -1      # the most right dimension (default value)
        else:
            axis_param = axis

        if n is None:
            boundarie = x1.shape[axis_param]
        else:
            boundarie = n

        if x1.size < 1:
            pass                 # let fallback to handle exception
        elif boundarie < 1:
            pass                 # let fallback to handle exception
        elif norm is not None:
            pass
        else:
            return dpnp_fft(x1, boundarie, axis_param)

    return call_origin(numpy.fft.fft, x1, n, axis, norm)


def fft2(x1, s=None, axes=(-2, -1), norm=None):
    """
    Compute the 2-dimensional discrete Fourier Transform

    Multi-dimensional arrays computed as batch of 1-D arrays

    Limitations
    -----------
    Parameter ``axes`` is unsupported.
    Parameter ``norm`` is unsupported.
    Parameter ``x1`` supports 1-D arrays only.
    Parameter ``x1`` supports `dpnp.int32`, `dpnp.int64`, `dpnp.float32` and `dpnp.float64` datatypes only.

    See Also
    --------
    :obj:`numpy.fft.fft2` : Compute the 2-dimensional discrete Fourier Transform

    """

    is_x1_dparray = isinstance(x1, dparray)

    if (not use_origin_backend(x1) and is_x1_dparray and 0):
        if s is None:
            output_size = x1.size
        else:
            output_size = n

        if output_size < 1:
            pass
        elif axes != (-2, -1):
            pass
        elif norm is not None:
            pass
        elif x1.ndim > 1:
            pass
        else:
            return dpnp_fft(x1, output_size)

    return call_origin(numpy.fft.fft2, x1, s, axes, norm)


def fftn(x1, s=None, axes=None, norm=None):
    """
    Compute the N-dimensional FFT.

    Multi-dimensional arrays computed as batch of 1-D arrays

    Limitations
    -----------
    Parameter ``axes`` is unsupported.
    Parameter ``norm`` is unsupported.
    Parameter ``x1`` supports 1-D arrays only.
    Parameter ``x1`` supports `dpnp.int32`, `dpnp.int64`, `dpnp.float32` and `dpnp.float64` datatypes only.

    See Also
    --------
    :obj:`numpy.fft.fftn` : Compute the N-dimensional FFT.

    """

    is_x1_dparray = isinstance(x1, dparray)

    if (not use_origin_backend(x1) and is_x1_dparray and 0):
        if s is None:
            output_size = x1.size
        else:
            output_size = n

        if output_size < 1:
            pass
        elif axes is not None:
            pass
        elif norm is not None:
            pass
        elif x1.ndim > 1:
            pass
        else:
            return dpnp_fft(x1, output_size)

    return call_origin(numpy.fft.fftn, x1, s, axes, norm)
