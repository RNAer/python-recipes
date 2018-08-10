import biom
import argparse
import sys


def trim_collapse(ifp, ofp, length):
    table = biom.load_table(ifp)
    new = table.collapse(lambda id_, x: id_[:length], norm=False, min_group_size=1, axis='observation')
    with biom_open(out, 'w') as f:
        new.to_hdf5(f, "trim-and-collapse-%dnt" % length)
    return new


def main(argv):
    parser=argparse.ArgumentParser(description='Trim the exact sequence variant and collapse the biom table')
    parser.add_argument('-i','--input',help='name of input fasta file')
    parser.add_argument('-l','--length',help='Trim all sequences to length (0 for full length)')
    parser.add_argument('-o','--output',help="output file path")

    args=parser.parse_args(argv)

    trim_collapse(args.input, args.output, args.length)


if __name__ == "__main__":
    main(sys.argv[1:])
