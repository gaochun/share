# -*- coding: utf-8 -*-

import argparse
import sys
import os

script_dir = sys.path[0]
user_data_dir = script_dir + '/user_data/'
tool_dir = '/workspace/project/chromium/src/tools/'

def info(msg):
    print '[INFO] ' + msg + '.'

def warn(msg):
    print '[WARNING] ' + msg + '.'

def error(msg):
    print '[ERROR] ' + msg + '!'

def cmd(msg):
    print '[COMMAND] ' + msg

def execute(command, ignore_return_value=False):
    cmd(command)
    if os.system(command) and not ignore_return_value:
        error('Failed to execute')
        quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script to bisect Chromium, good revision should be smaller than bad revision',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  python %(prog)s -g 218527 -b 226662 --run-option 'http://browsermark.rightware.com/tests'
''')

    parser.add_argument('-g', '--good-revision', dest='good_revision', help='good revision', required=True)
    parser.add_argument('-b', '--bad-revision', dest='bad_revision', help='bad revision', required=True)
    parser.add_argument('--run-option', dest='run_option', help='option to run test', default='')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    command = 'python ' + tool_dir + 'bisect-builds.py' + ' -a linux64' + ' -g ' + args.good_revision + ' -b ' + args.bad_revision + ' -p ' + user_data_dir + ' --'
    command += ' --no-first-run --start-maximized'
    if args.run_option:
        command += ' ' + args.run_option
    execute(command)