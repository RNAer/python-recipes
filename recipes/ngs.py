import re
import os
import itertools
import gzip
import mmap
from logging import getLogger
from collections import defaultdict

import pandas as pd
from skbio.io import read


def equal_seqs(seqs_1, seqs_2):
    '''Test two sequence collections are equal.

    The sequences are compared by their sequence char,
    their IDs, and their descriptions. If both are equal,
    they are considered as the same. Their order does
    not matter.

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


def split_paired_end(fastq, prefix):
    '''Split reads of paired end into separate files.

    Parameters
    ----------
    fastq : file object
        file path to the input fastq.
    '''
    r1, r2, r1_unpaired, r2_unpaired = ([] for _ in range(4))

    lines = fastq.readlines()
    # each seq has 4 lines in fastq file
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
            raise ValueError(
                'You have more than two reads in {}'.format(reads))

    files = ['{}.{}.fq.gz'.format(prefix, i) for i in
             ['r1', 'r2', 'r1_unpaired', 'r2_unpaired']]
    for r, f in zip([r1, r2, r1_unpaired, r2_unpaired], files):
        with gzip.open(f, 'wt') as fh:
            for seq in r:
                fh.write(''.join(seq))

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
    >>> nums = [400, 500, 502, 655, 634, 605, 590, 584, 552,
    ...         549, 545, 545, 542, 536, 526, 521, 517, 513]
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


def create_sample_table(d,
                        file_types, pattern_types,
                        get_id=lambda x: re.split('_L00[0-9]_R[12]_', x)[0],
                        select=lambda x: x.endswith('.fq.gz'),
                        negate=False):
    '''Return a sample-by-file-path table of the raw sequence files.

    Notes
    -----
    The returned data frame can serve as the input for operations done on
    each file. For example, you can calculate the reads number of each
    file using `pd.DataFrame.applymap`.

    Parameters
    ----------
    d : str
        dir to the raw sequence files
    file_types : list
    pattern_types : list
    get_id : callable
        how to create sample ID from a sequence file name
    select : callable
        what files to include
    negate : boolean
        negate the select.

    Returns
    -------
    pandas.DataFrame
    '''
    if len(file_types) != len(pattern_types):
        raise ValueError(
            'You need to provide a pattern ({}) '
            'for each file type ({}).'.format(pattern_types, file_types))

    logger = getLogger(__name__)

    samples = defaultdict(list)

    for f in os.listdir(d):
        if negate:
            flag = not select(f)
        else:
            flag = select(f)
        if flag:
            try:
                sid = get_id(f)
            except:
                raise ValueError('Can not extract sample ID from file name: %s' % f)
            samples[sid].append(f)

    for sid, files in samples.items():
        if len(files) != len(file_types):
            logger.warning(
                'For sample {}, you have unmatching file names:\n'
                '{}\n'
                'and file types:\n'
                '{}'.format(sid, files, file_types))
        # check the file name only matches one unique pattern
        sorting = sort_by_pattern(pattern_types)
        files.sort(key=sorting)

    df = pd.DataFrame.from_dict(samples, orient='index')
    df.columns = file_types

    return df


def sort_by_pattern(patterns):
    '''Sort the list by the order of matching patterns.

    Examples
    --------
    >>> a = ['a_R2_paired.fq', 'a_R1_paired.fq',
    ...      'a_R1_unpaired.fq', 'a_R2_unpaired.fq']
    >>> p = ['R1_paired', 'R2_paired', 'R1_unpaired', 'R2_unpaired']
    >>> match = sort_by_pattern(p)
    >>> a.sort(key=match)
    >>> a
    ['a_R1_paired.fq', 'a_R2_paired.fq', 'a_R1_unpaired.fq', 'a_R2_unpaired.fq']
    >>> b = ['a_R2_unpaired.fq', 'a_R1_paired.fq']
    >>> b.sort(key=match)
    >>> b
    ['a_R1_paired.fq', 'a_R2_unpaired.fq']
    >>> c = ['a_R2_unpaired.fq', 'a_R1_paired.fq', 'b_R1_paired.fq']
    >>> c.sort(key=match)
    >>> c
    ['a_R1_paired.fq', 'b_R1_paired.fq', 'a_R2_unpaired.fq']
    '''
    def _sort_key(s):
        l = [i for i, p in enumerate(patterns) if re.search(p, s)]
        if len(l) > 1:
            raise ValueError('')
        return l[0]

    return _sort_key


def count_lines(filename):
    '''Count line number in a file.'''
    if filename.endswith('.gz'):
        return count_gzip_lines(filename)
    else:
        return mapcount_lines(filename)


def mapcount_lines(filename):
    r'''Count line number in a file with `mmap`.

    It is faster than reading the file line by line.

    Notes
    -----
    It won't count the real line number of a compressed file,
    as `mmap` maps disk blocks into RAM almost as if
    you were adding swap. For a compressed file, you can't
    map the uncompressed data into RAM with mmap() as it is
    not on the disk.

    Examples
    --------
    >>> from tempfile import NamedTemporaryFile
    >>> with NamedTemporaryFile(delete=False) as fh:
    ...     _ = fh.write(b'a\nb\nc')
    ...     fh.close()
    ...     lc = mapcount_lines(fh.name)
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


def count_seq(filename):
    '''Count seq number in the file.

    The file can be gzipped.
    '''
    for i, s in enumerate(read(filename, format='fasta'), 1):
        pass
    return i


def summarize_blast6(filename):
    df = read(filename, format="blast+6", into=pd.DataFrame, default_columns=True)
    df_best = filter_best(df)


def filter_best_blast_hit(df, column='evalue'):
    '''Filter out the best hits by their e-value or bitscore.'''
    # pick the rows that have highest score for each qseqid
    # df_max = df.groupby('qseqid').apply(
    #     lambda r: r[r[column] == r[column].max()])
    if column == 'evalue':
        idx = df.groupby('qseqid')[column].idxmin()
    elif column == 'bitscore':
        idx = df.groupby('qseqid')[column].idxmax()
    df_best = df.loc[idx]
    # df_best.set_index('qseqid', drop=True, inplace=True)
    return df_best
