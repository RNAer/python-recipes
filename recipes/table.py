r'''
Functions manipulating 2-D tables
=================================

'''

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.lines import Line2D


def compute_prevalence(abundance):
    '''Return the prevalence at each abundance cutoffs.

    Parameters
    ----------
    abundance : iterable of numeric
        The abundance of a species across samples.

    Examples
    --------
    >>> abund = [0, 0, 1, 2, 4, 1]
    >>> x, y = compute_prevalence(abund)
    >>> x
    array([0, 1, 2, 4])
    >>> y
    array([ 0.66666667,  0.33333333,  0.16666667,  0.        ])

    '''
    # unique values are sorted
    cutoffs, counts = np.unique(abundance, return_counts=True)
    cum_counts = np.cumsum(counts)
    prevalences = 1 - cum_counts / counts.sum()
    # print(cutoffs, prevalences)
    return cutoffs, prevalences


def plot_abundance_prevalence_ave(table, grouping, colors=None, alpha=0.5, log=True, step=0.01):
    if colors is None:
        colors = dict(zip(grouping,
                          cm.Dark2(np.linspace(0, 1, len(grouping)))))
    elif len(colors) != len(grouping):
        raise ValueError('unequal colors and grouping')

    fig, ax = plt.subplots()

    categories = colors.keys()
    for category in categories:
        sub_sample = table[grouping[category], ]
        upper_bound = sub_sample.max()
        x = np.arange(0, upper_bound, step)
        y = [(sub_sample > i).sum() / sub_sample.size for i in x]
        ax.plot(x, y, color=colors[category], alpha=alpha)

    ax.set_ylabel('prevalence')
    if log is True:
        ax.set_xscale("log", nonposx='mask')
        ax.set_xlabel('log(abundance)')
    else:
        ax.set_xlabel('abundance')

    # ax.invert_xaxis()

    lines = [Line2D([0,1], [0, 1], color=colors[c]) for c in categories]
    ax.legend(lines, categories, numpoints=1, markerscale=1, fontsize='small')

    return fig


def plot_abundance_prevalence(table, grouping, colors=None, alpha=0.5, log=True, min_prev=0.2):
    '''Plot abundance against prevalence.

    Prevalence/abundance curve is a chart used to visualize the
    prevalence of OTUs. For each OTU, a curve was constructed
    measuring the percentage of a population that carries the OTU
    above a given abundance (normalized over the total abundance of
    the OTU). A steep curve indicates this OTU is shared prevalently
    among the population. If many OTUs show in steep curves, it
    indicates the population has a core set of microbes.

    Y-axis: prevalence of the OTU that above the abundance threshold.

    X-axis: abundance threshold. log-scale.

    Test on the IBD data.

    Parameters
    ----------
    table : 2-D array-like
        rows are samples and columns are species
    grouping : dict
        keys are categories and values are the row indices
        for each category
    colors : dict
        keys are categories and values are colors
    log : bool
        whether to plot abundance in log scale

    '''
    if colors is None:
        colors = dict(zip(grouping,
                          cm.Dark2(np.linspace(0, 1, len(grouping)))))
    elif len(colors) != len(grouping):
        raise ValueError('unequal colors and grouping')

    fig, ax = plt.subplots()

    categories = colors.keys()
    for category in categories:
        sub_sample = table[grouping[category], ]
        size = sub_sample.shape[0] * min_prev
        for species in sub_sample.T:
            if np.count_nonzero(species) > size:
                x, y = compute_prevalence(species)
                ax.plot(x, y, color=colors[category], alpha=alpha)

    ax.set_ylabel('prevalence')
    if log is True:
        ax.set_xscale("log", nonposx='mask')
        ax.set_xlabel('log(abundance)')
    else:
        ax.set_xlabel('abundance')

    # ax.invert_xaxis()

    lines = [Line2D([0,1], [0, 1], color=colors[c]) for c in categories]
    ax.legend(lines, categories, numpoints=1, markerscale=1, fontsize='small')

    return fig


def sort_trim(x):
    x.sort()
    return np.trim_zeros(x[::-1])


def plot_rank_abundance(table, grouping, colors=None, alpha=0.6, log=True, average=True):
    '''Plot rank-abundance curve.

    A rank abundance curve or Whittaker plot is a chart used to
    visualize both species richness and species evenness.

    X-axis: The abundance rank. The most abundant species is given
    rank 1, the second most abundant is 2 and so on.

    Y-axis: The relative abundance. Usually measured on a log scale,
    this is a measure of a species abundance (e.g., the number of
    individuals).

    Species richness can be viewed as the number of different species
    on the chart i.e., how many species were ranked. Species evenness
    is reflected in the slope of the line that fits the graph
    (assuming a linear, i.e. logarithmic series, relationship). A
    steep gradient indicates low evenness as the high-ranking species
    have much higher abundances than the low-ranking species. A
    shallow gradient indicates high evenness as the abundances of
    different species are similar.

    Parameters
    ----------
    table : 2-D array-like
        rows are samples and columns are species
    grouping : dict
        keys are categories and values are the row indices
        for each category
    colors : dict
        keys are categories and values are colors
    alpha : float
        transparency level of the lines
    log : bool
        whether to plot abundance in log scale
    average : bool
        plot the average for each group instead of plot each sample.

    Returns
    -------
    matplotlib.figure.Figure
    '''
    if colors is None:
        colors = dict(zip(grouping,
                          cm.Accent(np.linspace(0, 1, len(grouping)))))
    elif len(colors) != len(grouping):
        raise ValueError('unequal colors and grouping')

    fig, ax = plt.subplots()

    categories = colors.keys()
    for category in categories:
        rows = grouping[category]
        if average:
            ave = table[rows, ].mean(axis=0)
            ax.plot(sort_trim(ave), linewidth=3, color=colors[category])
        else:
            for row in rows:
                abundance = table[row, ]
                # TODO: could use LineCollection to be more efficient.
                ax.plot(sort_trim(abundance),
                        # '-o', markersize=7, markeredgewidth=0.0,
                        linewidth=3, color=colors[category], alpha=alpha)

    ax.set_xlabel('abundance rank')
    if log is True:
        ax.set_yscale("log", nonposx='clip')
        ax.set_ylabel('log(abundance)')
    else:
        ax.set_ylabel('abundance')

    lines = [Line2D([0,1], [0, 1], color=colors[c]) for c in categories]
    ax.legend(lines, categories, numpoints=1, markerscale=1, fontsize='small')

    return fig


if __name__ == '__main__':
    import sys
    from recipes.util import dict_indices
    from microLearner.study import Study
    from sklearn.preprocessing import normalize
    a = Study.read(sys.argv[1], sys.argv[2])
    a.matchup()
    md = a.sample_metadata.loc[:, ['disease_group']]
    grouping = dict_indices(md.itertuples(False))
    data = a.data.values.astype(float)
    data_normalize = normalize(data, axis=1, norm='l1')
    # fig = plot_rank_abundance(a.data.values.astype(float), grouping, log=True)
    fig = plot_abundance_prevalence_ave(data_normalize, grouping, log=True)
    fig.savefig('/tmp/a.pdf')
