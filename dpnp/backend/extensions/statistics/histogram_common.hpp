//*****************************************************************************
// Copyright (c) 2024-2025, Intel Corporation
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
// - Redistributions of source code must retain the above copyright notice,
//   this list of conditions and the following disclaimer.
// - Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
// THE POSSIBILITY OF SUCH DAMAGE.
//*****************************************************************************

#pragma once

#include <sycl/sycl.hpp>

#include "ext/common.hpp"

namespace dpctl::tensor
{
class usm_ndarray;
}

using dpctl::tensor::usm_ndarray;

using ext::common::AtomicOp;
using ext::common::IsNan;
using ext::common::Less;

namespace statistics::histogram
{

template <typename T, int Dims>
struct CachedData
{
    static constexpr bool const sync_after_init = true;
    using Shape = sycl::range<Dims>;
    using value_type = T;
    using pointer_type = value_type *;
    static constexpr auto dims = Dims;

    using ncT = typename std::remove_const<value_type>::type;
    using LocalData = sycl::local_accessor<ncT, Dims>;

    CachedData(T *global_data, Shape shape, sycl::handler &cgh)
    {
        this->global_data = global_data;
        local_data = LocalData(shape, cgh);
    }

    T *get_ptr() const
    {
        return &local_data[0];
    }

    template <int _Dims>
    void init(const sycl::nd_item<_Dims> &item) const
    {
        uint32_t llid = item.get_local_linear_id();
        auto local_ptr = &local_data[0];
        uint32_t size = local_data.size();
        auto group = item.get_group();
        uint32_t local_size = group.get_local_linear_range();

        for (uint32_t i = llid; i < size; i += local_size) {
            local_ptr[i] = global_data[i];
        }
    }

    size_t size() const
    {
        return local_data.size();
    }

    T &operator[](const sycl::id<Dims> &id) const
    {
        return local_data[id];
    }

    template <typename = std::enable_if_t<Dims == 1>>
    T &operator[](const size_t id) const
    {
        return local_data[id];
    }

private:
    LocalData local_data;
    value_type *global_data = nullptr;
};

template <typename T, int Dims>
struct UncachedData
{
    static constexpr bool const sync_after_init = false;
    using Shape = sycl::range<Dims>;
    using value_type = T;
    using pointer_type = value_type *;
    static constexpr auto dims = Dims;

    UncachedData(T *global_data, const Shape &shape, sycl::handler &)
    {
        this->global_data = global_data;
        _shape = shape;
    }

    T *get_ptr() const
    {
        return global_data;
    }

    template <int _Dims>
    void init(const sycl::nd_item<_Dims> &) const
    {
    }

    size_t size() const
    {
        return _shape.size();
    }

    T &operator[](const sycl::id<Dims> &id) const
    {
        return global_data[id];
    }

    template <typename = std::enable_if_t<Dims == 1>>
    T &operator[](const size_t id) const
    {
        return global_data[id];
    }

private:
    T *global_data = nullptr;
    Shape _shape;
};

template <typename T>
struct HistLocalType
{
    using type = T;
};

template <>
struct HistLocalType<uint64_t>
{
    using type = uint32_t;
};

template <>
struct HistLocalType<int64_t>
{
    using type = int32_t;
};

template <typename T, typename localT = typename HistLocalType<T>::type>
struct HistWithLocalCopies
{
    static constexpr bool const sync_after_init = true;
    static constexpr bool const sync_before_finalize = true;

    using LocalHist = sycl::local_accessor<localT, 2>;

    HistWithLocalCopies(T *global_data,
                        size_t bins_count,
                        int32_t copies_count,
                        sycl::handler &cgh)
    {
        local_hist = LocalHist(sycl::range<2>(copies_count, bins_count), cgh);
        global_hist = global_data;
    }

    template <int _Dims>
    void init(const sycl::nd_item<_Dims> &item, localT val = 0) const
    {
        uint32_t llid = item.get_local_linear_id();
        auto *local_ptr = &local_hist[0][0];
        uint32_t size = local_hist.size();
        auto group = item.get_group();
        uint32_t local_size = group.get_local_linear_range();

        for (uint32_t i = llid; i < size; i += local_size) {
            local_ptr[i] = val;
        }
    }

    template <int _Dims>
    void add(const sycl::nd_item<_Dims> &item, int32_t bin, localT value) const
    {
        int32_t llid = item.get_local_linear_id();
        int32_t local_hist_count = local_hist.get_range().get(0);
        int32_t local_copy_id =
            local_hist_count == 1 ? 0 : llid % local_hist_count;

        AtomicOp<localT, sycl::memory_order::relaxed,
                 sycl::memory_scope::work_group>::add(local_hist[local_copy_id]
                                                                [bin],
                                                      value);
    }

