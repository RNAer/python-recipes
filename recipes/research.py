import os
import argparse
from os.path import join


def interface():
    args = argparse.ArgumentParser(
        description='This creates the necessary files and dir structure for a project.')
    args.add_argument('-d', help='project directory name', required=True)
    args.add_argument('-r', help='remote server', default='barnacle')
    args = args.parse_args()
    return args


def create_research_project(d, remote='barnacle'):
    ''''''
    makefile = '''
####### variables to config #########
# define the remote server you wanna sync to.
# you can also pass this from cmd line: make push REMOTE=phelps
REMOTE ?= {remote}
# define the dir in remote server you wanna sync.
# you can also pass this from cmd line: make push DIR=ibd
DIR ?= {d}
# define the max file size your wanna sync.
# you can leave this as empty.
SIZE = 100m
# define the file name containing the include/exclude patterns.
# you can leave this as empty
FILE = rsync.ie


# size filter
ifeq ($(SIZE),)
    SIZE_FILTER =
else
    SIZE_FILTER = --max-size=$(SIZE)
endif

# check if you have the exclude file
ifeq ($(wildcard $(FILE)),)
    FILE_FILTER =
else
    FILE_FILTER = --filter '. $(FILE)'
endif

FLAGS = -avuhzi --prune-empty-dirs -e ssh

pull:
\trsync $(FLAGS) $(FILE_FILTER) $(SIZE_FILTER) -n $(REMOTE):$(DIR)/ .
push:
\trsync $(FLAGS) -n . $(REMOTE):$(DIR)/

pull_real:
\trsync $(FLAGS) $(FILE_FILTER) $(SIZE_FILTER) $(REMOTE):$(DIR)/ .
push_real:
\trsync $(FLAGS) . $(REMOTE):$(DIR)/
'''.format(remote=remote, d=d)

    ie = '''
# Set of include/exclude rules, for more information see 'man rsync'

# Exclude all objectfiles anywhere
- *.o
# Exclude all dot-files
- .*
# Exclude all dot-directories
- .*/

# Include the directories we want to sync
+ /
+ /rsync.ie
+ /Makefile
+ /Snakefile
+ /readme*
+ /config*
+ /*.json
- /*/*untrimmed*
+ /scripts/
# double asterisks is for both / and other char to include subdir
+ /scripts/**

# Exclude all the files
- *
'''

    gitignore = '''
# Ignore everything
/*

# But not these files...
!.gitignore
!Makefile
!rsync.ie
!README*
!readme*
!scripts/*
!Snakefile
'''

    os.mkdir(d)

    with open(join(d, 'Makefile'), 'w') as f:
        f.write(makefile)

    with open(join(d, 'rsync.ie'), 'w') as f:
        f.write(ie)

    with open(join(d, '.gitignore'), 'w') as f:
        f.write(gitignore)

    docd = join(d, 'doc')
    os.mkdir(docd)

    datad = join(d, 'data')
    os.mkdir(datad)

    scriptsd = join(d, 'scripts')
    os.mkdir(scriptsd)


if __name__ == '__main__':
    args = interface()
    create_research_project(args.d, args.r)
