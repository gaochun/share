#!/usr/bin/env python

from util import *
import operator

elf = ''


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to handle elf',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --revert -s --patch -b
''')
    parser.add_argument('--elf', dest='elf', help='elf file')
    parser.add_argument('--size', dest='size', help='size', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global elf

    elf = args.elf


def size():
    if not args.size:
        return

    name_size = {}
    lines = _get_lines(cmd='readelf -S --wide ' + elf)
    for line in lines:
        match = re.search('\[\s*(\d+)\]', line)
        if match:
            if int(match.group(1)) == 0:
                continue
            fields = line.split()
            if int(match.group(1)) < 10:
                fields[1] = fields[0] + fields[1]
                del fields[0]

            name_size[fields[1]] = int(fields[5], 16)

    sorted_size = sorted(name_size.items(), key=lambda x: x[1], reverse=True)
    for item in sorted_size:
        print item[0] + ' ' + str(item[1])


def _get_lines(cmd):
    result = execute(cmd, return_output=True)
    return result[1].split('\n')


if __name__ == '__main__':
    parse_arg()
    setup()
    size()
