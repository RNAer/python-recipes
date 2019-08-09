import numpy as np

def cooccur(a, b, cutoff=0, psudo=1, n=1000, negate=False):
    a, b = np.array(a), np.array(b)
    real = overlap(a, b, cutoff, psudo)
    dist = np.ones(n)
    for i in range(n):
        shuffled = np.random.permutation(b)
        dist[i] = overlap(a, shuffled, cutoff, psudo)
    if negate:
        # mutual exclusivity
        dist = 1 - dist
        real = 1 - real
    # co-existence
    pval = np.sum(dist > real) / n
    # import pdb; pdb.set_trace()
    return real, pval, dist


def overlap(a, b, cutoff=0, psudo=1):
    a = a > cutoff
    b = b > cutoff
    if np.all(a) or np.all(b) or not np.any(a) or not np.any(b):
        raise ValueError('one features is absent or present in all samples!')
    intersect = np.sum(a & b)
    union = min(np.sum(a), np.sum(b))
    # import pdb; pdb.set_trace()
    return (intersect + psudo) / (union + psudo)
