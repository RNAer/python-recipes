def split(is_another, constructor, ignore):
    def parse(stream):
        lines = []
        for line in stream:
            line = constructor(line)
            if ignore(line):
                continue
            if is_another(line):
                if lines:
                    yield lines
                    lines = []
            lines.append(line)
        if lines:
            yield lines
    return parse


def delimit(line, starting='>'):
    if line.startswith(starting):
        return True
    else:
        return False


class TailSplitter:
    def __init__(self, is_tail):
        self.is_tail = is_tail
        self.flag = False

    def __call__(self, line):
        if self.is_tail(line):
            self.flag = True
            return False
        else:
            if self.flag:
                self.flag = False
                return True


class IDSplitter:
    def __init__(self, identify, ident=None):
        self.ident = ident
        self.identify = identify

    def __call__(self, line):
        ident = self.identify(line)
        if self.ident == ident:
            return False
        else:
            self.ident = ident
            return True


if __name__ == '__main__':
    import io
    from functools import partial
    s1 = '''seq1\ta
seq1\tb
seq2\ta
seq2\tb
'''
    s2 = '''>seq1
A
>seq2
T
'''
    s3 = '''seq1
A
//
seq2
T
//
'''
    splitter = IDSplitter(lambda x: x.split()[0])
    splitter2 = TailSplitter(lambda x: x.startswith('//'))
    for stream, action in zip(
            [io.StringIO(i) for i in (s1, s2, s3)],
            [splitter, delimit, splitter2]):
        parser = split(action, lambda x: x.strip(), lambda x: x.startswith('#'))
        for lines in parser(stream):
            print(lines)
# ['seq1\ta', 'seq1\tb']
# ['seq2\ta', 'seq2\tb']
# ['>seq1', 'A']
# ['>seq2', 'T']
# ['seq1', 'A', '//']
# ['seq2', 'T', '//']
