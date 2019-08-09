import numpy as np
from numpy.testing import assert_almost_equal
from unittest import main, TestCase
from .analysis import overlap, cooccur


class Tests(TestCase):
    def setUp(self):
        self.a = np.zeros(100)
        self.b = np.ones(100)
        # c: --========
        # d: ==--------
        # e: --------==
        # f: =====-----
        # g: ---===----
        self.c = np.array([1] * 20 + [5] * 80)
        self.d = np.array([9] * 20 + [1] * 80)
        self.e = np.array([1] * 80 + [12] * 20)
        self.f = np.array([7] * 50 + [1] * 50)
        self.g = np.array([1] * 30 + [9] * 30 + [1] * 40)

    def test_cooccur_raise(self):
        with self.assertRaises(ValueError):
            cooccur(self.a, self.c, negate=True)
        with self.assertRaises(ValueError):
            cooccur(self.b, self.c, negate=False)

    def test_cooccur_mutual_exclusivity(self):
        obs1, obs2, dist = cooccur(self.c, self.d, cutoff=1, psudo=2, negate=True)
        assert_almost_equal(1 - 2/(20+2), obs1)
        assert_almost_equal(0, obs2)

        obs1, obs2, dist = cooccur(self.c, self.c, cutoff=1, psudo=2, negate=True)
        assert_almost_equal(0, obs1)
        assert_almost_equal(1, obs2)

        obs1, obs2, dist = cooccur(self.c, self.e, cutoff=1, psudo=2, negate=True)
        assert_almost_equal(0, obs1)
        assert_almost_equal(1, obs2)

        obs1, obs2, dist = cooccur(self.c, self.f, cutoff=1, psudo=2, negate=True)
        assert_almost_equal(1 - (30 + 2) / (50 + 2), obs1)
        assert_almost_equal(0, obs2)

        obs1, obs2, dist = cooccur(self.f, self.g, cutoff=1, psudo=2, negate=True)
        assert_almost_equal(1 - (20 + 2) / (30 + 2), obs1)
        self.assertGreater(obs2, 0.9)

    def test_cooccur_coexistence(self):
        obs1, obs2, dist = cooccur(self.c, self.d, cutoff=1, psudo=0, negate=False)
        assert_almost_equal(0, obs1)
        self.assertEqual(1, obs2)
        obs1, obs2, dist = cooccur(self.c, self.c, cutoff=1, psudo=0, negate=False)
        assert_almost_equal(1, obs1)
        self.assertEqual(0, obs2)


if __name__ == '__main__':
    main()
