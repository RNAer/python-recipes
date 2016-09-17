from unittest import TestCase, main
from tempfile import TemporaryDirectory
from os.path import join
import re

import numpy as np
import pandas as pd
from skbio.util import get_data_path
from skbio import DNA
import skbio

from recipes.ngs import create_sample_table, split_paired_end, equal_seqs


class Tests(TestCase):
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

    def test_equals_seqs(self):
        seq1 = [DNA('ATGC'), DNA('A')]
        seq2 = [DNA('A'), DNA('ATGC')]
        self.assertTrue(equal_seqs(seq1, seq2))

    def test_split_paired_end(self):
        merged, r1, r2, r1_unpaired, r2_unpaired = [
            get_data_path(i) for i in
            ['merged.fq', 'r1.fq', 'r2.fq',
             'r1_unpaired.fq', 'r2_unpaired.fq']]
        with TemporaryDirectory() as d, open(merged) as fh:
            fs = split_paired_end(fh, prefix=join(d, 'test'))
            for i, j in zip([r1, r2, r1_unpaired, r2_unpaired], fs):
                obs = list(skbio.io.read(i, format='fastq'))
                exp = list(skbio.io.read(j, format='fastq'))
                self.assertTrue(equal_seqs(obs, exp))


if __name__ == '__main__':
    main()
