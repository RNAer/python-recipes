from numpy import concatenate, linspace
from functools import wraps, partial
from collections import Iterable
import matplotlib


def which_df(df, select=lambda x: x is True):
    '''`which` function for pandas data frame.

    It yields the index and column that satisfy
    the select function.

    Parameters
    ----------
    df : pandas.DataFrame
    select : callable
        accept the value of a cell in the data frame
        and return a boolean.
    Yields
    ------
    tuple
        index, column
    '''
    for i in df.index:
        for j in df.columns:
            if select(df.loc[i, j]):
                yield i, j


def debug(func=None, *, prefix=''):
    '''Print debug msg for the decorated function.

    This is borrowed from David Beazzly.

    Parameters
    ----------
    func : function to be decorated.
    prefix : the prefix string printed before func name.

    Examples
    --------
    >>> from recipes.util import debug
    >>> @debug
    ... def add(x, y):
    ...     i = x + y
    ...     print(i)
    ...     return i
    >>> add(2, 3)
    add
    5
    5
    >>> @debug(prefix='***')
    ... def add(x, y):
    ...     i = x + y
    ...     print(i)
    ...     return i
    ...
    >>> add(2, 3)
    ***add
    5
    5
    '''
    if func is None:
        return partial(debug, prefix=prefix)

    msg = prefix + func.__qualname__

    @wraps(func)
    def decorator(*args, **kwargs):
        print(msg)
        return func(*args, **kwargs)
    return decorator


def flatten(x):
    '''Flatten any sequence to a flat list.

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples
    --------
    >>> flatten([1, 2, [3,4], (5,6)])
    [1, 2, 3, 4, 5, 6]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    '''

    result = []
    for el in x:
        # if isinstance(el, (list, tuple)):
        if isinstance(el, Iterable) and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def traverse(o, tree_types=(list, tuple)):
    '''Traverse the iterable types specified.

    Yields
    ------
    atomic values in the input o.

    Examples
    --------
    >>> list(traverse(['a', 'b']))
    ['a', 'b']
    >>> list(traverse(['a', 'b', ['bB']]))
    ['a', 'b', 'bB']

    See Also
    --------
    `flatten`
    '''
    # borrowed from:
    # http://stackoverflow.com/questions/6340351/python-iterating-through-list-of-list
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value):
                yield subvalue
    else:
        yield o


def yes_or_no(message="Yes or No? "):
    '''Prompt to answer 'yes' or 'no'.
    '''
    while True:
        try:
            reply = input(message)
        except EOFError:
            continue
        reply = reply.strip().lower()
        if reply in ('y', 'yes'):
            return True
        elif reply in ('n', 'no'):
            return False
        else:
            continue


def parse_function_call(expr):
    '''Parse a string similar to a function call.

    Examples
    --------
    >>> l = 'complement(join(97999..98793,69611..69724))'
    >>> parse_function_call(l)
    ['complement', ['join', ['97999..98793', '69611..69724']]]
    '''
    def parser(iter):
        items = []
        item = ''
        for char in iter:
            if char.isspace():
                continue
            if char in '(),' and item:
                items.append(item)
                item = ''
            if char == '(':
                result, close_paren = parser(iter)
                if not close_paren:
                    raise ValueError("Unbalanced parentheses")
                items.append(result)
            elif char == ')':
                return items, True
            elif char != ',':
                item += char
        if item:
            items.append(item)
        return items, False
    return parser(iter(expr))[0]


def cmap_discretize(cmap, N):
    '''Return a discrete colormap from the continuous colormap cmap.

    Parameters
    ----------
    cmap : colormap instance, eg. cm.jet.
    N : number of colors.

    Examples
    --------
    >>> from recipes.util import cmap_discretize
    >>> from numpy import arange, resize
    >>> from matplotlib import cm, pyplot
    >>> x = resize(arange(100), (5, 100))
    >>> djet = cmap_discretize(cm.jet, 5)
    >>> pyplot.imshow(x, cmap=djet)  # doctest: +ELLIPSIS
    <matplotlib.image.AxesImage object at ...>
    '''
    colors_i = concatenate((linspace(0, 1., N), (0., 0., 0., 0.)))
    colors_rgba = cmap(colors_i)
    indices = linspace(0, 1., N+1)
    cdict = {}
    for ki, key in enumerate(('red', 'green', 'blue')):
        cdict[key] = [(indices[i], colors_rgba[i-1, ki], colors_rgba[i, ki])
                      for i in range(N+1)]
    # Return colormap object.
    return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d" % N, cdict, 1024)
