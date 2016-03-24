from __future__ import print_function
from future.utils import with_metaclass

from abc import ABCMeta, abstractmethod
from string import Formatter
from os.path import join, exists
from os import mkdir
import pandas as pd

from .util import make_dir


class JobArrays(with_metaclass(ABCMeta, object)):
    def __init__(self, metadata,
                 raw_dir, out_dir, kwargs=None,
                 pbs_header=None):
        if kwargs is None:
            kwargs = {}
        self.raw_dir = raw_dir
        self.out_dir = out_dir
        self.metadata = metadata
        self.kwargs = kwargs
        self.kwargs['name'] = self.__class__.__name__.lower()
        self.kwargs['total'] = metadata.shape[0]
        self._set_default('ppn', 32)
        self._set_default('mem', 32)
        self._set_default('runs', 10)
        self._set_default('walltime', 1000)
        self._set_default('name', 'foo')
        if pbs_header is None:
            self.pbs_header = '''#!/bin/bash

#PBS -V
#PBS -N {name}
#PBS -l nodes=1:ppn={ppn}
#PBS -l mem={mem}gb
#PBS -l walltime={walltime}:00:00

#PBS -t 0-{total}%{runs}

#PBS -M zhx054@ucsd.edu
# email when job aborts, begins or ends.
#PBS -m abe

# keep output in real time
#PBS -k oe
#PBS -o log/{name}.o$PBS_JOBID
#PBS -e log/{name}.e$PBS_JOBID

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

'''
        else:
            self.pbs_header = pbs_header

    def _set_default(self, key, default):
        if key not in self.kwargs:
            self.kwargs[key] = default

    @abstractmethod
    def create_cmd(self, template, prolog='', epilog=''):
        pass

    def create(self, input_columns, fh, **kwargs):
        if not exists(self.out_dir):
            mkdir(self.out_dir)
        self.write(self.pbs_header.format(**self.kwargs), fh)
        self.write('scripts=(', fh)
        for i, (rowname, row) in enumerate(self.metadata.iterrows()):
            script = self.create_cmd(rowname, row, input_columns, **kwargs)
            self.write('"{script}"  # {i}\n'.format(script=script, i=i+1), fh)
        self.write(')\n', fh)
        self.write('bash ${scripts[$PBS_ARRAYID]}', fh)

    def write(self, s, fh):
        i = self._is_filled(s)
        if len(i) == 0:
            print('a%sb' % s)
            raise(ValueError, 'Unrealized variable: %s' % i)
        else:
            fh.write(s)

    @staticmethod
    def _is_filled(s):
        field_names = [v[1] for v in Formatter().parse(s)]
        return field_names


class Humann2(JobArrays):
    def create_cmd(self, sid, metadata, input_columns,
                   prolog='humann2_config --print',
                   epilog='echo "DONE $(\date)"'):

        input_files = [f for f in metadata[input_columns] if not pd.isnull(f)]
        input_fps = [join(self.raw_dir, f) for f in input_files]
        self.kwargs['out_dir'] = join(self.out_dir, sid)
        if not exists(self.kwargs['out_dir']):
            make_dir(self.kwargs['out_dir'])
        n = len(input_files)
        if n == 0:
            # no input file
            pass
        elif n == 1:
            self.kwargs['input'] = input_fps[0]
            template = (
                'if ! ls {out_dir}/*.tsv &> /dev/null ; then\n'
                '    humann2 --input {input} --output {out_dir} --threads {ppn}\n'
                'fi\n')
        elif n > 1:
            self.kwargs['input'] = ' '.join(input_fps)
            template = (
                'if ! ls {out_dir}/*.tsv &> /dev/null ; then\n'
                '    zless {input} >> {tmp} && '
                'humann2 --input {tmp} --output {out_dir} --threads {ppn} && rm -f {tmp}\n'
                'fi\n')
            self.kwargs['tmp'] = join(self.out_dir, sid, 'sid.fastq')
        s = '\n'.join([prolog, template, epilog])
        s = s.format(**self.kwargs)
        script = join(self.out_dir, sid, '%s.sh' % self.kwargs['name'])
        with open(script, 'w') as fh:
            self.write(s, fh)
        return script


