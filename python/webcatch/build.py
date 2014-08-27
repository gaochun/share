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

DRYRUN = False
dir_patch = dir_webcatch + '/patch'

rev_min = 0
rev_max = 0
build_fail = 0

# (target_os, target_arch, target_module): [binary_format, rev_min_built, rev_max_built]
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

# [target_os, target_arch, target_module, rev]
combs = []
COMB_INDEX_TARGET_OS = 0
COMB_INDEX_TARGET_ARCH = 1
COMB_INDEX_TARGET_MODULE = 2
COMB_INDEX_REV = 3

# [reva, revb], where reva is bad, and revb is good
expectfail = [
    233707, 236662, 234213, 234223, 234517, 234689, [235193, 235195], 237586,
    241661, 241848,
    [260605, 260606],  # roll angle
    [262675, 262701],  # Because of v8 error
    [275269, 275271],  # pdfium build
]

rev_expectfail = []

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
    parser.add_argument('--build-every', dest='build_every', help='build every number', type=int, default=5)
    parser.add_argument('--build-fail-max', dest='build_fail_max', help='maximum failure number of build', type=int, default=1)
    parser.add_argument('--keep-out', dest='keep_out', help='do not remove out dir after failure', action='store_true')
    parser.add_argument('--slave-only', dest='slave_only', help='only do things at slave machine, for sake of test', action='store_true')
    parser.add_argument('--clean-lock', dest='clean_lock', help='clean all lock files', action='store_true')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)


def setup():
    global rev_min, rev_max, dir_chromium_src_main, combs, build_every, rev_expectfail

    if not args.slave_only:
        for server in servers_webcatch:
            result = execute(remotify_cmd('ls ' + dir_server_chromium, server=server), show_cmd=False)
            if result[0]:
                error('Can not connect to build server')

    set_proxy()
    ensure_dir(dir_project_webcatch_log)
    ensure_dir(dir_project_webcatch_out)
    ensure_package('libnss3-dev ant libcups2-dev libcap-dev libxtst-dev libasound2-dev libxss-dev')

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

    build_every = args.build_every

    if args.rev:
        revs_temp = [int(x) for x in args.rev.split('-')]
        if len(revs_temp) > 1:
            rev_min = revs_temp[0]
            rev_max = revs_temp[1]
        else:
            rev_min = revs_temp[0]
            rev_max = revs_temp[0]
    else:
        rev_min = rev_default[0]
        rev_max = rev_default[1]

    if rev_min > rev_max:
        error('rev_min should not be greater than rev_max')

    target_os_main = ''
    for target_os, target_arch, target_module in [(target_os, target_arch, target_module) for target_os in arg_target_os for target_arch in arg_target_arch for target_module in arg_target_module]:
        if not (target_os, target_arch, target_module) in comb_valid:
            continue
        comb_name = _get_comb_name(target_os, target_arch, target_module)
        dir_comb_slave = dir_project_webcatch_out + '/' + comb_name
        ensure_dir(dir_comb_slave)
        dir_comb_server = dir_server_chromium + '/' + comb_name
        ensure_dir(dir_comb_server, server=server_webcatch)

        if not target_os_main:
            target_os_main = target_os

        rev_min_round = roundup(rev_min, build_every)
        if rev_min_round <= rounddown(rev_max, build_every):
            combs.append([target_os, target_arch, target_module, rev_min_round])

    dir_chromium_src_main = dir_project_webcatch_project + '/chromium-' + target_os_main + '/src'

    for rev in expectfail:
        if isinstance(rev, list):
            for i in range(rev[0], rev[1]):
                rev_expectfail.append(i)
        else:
            rev_expectfail.append(rev)


def build():
    if not args.build:
        return

    build_fail = 0
    interval_git = 300
    rev_git_max = _chromium_get_rev_max()
    time_git = get_epoch_second()
    while True:
        comb_next = _get_comb_next()
        rev_next = comb_next[COMB_INDEX_REV]

        if rev_next > rev_max:
            return
        elif rev_next <= rev_git_max:
            _build(comb_next)
        else:
            while True:
                time_diff = get_epoch_second() - time_git
                if time_diff > interval_git:
                    rev_git_max = _chromium_get_rev_max()
                    time_git = get_epoch_second()
                    if rev_next <= rev_git_max:
                        _build(comb_next)
                        break

                info('Sleeping ' + str(interval_git) + ' seconds...')
                time.sleep(interval_git)


