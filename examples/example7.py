# cython: language_level=3
# -*- coding: utf-8 -*-
# *****************************************************************************
# Copyright (c) 2016-2025, Intel Corporation
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

"""Example 7.

This example shows simple usage of the DPNP
to calculate square matrix multiplication

Also, it produces performance comparison between regular NumPy
and DPNP for several matrix multiplication

"""

import time

import dpctl
import numpy

import dpnp


def run_function(executor, name, size, test_type, repetition):
    x = executor.reshape(
        executor.arange(size * size, dtype=test_type), (size, size)
    )

    times = []
    for _ in range(repetition):
        start_time = time.perf_counter()
        result = executor.sum(x)
        # print("result[5]=%f" % (result.item(5)))
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    execution_time = numpy.median(times)
    return execution_time, result


def get_dtypes():
    _dtypes_list = [numpy.int32, numpy.int64, numpy.float32]
    device = dpctl.select_default_device()
    if device.has_aspect_fp64:
        _dtypes_list.append(numpy.float64)
    return _dtypes_list


if __name__ == "__main__":
    test_repetition = 5
    for test_type in get_dtypes():
        type_name = numpy.dtype(test_type).name
        print(
            f"...Test data type is {test_type}, each test repetitions {test_repetition}"
        )

        for size in [256, 512, 1024, 2048, 4096, 8192]:
            time_python, result_python = run_function(
                numpy, "<NumPy>", size, test_type, test_repetition
            )
            time_mkl, result_mkl = run_function(
                dpnp, " <DPNP>", size, test_type, test_repetition
            )

            if result_mkl == result_python:
                verification = True
            else:
                verification = f"({result_mkl} != {result_python})"

            msg = f"type:{type_name}:N:{size:4}:NumPy:{time_python:.3e}:DPNP:{time_mkl:.3e}"
            msg += f":ratio:{time_python/time_mkl:6.2f}:verification:{verification}"
            print(msg)