class Kraken(JobArrays):
    def create_cmd(self, sid, metadata, input_columns,
                   prolog='',
                   epilog='echo "DONE $(\date)"',
                   compress=None,
                   format='fastq'):

        self.kwargs['db'] = '~/softwares/kraken-0.10.5-beta/minikraken_20141208'
        self.kwargs['out'] = join(self.out_dir, sid)
        self.kwargs['out_dir'] = self.out_dir
        cmd_lines = ['if ! ls {out_dir}/%s.kraken &> /dev/null ; then' % sid]
        if isinstance(input_columns, dict):
            cmd = ['kraken',
                   '--preload',
                   '-db {db}',
                   '--paired {R1} {R2}',
                   '--output {out}',
                   '--threads {ppn}',
                   '--check-names']
            if isinstance(input_columns['R1'], str):
                self.kwargs['R1'] = join(
                    self.raw_dir, metadata[input_columns['R1']])
            else:
                self.kwargs['R1'] = join(self.out_dir, 'R1.%s' % sid)
                cmd_lines.append(
                    '    zless %s >> {R1}' %
                    ' '.join(
                        join(self.raw_dir, i) for i in metadata[input_columns['R1']]))
            if isinstance(input_columns['R2'], str):
                self.kwargs['R2'] = join(
                    self.raw_dir, metadata[input_columns['R2']])
            else:
                self.kwargs['R2'] = join(self.out_dir, 'R2.%s' % sid)
                cmd_lines.append(
                    '    zless %s >> {R2}' %
                    ' '.join(
                        join(self.raw_dir, i) for i in metadata[input_columns['R2']]))
        else:   # input_columns is a list
            input_files = [f for f in metadata[input_columns]
                           if not pd.isnull(f)]
            input_fps = [join(self.raw_dir, f) for f in input_files]
            self.kwargs['input'] = ' '.join(input_fps)
            cmd = ['kraken',
                   '--preload',
                   '-db {db}',
                   '{input}',
                   '--output {out}',
                   '--threads {ppn}']
        if format == 'fastq':
            cmd.append('--fastq-input')

        if compress == 'gzip':
            cmd.append('--gzip-compressed')
        elif compress == 'bzip':
            cmd.append('--bzip2-compressed')
        elif compress is not None:
            raise Exception('Unrecognized compress format %s' % compress)

        cmd_lines.append('    ' + ' '.join(cmd))
        cmd_lines.append(
            '    kraken-translate '
            '--db ~/softwares/kraken-0.10.5-beta/minikraken_20141208 '
            '--mpa-format {out} > {out}.kraken')
        cmd_lines.append('fi')

        s = '\n'.join([prolog, '\n'.join(cmd_lines), epilog])
        s = s.format(**self.kwargs)
        script = join(self.out_dir, '%s.sh' % sid)
        with open(script, 'w') as fh:
            self.write(s, fh)
        return script


def create_job_arrays(meta, sid_column, raw_dir, prefix, parent_dir, out,
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
    raw_dir : string
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
    >>> def create_script(raw_dir, out_dir, sample, fh, **resources):
    ...     fh.write('humann2 {r1} -t {ppn}-o {out}\n'.format(
    ...         r1=join(raw_dir, sample['one']),
    ...         out=out_dir, **resources))
    >>> with open('/tmp/foo.pbs', 'w') as fh:
    ...     create_job_arrays(meta, None, 'foo_run',
    ...                       'project', fh, create_script)
    ...     print(fh.getvalue())
    '''

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
            func(raw_dir, join(d, prefix), row, f, **resources)
        out.write('\n"{sid}"  #{i}'.format(sid=sid, i=i))
    out.write('\n)\n')
    out.write('bash %s\n' % join(
        parent_dir, '${%s[${PBS_ARRAYID}]}' % array_var, fn))
