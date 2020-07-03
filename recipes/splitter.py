
def split(is_another, construct=None, ignore=None, **kwargs):
    '''Return a function that reads a file to yield entry.

    Parameters
    ----------
    is_another : callable
        The callable accepts a string and returns a bool indicating if the string
        starts a new entry or not.
    construct : callable (optional)
        The callable accepts a string and returns a modified string. Do nothing if it is
        ``None``.
    ignore : callable (optional)
        The callable accepts a string and returns a bool indicating if the string should be ignored or returned.
        Do nothing if it is ``None``.
    kwargs : dict
        optional key word arguments passing to ``is_another``

    Returns
    -------
    function
        a function that accepts a file-object-like and yields entry
        one by one from it.


    Examples
    --------
    >>> import io
    >>> s = """>seq1
    ... ATGC
    ... >seq2
    ... A\t
    ...
    ... T
    ... """
    >>> f = io.StringIO(s)
    >>> gen = split(lambda s: s.startswith('>'), construct=lambda x: x.strip())
    >>> list(gen(f))
    [['>seq1', 'ATGC'], ['>seq2', 'A', '', 'T']]
    '''
    def parse(stream):
        lines = []
        for line in stream:
            if ignore is not None and ignore(line):
                continue
            if is_another(line, **kwargs):
                if lines:
                    yield lines
                    lines = []
            if construct is not None:
                line = construct(line)
            lines.append(line)
        if lines:
            yield lines
    return parse


class AnotherEntryTail:
    r'''Check if a new entry starts.

    This is for file format with entries delimited by some string
    pattern located at its tail. This is provided to the ``split``
    function as ``is_another`` parameter.

    Parameters
    ----------
    is_tail : callable
        to return a bool indicating if the current line concludes current entry

    Examples
    --------
    Let's create a file object that has sequences separated by "//" at
    the end of each entry (similar to multiple GenBank records in a file):

    >>> import io
    >>> s = """seq1
    ... AT
    ... //
    ... seq2
    ... ATGC
    ... //
    ... """
    >>> f = io.StringIO(s)

    And then we can yield each sequence with this code:

    >>> splitter = AnotherEntryTail(lambda x: x == '//\n')
    >>> gen = split(splitter, construct=lambda x: x.strip())
    >>> list(gen(f))
    [['seq1', 'AT', '//'], ['seq2', 'ATGC', '//']]

    See Also
    --------
    split
    AnotherEntryID

    '''
    def __init__(self, is_tail):
        self.is_tail = is_tail
        self._flag = False

    def __call__(self, line):
        if self.is_tail(line):
            self._flag = True
            return False
        else:
            if self._flag:
                self._flag = False
                return True


class AnotherEntryID:
    r'''Check if a new entry starts.

    This is for file format with entry IDs on every line. The lines
    with the same ID belongs to the same entry. This is provided to
    the ``split`` function as ``is_another`` parameter.

    Parameters
    ----------
    identify : callable
        accept a string and return a value (ID). By comparing the value to
        that of its previous line, it judges if the current line is
        like its previous line belonging to the same entry.

    Examples
    --------
    >>> from pprint import pprint
    >>> import io
    >>> s = """##gff-version 3
    ... ctg123\t.\texon\t1300\t1500\t.\t+\t.\tID=exon00001
    ... ctg123\t.\texon\t1050\t1500\t.\t+\t.\tID=exon00002
    ... ctg124\t.\texon\t3000\t3902\t.\t+\t.\tID=exon00003
    ... """
    >>> f = io.StringIO(s)
    >>> splitter = AnotherEntryID(lambda x: x.split('\t')[0])
    >>> gen = split(splitter, lambda x: x.strip(), lambda x: x.startswith('#'))
    >>> pprint(list(gen(f)))
    [['ctg123\t.\texon\t1300\t1500\t.\t+\t.\tID=exon00001',
      'ctg123\t.\texon\t1050\t1500\t.\t+\t.\tID=exon00002'],
     ['ctg124\t.\texon\t3000\t3902\t.\t+\t.\tID=exon00003']]

    See Also
    --------
    split
    AnotherEntryTail

    '''
    def __init__(self, identify):
        self._ident = None
        self.identify = identify

    def __call__(self, line):
        ident = self.identify(line)
        if self._ident == ident:
            return False
        else:
            self._ident = ident
            return True


if __name__ == '__main__':
    import doctest
    print(doctest.testmod())
