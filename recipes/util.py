from functools import wraps, partial
from collections import Iterable, defaultdict
import time
import os
from contextlib import contextmanager

from numpy import concatenate, linspace
import matplotlib


def _get_named_data_path(fname):
    # get caller's file path
    caller_fp = abspath(stack()[1][1])
    d = dirname(caller_fp)
    # remove file suffix and prefix of "test_"
    name = splitext(basename(caller_fp))[0][5:]
    return join(d, 'data', name, fname)


def _overwrite(path, overwrite=False, append=False):
    if exists(path):
        if overwrite:
            if isdir(path):
                shutil.rmtree(path)
            else:
                remove(path)
        elif append:
            return
        else:
            raise FileExistsError('The file path {} already exists.'.format(path))


def _download(src, dest, **kwargs):
    _overwrite(dest, **kwargs)
    with urlopen(src) as i_f, open(dest, 'wb') as o_f:
        shutil.copyfileobj(i_f, o_f)


def time_func(func):
    '''Time the docorated function.

    Parameters
    ----------
    func : function to be decorated.
    prefix : the prefix string printed before func name.

    Examples
    --------
    >>> @time_func
    ... def countdown(n):
    ...     while n > 0:
    ...         n -= 1
    >>> countdown(100)   # doctest: +ELLIPSIS
    recipes.util.countdown: ...
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        r = func(*args, **kwargs)
        end = time.perf_counter()
        print('{}.{}: {}'.format(
            func.__module__, func.__qualname__, end-start))
        return r
    return wrapper


@contextmanager
def time_block(label):
    '''Time a block of statments.

    Examples
    --------
    >>> with time_block('time countdown'):  # doctest: +ELLIPSIS
    ...     n = 100
    ...     while n > 0:
    ...         n -= 1
    time countdown: ...
    '''
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
    print('{}: {}'.format(label, end - start))


def debug(func=None, *, prefix=''):
    '''Print debug msg for the decorated function.

    This is borrowed from David Beazzly's talk of Python 3
    Metaprogramming. So when you insert a print in a function, the
    function name will also be printed with a prefix to be easily
    identified.

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
    # if 'DEBUG' not in os.environ:
    #     return func

    if func is None:
        return partial(debug, prefix=prefix)

    # __qualname__ fully qualified name (with class name)
    msg = prefix + func.__qualname__

    @wraps(func)
    def decorator(*args, **kwargs):
        print(msg)
        return func(*args, **kwargs)
    return decorator


def flatten(items, ignore_types=(str, bytes)):
    '''Flatten any nested iterators.

    Returns a single, flat iterator which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Parameters
    ----------
    items : Iterable
    ignore_types : type
        variable type you ignore to iterate thru.

    Return
    ------
    Iterator

    Examples
    --------
    >>> list(flatten([1, 2, [3,4], (5,6)]))
    [1, 2, 3, 4, 5, 6]
    >>> list(flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)]))
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    >>> list(flatten([1, 2, 'abc'], ignore_types=()))
    [1, 2, 'a', 'b', 'c']
    >>> list(flatten([1, 2, 'abc']))
    [1, 2, 'abc']
    '''
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, ignore_types):
            yield from flatten(x)
        else:
            yield x


def parse_function_call(expr):
    '''Parse a string similar to a function call.

    Examples
    --------
    >>> l = 'complement(join(97999..98793,69611..69724))'
    >>> parse_function_call(l)
    ['complement', ['join', ['97999..98793', '69611..69724']]]
    >>> parse_function_call('join(12..78,134..202)')
    ['join', ['12..78', '134..202']]
    >>> parse_function_call('102.110')
    ['102.110']
    >>> parse_function_call('join(complement(4918..5163),complement(2691..4571))')
    ['join', ['complement', ['4918..5163'], 'complement', ['2691..4571']]]
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
