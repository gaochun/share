#! N:\Python27\python.exe
# -*- coding: utf-8 -*-


import re
import os
import datetime
import argparse
import platform
import sys
import datetime

root_dir = '/workspace/project/android/'
backup_dir = '/workspace/topic/android/image/'


def get_datetime():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

def info(msg):
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"

def cmd(msg):
    print '[COMMAND] ' + msg

def execute(command):
    cmd(command)
    if os.system(command):
        error('Failed to execute')
        quit()

def flash(args):
    if not args.flash:
        return()

    if args.flash == 'all':
        execute('bash -c ". build/envsetup.sh && lunch full_' + args.device + '-' + args.level + ' && fastboot -w flashall"')

def build(args):
    if not args.build:
        return()

    # Check proprietary binaries. Different version needs different binaries.
    if not os.path.exists('vendor'):
        error('Please copy the proprietary binaries')
        quit()

    start = datetime.datetime.now()
    execute('bash -c ". build/envsetup.sh && lunch full_' + args.device + '-' + args.level + ' && make -j12"')
    elapsed = (datetime.datetime.now() - start)
    info('Time elapsed to build: ' + str(elapsed.seconds) + 's')

    # Backup
    dest_dir = backup_dir + get_datetime() + '-' + args.device + '-' + args.level + '/'
    os.mkdir(dest_dir)
    execute('cp ' + root_dir + 'out/target/product/' + args.device + '/*.img ' + dest_dir)

def sync(args):
    if not args.sync:
        return()

    execute('repo init -u https://android.googlesource.com/platform/manifest -b ' + args.sync)
    execute('repo sync')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script to sync, build Android',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  python %(prog)s -s android-4.2.2_r1.1 -b -f all
  python %(prog)s -s android-4.3_r1 -l userdebug
  python %(prog)s -s android-4.4_r1.1
  python %(prog)s -f all

  python %(prog)s -s android-4.3_r1 -b -f all

''')

    parser.add_argument('-l', '--level', dest='level', help='level', choices=['user', 'userdebug', 'eng'], default='userdebug')
    parser.add_argument('-d', '--device', dest='device', help='device', choices=['mako'], default='mako')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('-s', '--sync', dest='sync', help='tag to sync')
    parser.add_argument('-f', '--flash', dest='flash', help='type to flash', choices=['all'])

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    if args.build != '':
        build_type = args.build

    os.chdir(root_dir)
    sync(args)
    build(args)
    flash(args)

