#/usr/bin/python

import os
import commands
import argparse
import platform
import re
import sys

# Global variables
root_dir = ''
src_dir = ''
system = platform.system()

def is_system(name):
    if system == name:
        return True
    else:
        return False

def is_windows():
    if is_system('Windows'):
        return True
    else:
        return False

def is_linux():
    if is_system('Linux'):
        return True
    else:
        return False

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

def has_build_dir(name):
    out_dir = src_dir + '/out'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    build_dir = out_dir + '/' + name
    if not os.path.exists(build_dir):
        warning(name + ' directory doesn\'t exist. Will create the directory for you and perform a clean build')
        os.mkdir(build_dir)
        return False

    return True

def layout_test(args):
    if not args.layout_test:
        return()

    os.chdir(src_dir + '/out/Release')
    if os.path.isdir('content_shell'):
        execute('rm -rf content_shell_dir')
        execute('mv content_shell content_shell_dir')

    os.chdir(src_dir)
    execute('ninja -C out/Release content_shell')
    execute('webkit/tools/layout_tests/run_webkit_tests.sh ' + args.layout_test)

def update(args):
    if not args.update:
        return()

    # 'third_party/skia/src' is not on master
    repos = ['./', 'third_party/WebKit']
    for repo in repos:
        is_master = False
        os.chdir(src_dir + '/' + repo)
        branches = commands.getoutput('git branch').split('\n')
        for branch in branches:
            if branch == '* master':
                is_master = True

        if not is_master:
            error('Repo ' + repo + ' is not on master')
            quit()

    os.chdir(root_dir)
    if is_windows():
        cmd = 'd:/user/ygu5/project/chromium/depot_tools/gclient'
    else:
        cmd = 'gclient'

    cmd = cmd + ' ' + args.update
    execute(cmd)

