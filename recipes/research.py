import os
import argparse
from os.path import join


def interface():
    args = argparse.ArgumentParser()
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

FLAGS = -avuhzi --prune-empty-dirs $(FILE_FILTER) $(SIZE_FILTER) -e ssh

pull:
\trsync $(FLAGS) -n $(REMOTE):$(DIR)/ .
push:
\trsync $(FLAGS) -n . $(REMOTE):$(DIR)/

pull_real:
\trsync $(FLAGS) $(REMOTE):$(DIR)/ .
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
+ /dir_under_the_root/
# double asterisks is for both / and other char to include subdir
+ /dir_under_the_root/**

# Exclude all the files
- *
'''
    os.mkdir(d)

    with open(join(d, 'Makefile'), 'w') as f:
        f.write(makefile)

    with open(join(d, 'rsync.ie'), 'w') as f:
        f.write(ie)

    docd = join(d, 'doc')
    os.mkdir(docd)

    datad = join(d, 'data')
    os.mkdir(datad)


if __name__ == '__main__':
    args = interface()
    create_research_project(args.d, args.r)
