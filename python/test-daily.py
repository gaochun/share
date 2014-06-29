#!/usr/bin/env python

from util import *

dir_root = '/workspace/project'
target_archs = ''
target_devices_type = ''
dryrun = False


def handle_option():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to run daily test',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --target-arch x86
  python %(prog)s --target-arch x86_64
  python %(prog)s --target-arch x86,x86_64
  python %(prog)s --target-arch x86,x86_64 --dir-aosp aosp-stable-daily --last-phase 1

  crontab -e
  0 1 * * * cd /workspace/project/share/python && python %(prog)s --target-arch x86_64
''')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch, such as x86, x86_64', default='x86_64')
    parser.add_argument('--target-device-type', dest='target_device_type', help='target device type, such as baytrail, generic', default='baytrail')
    parser.add_argument('--dir-aosp', dest='dir_aosp', help='dir for aosp', default='aosp-stable')
    parser.add_argument('--dir-chromium', dest='dir_chromium', help='dir for chromium', default='chromium-android-test')
    # phase 1: aosp build, backup
    # phase 2: aosp flash
    # phase 3: chromium run test
    parser.add_argument('--last-phase', dest='last_phase', help='last phase to execute', type=int, default=3)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global target_archs, target_devices_type

    backup_dir(dir_root)

    pkgs = ['android-tools-adb']
    for pkg in pkgs:
        if not package_installed(pkg):
            error('You need to install package ' + pkg)

    projects = ['aosp-stable', 'chromium-android-test', 'depot_tools', 'share']
    for project in projects:
        if not os.path.exists(project):
            error('You need to put project ' + project + ' into ' + dir_root)

    path = os.getenv('PATH')
    path += ':/usr/bin:/usr/sbin'
    setenv('PATH', path)

    set_proxy()

    if args.target_arch == 'all':
        target_archs = ['x86_64', 'x86']
    else:
        target_archs = args.target_arch.split(',')

    if args.target_device_type == 'all':
        target_devices_type = ['baytrail', 'generic']
    else:
        target_devices_type = args.target_device_type.split(',')

    backup_dir(args.dir_aosp)
    if not os.path.exists('aosp.py'):
        execute('ln -s %s/share/python/aosp/aosp.py .' % dir_root)
    restore_dir()

    backup_dir(args.dir_chromium)
    if not os.path.exists('x64-upstream.py'):
        execute('ln -s %s/share/python/x64-upstream/x64-upstream.py .' % dir_root)
    restore_dir()


def test():
    backup_dir('share')
    execute('git pull', interactive=True, dryrun=dryrun)
    restore_dir()

    backup_dir(args.dir_aosp)
    cmd = 'python aosp.py --remove-out -s aosp --patch'
    execute(cmd, dryrun=dryrun)
    restore_dir()

    for arch in target_archs:
        backup_dir(args.dir_aosp)

        # build aosp
        cmd = 'python aosp.py --extra-path=/workspace/project/depot_tools --target-arch %s --target-device-type %s --build --backup' % (arch, args.target_device_type)
        execute(cmd, interactive=True, dryrun=dryrun)

        # flash image
        if args.last_phase >= 2:
            cmd = 'python aosp.py --extra-path=/workspace/project/depot_tools --target-arch %s --target-device-type %s --flash-image' % (arch, args.target_device_type)
            execute(cmd, interactive=True, dryrun=dryrun)

        restore_dir()

        if args.last_phase >= 3:
            backup_dir(args.dir_chromium)
            execute('python x64-upstream.py --extra-path=/workspace/project/depot_tools --target-arch %s --batch-test --test-formal' % arch, interactive=True, dryrun=dryrun)
            restore_dir()


if __name__ == '__main__':
    handle_option()
    setup()
    test()
