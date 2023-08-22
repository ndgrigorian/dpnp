# cython: language_level=3
# cython: linetrace=True
# -*- coding: utf-8 -*-
# *****************************************************************************
# Copyright (c) 2016-2023, Intel Corporation
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

"""Module Backend (Array manipulation routines)

This module contains interface functions between C backend layer
and the rest of the library

"""

# NO IMPORTs here. All imports must be placed into main "dpnp_algo.pyx" file

__all__ += [
    "dpnp_atleast_2d",
    "dpnp_atleast_3d",
    "dpnp_expand_dims",
    "dpnp_repeat",
    "dpnp_reshape",
]


# C function pointer to the C library template functions
ctypedef c_dpctl.DPCTLSyclEventRef(*fptr_dpnp_repeat_t)(c_dpctl.DPCTLSyclQueueRef,
                                                        const void *, void * , const size_t , const size_t,
                                                        const c_dpctl.DPCTLEventVectorRef)


cpdef utils.dpnp_descriptor dpnp_atleast_2d(utils.dpnp_descriptor arr):
    # it looks like it should be dpnp.copy + dpnp.reshape
    cdef utils.dpnp_descriptor result
    cdef size_t arr_ndim = arr.ndim
    cdef long arr_size = arr.size
    if arr_ndim == 1:
        arr_obj = arr.get_array()
        result = utils_py.create_output_descriptor_py((1, arr_size),
                                                      arr.dtype,
                                                      None,
                                                      device=arr_obj.sycl_device,
                                                      usm_type=arr_obj.usm_type,
                                                      sycl_queue=arr_obj.sycl_queue)
        for i in range(arr_size):
            result.get_pyobj()[0, i] = arr.get_pyobj()[i]
        return result
    else:
        return arr


cpdef utils.dpnp_descriptor dpnp_atleast_3d(utils.dpnp_descriptor arr):
    # it looks like it should be dpnp.copy + dpnp.reshape
    cdef utils.dpnp_descriptor result
    cdef size_t arr_ndim = arr.ndim
    cdef shape_type_c arr_shape = arr.shape
    cdef long arr_size = arr.size

    arr_obj = arr.get_array()

    if arr_ndim == 1:
        result = utils_py.create_output_descriptor_py((1, 1, arr_size),
                                                      arr.dtype,
                                                      None,
                                                      device=arr_obj.sycl_device,
                                                      usm_type=arr_obj.usm_type,
                                                      sycl_queue=arr_obj.sycl_queue)
        for i in range(arr_size):
            result.get_pyobj()[0, 0, i] = arr.get_pyobj()[i]
        return result
    elif arr_ndim == 2:
        result = utils_py.create_output_descriptor_py((1, arr_shape[0], arr_shape[1]),
                                                      arr.dtype,
                                                      None,
                                                      device=arr_obj.sycl_device,
                                                      usm_type=arr_obj.usm_type,
                                                      sycl_queue=arr_obj.sycl_queue)
        for i in range(arr_shape[0]):
            for j in range(arr_shape[1]):
                result.get_pyobj()[0, i, j] = arr.get_pyobj()[i, j]
        return result
    else:
        return arr


cpdef utils.dpnp_descriptor dpnp_expand_dims(utils.dpnp_descriptor in_array, axis):
    axis_tuple = utils._object_to_tuple(axis)
    result_ndim = len(axis_tuple) + in_array.ndim

    if len(axis_tuple) == 0:
        axis_ndim = 0
    else:
        axis_ndim = max(-min(0, min(axis_tuple)), max(0, max(axis_tuple))) + 1

    axis_norm = utils._object_to_tuple(utils.normalize_axis(axis_tuple, result_ndim))

    if axis_ndim - len(axis_norm) > in_array.ndim:
        utils.checker_throw_axis_error("dpnp_expand_dims", "axis", axis, axis_ndim)

    if len(axis_norm) > len(set(axis_norm)):
        utils.checker_throw_value_error("dpnp_expand_dims", "axis", axis, "no repeated axis")

    cdef shape_type_c shape_list
    axis_idx = 0
    for i in range(result_ndim):
        if i in axis_norm:
            shape_list.push_back(1)
        else:
            shape_list.push_back(in_array.shape[axis_idx])
            axis_idx = axis_idx + 1

    return dpnp_reshape(in_array, shape_list)


cpdef utils.dpnp_descriptor dpnp_repeat(utils.dpnp_descriptor array1, repeats, axes=None):
    cdef DPNPFuncType param1_type = dpnp_dtype_to_DPNPFuncType(array1.dtype)

    cdef DPNPFuncData kernel_data = get_dpnp_function_ptr(DPNP_FN_REPEAT_EXT, param1_type, param1_type)

    array1_obj = array1.get_array()

    # ceate result array with type given by FPTR data
    cdef shape_type_c result_shape = (array1.size * repeats, )
    cdef utils.dpnp_descriptor result = utils.create_output_descriptor(result_shape,
                                                                       kernel_data.return_type,
                                                                       None,
                                                                       device=array1_obj.sycl_device,
                                                                       usm_type=array1_obj.usm_type,
                                                                       sycl_queue=array1_obj.sycl_queue)
    result_sycl_queue = result.get_array().sycl_queue

    cdef c_dpctl.SyclQueue q = <c_dpctl.SyclQueue> result_sycl_queue
    cdef c_dpctl.DPCTLSyclQueueRef q_ref = q.get_queue_ref()

    cdef fptr_dpnp_repeat_t func = <fptr_dpnp_repeat_t > kernel_data.ptr
    cdef c_dpctl.DPCTLSyclEventRef event_ref = func(q_ref,
                                                    array1.get_data(),
                                                    result.get_data(),
                                                    repeats,
                                                    array1.size,
                                                    NULL)  # dep_events_ref

    with nogil: c_dpctl.DPCTLEvent_WaitAndThrow(event_ref)
    c_dpctl.DPCTLEvent_Delete(event_ref)

    return result


cpdef utils.dpnp_descriptor dpnp_reshape(utils.dpnp_descriptor array1, newshape, order="C"):
    # return dpnp.get_dpnp_descriptor(dpctl.tensor.usm_ndarray(newshape, dtype=numpy.dtype(array1.dtype).name, buffer=array1.get_pyobj()))
    # return dpnp.get_dpnp_descriptor(dpctl.tensor.reshape(array1.get_pyobj(), newshape))
    array1_obj = array1.get_array()
    array_obj = dpctl.tensor.reshape(array1_obj, newshape, order=order)
    return dpnp.get_dpnp_descriptor(dpnp_array(array_obj.shape,
                                               buffer=array_obj,
                                               order=order,
                                               device=array1_obj.sycl_device,
                                               usm_type=array1_obj.usm_type,
                                               sycl_queue=array1_obj.sycl_queue),
                                    copy_when_nondefault_queue=False)