def clean_lock():
    if not args.clean_lock:
        return

    for comb in combs:
        target_os = comb[COMB_INDEX_TARGET_OS]
        target_arch = comb[COMB_INDEX_TARGET_ARCH]
        target_module = comb[COMB_INDEX_TARGET_MODULE]
        comb_name = _get_comb_name(target_os, target_arch, target_module)

        if args.slave_only:
            cmd = 'rm ' + dir_project_webcatch_out + '/' + comb_name + '/*.LOCK'
        else:
            cmd = _remotify_cmd('rm ' + dir_server_chromium + '/' + comb_name + '/*.LOCK')

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
    dir_comb_server = dir_server_chromium + '/' + _get_comb_name(target_os, target_arch, target_module)
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


def _build(comb_next):
    result = _build_one(comb_next)
    comb_next[COMB_INDEX_REV] += build_every
    if result:
        build_fail += 1
        if build_fail >= args.build_fail_max:
            error('You have reached maximum failure number')
    else:
        build_fail = 0

    # Allow pause
    if comb_next[COMB_INDEX_REV] > rev_max:
        return

    seconds = 5
    info('You have ' + str(seconds) + ' seconds to type "enter" to pause')
    i, o, e = select.select([sys.stdin], [], [], seconds)
    if i:
        info('Please type "r" to resume')
        while True:
            input = raw_input()
            if input == 'r':
                break


def _build_one(comb_next):
    (target_os, target_arch, target_module, rev) = comb_next
    comb_name = _get_comb_name(target_os, target_arch, target_module)
    dir_comb = dir_project_webcatch_out + '/' + comb_name

    if rev in rev_expectfail:
        file_final = dir_comb + '/' + str(rev) + '.EXPECTFAIL'
        execute('touch ' + file_final)
        _move_to_server(file_final, target_os, target_arch, target_module)
        return 0

    if not chromium_get_hash(dir_chromium_src_main, rev):
        file_final = dir_comb + '/' + str(rev) + '.NULL'
        execute('touch ' + file_final)
        _move_to_server(file_final, target_os, target_arch, target_module)
        return 0

    info('Begin to build ' + comb_name + '@' + str(rev) + '...')
    dir_repo = dir_project_webcatch_project + '/chromium-' + target_os
    file_log = dir_project_webcatch_log + '/' + comb_name + '@' + str(rev) + '.log'

    # lock
    if not args.slave_only:
        file_lock = dir_server_chromium + '/' + comb_name + '/' + str(rev) + '.LOCK'
        execute(_remotify_cmd('touch ' + file_lock))

    # sync
    cmd_sync = python_chromium + ' --sync --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_sync, dryrun=DRYRUN, interactive=True)
    if result[0]:
        execute(_remotify_cmd('rm -f ' + file_lock))
        send_mail('webcatch@intel.com', 'yang.gu@intel.com', '[webcatch] Failed to sync at ' + host_name, '')
        error('Sync failed', error_code=result[0])

    _patch_after_sync(target_os, target_arch, target_module, rev)

    # makefile
    cmd_makefile = python_chromium + ' --makefile --target-arch ' + target_arch + ' --target-module ' + target_module + ' --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_makefile, dryrun=DRYRUN, show_progress=True)
    if result[0]:
        # Run hook to retry. E.g., for revision >=252065, we have to run with hook to update gn tool.
        cmd_sync_hook = cmd_sync.replace('-n ', '')
        execute(cmd_sync_hook, dryrun=DRYRUN, show_progress=True)
        result = execute(cmd_makefile, dryrun=DRYRUN)
        if result[0]:
            execute(_remotify_cmd('rm -f ' + file_lock))
            send_mail('webcatch@intel.com', 'yang.gu@intel.com', '[webcatch] Failed to generate makefile at ' + host_name, '')
            error('Failed to generate makefile')

    # build
    _patch_before_build(target_os, target_arch, target_module, rev)

    dir_out_build_type = dir_repo + '/src/out-%s/out/Release' % target_arch
    ## remove apks first as sometimes ninja build error doesn't actually return error.
    execute('rm -f %s/apks/*' % dir_out_build_type)
    cmd_build = python_chromium + ' --build --target-arch ' + target_arch + ' --target-module ' + target_module + ' --dir-root ' + dir_repo + ' --rev ' + str(rev)
    result = execute(cmd_build, dryrun=DRYRUN, show_progress=True)

    ## retry here
    if result[0]:
        if target_os == 'android':
            execute('sudo ' + dir_repo + '/src/build/install-build-deps-android.sh', interactive=True, dryrun=DRYRUN)
        if result[0] and not args.keep_out:
            execute('rm -rf ' + dir_repo + '/src/out*', dryrun=DRYRUN)

        result = execute(cmd_build, dryrun=DRYRUN)

    ## handle result, either success or failure. TODO: Need to handle other comb.
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

    # backup
    if not args.slave_only:
        _move_to_server(file_final, target_os, target_arch, target_module)
        execute(_remotify_cmd('rm -f ' + file_lock))

    return result[0]


