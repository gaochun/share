from util import *
from chromium import ver_info
from chromium import VER_INFO_INDEX_TYPE
from chromium import VER_INFO_INDEX_STAGE
from chromium import VER_INFO_INDEX_BUILD_ID

# apk tool is downloaded from https://code.google.com/p/android-apktool/downloads/list
# http://connortumbleson.com/apktool/test_versions

# tools: android-sdk-linux/build-tools/20.0.0

dir_root = ''
vers = []
ver_types = []
target_archs = []

phases = []
phases_all = ['init', 'sync', 'runhooks', 'prebuild', 'makefile', 'build', 'postbuild']


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --phase all
''')
    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')
    parser.add_argument('--phase', dest='phase', help='phase, including ' + ','.join(phases_all), default='all')
    parser.add_argument('--check', dest='check', help='check', action='store_true')
    parser.add_argument('--run', dest='run', help='run', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, vers, ver_types, target_archs, phases

    if not args.ver:
        error('You must designate version using --ver option')

    dir_root = get_symbolic_link_dir()

    if args.ver == 'all':
        vers = ver_info.keys()
    else:
        vers = args.ver.split(',')

    if args.ver_type == 'all':
        ver_types = ['stable', 'beta']
    else:
        ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['x86', 'arm']
    else:
        target_archs = args.target_arch.split(',')

    if args.phase == 'all':
        phases = phases_all
    else:
        phases = args.phase.split(',')


def run():
    if not args.run:
        return

    for ver in vers:
        if ver_info[ver][VER_INFO_INDEX_STAGE] == 'end':
            info('%s has been marked as built' % ver)
            continue
        for phase in ['init', 'sync', 'runhooks']:
            if phase in phases:
                execute(_get_cmd(phase, ver), interactive=True)
        for target_arch in target_archs:
            for phase in ['prebuild', 'makefile', 'build']:
                if phase in phases:
                    execute(_get_cmd(phase, ver, target_arch), interactive=True)
            for ver_type in ver_types:
                for phase in ['postbuild']:
                    if phase in phases:
                        execute(_get_cmd(phase, ver, target_arch, ver_type), interactive=True)


def check():
    if not args.check:
        return

    for target_arch, ver, ver_type in [(target_arch, ver, ver_type) for target_arch in target_archs for ver in vers for ver_type in ver_types]:
        if ver_info[ver][VER_INFO_INDEX_BUILD_ID] == '':
            continue

        if ver_type not in ver_info[ver][VER_INFO_INDEX_TYPE]:
            continue

        if not os.path.exists(dir_server_chromium + '/android-%s-chrome/%s-%s/Chromium.apk' % (target_arch, ver, ver_type)):
            info('%s,%s,%s has not been built' % (target_arch, ver, ver_type))


def _get_cmd(phase, ver, target_arch='', ver_type=''):
    cmd = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome --dir-root ' + dir_root + '/' + ver + ' --' + phase
    if target_arch != '':
        cmd += ' --target-arch ' + target_arch
    if ver_type != '':
        cmd += ' --ver-type ' + ver_type

    if phase == 'build':
        cmd += ' --build-skip-mk'

    return cmd

if __name__ == "__main__":
    parse_arg()
    setup()
    check()
    run()
