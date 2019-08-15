import numpy as np
import math
import itertools

from skbio import DistanceMatrix


def filter_matrix(mat, cutoff=0.95, strict=True):
    '''filter symmetric correlation or distance matrix.

    Parameters
    ----------
    mat : square 2D numeric numpy.array
    cutoff : float
    strict : bool
        only select the ones that greater than cutoff

    Returns
    -------
    set
        the indices that are selected
    '''
    if strict:
        # only care about upper triangle
        high = np.triu(mat > cutoff, 1)
    else:
        high = np.triu(mat >= cutoff, 1)

    s = set()
    for i, j in zip(*np.where(high)):
        if i in s or j in s:
            continue
        sumi = np.sum(mat[i, :])
        sumj = np.sum(mat[:, j])
        if sumi > sumj:
            s.add(i)
        else:
            s.add(j)
    return s


def group_dist_agg(distance, pairs, statistic):
    '''Compute the `statistic` of the given pairs of distances.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    pairs : list of tuples
        For example, [(1, 9), (5, 9), (5, 7)]
    statistic : str or Callable
        The statistic to compute for the 2-pairs comparison.'mean', 'median',
        or functions that accept an array of numeric and return a single numeric

    Examples
    --------
    >>> distance = np.array([[0, 0.1, 0.2],
    ...                      [0.1, 0, 0.5],
    ...                      [0.2, 0.5, 0]])
    >>> group_dist_agg(distance, [(0, 1), (1, 2)], 'mean') == 0.3
    True
    >>> group_dist_agg(distance, [(0, 1), (1, 2), (0, 2)], 'median') == 0.2
    True
    '''
    grp = np.zeros(len(pairs))
    for k, pair in enumerate(pairs):
        grp[k] = distance[pair[0], pair[1]]
    if statistic == 'mean':
        return np.mean(grp)
    elif statistic == 'median':
        return np.median(grp)
    else:
        return statistic(grp)


def distance_permute_test(distance, group_1, group_2,
                          two_sided=False, statistic='mean',
                          permutations=999, random_state=None):
    '''Statistically compare if there is difference between 2 groups of distances.

    Compute the given `statistic` between 2 groups of distances and
    statistically test it by permuting the sample labels.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array
    group_1 :
    group_2 : list of tuples
        For example, [(1, 9), (5, 9), (5, 7)]
    two_sided : bool
        if True, do 2-sided test to see if group_1 != group_2;
        otherwise, do 1-sided test to see if group_2 > group_1.
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
    for k in range(permutations):
        if isinstance(distance, DistanceMatrix):
            ids = distance.ids
        else:
            ids = np.arange(n)
        idx_map = dict(zip(ids, rand.permutation(ids)))
        group_1_rand = [(idx_map[pair[0]], idx_map[pair[1]]) for pair in group_1]
        group_2_rand = [(idx_map[pair[0]], idx_map[pair[1]]) for pair in group_2]
        # print(idx_map, group_1_rand, group_2_rand)
        delta_rand[k] = group_dist_agg(distance, group_2_rand, statistic) - group_dist_agg(distance, group_1_rand, statistic)
    if two_sided:
        p = np.sum(np.abs(delta_rand) > np.abs(delta)) / (permutations + 1)
    else:
        p = np.sum(delta_rand > delta) / (permutations + 1)
    return p, delta, delta_rand


def distance_uniq_permute_test(distance, group_1, group_2, statistic='mean', permutations=999, random_state=None):
    '''Statistically compare if there is difference between 2 groups of distances.

    .. note:: it is different from `distance_permute_test` in that
       each random permutation is different from the other permutations.

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
    p = np.sum(delta_rand > delta) / (permutations + 1)
    return p, delta, delta_rand


def plot_distribution(distance, groups):
    '''Plot distance distribution.

    Parameters
    ----------
    distance : skbio.DistanceMatrix or square numpy.array

    groups :
    '''
    fig, ax = plt.subplots()
    ax.hist(dsum, bins=10, alpha=0.9)
    ax.hist(temporal.query('distance!=0')['distance'], bins=10, alpha=0.9)
    ax.set_xlabel('weighted UniFrac distance')
    ax.set_ylabel('counts')
    ax.legend(['within individual', 'across individual'])


if __name__ == '__main__':
    distance = np.array([[0, 0.1, 0.2], [0.1, 0, 0.5], [0.2, 0.5, 0]])
    o = distance_permute_test(distance, [(0, 1), (1, 2)], [(0, 2)], 'mean', 5, random_state=0)
    print(o)
    o = distance_uniq_permute_test(distance, [(0, 1), (1, 2)], [(0, 2)], 'mean', 5, random_state=0)
    print(o)

    import doctest
    print(doctest.testmod())