# get the smallest rev in combs
def _get_comb_next():
    comb_next = []
    for comb in combs:
        comb_temp = comb
        while (comb[COMB_INDEX_REV] <= rev_max and _rev_is_built(comb)):
            info(str(comb) + ' has been built')
            comb[COMB_INDEX_REV] += build_every

        if not comb_next:
            comb_next = comb
        elif rev_temp < comb_next[COMB_INDEX_REV]:
            comb_next = comb

    return comb_next


def _rev_is_built(comb):
    target_os = comb[COMB_INDEX_TARGET_OS]
    target_arch = comb[COMB_INDEX_TARGET_ARCH]
    target_module = comb[COMB_INDEX_TARGET_MODULE]
    rev = comb[COMB_INDEX_REV]
    comb_name = _get_comb_name(target_os, target_arch, target_module)

    # skip the rev marked as built
    if not args.slave_only:
        comb_valid_rev_min = comb_valid[(target_os, target_arch, target_module)][COMB_VALID_INDEX_REV_MIN]
        comb_valid_rev_max = comb_valid[(target_os, target_arch, target_module)][COMB_VALID_INDEX_REV_MAX]
        if rev >= comb_valid_rev_min and rev <= comb_valid_rev_max:
            return True

    # check for slave_only
    if args.slave_only:
        cmd = 'ls ' + dir_project_webcatch_out + '/' + comb_name + '/' + str(rev) + '*'
        result = execute(cmd, show_cmd=False)
        if result[0] == 0:
            return True
        return False

    # check in server
    cmd = 'ls ' + dir_server_chromium + '/' + comb_name + '/' + str(rev) + '*'

    if _rev_is_built_one(cmd):
        return True

    # check again to avoid conflict among parallel build machines
    second = random.randint(1, 10)
    info('sleep ' + str(second) + ' seconds and check again')
    time.sleep(second)

    if _rev_is_built_one(cmd):
        return True

    return False


# check if rev is built in server
def _rev_is_built_one(cmd):
    for server in servers_webcatch:
        cmd_server = remotify_cmd(cmd, server=server)
        result = execute(cmd_server, show_cmd=True)
        if result[0] == 0:
            return True
    return False


def _get_comb_name(*subs):
    return get_comb_name('-', *subs)


def _remotify_cmd(cmd):
    return remotify_cmd(cmd=cmd, server=server_webcatch)


def _roundup(num):
    return roundup(num, build_every)


def _rounddown(num):
    return rounddown(num, build_every)


def _chromium_get_rev_max():
    return chromium_get_rev_max(dir_chromium_src_main)
# </internal>


if __name__ == '__main__':
    parse_arg()
    setup()
    clean_lock()
    build()
