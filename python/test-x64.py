#!/usr/bin/env python

from util import *

target_archs = ''
target_devices_type = ''
dryrun = False

phases_all = ['aosp-prebuild', 'aosp-build', 'aosp-flash', 'chromium-x64']
phases = []

dir_aosp = ''
dir_chromium = ''


def handle_option():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to run daily test',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --target-arch x86
  python %(prog)s --target-arch x86_64
  python %(prog)s --target-arch x86,x86_64
  python %(prog)s --target-arch x86,x86_64 --dir-aosp aosp-stable-daily

  crontab -e
  0 1 * * * cd /workspace/project/share/python && git reset --hard && git pull && python %(prog)s --target-arch x86_64
''')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch, such as x86, x86_64', default='x86_64')
    parser.add_argument('--target-device-type', dest='target_device_type', help='target device type, such as baytrail, generic', default='baytrail')
    parser.add_argument('--dir-aosp', dest='dir_aosp', help='dir for aosp', default='aosp-stable')
    parser.add_argument('--dir-chromium', dest='dir_chromium', help='dir for chromium', default='chromium-android-x64')
    parser.add_argument('--phase', dest='phase', help='phase, including ' + ','.join(phases_all), default='all')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global target_archs, target_devices_type, phases
    global dir_aosp, dir_chromium

    backup_dir(dir_project)
    dir_aosp = args.dir_aosp
    dir_chromium = args.dir_chromium

    pkgs = ['android-tools-adb']
    for pkg in pkgs:
        if not package_installed(pkg):
            error('You need to install package ' + pkg)

    projects = ['depot_tools', 'share']
    for project in projects:
        if not os.path.exists(project):
            error('You need to put project ' + project + ' into ' + dir_project)

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

    copy_file(file_aosp, dir_aosp, is_sylk=True)
    copy_file(file_chromium, dir_chromium, is_sylk=True)

    if args.phase == 'all':
        phases = phases_all
    else:
        phases = args.phase.split(',')


def test():
    cmd_aosp = python_aosp + ' --extra-path=/workspace/project/depot_tools '

    if 'aosp-prebuild' in phases:
        if not os.path.exists(dir_aosp):
            error(dir_aosp + ' does not exist')
        backup_dir(dir_aosp)
        cmd = cmd_aosp + '--sync --patch --remove-out'
        execute(cmd, interactive=True, abort=True, dryrun=dryrun)
        restore_dir()

    if 'aosp-build' in phases:
        if not os.path.exists(dir_aosp):
            error(dir_aosp + ' does not exist')
        for arch in target_archs:
            backup_dir(dir_aosp)
            cmd = cmd_aosp + '--target-arch %s --target-device-type %s --build --backup' % (arch, args.target_device_type)
            execute(cmd, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()

    for arch in target_archs:
        if 'aosp-flash' in phases:
            if not os.path.exists(dir_aosp):
                error(dir_aosp + ' does not exist')
            backup_dir(dir_aosp)
            cmd = cmd_aosp + '--target-arch %s --target-device-type %s --flash-image' % (arch, args.target_device_type)
            execute(cmd, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()

        if 'chromium-x64' in phases:
            if not os.path.exists(dir_chromium):
                error(dir_chromium + ' does not exist')
            backup_dir(dir_chromium)
            execute(python_chromium + ' --extra-path=/workspace/project/depot_tools --target-arch %s --repo-type x64 --sync --runhooks --patch --build --test-run --test-formal ' % arch, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()


if __name__ == '__main__':
    handle_option()
    setup()
    test()
