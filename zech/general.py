from os import listdir, remove, rmdir
from os.path import isfile, isdir, join


def delete_dir(d):
    ''' Deletes a directory and its content recursively.
    '''
    for name in listdir(d):
        fp = join(d, name)
        if not isfile(fp) and isdir(fp):
            # It's another directory - recurse in to it...
            delete_dir(fp)
        else:
            # It's a file - remove it...
            remove(fp)
    rmdir(d)


def flatten(x):
    """Flatten any sequence to a flat list.

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> flatten([1, 2, [3,4], (5,6)])
    [1, 2, 3, 4, 5, 6]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    """

    result = []
    for el in x:
        # if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def yes_or_no(message=""):
    '''Prompt to answer 'yes' or 'no'.
    '''
    while True:
        try:
            reply = raw_input(message)
        except EOFError:
            print
            continue
        reply = reply.strip().lower()
        if reply in ('y', 'yes'):
            return True
        elif reply in ('n', 'no'):
            return False
        else:
            continue
