import biom

import argparse
import sys


def get_seq_from_biom(tablefilename,fastaname,sizeout=False,sampleid=''):
    table=biom.load_table(tablefilename)
    with open(fastaname,'w') as outfile:
        if sizeout:
            if sampleid=='':
                allsum=table.sum(axis='observation')
            else:
                allsum=table.data(sampleid,axis='sample',dense=True)
        for idx,cid in enumerate(table.ids(axis='observation')):
            if not sizeout:
                outfile.write('>%s\n%s\n' % (cid,cid))
            else:
                if allsum[idx]>0:
                    outfile.write('>%s;size=%d;\n%s\n' % (cid,allsum[idx],cid))


def main(argv):
    parser=argparse.ArgumentParser(description='Get sequences from biom table into a fasta file. Version '+__version__)
    parser.add_argument('-i','--input',help='input biom table file name')
    parser.add_argument('-o','--output',help='output fasta file name')
    parser.add_argument('-s','--sizeout',help='put the size field in each sequence as the sum of the sequence in the table',action='store_true')
    parser.add_argument('--sampleid',help='name of the sample to get the sizes for (if -s is set) or none to get all samples summed',default='')

    args=parser.parse_args(argv)

    get_seq_from_biom(args.inputtable,args.output,args.sizeout,args.sampleid)

if __name__ == "__main__":
    main(sys.argv[1:])
