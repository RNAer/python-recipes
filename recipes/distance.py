import numpy as np


def group_dist_agg(distance, group, statistic):
    grp = np.zeros(len(group))
    for i, j in group:
        grp += distance[i, j]
    if statistic == 'mean':
        return np.mean(grp)
    elif statistic == 'median':
        return np.median(grp)
    else:
        return statistic(grp)

def distance(distance, group_1, group_2, statistic='mean', permutations=999, random_state=None):
    '''
    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    group_1 :
    group_2 : list of tuples
        For example, [(s1, s9), (s5, s9), (s5, s7)]
    statistic : str or Callable
        The statistic to compute for the 2-group comparison.'mean', 'median',
        or functions that accept an array of numeric and return a single numeric
    permuations : int
        Number of permutations
    random_state : None, int
        random seed
    '''
    n = distance.shape[0]
    grp1 = group_dist_agg(group_1, statistic)
    grp2 = group_dist_agg(group_2, statistic)
    delta = grp2 - grp1
    rand = np.random.RandomState(random_state)
    delta_rand = np.zeros(permutations)
    for k in range(permutations):
        idx_map = dict(range(n), zip(rand.permutation(n)))
        group_1_rand = [(idx_map[i], idx_map[j]) for i, j in group_1]
        group_2_rand = [(idx_map[i], idx_map[j]) for i, j in group_2]
        delta_rand[k] = group_dist_agg(group_2_rand, statistic) - group_dist_agg(group_1_rand, statistic)

    p = np.sum(delta_rand < delta) / (permutations + 1)
    return delta, delta_rand, p

