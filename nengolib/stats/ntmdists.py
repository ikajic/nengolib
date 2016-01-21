import numpy as np
from scipy.special import beta, betainc, betaincinv

from nengo.dists import Distribution, UniformHypersphere
from nengo.utils.numpy import norm

from nengolib.linalg.ortho import random_orthogonal
from nengolib.stats._sobol_seq import i4_sobol_generate

__all__ = ['SphericalCoords', 'Sobol', 'ScatteredHypersphere']


class SphericalCoords(Distribution):

    def __init__(self, m):
        self.m = m

    def sample(self, num, d=None, rng=np.random):
        shape = self._sample_shape(num, d)
        y = rng.uniform(size=shape)
        return self.ppf(y)

    def pdf(self, x):
        return (np.pi * np.sin(np.pi * x) ** (self.m-1) /
                beta(self.m / 2.0, 0.5))

    def cdf(self, x):
        y = 0.5 * betainc(self.m / 2.0, 0.5, np.sin(np.pi * x) ** 2)
        return np.where(x < 0.5, y, 1 - y)

    def ppf(self, y):
        y_reflect = np.where(y < 0.5, y, 1 - y)
        z_sq = betaincinv(self.m / 2.0, 0.5, 2 * y_reflect)
        x = np.arcsin(np.sqrt(z_sq)) / np.pi
        return np.where(y < 0.5, x, 1 - x)


class Sobol(Distribution):

    def sample(self, num, d=None, rng=np.random):
        if d is None or d < 1 or d > 40:  # TODO: also check if integer
            # TODO: this should be raised when the ensemble is created
            raise ValueError("d (%d) must be integer in range [1, 40]" % d)
        num, d = self._sample_shape(num, d)
        return i4_sobol_generate(d, num, skip=0)


class ScatteredHypersphere(UniformHypersphere):

    def sample(self, num, d=1.0, rng=np.random, ntm=Sobol()):
        if self.surface:
            cube = ntm.sample(num, d-1)
            radius = 1.0
        else:
            dcube = ntm.sample(num, d)
            cube, radius = dcube[:, :-1], dcube[:, -1:] ** (1.0 / d)

        # inverse transform method (section 1.5.2)
        for j in range(d-1):
            cube[:, j] = SphericalCoords(d-1-j).ppf(cube[:, j])

        # spherical coordinate transform
        i = np.ones(d-1)
        i[-1] = 2.0
        s = np.sin(i[None, :] * np.pi * cube)
        c = np.cos(i[None, :] * np.pi * cube)
        mapped = np.ones((num, d))
        mapped[:, 1:] = np.cumprod(s, axis=1)
        mapped[:, :-1] *= c
        assert np.allclose(norm(mapped, axis=1, keepdims=True), 1)

        # radius adjustment for ball versus sphere, and rotate
        rotation = random_orthogonal(d, rng=rng)
        return np.dot(mapped * radius, rotation)