#!/usr/bin/env python

import os
import commands
import argparse
import platform
import re
import sys

script_dir = ''
webview_dir = ''
args = ''

patches = [
    # Patches borrowed from other groups

    # Patches by our own
    'git fetch https://aia-review.intel.com/platform/external/chromium_org refs/changes/29/2329/1 && git checkout FETCH_HEAD',
]

def info(msg):
    print '[INFO] ' + msg + '.'

def warning(msg):
    print '[WARNING] ' + msg + '.'

def error(msg):
    print '[ERROR] ' + msg + '!'

def cmd(msg):
    print '[COMMAND] ' + msg

def execute(command):
    cmd(command)
    if os.system(command):
        error('Failed to execute')
        quit()

def shell_source(shell_cmd):
    """Sometime you want to emulate the action of "source" in bash,
    settings some environment variables. Here is a way to do it."""
    import subprocess, os
    pipe = subprocess.Popen(". %s; env" % shell_cmd, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    for line in output.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value

def get_script_dir():
    script_path = os.getcwd() + '/' + sys.argv[0]
    return os.path.split(script_path)[0]

def handle_option():
    global args
    parser = argparse.ArgumentParser(description = 'Script to sync, build Chromium x64',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  python %(prog)s


''')

    parser.add_argument('--patch', dest='patch', help='apply patch from Gerrit', action='store_true')
    parser.add_argument('--mk64', dest='mk64', help='generate mk for x86_64', action='store_true')
    parser.add_argument('-b', '--build', dest='build', help='build', action='store_true')
    parser.add_argument('-c', '--build-clean', dest='build_clean', help='clean build', action='store_true')
    args = parser.parse_args()

def setup():
    global script_dir, webview_dir

    script_dir = get_script_dir()
    webview_dir = script_dir + '/external/chromium_org'
    os.chdir(webview_dir)

def patch():
    if not args.patch:
        return

    for patch in patches:
        pattern = re.compile('platform/(.*) (.*) &&')
        match = pattern.search(patch)
        project = match.group(1)
        change = match.group(2)
        command = 'git fetch ssh://aia-review.intel.com/platform/' + project + ' ' + change + ' && git cherry-pick FETCH_HEAD'
        os.chdir(script_dir + '/' + project)
        execute(command)

    os.chdir(webview_dir)

def mk64():
    if not args.mk64:
        return

    backups = [
        'GypAndroid.linux-x86_64.mk', # good
        'third_party/openssl/openssl.target.linux-x86_64.mk', # good
        #./media/media.target.linux-x86_64.mk
        #third_party/x86inc ./media/media_asm.target.linux-x86_64.mk
        #refer ./v8/tools/gyp/v8_base.ia32.target.linux-x86_64.mk
        #refer ./v8/tools/gyp/v8_base.ia32.host.linux-x86_64.mk
        #refer ./base/base.target.linux-x86_64.mk
        #refer ./third_party/protobuf/protobuf_lite.target.linux-x86_64.mk
        #refer ./third_party/protobuf/protobuf_full_do_not_use.host.linux-x86_64.mk
        #bad ./third_party/yasm/generate_files.host.linux-x86_64.mk
        #bad ./third_party/yasm/yasm.host.linux-x86_64.mk
    ]

    r = os.popen('find -name "*linux-x86.mk"')
    files = r.read().split('\n')
    # Remove last empty one
    del files[len(files) - 1]

    for file in files:
        command = 'cp -f ' + file + ' ' + file.replace('x86', 'x86_64')
        execute(command)
        #r = os.popen('grep -c x86 ' + file)
        #count = int(r.read())
        #if count > 0:
        #    print file

    for file in backups:
        command = 'cp -f /workspace/topic/x64/' + file.rsplit('/')[-1] + ' ' + file
        execute(command)

def build():
    if not args.build:
        return

    command = '. /workspace/project/android-ia/build/envsetup.sh && lunch kvm_initrd_64bit-eng && '

    if args.build_clean:
        command += 'mma'
    else:
        command += 'mmm ./'

    command += ' -j16'
    execute(command)

if __name__ == '__main__':
    handle_option()
    setup()
    patch()
    mk64()
    build()
