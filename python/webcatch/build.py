# TODO:
# Update revs once all builds are finished for a rev, which would free some memory.
# From 245002, may need to manually execute "gclient sync -f" with hook to check out gn related code.

# Build speed
# android_content_shell: 25/hour
# linux_chrome: 30/hour

# build:
# linux-x86-chrome: rev.tar.gz, rev.FAIL, rev.NULL
# android-x86-content_shell: rev.apk, rev.FAIL, rev.NULL. Finished: 235194-238638

# Build master: host all the builds.
# Build slave: ssh-keygen && ssh-add ~/.ssh/id_rsa && cat ~/.ssh/id_rsa.pub | ssh ubuntu-ygu5-02 cat - >>~/.ssh/authorized_keys

# Chromium revision can be checked at https://src.chromium.org/viewvc/chrome?view=revision&revision=xxxxxx

import sys
sys.path.append(sys.path[0] + '/..')
from util import *

revs = {}

# target_os -> [build, rev_min, rev_max, fetch_time, rev_git_max]
# build -> [[target_arch, target_module, rev_next], [target_arch, target_module, rev_next]]
# Example: {'android': [[['x86', 'webview', 100000], ['x86', 'content_shell', 200000]], 10000, 999999, 1408649648, 150000]}

target_os_info = {}
TARGET_OS_INFO_INDEX_BUILD = 0
TARGET_OS_INFO_INDEX_REV_MIN = 1
TARGET_OS_INFO_INDEX_REV_MAX = 2
TARGET_OS_INFO_INDEX_TIME = 3
TARGET_OS_INFO_INDEX_REV_GIT = 4

TARGET_OS_INFO_INDEX_BUILD_ARCH = 0
TARGET_OS_INFO_INDEX_BUILD_MODULE = 1
TARGET_OS_INFO_INDEX_BUILD_REV_NEXT = 2

# build_next = [target_os, target_arch, target_module, rev_next, index_next]
BUILD_NEXT_INDEX_OS = 0
BUILD_NEXT_INDEX_ARCH = 1
BUILD_NEXT_INDEX_MODULE = 2
BUILD_NEXT_INDEX_REV_NEXT = 3
BUILD_NEXT_INDEX_INDEX_NEXT = 4

DRYRUN = False

time_sleep_default = 300

# [reva, revb], where reva is bad, and revb is good
expectfail = [
    233707, 236662, 234213, 234223, 234517, 234689, [235193, 235195], 237586,
    241661, 241848,
    [262675, 262701],  # Because of v8 error
    [275269, 275271],  # pdfium build
]

rev_expectfail = []

run_chromium_script = 'python ' + dir_python + '/chromium.py'

dir_webcatch = dir_python + '/webcatch'
dir_patch = dir_webcatch + '/patch'

# comb: [binary_format, rev_min_built, rev_max_built]
comb_valid = {
    ('android', 'x86', 'content_shell'): ['(.*).apk$', 233137, 233137],  # 250735
    ('android', 'x86_64', 'content_shell'): ['(.*).apk$', 233137, 278978],
    ('android', 'x86', 'webview'): ['(.*).apk$', 233137, 252136],
    ('linux', 'x86', 'chrome'): ['(.*).tar.gz$', 233137, 236088],
    #['android', 'arm', 'content_shell'],
}
COMB_VALID_INDEX_FORMAT = 0
COMB_VALID_INDEX_REV_MIN = 1
COMB_VALID_INDEX_REV_MAX = 2

################################################################################


