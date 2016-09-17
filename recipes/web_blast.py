'''Search NCBI blast server on terminal.'''
import sys
import argparse

from Bio.Blast import NCBIWWW, NCBIXML
from Bio import SeqIO


def interface():
    args = argparse.ArgumentParser()
    args.add_argument('-i', help='input seq file')
    args.add_argument('-s', help='input seq')
    args.add_argument('-r', help='remote server', default='barnacle')
    args = args.parse_args()
    return args


def blast(seq):
    b_results = NCBIWWW.qblast('blastn', 'nr', seq)
    blast_records = NCBIXML.parse(b_results)
    for blast_record in blast_records:
        for alignment in blast_record.alignments:
            for hsp in alignment.hsps:
                print('****Alignment****')
                print('sequence:', alignment.title)
                print('length:', alignment.length)
                print('score:', hsp.score)
                print('gaps:', hsp.gaps)
                print('e-value:', hsp.expect)
                print(hsp.query[0:90] +'...')
                print(hsp.match[0:90] +'...')
                print(hsp.sbjct[0:90] +'...')


if __name__ == '__main__':
    args = interface()
    if args.i:
        with open(args.i) as fh:
            seqs = SeqIO.parse(fh, 'fasta')
            for seq in seqs:
                blast(str(seq.seq))
    elif args.s:
        blast(args.s)
    else:
        raise ValueError('a')