    template <int _Dims>
    void finalize(const sycl::nd_item<_Dims> &item) const
    {
        uint32_t llid = item.get_local_linear_id();
        uint32_t bins_count = local_hist.get_range().get(1);
        uint32_t local_hist_count = local_hist.get_range().get(0);
        auto group = item.get_group();
        uint32_t local_size = group.get_local_linear_range();

        for (uint32_t i = llid; i < bins_count; i += local_size) {
            auto value = local_hist[0][i];
            for (uint32_t lhc = 1; lhc < local_hist_count; ++lhc) {
                value += local_hist[lhc][i];
            }
            if (value != T(0)) {
                AtomicOp<T, sycl::memory_order::relaxed,
                         sycl::memory_scope::device>::add(global_hist[i],
                                                          value);
            }
        }
    }

    uint32_t size() const
    {
        return local_hist.size();
    }

private:
    LocalHist local_hist;
    T *global_hist = nullptr;
};

template <typename T>
struct HistGlobalMemory
{
    static constexpr bool const sync_after_init = false;
    static constexpr bool const sync_before_finalize = false;

    HistGlobalMemory(T *global_data)
    {
        global_hist = global_data;
    }

    template <int _Dims>
    void init(const sycl::nd_item<_Dims> &) const
    {
    }

    template <int _Dims>
    void add(const sycl::nd_item<_Dims> &, int32_t bin, T value) const
    {
        AtomicOp<T, sycl::memory_order::relaxed,
                 sycl::memory_scope::device>::add(global_hist[bin], value);
    }

    template <int _Dims>
    void finalize(const sycl::nd_item<_Dims> &) const
    {
    }

private:
    T *global_hist = nullptr;
};

template <typename T = uint32_t>
struct NoWeights
{
    constexpr T get(size_t) const
    {
        return 1;
    }
};

template <typename T>
struct Weights
{
    Weights(T *weights)
    {
        data = weights;
    }

    T get(size_t id) const
    {
        return data[id];
    }

private:
    T *data = nullptr;
};

template <typename dT>
bool check_in_bounds(const dT &val, const dT &min, const dT &max)
{
    Less<dT> _less;
    return !_less(val, min) && !_less(max, val) && !IsNan<dT>::isnan(val);
}

template <typename T, typename HistImpl, typename Edges, typename Weights>
class histogram_kernel;

template <typename T, typename HistImpl, typename Edges, typename Weights>
void submit_histogram(const T *in,
                      const size_t size,
                      const size_t dims,
                      const uint32_t WorkPI,
                      const HistImpl &hist,
                      const Edges &edges,
                      const Weights &weights,
                      sycl::nd_range<1> nd_range,
                      sycl::handler &cgh)
{
    cgh.parallel_for<histogram_kernel<T, HistImpl, Edges, Weights>>(
        nd_range, [=](sycl::nd_item<1> item) {
            auto id = item.get_group_linear_id();
            auto lid = item.get_local_linear_id();
            auto group = item.get_group();
            auto local_size = item.get_local_range(0);

            hist.init(item);
            edges.init(item);

            if constexpr (HistImpl::sync_after_init || Edges::sync_after_init) {
                sycl::group_barrier(group, sycl::memory_scope::work_group);
            }

            auto bounds = edges.get_bounds();

            for (uint32_t i = 0; i < WorkPI; ++i) {
                auto data_idx = id * WorkPI * local_size + i * local_size + lid;
                if (data_idx < size) {
                    auto *d = &in[data_idx * dims];

                    if (edges.in_bounds(d, bounds)) {
                        auto bin = edges.get_bin(item, d, bounds);
                        auto weight = weights.get(data_idx);
                        hist.add(item, bin, weight);
                    }
                }
            }

            if constexpr (HistImpl::sync_before_finalize) {
                sycl::group_barrier(group, sycl::memory_scope::work_group);
            }

            hist.finalize(item);
        });
}

void validate(const usm_ndarray &sample,
              const std::optional<const dpctl::tensor::usm_ndarray> &bins,
              const std::optional<const dpctl::tensor::usm_ndarray> &weights,
              const usm_ndarray &histogram);

uint32_t get_local_hist_copies_count(uint32_t loc_mem_size_in_items,
                                     uint32_t local_size,
                                     uint32_t hist_size_in_items);

} // namespace statistics::histogram