def parse_arg():
    global args
    parser = argparse.ArgumentParser(description='Script to build automatically',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -b -r 217377-225138
  python %(prog)s -b --target-os linux --target-module chrome -r 233137-242710 --build-every 5
  python %(prog)s -b --target-os android --target-module content_shell --keep_out

''')
    parser.add_argument('--target-os', dest='target_os', help='target os', choices=target_os_all + ['all'], default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=target_arch_all + ['all'], default='all')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all + ['all'], default='all')
    parser.add_argument('-r', '--rev', dest='rev', help='revisions to build. E.g., 233137, 217377-225138')
    parser.add_argument('--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-every', dest='build_every', help='build every number', type=int, default=1)
    parser.add_argument('--build-fail-max', dest='build_fail_max', help='maximum failure number of build', type=int, default=1)
    parser.add_argument('--keep-out', dest='keep_out', help='do not remove out dir after failure', action='store_true')
    parser.add_argument('--slave-only', dest='slave_only', help='only do things at slave machine, for sake of test', action='store_true')
    parser.add_argument('--clean-lock', dest='clean_lock', help='clean all lock files', action='store_true')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)


def setup():
    global target_os_info, build_every, build_fail_max, rev_expectfail

    set_proxy()

    if not args.slave_only:
        for server in servers_webcatch:
            result = execute(remotify_cmd('ls ' + dir_server_chromium, server=server), show_cmd=True)
            if result[0]:
                error('Can not connect to build server')

    build_every = args.build_every
    build_fail_max = args.build_fail_max

    backup_dir(get_symbolic_link_dir())
    # Packages is split by white space so that you may easily install them all
    ensure_package('libnss3-dev ant libcups2-dev libcap-dev libxtst-dev libasound2-dev libxss-dev')

    setenv('JAVA_HOME', '/usr/lib/jvm/jdk1.6.0_45')

    if args.target_os == 'all':
        arg_target_os = target_os_all
    else:
        arg_target_os = args.target_os.split(',')

    if args.target_arch == 'all':
        arg_target_arch = target_arch_all
    else:
        arg_target_arch = args.target_arch.split(',')

    if args.target_module == 'all':
        arg_target_module = target_module_all
    else:
        arg_target_module = args.target_module.split(',')

    for target_os, target_arch, target_module in [(target_os, target_arch, target_module) for target_os in arg_target_os for target_arch in arg_target_arch for target_module in arg_target_module]:
        if not (target_os, target_arch, target_module) in comb_valid:
            continue

        if target_os not in target_os_info:
            target_os_info[target_os] = [[], 0, 0, 0, 0]
            if args.rev:
                revs_temp = [int(x) for x in args.rev.split('-')]
                if len(revs_temp) > 1:
                    rev_min = revs_temp[0]
                    rev_max = revs_temp[1]
                else:
                    rev_min = revs_temp[0]
                    rev_max = revs_temp[0]

                target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MIN] = rev_min
                target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MAX] = rev_max
            else:
                target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MIN] = rev_default[0]
                target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MAX] = rev_default[1]

        target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD].append([target_arch, target_module, target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MIN]])

    _update_git_info()

    ensure_dir(dir_webcatch_log)
    ensure_dir(dir_project_webcatch_out)

    for target_os in target_os_info:
        for build in target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD]:
            target_arch = build[TARGET_OS_INFO_INDEX_BUILD_ARCH]
            target_module = build[TARGET_OS_INFO_INDEX_BUILD_MODULE]
            dir_comb_slave = dir_project_webcatch_out + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module)
            dir_comb_server = dir_server_chromium + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module)
            # Make dir_comb for slave
            if not os.path.exists(dir_comb_slave):
                os.mkdir(dir_comb_slave)
            # Make dir_comb for server
            result = execute(remotify_cmd('ls ' + dir_comb_server, server=server_webcatch))
            if result[0]:
                execute(remotify_cmd('mkdir -p ' + dir_comb_server, server=server_webcatch))

    for rev in expectfail:
        if isinstance(rev, list):
            for i in range(rev[0], rev[1]):
                rev_expectfail.append(i)
        else:
            rev_expectfail.append(rev)

    restore_dir()


def build():
    if not args.build:
        return

    fail_number = 0
    need_sleep = False
    while True:
        build_next = _get_build_next()
        target_os_next = build_next[BUILD_NEXT_INDEX_OS]
        rev_next = build_next[BUILD_NEXT_INDEX_REV_NEXT]
        index_next = build_next[BUILD_NEXT_INDEX_INDEX_NEXT]
        if rev_next in revs:
            target_os_info[target_os_next][TARGET_OS_INFO_INDEX_BUILD][index_next][TARGET_OS_INFO_INDEX_BUILD_REV_NEXT] = rev_next + 1
            result = _build_one(build_next)
            if result:
                fail_number += 1
                if fail_number >= build_fail_max:
                    error('You have reached maximum failure number')
            else:
                fail_number = 0
        else:
            target_os = build_next[BUILD_NEXT_INDEX_OS]
            rev_max = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MAX]
            if rev_next > rev_max:
                return

            time_fetch = target_os_info[target_os][TARGET_OS_INFO_INDEX_TIME]
            time_diff = get_epoch_second() - time_fetch

            if time_diff < time_sleep_default:
                time_sleep = time_sleep_default - time_diff
            else:
                time_sleep = time_sleep_default

            if need_sleep:
                info('Sleeping ' + str(time_sleep) + ' seconds...')
                time.sleep(time_sleep)
            else:
                need_sleep = True
            _update_git_info()

        # Allow pause
        seconds = 3
        info('You have ' + str(seconds) + ' seconds to type "enter" to pause')
        i, o, e = select.select([sys.stdin], [], [], seconds)
        if i:
            info('Please type "r" to resume')
            while True:
                input = raw_input()
                if input == 'r':
                    break


def clean_lock():
    if not args.clean_lock:
        return

    for target_os in target_os_info:
        for comb in target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD]:
            target_arch = comb[0]
            target_module = comb[1]

            if args.slave_only:
                cmd = 'rm ' + dir_project_webcatch_out + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '/*.LOCK'
            else:
                cmd = remotify_cmd('rm ' + dir_server_chromium + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '/*.LOCK', server=server_webcatch)

            execute(cmd)


def init():
    dir_chromium_android = dir_project_webcatch_project + '/chromium-android'
    if os.path.exists(dir_chromium_android):
        backup_dir(dir_chromium_android)
        cmd = 'src/build/install-build-deps-android.sh'
        execute(cmd, interactive=True)
        cmd = 'GYP_DEFINES="werror= disable_nacl=1 component=shared_library enable_svg=0" gclient sync -f -j16'
        execute(cmd, interactive=True)
        restore_dir()

    dir_chromium_linux = dir_project_webcatch_project + '/chromium-linux'
    if os.path.exists(dir_chromium_linux):
        backup_dir(dir_chromium_linux)
        cmd = 'src/build/install-build-deps.sh'
        execute(cmd, interactive=True)
        cmd = 'GYP_DEFINES="werror= disable_nacl=1 component=shared_library enable_svg=0" gclient sync -f -j16'
        execute(cmd, interactive=True)
        restore_dir()

    if not os.path.exists('/usr/lib/jvm/jdk1.6.0_45'):
        warning('Sun jdk 1.6 does not exist')

    if not os.path.exists('java-7-openjdk-amd64'):
        warning('Open jdk 1.7 does not exist')


# <internal>
# Patch the code to solve some build error problem in upstream
def _patch_after_sync(target_os, target_arch, target_module, rev):
    dir_repo = dir_project_webcatch_project + '/chromium-' + target_os
    backup_dir(dir_repo)

    if rev >= 233687 and rev < 233690:
        _patch_func('opus_celt')

    if rev >= 234913 and rev < 234919:
        _patch_func('openssl_int128')

    if rev >= 235053 and rev < 235114:
        _patch_func('src_disable_nacl')

    if rev >= 235193 and rev < 235196:
        _patch_func('webrtc')

    if rev >= 236727 and rev < 237081:
        _patch_func('src_basename')

    if rev >= 242671 and rev < 242679:
        _patch_func('src_sampling')

    if rev >= 244572 and rev < 244600:
        _patch_func('libyuv_neon')

    if rev >= 247840 and rev < 248040:
        _patch_func('libvpx_neon')

    if rev >= 276595 and rev < 277148:
        _patch_func('regs_struct')

    restore_dir()


def _patch_before_build(target_os, target_arch, target_module, rev):
    dir_repo = dir_project_webcatch_project + '/chromium-' + target_os

    # For 7c849b3d759fa9fedd7d4aea73577d643465918d (rev 253545)
    # http://comments.gmane.org/gmane.comp.web.chromium.devel/50482
    execute('rm -f ' + dir_repo + '/src/out-%s/out/Release/gen/templates/org/chromium/base/ActivityState.java' % target_arch)


def _patch_func(name):
    func_name = '_patch_' + name
    info(func_name)
    globals()[func_name]()


# Patch the problem disable_nacl=1
def _patch_src_disable_nacl():
    backup_dir('src/build')

    for line in fileinput.input('all.gyp', inplace=1):
        if re.search('native_client_sdk_untrusted', line):
            continue
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()
    restore_dir()


# Fix the issue using the same way introduced by @237081
def _patch_src_basename():
    backup_dir('src/chrome')

    file_browser = 'browser/component_updater/test/update_manifest_unittest.cc'
    file_browser_new = file_browser.replace('update_manifest_unittest', 'component_update_manifest_unittest')
    file_common = 'common/extensions/update_manifest_unittest.cc'

    if not os.path.exists(file_browser) or not os.path.exists(file_common):
        return

    gypi_file = 'chrome_tests_unit.gypi'
    for line in fileinput.input(gypi_file, inplace=1):
        if re.search(file_browser, line):
            line = line.replace(file_browser, file_browser_new)
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()

    execute('mv ' + file_browser + ' ' + file_browser_new)

    restore_dir()


# Patch the problem of __int128 in openssl
def _patch_openssl_int128():
    backup_dir('src/third_party/openssl')
    execute('git reset --hard 08086bd0f0dfbc08d121ccc6fbd27de9eaed55c7')
    restore_dir()


# Patch the problem of -mfpu=neon in libyuv
def _patch_libyuv_neon():
    backup_dir('src/third_party/libyuv')
    execute('git reset --hard dd4995805827539ee2c5b4b65c7514e62df2d358')
    restore_dir()


def _patch_libvpx_neon():
    backup_dir('src/third_party/libvpx')
    file = 'libvpx.gyp'
    old = '\'OS=="android"\', {'
    new = '\'OS=="android" and ((target_arch=="arm" or target_arch=="armv7") and arm_neon==0)\', {'
    need_change = True
    for line in fileinput.input(file, inplace=1):
        if need_change and re.search(old, line):
            line = line.replace(old, new)
            need_change = False
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()
    restore_dir()


def _patch_opus_celt():
    backup_dir('src/third_party/opus/src')
    result = execute('git reset --hard e3ea049fcaee2247e45f0ce793d4313babb4ef69')
    if result[0]:
        error('Fail to patch')
    restore_dir()


def _patch_src_sampling():
    backup_dir('src')
    result = execute('git revert -n 462ceb0a79acbd01421795bf2391643ca6d73f78')
    if result[0]:
        error('Fail to patch')
    restore_dir()


def _patch_regs_struct():
    backup_dir('src/sandbox/linux/seccomp-bpf')

    file = 'linux_seccomp.h'
    old = 'typedef user_regs_struct regs_struct;'
    new = '''

#if defined(__BIONIC__)
// Old Bionic versions don't have sys/user.h, so we just define regs_struct
// directly.  This can be removed once we no longer need to support these old
// Bionic versions.
struct regs_struct {
  long int ebx;
  long int ecx;
  long int edx;
  long int esi;
  long int edi;
  long int ebp;
  long int eax;
  long int xds;
  long int xes;
  long int xfs;
  long int xgs;
  long int orig_eax;
  long int eip;
  long int xcs;
  long int eflags;
  long int esp;
  long int xss;
};
#else
typedef user_regs_struct regs_struct;
#endif

    '''
    need_change = True
    for line in fileinput.input(file, inplace=1):
        if need_change and re.search(old, line):
            line = line.replace(old, new)
            need_change = False
        # We can not use print here as it will generate blank line
        sys.stdout.write(line)
    fileinput.close()
    restore_dir()


def _move_to_server(file, target_os, target_arch, target_module):
    dir_comb_server = dir_server_chromium + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module)
    if re.match('ubuntu', server_webcatch):
        username = 'gyagp'
    else:
        username = 'wp'
    result = execute('scp %s %s@%s:%s' % (file, username, server_webcatch, dir_comb_server))
    if result[0]:
        # If the failure is caused by network issue of slave machine, most likely it could not send mail too.
        send_mail('webcatch@intel.com', 'yang.gu@intel.com', '[webcatch] Failed to upload files at ' + host_name, '')
        error('Failed to upload files to server')
    execute('rm -f ' + file)


def _build_one(build_next):
    (target_os, target_arch, target_module, rev, index) = build_next

    info('Begin to build ' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '@' + str(rev) + '...')
    dir_comb = dir_project_webcatch_out + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module)
    if rev in rev_expectfail:
        file_final = dir_comb + '/' + str(rev) + '.EXPECTFAIL'
        execute('touch ' + file_final)
        _move_to_server(file_final, target_os, target_arch, target_module)
        return 0

    file_log = dir_webcatch_log + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '@' + str(rev) + '.log'

    if not args.slave_only:
        file_lock = dir_server_chromium + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '/' + str(rev) + '.LOCK'
        execute(remotify_cmd('touch ' + file_lock, server=server_webcatch))

    dir_repo = dir_project_webcatch_project + '/chromium-' + target_os

    cmd_sync = run_chromium_script + ' --sync --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_sync, dryrun=DRYRUN, interactive=True)
    if result[0]:
        execute(remotify_cmd('rm -f ' + file_lock, server=server_webcatch))
        send_mail('webcatch@intel.com', 'yang.gu@intel.com', '[webcatch] Failed to sync at ' + host_name, '')
        error('Sync failed', error_code=result[0])

    _patch_after_sync(target_os, target_arch, target_module, rev)

    cmd_makefile = run_chromium_script + ' --makefile --target-arch ' + target_arch + ' --target-module ' + target_module + ' --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_makefile, dryrun=DRYRUN, show_progress=True)
    if result[0]:
        # Run hook to retry. E.g., for revision >=252065, we have to run with hook to update gn tool.
        cmd_sync_hook = cmd_sync.replace('-n ', '')
        execute(cmd_sync_hook, dryrun=DRYRUN, show_progress=True)
        result = execute(cmd_makefile, dryrun=DRYRUN)
        if result[0]:
            execute(remotify_cmd('rm -f ' + file_lock, server=server_webcatch))
            send_mail('webcatch@intel.com', 'yang.gu@intel.com', '[webcatch] Failed to generate makefile at ' + host_name, '')
            error('Failed to generate makefile')

    _patch_before_build(target_os, target_arch, target_module, rev)

    dir_out_build_type = dir_repo + '/src/out-%s/out/Release' % target_arch
    # Remove apks first as sometimes ninja build error doesn't actually return error.
    execute('rm -f %s/apks/*' % dir_out_build_type)
    cmd_build = run_chromium_script + ' --build --target-arch ' + target_arch + ' --target-module ' + target_module + ' --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_build, dryrun=DRYRUN, show_progress=True)

    # Retry here
    if result[0]:
        if target_os == 'android':
            execute('sudo ' + dir_repo + '/src/build/install-build-deps-android.sh', interactive=True, dryrun=DRYRUN)
        if result[0] and not args.keep_out:
            execute('rm -rf ' + dir_repo + '/src/out*', dryrun=DRYRUN)

        result = execute(cmd_build, dryrun=DRYRUN)

    # Handle result, either success or failure. TODO: Need to handle other comb.
    if target_os == 'android' and target_module == 'content_shell':
        if result[0] or not os.path.exists(dir_out_build_type + '/apks/ContentShell.apk'):
            file_final = dir_comb + '/' + str(rev) + '.FAIL'
            execute('touch ' + file_final)
        else:
            file_final = dir_comb + '/' + str(rev) + '.apk'
            execute('cp ' + dir_out_build_type + '/apks/ContentShell.apk ' + file_final, dryrun=DRYRUN)
            execute('rm -f ' + file_log)
    elif target_os == 'android' and target_module == 'webview':
        if result[0] or not os.path.exists(dir_out_build_type + '/apks/AndroidWebView.apk'):
            file_final = dir_comb + '/' + str(rev) + '.FAIL'
            execute('touch ' + file_final)
        else:
            file_final = dir_comb + '/' + str(rev) + '.apk'
            execute('cp ' + dir_out_build_type + '/apks/AndroidWebView.apk ' + file_final, dryrun=DRYRUN)
            execute('rm -f ' + file_log)
    elif target_os == 'linux' and target_module == 'chrome':
        dir_test = dir_comb + '/' + str(rev)
        if result[0]:
            file_final = dir_test + '.FAIL'
            execute('touch ' + file_final)
        else:
            os.mkdir(dir_test)
            config_file = dir_repo + '/src/chrome/tools/build/' + target_os + '/FILES.cfg'
            file = open(config_file)
            lines = file.readlines()
            file.close()
            pattern = re.compile("'filename': '(.*)'")
            files = []
            for line in lines:
                match = pattern.search(line)
                if match and os.path.exists(dir_out_build_type + '/' + match.group(1)):
                    files.append(match.group(1))

            # This file is not included in FILES.cfg. Bug?
            files.append('lib/*.so')

            for file_name in files:
                dir_test_temp = os.path.dirname(dir_test + '/' + file_name)
                if not os.path.exists(dir_test_temp):
                    execute('mkdir -p ' + dir_test_temp)

                # Some are just dir, so we need -r option
                execute('cp -rf ' + dir_out_build_type + '/' + file_name + ' ' + dir_test_temp)

            backup_dir(dir_comb)
            # It's strange some builds have full debug info
            #size = int(os.path.getsize(str(rev) + '/chrome'))
            #if size > 300000000:
            #    execute('strip ' + str(rev) + '/chrome')
            execute('tar zcf ' + str(rev) + '.tar.gz ' + str(rev))
            execute('rm -rf ' + str(rev))
            execute('rm -f ' + file_log)
            restore_dir()

            file_final = dir_comb + '/' + str(rev) + '.tar.gz'

    if not args.slave_only:
        _move_to_server(file_final, target_os, target_arch, target_module)
        execute(remotify_cmd('rm -f ' + file_lock, server=server_webcatch))

    return result[0]


def _rev_is_built_one(cmd):
    if args.slave_only:
        result = execute(cmd, show_cmd=True)
        if result[0] == 0:
            return True
        return False
    else:
        for server in servers_webcatch:
            cmd_server = remotify_cmd(cmd, server=server)
            result = execute(cmd_server, show_cmd=True)
            if result[0] == 0:
                return True
        return False


def _rev_is_built(target_os, target_arch, target_module, rev):
    # Skip the revision marked as built
    if not args.slave_only:
        rev_min = comb_valid[(target_os, target_arch, target_module)][COMB_VALID_INDEX_REV_MIN]
        rev_max = comb_valid[(target_os, target_arch, target_module)][COMB_VALID_INDEX_REV_MAX]
        if rev >= rev_min and rev <= rev_max:
            return True

    # Check if file exists or not
    if args.slave_only:
        cmd = 'ls ' + dir_project_webcatch_out + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '/' + str(rev) + '*'
    else:
        cmd = 'ls ' + dir_server_chromium + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module) + '/' + str(rev) + '*'

    if _rev_is_built_one(cmd):
        return True

    # Check again to avoid conflict among parallel build machines
    second = random.randint(1, 10)
    info('sleep ' + str(second) + ' seconds and check again')
    time.sleep(second)

    if _rev_is_built_one(cmd):
        return True

    return False


def _get_rev_next(target_os, index):
    target_arch = target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD][index][TARGET_OS_INFO_INDEX_BUILD_ARCH]
    target_module = target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD][index][TARGET_OS_INFO_INDEX_BUILD_MODULE]
    rev_next = target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD][index][TARGET_OS_INFO_INDEX_BUILD_REV_NEXT]
    rev_max = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MAX]
    rev_git = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_GIT]

    for rev in range(rev_next, rev_max + 1):
        if rev > rev_git:
            return rev

        if not rev % build_every == 0:
            continue

        if _rev_is_built(target_os, target_arch, target_module, rev):
            info(str(rev) + ' has been built')
            target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD][index][TARGET_OS_INFO_INDEX_BUILD_REV_NEXT] = rev + 1
            continue

        # Does not exist from here
        if rev in revs:
            return rev

        # Handle invalid revision number here. TODO: Need to handle other comb.
        dir_comb = dir_project_webcatch_out + '/' + get_comb_name(splitter='-', target_os, target_arch, target_module)
        file_final = dir_comb + '/' + str(rev) + '.NULL'
        info(str(rev) + ' does not exist')
        execute('touch ' + file_final)
        if not args.slave_only:
            _move_to_server(file_final, target_os, target_arch, target_module)
    return rev_max + 1


# Get the smallest revision from all targeted builds
def _get_build_next():
    is_base = True
    for target_os in target_os_info:
        for index, comb in enumerate(target_os_info[target_os][TARGET_OS_INFO_INDEX_BUILD]):
            target_arch = comb[0]
            target_module = comb[1]
            rev_next_temp = _get_rev_next(target_os, index)

            if is_base or rev_next_temp < rev_next:
                target_os_next = target_os
                target_arch_next = target_arch
                target_module_next = target_module
                rev_next = rev_next_temp
                index_next = index

            if is_base:
                is_base = False

    build_next = [target_os_next, target_arch_next, target_module_next, rev_next, index_next]
    return build_next


def _update_git_info_one(target_os):
    global revs

    dir_src = dir_project_webcatch_project + '/chromium-' + target_os + '/src'
    rev_min = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MIN]
    rev_max = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_MAX]
    rev_git = target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_GIT]
    rev_hash = chromium_get_rev_hash(dir_src, max(rev_min, rev_git), rev_max)
    revs_new = sorted(rev_hash.keys())
    rev_git_new = revs_new[-1]
    if rev_git_new > target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_GIT]:
        target_os_info[target_os][TARGET_OS_INFO_INDEX_REV_GIT] = rev_git_new
    revs.extend(revs_new)


def _update_git_info():
    for target_os in target_os_info:
        target_os_info[target_os][TARGET_OS_INFO_INDEX_TIME] = get_epoch_second()
        _update_git_info_one(target_os)
# </internal>


if __name__ == '__main__':
    parse_arg()
    setup()
    clean_lock()
    build()
