import numpy as np
import math
import itertools


def group_dist_agg(distance, group, statistic):
    '''Compute the ``statistic`` of the given group of distances.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    group : list of tuples
        For example, [(1, 9), (5, 9), (5, 7)]
    statistic : str or Callable
        The statistic to compute for the 2-group comparison.'mean', 'median',
        or functions that accept an array of numeric and return a single numeric

    '''
    grp = np.zeros(len(group))
    for k, (i, j) in enumerate(group):
        grp[k] = distance[i, j]
    if statistic == 'mean':
        return np.mean(grp)
    elif statistic == 'median':
        return np.median(grp)
    else:
        return statistic(grp)


def distance_permute_test(distance, group_1, group_2, statistic='mean', permutations=999, random_state=None):
    '''Statistically compare if there is difference between 2 groups of distances.

    Compute the given ``statistic`` between 2 groups of distances and
    statistically test it by permuting the sample labels.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    group_1 :
    group_2 : list of tuples
        For example, [(1, 9), (5, 9), (5, 7)]
    statistic : str or Callable
        The statistic to compute for the 2-group comparison.'mean', 'median',
        or functions that accept an array of numeric and return a single numeric
    permuations : int
        Number of permutations
    random_state : None, int
        random seed

    Returns
    -------
    tuple
        p-value, the difference between 2 groups, the array of differences after permutations

    '''
    n = distance.shape[0]
    grp1 = group_dist_agg(distance, group_1, statistic)
    grp2 = group_dist_agg(distance, group_2, statistic)
    delta = grp2 - grp1
    rand = np.random.RandomState(random_state)
    delta_rand = np.zeros(permutations)
    # print(group_1, group_2)
    for k in range(permutations):
        idx_map = dict(zip(range(n), rand.permutation(n)))
        group_1_rand = [(idx_map[i], idx_map[j]) for i, j in group_1]
        group_2_rand = [(idx_map[i], idx_map[j]) for i, j in group_2]
        # print(idx_map, group_1_rand, group_2_rand)
        delta_rand[k] = group_dist_agg(distance, group_2_rand, statistic) - group_dist_agg(distance, group_1_rand, statistic)

    p = np.sum(delta_rand < delta) / (permutations + 1)
    return p, delta, delta_rand


def distance_uniq_permute_test(distance, group_1, group_2, statistic='mean', permutations=999, random_state=None):
    '''
    .. note:: it is different from ``distance_permute_test`` in that each random permutation is unique.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    group_1 :
    group_2 : list of tuples
        For example, [(1, 9), (5, 9), (5, 7)]
    statistic : str or Callable
        The statistic to compute for the 2-group comparison.'mean', 'median',
        or functions that accept an array of numeric and return a single numeric
    permuations : int
        Number of permutations
    random_state : None, int
        random seed

    Returns
    -------
    tuple
        p-value, the difference between 2 groups, the array of differences after permutations
    '''
    n = distance.shape[0]
    counts = math.factorial(n)
    if permutations > counts - 1:
        raise ValueError('There are not unique permutations for %d' % permutations)
    rand = np.random.RandomState(random_state)
    perm_set = set(rand.choice(range(1, counts), permutations, replace=False))
    perm_iter = itertools.permutations(range(n))
    next(perm_iter)
    delta_rand = np.zeros(permutations)
    x = 0
    # print(group_1, group_2)
    for m, k in enumerate(perm_iter, 1):
        if m in perm_set:
            idx_map = dict(zip(range(n), k))
            group_1_rand = [(idx_map[i], idx_map[j]) for i, j in group_1]
            group_2_rand = [(idx_map[i], idx_map[j]) for i, j in group_2]
            # print(k, group_1_rand, group_2_rand)
            delta_rand[x] = group_dist_agg(distance, group_2_rand, statistic) - group_dist_agg(distance, group_1_rand, statistic)
            x += 1
    grp1 = group_dist_agg(distance, group_1, statistic)
    grp2 = group_dist_agg(distance, group_2, statistic)
    delta = grp2 - grp1
    p = np.sum(delta_rand < delta) / (permutations + 1)
    return p, delta, delta_rand


if __name__ == '__main__':
    distance = np.array([[0, 0.1, 0.2],
                         [0.1, 0, 0.5],
                         [0.2, 0.5, 0]])
    assert group_dist_agg(distance, [(0, 1), (1, 2)], 'mean') == 0.3

    assert group_dist_agg(distance, [(0, 1), (1, 2), (0, 2)], 'median') == 0.2
    o = distance_permute_test(distance, [(0, 1), (1, 2)], [(0, 2)], 'mean', 5, random_state=0)
    print(o)
    o = distance_uniq_permute_test(distance, [(0, 1), (1, 2)], [(0, 2)], 'mean', 5, random_state=0)
    print(o)

    import doctest
    print(doctest.testmod())

