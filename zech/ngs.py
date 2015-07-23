import re
import os
import pandas as pd


def form_sample_table(d,
                      patterns=None,
                      sid=lambda x: re.split('_L00[0-9]_R[12]_', x)[0],
                      select=lambda x: x.endswith('.fq'), negate=False):
    '''Return tables of the raw sequence files.
    '''
    if patterns is None:
        patterns = {'R1_paired':   r'R1_[0-9]{3}_paired',
                    'R1_unpaired': r'R1_[0-9]{3}_unpaired',
                    'R2_paired':   r'R2_[0-9]{3}_paired',
                    'R2_unpaired': r'R2_[0-9]{3}_unpaired'}
    samples = pd.DataFrame(columns=patterns)
    for f in os.listdir(d):
        if negate:
            flag = not select(f)
        else:
            flag = select(f)
        if flag:
            s_id = sid(f)
            t = [i for i in patterns if re.search(patterns[i], f)]
            assert len(t) == 1, "File %s matches multiple patterns."
            samples.loc[s_id, t[0]] = f

    return samples
