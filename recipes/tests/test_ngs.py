import unittest
from tempfile import TemporaryDirectory
from os.path import join
import re

import numpy as np
import pandas as pd

from recipes.ngs import create_sample_table


class Tests(unittest.TestCase):
    def test_create_sample_table(self):
        with TemporaryDirectory() as d:
            sids = ['285', 'Dust.1', 'Dust.2']
            types = ['R1_paired', 'R1_unpaired', 'R2_paired', 'R2_unpaired']
            files = np.array(['{}_{}.fq'.format(i, j) for i in sids for j in types])
            exp = pd.DataFrame(data=files.reshape((3, 4)), index=sids, columns=types)

            for i in files:
                open(join(d, i), 'w').close()
            obs = create_sample_table(
                d,
                sid=lambda x: re.split('_R[12]_', x)[0],
                select=lambda x: x.endswith('.fq'))

            self.assertEqual(exp.to_dict(), obs.to_dict())


if __name__ == '__main__':
    unittest.main()
