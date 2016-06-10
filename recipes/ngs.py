import re
import os
import pandas as pd
from collections import Iterator


def compute_n50(nums, cutoff=500):
    '''Compute N50 of the input contig lengths.

    Parameters
    ----------
    nums : Iterable, int
        contig lengths
    cutoff : int
        only consider the contigs >= cutoff.
    Returns
    -------
    int

    Examples
    --------
    >>> from . import compute_n50
    >>> nums = [400, 500, 502, 655, 634, 605, 590, 584, 552, 549, 545, 545, 542, 536, 526, 521, 517, 513]
    >>> compute_n50(nums)
    ... 545
    '''
    if isinstance(nums, Iterator):
        raise TypeError('Must supply a container, not an iterator.')
    n50_len = sum(i for i in nums if i >= cutoff) / 2
    length = 0
    for i in sorted(nums, reverse=True):
        length += i
        if length >= n50_len:
            return i


def create_sample_table(d, patterns=None,
                        sid=lambda x: re.split('_L00[0-9]_R[12]_', x)[0],
                        select=lambda x: x.endswith('.fq.gz'),
                        negate=False):
    '''Return a sample-by-file-path table of the raw sequence files.

    Parameters
    ----------
    d : str
        dir to the raw sequence files
    patterns : dict-like
        file patterns for each sample. keys will be used as column name
        of the return table and values will be used in `re.search`
    sid : callable
        how to create sample IDs from sequence file name
    select : callable
        what files to include
    negate : boolean
        negate the select.

    Returns
    -------
    pandas.DataFrame
    '''
    if patterns is None:
        patterns = {'R1_paired':   r'R1_[0-9]{3}_paired',
                    'R1_unpaired': r'R1_[0-9]{3}_unpaired',
                    'R2_paired':   r'R2_[0-9]{3}_paired',
                    'R2_unpaired': r'R2_[0-9]{3}_unpaired'}
    samples = pd.DataFrame(columns=patterns.keys())
    for f in os.listdir(d):
        if negate:
            flag = not select(f)
        else:
            flag = select(f)
        if flag:
            try:
                s_id = sid(f)
            except:
                raise ValueError('Can not extract sample ID from file name: %s' % f)
            # check the file name only matches one unique pattern
            t = [i for i in patterns if re.search(patterns[i], f)]
            if len(t) != 1:
                raise ValueError('File name {} matches none or multiple patterns: {}'.format(f, t))

            samples.loc[s_id, t[0]] = f

    return samples
