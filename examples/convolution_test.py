# -*- coding: utf-8 -*-
"""
simple_test_astra.py -- a simple test script

Copyright 2014, 2015 Holger Kohr

This file is part of ODL.

ODL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ODL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ODL.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
from future import standard_library

import odl.operator.operator as op
import odl.operator.solvers as solvers
import odl.space.cartesian as ds
import odl.space.set as sets
import odl.discr.discretization as dd
import odl.space.function as fs
import solverExamples

from odl.utility.testutils import Timer

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

standard_library.install_aliases()


class Convolution(op.LinearOperator):
    def __init__(self, kernel, adjkernel=None):
        if not isinstance(kernel.space, ds.Rn):
            raise TypeError("Kernel must be Rn vector")

        self.kernel = kernel
        self.adjkernel = (adjkernel if adjkernel is not None
                          else kernel.space.element(kernel.data[::-1]))
        self.space = kernel.space
        self.norm = float(sum(abs(self.kernel.data)))

    def _apply(self, rhs, out):
        ndimage.convolve(rhs.data, self.kernel, output=out.data,
                         mode='wrap')

    @property
    def adjoint(self):
        return Convolution(self.adjkernel, self.kernel)

    def opNorm(self):
        return self.norm

    @property
    def domain(self):
        return self.space

    @property
    def range(self):
        return self.space


# Continuous definition of problem
continuousSpace = fs.L2(sets.Interval(0, 10))

# Complicated functions to check performance
continuousKernel = continuousSpace.element(lambda x: np.exp(x/2) *
                                           np.cos(x*1.172))
continuousRhs = continuousSpace.element(lambda x: x**2 *
                                        np.sin(x)**2*(x > 5))

# Discretization
rn = ds.EuclideanRn(500)
d = dd.uniform_discretization(continuousSpace, rn)
kernel = d.element(continuousKernel)
rhs = d.element(continuousRhs)

# Create operator
conv = Convolution(kernel)

# Dampening parameter for landweber
iterations = 100
omega = 1/conv.opNorm()**2

# Display partial
partial = solvers.ForEachPartial(lambda result: plt.plot(conv(result)[:]))

# Test CGN
plt.figure()
plt.plot(rhs)
solvers.conjugate_gradient(conv, d.zero(), rhs, iterations, partial)

# Landweber
plt.figure()
plt.plot(rhs)
solvers.landweber(conv, d.zero(), rhs, iterations, omega, partial)

# testTimingCG
with Timer("Optimized CG"):
    solvers.conjugate_gradient(conv, d.zero(), rhs, iterations)

with Timer("Base CG"):
    solverExamples.conjugate_gradient_base(conv, d.zero(), rhs, iterations)

# Landweber timing
with Timer("Optimized LW"):
    solvers.landweber(conv, d.zero(), rhs, iterations, omega)

with Timer("Basic LW"):
    solverExamples.landweberBase(conv, d.zero(), rhs, iterations, omega)

plt.show()
