#/usr/bin/python

import os
import commands
import argparse
import platform
import time

# Global variables
args = None

def info(msg):
    print '[INFO] ' + msg + '.'

def warning(msg):
    print '[WARNING] ' + msg + '.'

def error(msg):
    print '[ERROR] ' + msg + '!'
    quit()

def cmd(msg):
    print '[COMMAND] ' + msg

def execute(command):
    cmd(command)
    if os.system(command):
        error('Failed to execute')
        quit()

def rest():
    if args.hibernate:
        cmd = 'rundll32.exe powrprof.dll,SetSuspendState'

    if args.restart:
        cmd = 'shutdown.exe -r -t 0 -f'

    if args.poweroff:
        cmd = 'shutdown.exe -s -t 0 -f'

    info(time.strftime("%Y-%m-%d %X", time.localtime()))
    execute(cmd)

def sleep():
    time.sleep(float(args.work))

def check():
    count = 0
    if args.hibernate:
        count = count + 1

    if args.restart:
        count = count + 1

    if args.poweroff:
        count = count + 1

    if count < 1:
        error('Please choose a rest mode')

    if count > 1:
        error('More than one rest mode is chosen')

if __name__ == '__main__':
    # Handle options
    parser = argparse.ArgumentParser(description = 'Script to sleep several seconds, and hibernate|restart|poweroff on Windows',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  python %(prog)s --hibernate
  python %(prog)s -w 5 --hibernate
''')

    parser.add_argument('-w', '--work', dest='work', help='seconds to work', default=3600)
    parser.add_argument('--hibernate', dest='hibernate', help='choose to hibernate', action='store_true')
    parser.add_argument('--restart', dest='restart', help='choose to restart', action='store_true')
    parser.add_argument('--poweroff', dest='poweroff', help='choose to poweroff', action='store_true')

    args = parser.parse_args()

    check()
    sleep()
    rest()


