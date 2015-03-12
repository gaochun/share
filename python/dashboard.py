#!/usr/bin/env python

from util import *

COUNT_MESSAGE = 100


def parse_arg():
    global args

    parser = argparse.ArgumentParser(description='Script to control server',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --cron
''')

    parser.add_argument('--message', dest='message', help='message')
    parser.add_argument('--machine', dest='machine', help='machine')
    add_argument_common(parser)

    args = parser.parse_args()
    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    pass


def message():
    if not args.message:
        return

    file_name = dir_server_dashboard + '/' + args.machine
    if not os.path.exists(file_name):
        execute('touch ' + file_name)
    f = file(file_name, 'r+')
    lines = f.readlines()
    f.seek(0)
    f.truncate()
    result = execute('date', return_output=True)
    line = '[' + result[1].strip('\n') + '] ' + args.message + '\n'
    f.write(line)
    for index, line in enumerate(lines):
        if index > COUNT_MESSAGE - 2:
            break
        print line
        f.write(line)
    f.close()


def _teardown():
    execute('rm -f %s' % file_lock)


if __name__ == '__main__':
    parse_arg()
    setup()
    message()