def shell_source(shell_cmd):
    """Sometime you want to emulate the action of "source" in bash,
    settings some environment variables. Here is a way to do it."""
    import subprocess, os
    pipe = subprocess.Popen(". %s; env" % shell_cmd, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    for line in output.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value

def build(args):
    if not args.build:
        return()

    build_clean = args.build_clean

    if not has_build_dir(args.build.capitalize()):
        build_clean = True

    print '== Build Environment =='
    print 'Directory of src: ' + src_dir
    print 'Build type: ' + args.build
    print 'Build system: Ninja'
    print 'Need clean build: ' + str(build_clean)
    print 'System: ' + system
    print 'Platform: ' + args.platform
    print '======================='

    os.chdir(src_dir)

    if build_clean:
        if args.platform == 'android':
            shell_source('build/android/envsetup.sh --target-arch=x86')
        cmd = 'python build/gyp_chromium -Dwerror='
        execute(cmd)

    if args.build_verbose:
        cmd = 'ninja -v'
    else:
        cmd = 'ninja'

    if args.platform == 'desktop':
        cmd += ' chrome'
    else:
        cmd += ' content_shell_apk'

    cmd += ' -C out/' + args.build.capitalize()

    if args.platform == 'android':
        os.chdir(src_dir + '/out/' + args.build.capitalize())
        if os.path.isfile('content_shell'):
            execute('rm -f content_shell_file')
            execute('mv content_shell content_shell_file')
        os.chdir(src_dir)

    execute(cmd)

def install(args):
    if not args.install:
        return

    if not args.platform == 'android':
        return

    os.chdir(src_dir)
    execute('python build/android/adb_install_apk.py --apk ContentShell.apk --' + args.install)


def run(args):
    if not args.run:
        return()

    if args.platform == 'desktop':
        option = ' --flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + root_dir + '/user-data'

        if args.run_GPU:
            option += ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

        if args.run_debug_renderer:
            if args.run.upper() == 'RELEASE':
                warning('Debugger should run with debug version. Switch to it automatically')
                args.run = 'debug'
            option = option + ' --renderer-cmd-prefix="xterm -title renderer -e gdb --args"'

        cmd = root_dir + '/src/out/' + args.run.capitalize() + '/chrome ' + option
    else:
        cmd = root_dir + '/src/build/android/adb_run_content_shell'

    if args.run_option:
        cmd += ' ' + args.run_option

    execute(cmd)

def find_owner(args):
    if not args.owner:
        return()

    os.chdir(src_dir)
    files = commands.getoutput('git diff --name-only HEAD origin/master').split('\n')
    owner_file_map = {} # map from OWNERS file to list of modified files
    for file in files:
        dir = os.path.dirname(file)
        while not os.path.exists(dir + '/OWNERS'):
            dir = os.path.dirname(dir)

        owner_file = dir + '/OWNERS'
        if owner_file in owner_file_map:
            owner_file_map[owner_file].append(file)
        else:
            owner_file_map[owner_file] = [file]

    for owner_file in owner_file_map:
        owner = commands.getoutput('cat ' + dir + '/OWNERS')
        print '--------------------------------------------------'
        print '[Modified Files]'
        for modified_file in owner_file_map[owner_file]:
            print modified_file
        print '[OWNERS File]'
        print owner


# override format_epilog to make it format better
argparse.format_epilog = lambda self, formatter: self.epilog

if __name__ == '__main__':
    # System sanity check
    if not is_windows() and not is_linux():
        error('Current system is not suppported')
        quit()

    # Handle options
    parser = argparse.ArgumentParser(description = 'Script to update, build and run Chromium',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  update:
  python %(prog)s -u sync
  python %(prog)s -u 'sync --force'
  python %(prog)s -u runhooks

  build:
  python %(prog)s -b release
  python %(prog)s -b all
  python %(prog)s -b release -c -v
  python %(prog)s -p android -b release

  run:
  python %(prog)s -r release
  python %(prog)s -r release -g
  python %(prog)s -r debug
  python %(prog)s -r release -o=--enable-logging=stderr
  python %(prog)s -r release -o--enable-logging=stderr
  python %(prog)s -r release '-o --enable-logging=stderr'
  python %(prog)s -r release --run-debug-renderer
  python %(prog)s -p android -r release --run-option 'http://browsermark.rightware.com'

  python %(prog)s --owner

  update & build & run
  python %(prog)s -u sync -b release -r release
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupBuild = parser.add_argument_group('build')
    groupBuild.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug'])
    groupBuild.add_argument('-c', '--build-clean', dest='build_clean', help='regenerate gyp', action='store_true')
    groupBuild.add_argument('-v', '--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')

    groupRun = parser.add_argument_group('run')
    groupRun.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupRun.add_argument('-o', '--run-option', dest='run_option', help='option to run')
    groupRun.add_argument('-g', '--run-gpu', dest='run_GPU', help='enable GPU acceleration', action='store_true')
    groupRun.add_argument('--run-debug-renderer', dest='run_debug_renderer', help='run gdb before renderer starts', action='store_true')

    # Other options
    parser.add_argument('--owner', dest='owner', help='find owner for latest commit', action='store_true')
    parser.add_argument('-d', '--root-dir', dest='root_dir', help='set root directory')
    parser.add_argument('--layout-test', dest='layout_test', help='cases to run against')
    parser.add_argument('-p', '--platform', dest='platform', help='platform', choices=['desktop', 'android'], default='desktop')
    parser.add_argument('-i', '--install', dest='install', help='install chrome for android', choices=['release', 'debug'])


    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    # Global variables
    if not args.root_dir:
        if is_windows():
            root_dir = "d:/user/ygu5/project/chromium"
        else:
            root_dir = '/workspace/project/chromium'
    else:
        root_dir = args.root_dir

    src_dir = root_dir + '/src'

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')

    if is_windows():
        path = os.getenv('PATH')
        p = re.compile('depot_tools')
        if not p.search(path):
            path = 'd:\user\ygu5\project\chromium\depot_tools;' + path
            os.putenv('PATH', path)

    os.putenv('GYP_GENERATORS', 'ninja')
    if is_windows() and args.platform == 'desktop':
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        os.putenv('GYP_MSVS_VERSION', '2010e')
        os.putenv('GYP_MSVS_OVERRIDE_PATH', 'd:/user/ygu5/project/chromium/win_toolchain')
        os.putenv('WDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/WDK')
        os.putenv('DXSDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/DXSDK')
        os.putenv('WindowsSDKDir', 'd:/user/ygu5/project/chromium/win_toolchain/win8sdk')
    elif is_linux() and args.platform == 'desktop':
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0')
        os.putenv('CHROME_DEVEL_SANDBOX', '/usr/local/sbin/chrome-devel-sandbox')
    elif args.platform == 'android':
        os.chdir(src_dir)
        shell_source('build/android/envsetup.sh --target-arch=x86')
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 enable_svg=0')

    # Real work
    update(args)
    build(args)
    install(args)
    run(args)
    find_owner(args)
    layout_test(args)
