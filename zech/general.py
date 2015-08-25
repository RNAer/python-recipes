from __future__ import print_function, unicode_literals

from os import listdir, remove, rmdir, mkdir
from os.path import isfile, isdir, join, exists
from numpy import concatenate, linspace
import matplotlib


def create_job_arrays(meta, sid_column, raw_fp, prefix, parent_dir, out,
                      func, **resources):
    '''Create script for array jobs.

    It will create a sub directory in ``parent_dir`` directory for each
    sample. In that sub dir, a script will be created with commands to
    run. A master launcher is written to ``out``.

    Parameters
    ----------
    meta : pandas DataFrame, metadata table
    sid_column : string or int or None
        Column name or index to obtain the sample ID. If it is None, sample
        IDs will be the row names.
    raw_fp : string
        The file path where input files are located.
    prefix : string
        The file name of the script for each sample.
    parent_dir : string
        The directory where the newly created sub directories are located.
    out : file handler
        The master launch script output.
    resources : dict
        key-word parameter for PBS resource request.

    Examples
    --------
    >>> from io import StringIO
    >>> from os.path import join
    >>> meta = pd.DataFrame({'one': pd.Series(['a','b'], index=['s1', 's2']),
    ...                      'two': pd.Series([1, 2],  index=['s1', 's2'])})
    >>> def create_script(raw_fp, out_fp, sample, fh, **resources):
    ...     fh.write('humann2 {r1} -t {ppn}-o {out}\n'.format(
    ...         r1=join(raw_fp, sample['one']),
    ...         out=out_fp, **resources))
    >>> with open('/tmp/foo.pbs', 'w') as fh:
    ...     create_job_arrays(meta, None, 'foo_run',
    ...                       'project', fh, create_script)
    ...     print(fh.getvalue())
    '''
    if 'ppn' not in resources:
        resources['ppn'] = 32
    if 'mem' not in resources:
        resources['mem'] = 32
    if 'walltime' not in resources:
        resources['walltime'] = 1000
    header = '''#!/bin/bash

#PBS -l nodes=1:ppn={ppn}
#PBS -l mem={mem}gb
#PBS -l walltime={walltime}:00:00
#PBS -o log/{prefix}.o$PBS_JOBID
#PBS -e log/{prefix}.e$PBS_JOBID
#PBS -N {prefix}
# keep output in real time
#PBS -k oe

cd $PBS_O_WORKDIR

echo ------------------------------------------------------
echo PBS: qsub is running on $PBS_O_HOST
echo PBS: originating queue is $PBS_O_QUEUE
echo PBS: executing queue is $PBS_QUEUE
echo PBS: working directory is $PBS_O_WORKDIR
echo PBS: execution mode is $PBS_ENVIRONMENT
echo PBS: job identifier is $PBS_JOBID
echo PBS: job name is $PBS_JOBNAME
echo PBS: node file is $PBS_NODEFILE
echo PBS: current home directory is $PBS_O_HOME
echo PBS: PATH = $PBS_O_PATH
echo ------------------------------------------------------

'''.format(prefix=prefix, **resources)
    array_var = 'samples'
    fn = '%s.pbs' % prefix
    out.write(header)
    out.write('%s=(' % array_var)
    if not exists(parent_dir):
        mkdir(parent_dir)
    for i, (rowname, row) in enumerate(meta.iterrows()):
        if sid_column is None:
            sid = rowname
        else:
            sid = row[sid_column]
        d = join(parent_dir, sid)
        if not exists(d):
            mkdir(d)
        with open(join(d, fn), 'w') as f:
            func(raw_fp, join(d, prefix), row, f, **resources)
        out.write('\n"{sid}"  #{i}'.format(sid=sid, i=i))
    out.write('\n)\n')
    out.write('bash %s\n' % join(
        parent_dir, '${%s[${PBS_ARRAYID}]}' % array_var, fn))


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


def traverse(o, tree_types=(list, tuple)):
    # borrowed from:
    # http://stackoverflow.com/questions/6340351/python-iterating-through-list-of-list
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value):
                yield subvalue
    else:
        yield o


def parse_function_call(expr):
    '''Parse a string similar to a function call.

    Examples
    --------
    >>> l = 'complement(join(97999..98793,69611..69724))'
    >>> parse_function_call(l)
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
    """Return a discrete colormap from the continuous colormap cmap.

    Parameters
    ----------
    cmap : colormap instance, eg. cm.jet.
    N : number of colors.

    Examples
    --------
    >>> x = resize(arange(100), (5,100))
    >>> djet = cmap_discretize(cm.jet, 5)
    >>> imshow(x, cmap=djet)
    """
    colors_i = concatenate((linspace(0, 1., N), (0.,0.,0.,0.)))
    colors_rgba = cmap(colors_i)
    indices = linspace(0, 1., N+1)
    cdict = {}
    for ki,key in enumerate(('red','green','blue')):
        cdict[key] = [(indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki]) for i in xrange(N+1)]
    # Return colormap object.
    return matplotlib.colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)
