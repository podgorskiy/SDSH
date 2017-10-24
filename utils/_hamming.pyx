# Copyright 2017 Stanislav Pidhorskyi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Faster hamming distance using cython"""

import numpy as np
cimport numpy as np
cimport cython


cdef inline np.int8_t __hamming_distance_2(np.uint32_t x, np.uint32_t y):
    cdef np.uint32_t v = x ^ y
    v = v - ((v >> 1) & 0x55555555U)
    v = (v & 0x33333333U) + ((v >> 2) & 0x33333333U)
    v = (v + (v >> 4)) & 0x0f0f0f0fU
    return (v * 0x01010101U) >> 24


cdef inline np.int8_t __hamming_distance(np.uint32_t x, np.uint32_t y):
    cdef np.int8_t dist = 0
    cdef np.uint32_t val = x ^ y
    while val:
        dist += 1
        val &= val - 1

    return dist


@cython.boundscheck(False)
@cython.wraparound(False)
cdef np.uint32_t[::1] __to_int32_hashes(np.ndarray[np.float_t, ndim=2] p):
    cdef np.intp_t w = p.shape[1]
    cdef np.intp_t h = p.shape[0]
    cdef np.uint32_t output = 0
    cdef np.uint32_t power = 1
    cdef np.float_t[:, ::1] p_v = p;

    cdef np.uint32_t[::1] out = np.zeros(h, dtype=np.uint32)
    for x in range(h):
        output = 0
        power = 1
        for y in range(w):
            output += power if p_v[x, y] > 0.0 else 0
            power *= 2
        out[x] = output
    return out


@cython.boundscheck(False)
@cython.wraparound(False)
def calc_hamming_dist(b1, b2):
    """Compute the hamming distance between every pair of data points represented in each row of b1 and b2"""
    cdef np.uint32_t[::1] p1 = __to_int32_hashes(b1)
    cdef np.uint32_t[::1] p2 = __to_int32_hashes(b2)

    cdef np.intp_t l = p1.shape[0]

    cdef np.ndarray[np.int8_t, ndim=2] out = np.zeros([l, l], dtype=np.int8)
    cdef np.int8_t[:, ::1] out_v = out;

    cdef np.int8_t d = 0
    cdef np.int8_t dist = 0
    cdef np.uint32_t val = 0

    for x in range(l):
        for y in range(l):
            out_v[x, y] = __hamming_distance_2(p1[x], p2[y])

    return out


@cython.boundscheck(False)
@cython.wraparound(False)
def sort(a):
    cdef np.int8_t[:, ::1] a_v = a;
    cdef np.intp_t l = a.shape[0]

    cdef np.int32_t[33] count
    cdef np.int32_t total
    cdef np.int32_t old_count
    cdef np.int8_t key

    cdef np.ndarray[np.int32_t, ndim=2] out = np.zeros([l, l], dtype=np.int32)
    cdef np.int32_t[:, ::1] out_v = out;

    cdef np.int32_t[::1] tmp = np.zeros([l], dtype=np.int32)

    for x in range(l):
        for i in range(33):
            count[i] = 0
        for y in range(l):
            count[a_v[x, y]] += 1
        total = 0
        old_count = 0
        for i in range(33):
            old_count = count[i]
            count[i] = total
            total += old_count

        for y in range(l):
            key = a_v[x, y]
            tmp[y] = count[key]
            count[key] += 1

        for y in range(l):
            out_v[x, tmp[y]] = y

    return out
