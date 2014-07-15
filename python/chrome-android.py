from util import *


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
    parser = argparse.ArgumentParser(description='Script to build chrome for android with symbol',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --phase all
''')
    parser.add_argument('--ver', dest='ver', help='version', required=True)
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='beta,stable')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='x86')
    parser.add_argument('--phase', dest='phase', help='phase', default='all')

    args = parser.parse_args()
    args_dict = vars(args)


def setup():
    global dir_root, vers, ver_types, target_archs, phases

    dir_root = get_symbolic_link_dir()

    if args.ver == 'all':
        vers = ver_info.keys()
    else:
        vers = args.ver.split(',')

    ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['arm', 'x86']
    else:
        target_archs = args.target_arch.split(',')

    if args.phase == 'all':
        phases = phases_all
    else:
        phases = args.phase.split(',')


def run():
    for phase in phases_all:
        if phase not in phases:
            continue
        for ver in vers:
            if phase in ['init', 'sync', 'runhooks']:
                execute(_get_cmd(phase, ver), interactive=True)
                continue
            for target_arch in target_archs:
                if phase in ['prebuild', 'makefile', 'build']:
                    execute(_get_cmd(phase, ver, target_arch), interactive=True)
                    continue
                for ver_type in ver_types:
                    if phase in ['postbuild']:
                        execute(_get_cmd(phase, ver, target_arch, ver_type), interactive=True)


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
    run()
