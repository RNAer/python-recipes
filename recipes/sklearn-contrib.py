import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import make_scorer


def weighted_score(yobs, yhat, weights):
    '''Compute the accuracy score with weights.

    Parameters
    ----------
    yobs : array-like int or str
        true labels
    yhat : array-like int or str
        predicted labels
    weights : numeric
        the weights for each prediction

    Returns
    -------
    float
        the weighted accuracy score (between 0 and 1)

    Examples
    --------
    >>> yobs = ['y', 'y', 'n', 'n', 'n']
    >>> yhat = ['y', 'n', 'n', 'y', 'n']
    >>> weights = [2, 1, 2, 3, 2]
    >>> score = weighted_score(yobs, yhat, weights)
    >>> score == 0.6
    True
    '''
    agrees = np.array(yobs) == np.array(yhat)
    score = np.sum(agrees.astype(int) * np.array(weights))
    return score / np.sum(weights)


weighted_scorer = make_scorer(weighted_score)


# Inspired from stackoverflow.com/questions/25239958
class MostFrequentImputer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.most_frequent = pd.Series([X[c].value_counts().index[0] for c in X],
                                       index=X.columns)
        return self
    def transform(self, X, y=None):
        return X.fillna(self.most_frequent)


# A class to select numerical or categorical columns
# since Scikit-Learn doesn't handle DataFrames yet
class MetadataSelector(BaseEstimator, TransformerMixin):
    def __init__(self, attribute_names):
        self.attribute_names = attribute_names
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X[self.attribute_names]
