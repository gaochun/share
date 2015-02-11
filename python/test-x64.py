#!/usr/bin/env python

from util import *

target_archs = ''
targets_type = ''
dryrun = False

phases_all = ['aosp-prebuild', 'aosp-build', 'aosp-flash', 'chromium-x64']
phases = []

dir_aosp = ''
dir_chromium = ''

devices_info = {}


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
    parser.add_argument('--target-type', dest='target_type', help='target type, such as baytrail, generic', default='baytrail')
    parser.add_argument('--dir-aosp', dest='dir_aosp', help='dir for aosp', default='aosp-stable')
    parser.add_argument('--dir-chromium', dest='dir_chromium', help='dir for chromium', default='chromium-android-x64')
    parser.add_argument('--phase', dest='phase', help='phase, including ' + ','.join(phases_all), default='all')
    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global target_archs, targets_type, phases
    global dir_aosp, dir_chromium, dir_root
    global log, timestamp, devices_info

    (timestamp, dir_root, log) = setup_common(args, _teardown)

    dir_aosp = dir_project + '/' + args.dir_aosp
    dir_chromium = dir_project + '/' + args.dir_chromium
    copy_file(dir_share_python, 'aosp.py', dir_aosp, is_sylk=True)
    copy_file(dir_share_python, 'chromium.py', dir_chromium, is_sylk=True)

    pkgs = ['android-tools-adb']
    for pkg in pkgs:
        if not package_installed(pkg):
            error('You need to install package ' + pkg)

    projects = ['depot_tools', 'share']
    for project in projects:
        if not os.path.exists(dir_project + '/' + project):
            error('You need to put project ' + project + ' into ' + dir_project)

    if args.target_arch == 'all':
        target_archs = ['x86_64', 'x86']
    else:
        target_archs = args.target_arch.split(',')

    if args.target_type == 'all':
        targets_type = ['baytrail', 'generic']
    else:
        targets_type = args.target_type.split(',')

    if args.phase == 'all':
        phases = phases_all
    else:
        phases = args.phase.split(',')

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device()

    for index, device_id in enumerate(devices_id):
        if devices_arch[index] in target_archs and devices_arch[index] not in devices_info:
            devices_info[devices_arch[index]] = device_id

    if len(devices_info) != len(target_archs):
        error('Please ensure correct devices are connected')


def test():
    if 'aosp-prebuild' in phases:
        if not os.path.exists(dir_aosp):
            error(dir_aosp + ' does not exist')
        backup_dir(dir_aosp)
        cmd = python_aosp + ' --sync --patch --remove-out'
        cmd = suffix_cmd(cmd, args, log)
        execute(cmd, interactive=True, abort=True, dryrun=dryrun)
        restore_dir()

    if 'aosp-build' in phases:
        if not os.path.exists(dir_aosp):
            error(dir_aosp + ' does not exist')
        for arch in target_archs:
            backup_dir(dir_aosp)
            cmd = python_aosp + ' --target-arch %s --target-type %s --build --backup' % (arch, args.target_type)
            cmd = suffix_cmd(cmd, args, log)
            execute(cmd, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()

    for arch in target_archs:
        if 'aosp-flash' in phases:
            if not os.path.exists(dir_aosp):
                error(dir_aosp + ' does not exist')
            backup_dir(dir_aosp)
            cmd = python_aosp + ' --target-arch %s --target-type %s --device-id %s --flash-image ' % (arch, args.target_type, devices_info[arch])
            cmd = suffix_cmd(cmd, args, log)
            execute(cmd, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()

        if 'chromium-x64' in phases:
            if not os.path.exists(dir_chromium):
                error(dir_chromium + ' does not exist')
            backup_dir(dir_chromium)
            cmd = python_chromium + ' --target-arch %s --repo-type x64 --device-id %s --sync --runhooks --patch --build --test-run --test-formal' % (arch, devices_info[arch])
            cmd = suffix_cmd(cmd, args, log)
            execute(cmd, abort=True, interactive=True, dryrun=dryrun)
            restore_dir()


def _teardown():
    pass


if __name__ == '__main__':
    handle_option()
    setup()
    test()
