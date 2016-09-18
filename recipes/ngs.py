import re
import os
import itertools
import gzip
import mmap

import pandas as pd


def equal_seqs(seqs_1, seqs_2):
    '''Test two sequence collections are equal.




    The sequences are compared by their sequence char,
    their IDs, and their descriptions. If both are equal,
    they are considered as the same.

    Parameters
    ----------
    seqs_1, seqs_2 : list of skbio.Sequence
    '''
    if len(seqs_1) != len(seqs_2):
        return False

    def sortable_key(seq):
        l = [str(seq)]
        md = seq.metadata
        for k in ['id', 'description']:
            if k in md:
                l.append(md[k])
            else:
                l.append('')
        return l

    for i, j in zip(sorted(seqs_1, key=sortable_key),
                    sorted(seqs_2, key=sortable_key)):
        if i != j:
            return False
    return True


def split_paired_end(seq_fp, prefix):
    '''Split reads of paired end into separate files.

    Parameters
    ----------
    seq_fp : file object
        file path to the input fastq.
    '''
    r1, r2, r1_unpaired, r2_unpaired = ([] for _ in range(4))

    lines = seq_fp.readlines()
    seqs = [lines[i:i + 4] for i in range(0, len(lines), 4)]
    seqs.sort()

    for seq_id, group in itertools.groupby(
            seqs, key=lambda seq: seq[0].split(None, 1)[0]):
        reads = list(group)
        # print('%r   -->  %r' % (seq_id, reads))
        strands = [read[0].split()[1][0] for read in reads]
        if len(reads) == 2:
            # seqs is sorted, so the 1st must be R1 and 2nd must be R2
            r1.append(reads[0])
            r2.append(reads[1])
        elif len(reads) == 1:
            if strands[0] == '1':
                r1_unpaired.append(reads[0])
            elif strands[0] == '2':
                r2_unpaired.append(reads[0])
        else:
            raise ValueError('af')

    files = ['{}.{}.fq.gz'.format(prefix, i) for i in
             ['r1', 'r2', 'r1_unpaired', 'r2_unpaired']]
    with gzip.open(files[0], 'wt') as f:
        for seq in r1:
            f.write(''.join(seq))
    with gzip.open(files[1], 'wt') as f:
        for seq in r2:
            f.write(''.join(seq))
    with gzip.open(files[2], 'wt') as f:
        for seq in r1_unpaired:
            f.write(''.join(seq))
    with gzip.open(files[3], 'wt') as f:
        for seq in r2_unpaired:
            f.write(''.join(seq))

    return files


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
    >>> nums = [400, 500, 502, 655, 634, 605, 590, 584, 552, 549, 545, 545, 542, 536, 526, 521, 517, 513]
    >>> compute_n50(nums)
    545
    >>> compute_n50([0, 499])
    0
    >>> compute_n50(i for i in nums)
    545
    '''
    nums = [i for i in nums if i >= cutoff]
    n50_len = sum(nums) / 2
    length = 0
    for i in sorted(nums, reverse=True):
        length += i
        if length >= n50_len:
            return i
    # if nums is empty
    return 0


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
        patterns = {'R1_paired':   r'R1_paired',
                    'R1_unpaired': r'R1_unpaired',
                    'R2_paired':   r'R2_paired',
                    'R2_unpaired': r'R2_unpaired'}
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


def count_lines(filename):
    ''''''
    if filename.endswith('.gz'):
        return count_gzip_lines(filename)
    else:
        return mapcount_lines(filename)


def mapcount_lines(filename):
    '''Count line number in a file with ``mmap``.

    It is faster than reading the file line by line.

    Notes
    -----
    It won't count the real line number of a compressed file,
    as ``mmap`` maps disk blocks into RAM almost as if
    you were adding swap. For a compressed file, you can't
    map the uncompressed data into RAM with mmap() as it is
    not on the disk.

    Examples
    --------
    >>> from tempfile import NamedTemporaryFile
    >>> with NamedTemporaryFile(delete=False) as fh:
    ...     fh.write(b'a\nb\nc')
    ...     fh.close()
    ...     lc = mapcount(fh.name)
    ...     print(lc)
    3
    '''
    with open(filename, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as buf:
            lines = 0
            while buf.readline():
                lines += 1
            return lines


def count_gzip_lines(filename):
    '''Count line number in a gzipped file.
    '''
    with gzip.open(filename) as f:
        for i, l in enumerate(f, 1):
            pass
        return i
