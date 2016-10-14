r'''
Functions manipulating 2-D tables
=================================

'''

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.lines import Line2D


def plot_abund_prev(table, grouping, colors=None, alpha=0.5, log=True):
    '''Plot abundance against prevalence.

    Prevalence/abundance curve is a chart used to visualize the
    prevalence of OTUs. For each OTU, a curve was constructed
    measuring the percentage of a population that carries the OTU
    above a given abundance (normalized over the total abundance of
    the OTU). A steep curve indicates this OTU is shared prevalently
    among the population. If many OTUs show in steep curves, it
    indicates the population has a core set microbes.

    Y-axis: prevalance of the OTU that above the abundance threshold.

    X-axis: abundance threshold. log-scale.

    Test on the IBD data.

    Parameters
    ----------
    table : 2-D array-like
        rows are samples and columns are species
    step_size : numeric
        the step size for abundance threshold
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
                          cm.Accent(np.linspace(0, 1, len(grouping)))))
    elif len(colors) != len(grouping):
        raise ValueError('unequal colors and grouping')

    fig, ax = plt.subplots()

    categories = colors.keys()
    for category in categories:
        sub_sample = table[grouping[category], ]
        sub_sample_size = sub_sample.shape[1]
        for species in sub_sample.T:
            # unique values are sorted
            unique, counts = np.unique(sepcies, return_counts=True)
            cum_counts = np.cumsum(counts)
            ax.plot(cum_counts / sub_sample_size, color=colors[category], alpha=alpha)

    ax.set_xlabel('prevalence')
    if log is True:
        ax.set_ylabel('log(abundance)')
    else:
        ax.set_ylabel('abundance')

    lines = [Line2D([0,1], [0, 1], color=colors[c]) for c in categories]
    ax.legend(lines, categories, numpoints=1, markerscale=2)

    return fig


def plot_rank_abundance(table, grouping, colors=None, alpha=0.5, log=True):
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
    log : bool
        whether to plot abundance in log scale

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
        for row in grouping[category]:
            abundance = table[row, ]
            abundance.sort()
            # reverse the sort
            y = np.trim_zeros(abundance[::-1])
            if log is True:
                y = np.log(y)
            ax.plot(y, '-o', markersize=7, color=colors[category], alpha=alpha)

    bottom, _ = ax.get_ylim()
    ax.set_ylim(bottom=bottom-0.1)
    ax.set_xlabel('abundance rank')
    if log is True:
        ax.set_ylabel('log(abundance)')
    else:
        ax.set_ylabel('abundance')

    lines = [Line2D([0,1], [0, 1], color=colors[c]) for c in categories]
    ax.legend(lines, categories, numpoints=1, markerscale=2)

    return fig
