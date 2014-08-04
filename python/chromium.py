#!/usr/bin/env python

import fileinput
from multiprocessing import Pool
from util import *

# Each chromium version is: major.minor.build.patch
# major -> svn rev, git commit, build. major commit is after build commit.
# To get this, search 'The atomic number' in 'git log origin master chrome/VERSION'
majorver_info = {
    38: [278979, '85c11da0bf7aad87c0a563c7093cb52ee58e4666', 2063],
    37: [269579, '47c9991b3153128d79eac26ad0e8ecb3d7e21128', 1986],
    36: [260368, 'b1f8bdb570beade2a212e69bee1ea7340d80838e', 1917],
    35: [252136, '6d5ba2122914c53d753e5fb960a601b43cb79c60', 1848],
    34: [241271, '3824512f1312ec4260ad0b8bf372619c7168ef6b', 1751],
    33: [233137, 'eeaecf1bb1c52d4b9b56a620cc5119409d1ecb7b', 1701],
    32: [225138, '6a384c4afe48337237e3da81ccff8658755e2a02', 1652],
    31: [217377, 'c95dd877deb939ec7b064831c2d20d92e93a4775', 1600],
    30: [208581, '88367e9bf6a10b9e024ec99f12755b6f626bbe0c', 1548],
}
MAJORVER_INFO_INDEX_REV = 0

args = ''
args_dict = []
repo_type = ''

target_os = ''
target_arch = ''
target_module = ''

timestamp = ''
build_type = ''

dir_patches = ''
patches = {}
test_filter = {}

dir_root = ''  # /workspace/project/chromium-android
dir_src = ''  # /workspace/project/chromium-android/src
dir_test = ''  # /workspace/project/chromium-android/test
dir_out_build_type = ''  # /workspace/project/chromium-android/src/out-x86_64/out/Release
dir_test_timestamp = ''  # /workspace/project/chromium-android/test

name_file = sys._getframe().f_code.co_filename
file_log = ''

devices = []
devices_name = []
devices_type = []
devices_target_arch = []

# rev related
rev = 0
rev_hash = {}
REV_MAX = 9999999

# From this rev, do not append --target-arch to envsetup.sh, instead, use android_gyp -Dtarget_arch.
# From rev 252166, envsetup.sh --target-arch would report an error.
rev_envsetup = 252034
ver_envsetup = '35.0.0.0'

# Form this rev, envsetup would no longer set OS=android, we need to define it using GYP_DEFINES='OS=android'
rev_gyp_defines = 260548
ver_gyp_defines = '34.0.0.0'

# From this rev, android_gyp is no longer supported. Use gyp_chromium instead.
rev_no_android_gyp = 262292
ver_no_android_gyp = '34.0.1847.61'

# repo type specific variables
# chrome-android

# download: download Chrome.apk and put into todo
# buildid: install Chrome.apk to device to check version, version type, arch, and create README to record build id and phase.
# init: init the source code repo. depends on ver.
# sync: sync source code. depends on ver.
# runhooks: runhooks to make source code directory ready to build. depends on ver and parts of them rely on target_arch.
# prebuild: extra things to prepare for prebuild. depends on ver and target_arch.
# makefile: generate makefile. depends on ver and target_arch.
# build: build. depends on ver and target_arch.
# postbuild: generate new package, so with symbol, etc. depends on ver, target_arch and ver_type.
# verify: install new package to device to verify its correctness.  depends on ver, target_arch and ver_type.
# notify: send out email notification.  depends on ver, target_arch and ver_type.
chrome_android_phase_all = ['buildid', 'init', 'sync', 'runhooks', 'prebuild', 'makefile', 'build', 'postbuild', 'verify', 'backup', 'notify']
ver = ''
ver_type = ''
chrome_android_soname = ''
chrome_android_dir_server_root = ''
chrome_android_file_readme = ''

test_command_default = [
    'gtest',
    'instrumentation',
    #'linker',
    #'uiautomator',
    #'monkey',
    #'perf'
]

# See details at build/android/pylib/gtest/gtest_config.py
gtest_suite_default = [
    'android_webview_unittests',
    'base_unittests',
    'breakpad_unittests',  # Need breakpad
    'cc_unittests',
    'components_unittests',
    'content_unittests',
    'events_unittests',
    'gl_tests',
    'gpu_unittests',
    'ipc_tests',
    'media_unittests',
    'net_unittests',
    'sandbox_linux_unittests',
    'sql_unittests',
    'sync_unit_tests',
    'ui_unittests',
    'unit_tests',  # Need breakpad
    'webkit_unit_tests',
    'content_gl_tests',  # experimental suite
    #'content_browsertests',  # webrtc
]

instrumentation_suite_default = [
    'ContentShellTest',
    'ChromeShellTest',
    'AndroidWebViewTest',
    'MojoTest',
]

test_suite = {}

repo_type_info = {
    'default': {
        'rev': REV_MAX,
        'dir_patches': dir_python,
        'patches': {},
        # (device_type, target_arch): {}
        # device_type can be 'baytrail', 'generic'
        'test_filter': {},
    },
    'x64': {
        'rev': 284889,
        'dir_patches': dir_python + '/chromium-patches/x64',
        'patches': {
            'src': [
                '0001-Enlarge-kThreadLocalStorageSize-to-satisfy-test.patch',
            ],
        },
        'test_filter': {
            ('all', 'all'): {},
            ('all', 'x86_64'): {},
            ('all', 'x86'): {},
            ('baytrail', 'all'): {
                'media_unittests': [
                    # Status: TODO
                    'MediaDrmBridgeTest.AddNewKeySystemMapping',
                    'MediaDrmBridgeTest.ShouldNotOverwriteExistingKeySystem',
                    'YUVConvertTest.YUVAtoARGB_MMX_MatchReference',
                    'MediaDrmBridgeTest.IsKeySystemSupported_Widevine',
                    'MediaDrmBridgeTest.IsSecurityLevelSupported_Widevine',
                ],
                'sandbox_linux_unittests': [
                    # Status: Verified with stable image
                    'BaselinePolicy.CreateThread',
                    'BaselinePolicy.DisallowedCloneFlagCrashes',
                    'BrokerProcess.RecvMsgDescriptorLeak',

                    # The following cases are due to https://codereview.chromium.org/290143006
                    # These are false positive cases and test infrastructure needs to improve to support them.
                    'BaselinePolicy.DisallowedKillCrashes',
                    'BaselinePolicy.SIGSYS___NR_acct',
                    'BaselinePolicy.SIGSYS___NR_chroot',
                    'BaselinePolicy.SIGSYS___NR_eventfd',
                    'BaselinePolicy.SIGSYS___NR_fanotify_init',
                    'BaselinePolicy.SIGSYS___NR_fgetxattr',
                    'BaselinePolicy.SIGSYS___NR_getcpu',
                    'BaselinePolicy.SIGSYS___NR_getitimer',
                    'BaselinePolicy.SIGSYS___NR_init_module',
                    'BaselinePolicy.SIGSYS___NR_inotify_init',
                    'BaselinePolicy.SIGSYS___NR_io_cancel',
                    'BaselinePolicy.SIGSYS___NR_keyctl',
                    'BaselinePolicy.SIGSYS___NR_mq_open',
                    'BaselinePolicy.SIGSYS___NR_ptrace',
                    'BaselinePolicy.SIGSYS___NR_sched_setaffinity',
                    'BaselinePolicy.SIGSYS___NR_setpgid',
                    'BaselinePolicy.SIGSYS___NR_swapon',
                    'BaselinePolicy.SIGSYS___NR_sysinfo',
                    'BaselinePolicy.SIGSYS___NR_syslog',
                    'BaselinePolicy.SIGSYS___NR_timer_create',
                    'BaselinePolicy.SIGSYS___NR_vserver',
                    'BaselinePolicy.SocketpairWrongDomain',
                ],
                'ContentShellTest': [
                    # Status: TODO
                    'JavaBridgeCoercionTest#testPassJavaObject',
                    'ContentViewScrollingTest#testFling',
                ],
                'AndroidWebViewTest': [
                    # Status: TODO
                    'AndroidScrollIntegrationTest#testUiScrollReflectedInJs',
                    'AwContentsTest#testCreateAndGcManyTimes',
                    'AwSettingsTest#testAllowMixedMode',
                    'AwSettingsTest#testLoadWithOverviewModeViewportTagWithTwoViews',
                    'AwSettingsTest#testLoadWithOverviewModeWithTwoViews',
                    'AwSettingsTest#testUserAgentStringDefault',

                    # Crash
                    'AndroidScrollIntegrationTest#testFlingScroll',
                    'AndroidScrollIntegrationTest#testJsScrollCanBeAlteredByUi',
                    'AndroidScrollIntegrationTest#testJsScrollFromBody',
                    'AndroidScrollIntegrationTest#testJsScrollReflectedInUi',
                    'AndroidScrollIntegrationTest#testTouchScrollCanBeAlteredByUi',
                    'ClientOnPageFinishedTest#testOnPageFinishedCalledAfterError',
                ],
                'MojoTest': [
                    # TODO
                    'CoreImplTest#testDataPipeCreation',
                    'CoreImplTest#testSharedBufferCreation',
                ]
            },
            ('baytrail', 'x86_64'): {},
            ('baytrail', 'x86'): {
                # status Done
                'base_unittests': [
                    # This case is only needed for x86. x64 doesn't have this problem.
                    'ThreadTest.StartWithOptions_StackSize',
                ],
                'gl_tests': [
                    # Status: TODO
                    'TextureStorageTest.CorrectPixels',
                ],
            },
            ('generic', 'all'): {},
            ('generic', 'x86_64'): {},
            ('generic', 'x86'): {},
        }
    }
}
################################################################################

# override format_epilog to make it format better
# argparse.format_epilog = lambda self, formatter: self.epilog


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script to sync, build upstream x64 Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --revert -s --patch -b
  python %(prog)s --batch-build
  python %(prog)s --batch-build --sync-upstream
  python %(prog)s --revert -s --sync-upstream --patch
  python %(prog)s --batch-build --test-run
  python %(prog)s --batch-test
  python %(prog)s --test-dryrun --time-fixed
  python %(prog)s --test-to yang.gu@intel.com --test-case 'webkit_compositor_bindings_unittests' --test-run
  python %(prog)s --instrumentation-suite ContentShellTest --test-run --test-command instrumentation --test-formal --test-to yang.gu@intel.com


  gclient:
  python %(prog)s --revert
  python %(prog)s --fetch
  python %(prog)s --sync --rev 270000
  python %(prog)s --sync --repo_type x64
  python %(prog)s --sync --repo_type x64 --sync-upstream
  python %(prog)s --runhooks

  build:
  python %(prog)s -b --target-module webview // out/Release/lib/libstandalonelibwebviewchromium.so->Release/android_webview_apk/libs/x86/libstandalonelibwebviewchromium.so
  python %(prog)s -b --target-module chrome

  run:
  python %(prog)s -r --build-type release
  python %(prog)s -r -run-option=--enable-logging=stderr
  python %(prog)s -r --run-option--enable-logging=stderr
  python %(prog)s -r '--run-option --enable-logging=stderr'
  python %(prog)s -r --run-debug-renderer
  python %(prog)s -r --run-option 'http://browsermark.rightware.com'

  misc:
  python %(prog)s --owner


  crontab -e
  0 1 * * * cd /workspace/project/chromium64-android && python %(prog)s -s --extra-path=/workspace/project/depot_tools
''')
    group_common = parser.add_argument_group('common')
    group_common.add_argument('--repo-type', dest='repo_type', help='repo type. default for upstream, x64 for x64 test, chrome-android for "Chrome for Android"', default='default')
    #dir: <arch>-<target-os>/out/<build_type>, example: x86-linux/out/Release
    group_common.add_argument('--target-os', dest='target_os', help='target os', choices=['android', 'linux'])
    group_common.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64', 'arm64'], default='x86')
    group_common.add_argument('--target-module', dest='target_module', help='target module to build', choices=['chrome', 'webview', 'content_shell'], default='webview')
    group_common.add_argument('--devices', dest='devices', help='device id list separated by ","', default='')
    group_common.add_argument('--dir-root', dest='dir_root', help='set root directory')
    group_common.add_argument('--just-out', dest='just_out', help='stick to out, instead of out-x86_64/out', action='store_true')
    group_common.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
    group_common.add_argument('--time-fixed', dest='time_fixed', help='fix the time for test sake. We may run multiple tests and results are in same dir', action='store_true')
    group_common.add_argument('--rev', dest='rev', type=int, help='revision, will override --sync-upstream')
    group_common.add_argument('--ver', dest='ver', help='ver for chrome-android')
    group_common.add_argument('--ver-type', dest='ver_type', help='ver type, stable or beta')
    group_common.add_argument('--chrome-android-apk', dest='chrome_android_apk', help='chrome android apk')
    group_common.add_argument('--phase-continue', dest='phase_continue', help='run all left phases', action='store_true')
    group_common.add_argument('--build-type', dest='build_type', help='build type', choices=['release', 'debug'], default='release')

    group_gclient = parser.add_argument_group('gclient')
    group_gclient.add_argument('--revert', dest='revert', help='revert', action='store_true')
    group_gclient.add_argument('--fetch', dest='fetch', help='fetch', action='store_true')
    group_gclient.add_argument('--sync', dest='sync', help='sync', action='store_true')
    group_gclient.add_argument('--sync-upstream', dest='sync_upstream', help='sync with upstream latest', action='store_true')
    group_gclient.add_argument('--runhooks', dest='runhooks', help='runhooks', action='store_true')

    group_basic = parser.add_argument_group('basic')
    group_basic.add_argument('--download', dest='download', help='download', action='store_true')
    group_basic.add_argument('--buildid', dest='buildid', help='buildid', action='store_true')
    group_basic.add_argument('--init', dest='init', help='init', action='store_true')
    group_basic.add_argument('--patch', dest='patch', help='apply patches', action='store_true')
    group_basic.add_argument('--prebuild', dest='prebuild', help='prebuild', action='store_true')
    group_basic.add_argument('--makefile', dest='makefile', help='generate makefile', action='store_true')
    group_basic.add_argument('--build', dest='build', help='build', action='store_true')
    group_basic.add_argument('--build-skip-mk', dest='build_skip_mk', help='skip the generation of makefile', action='store_true')
    group_basic.add_argument('--build-fail-max', dest='build_fail_max', help='allow n build failures before it stops', default='0')
    group_basic.add_argument('--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')
    group_basic.add_argument('--postbuild', dest='postbuild', help='postbuild', action='store_true')
    group_basic.add_argument('--verify', dest='verify', help='verify', action='store_true')
    group_basic.add_argument('--backup', dest='backup', help='backup', action='store_true')
    group_basic.add_argument('--notify', dest='notify', help='notify', action='store_true')
    group_basic.add_argument('--install', dest='install', help='install chrome for android', choices=['release', 'debug'])
    group_basic.add_argument('--run', dest='run', help='run', action='store_true')
    group_basic.add_argument('--run-option', dest='run_option', help='option to run')
    group_basic.add_argument('--run-gpu', dest='run_GPU', help='enable GPU acceleration', action='store_true')
    group_basic.add_argument('--run-debug-renderer', dest='run_debug_renderer', help='run gdb before renderer starts', action='store_true')

    group_test = parser.add_argument_group('test')
    group_test.add_argument('--test-build', dest='test_build', help='build test', action='store_true')
    group_test.add_argument('--test-run', dest='test_run', help='run test and generate report', action='store_true')
    group_test.add_argument('--test-to', dest='test_to', help='test email receivers that would override the default for test sake')
    group_test.add_argument('--test-formal', dest='test_formal', help='formal test, which would send email and backup to samba server', action='store_true')
    group_test.add_argument('--test-command', dest='test_command', help='test command split by ","')
    group_test.add_argument('--test-drybuild', dest='test_drybuild', help='skip the build of test', action='store_true')
    group_test.add_argument('--test-dryrun', dest='test_dryrun', help='dry run test', action='store_true')
    group_test.add_argument('--test-verbose', dest='test_verbose', help='verbose output for test', action='store_true')
    group_test.add_argument('--test-filter', dest='test_filter', help='filter for test')
    group_test.add_argument('--test-debug', dest='test_debug', help='enter debug mode', action='store_true')
    group_test.add_argument('--gtest-suite', dest='gtest_suite', help='gtest suite')
    group_test.add_argument('--instrumentation-suite', dest='instrumentation_suite', help='instrumentation suite')

    group_misc = parser.add_argument_group('misc')
    group_misc.add_argument('--analyze', dest='analyze', help='analyze test tombstone', action='store_true')
    group_misc.add_argument('--owner', dest='owner', help='find owner for latest commit', action='store_true')
    group_misc.add_argument('--layout', dest='layout', help='layout test')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, dir_src, dir_out_build_type, dir_test, dir_test_timestamp
    global target_os, target_arch, target_module
    global devices, devices_name, devices_type, devices_target_arch
    global file_log, timestamp, test_suite, build_type, rev, dir_patches, patches, test_filter, repo_type
    global ver, ver_type, chrome_android_soname, chrome_android_dir_server_root, chrome_android_file_readme, chrome_android_apk

    if args.dir_root:
        dir_root = args.dir_root
    elif os.path.islink(sys.argv[0]):
        dir_root = get_symbolic_link_dir()
    else:
        dir_root = os.path.abspath(os.getcwd())

    repo_type = args.repo_type

    # set repo_type related global variables
    for key in repo_type_info['default']:
        if repo_type == 'default' or not repo_type in repo_type_info or not key in repo_type_info[repo_type]:
            globals()[key] = repo_type_info['default'][key]
        else:
            globals()[key] = repo_type_info[repo_type][key]

    if args.sync_upstream:
        rev = REV_MAX

    if args.rev:
        rev = args.rev

    if args.time_fixed:
        timestamp = get_datetime(format='%Y%m%d')
    else:
        timestamp = get_datetime()

    set_proxy()
    set_path(args.extra_path)

    for cmd in ['adb', 'git', 'gclient']:
        result = execute('which ' + cmd, show_command=False)
        if result[0]:
            error('Could not find ' + cmd + ', and you may use --extra-path to designate it')

    target_arch = args.target_arch
    if not args.target_module:
        if target_os == 'linux':
            target_module = 'chrome'
        elif target_os == 'android':
            target_module = 'webview'
    else:
        target_module = args.target_module

    if not os.path.exists(dir_root):
        os.makedirs(dir_root)

    dir_src = dir_root + '/src'
    build_type = args.build_type
    if args.just_out:
        dir_out_build_type = dir_src + '/out/' + build_type.capitalize()
    else:
        dir_out_build_type = dir_src + '/out-' + target_arch + '/out/' + build_type.capitalize()
    dir_test = dir_root + '/test'
    dir_test_timestamp = dir_test + '/' + timestamp

    setenv('GYP_GENERATORS', 'ninja')
    backup_dir(dir_root)

    # set target_os
    if args.target_os:
        target_os = args.target_os
    else:
        found = False
        f = open('.gclient')
        lines = f.readlines()
        f.close()
        for line in lines:
            if re.match("target_os = \['android'\]", line):
                found = True
                break
        if found:
            target_os = 'android'
        else:
            target_os = 'linux'

    if _need_device():
        if args.devices:
            devices_limit = args.devices.split(',')
        else:
            devices_limit = []

        connect_device()
        (devices, devices_name, devices_type, devices_target_arch) = setup_device(devices_limit=devices_limit)

        _hack_app_process()

    target_module = args.target_module

    file_log = dir_root + '/log-' + timestamp + '.txt'

    # repo type specific variables
    if repo_type == 'chrome-android':
        if args.chrome_android_apk:
            chrome_android_apk = args.chrome_android_apk
        else:
            ver = args.ver
            ver_type = args.ver_type
            chrome_android_soname = _get_soname()
            chrome_android_dir_server_root = chrome_android_dir_server_todo + '/' + target_arch + '/' + ver + '-' + ver_type
            chrome_android_file_readme = chrome_android_dir_server_root + '/README'

    if target_os == 'windows':
        setenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        setenv('GYP_MSVS_VERSION', '2010e')
        setenv('GYP_MSVS_OVERRIDE_PATH', 'd:/user/ygu5/project/chromium/win_toolchain')
        setenv('WDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/WDK')
        setenv('DXSDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/DXSDK')
        setenv('WindowsSDKDir', 'd:/user/ygu5/project/chromium/win_toolchain/win8sdk')
    elif target_os == 'linux':
        setenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0')
        setenv('CHROME_DEVEL_SANDBOX', '/usr/local/sbin/chrome-devel-sandbox')
    elif target_os == 'android':
        if rev < rev_envsetup:
            backup_dir(dir_src)
            shell_source('build/android/envsetup.sh --target-arch=' + target_arch, use_bash=True)
            restore_dir()
            if not getenv('ANDROID_SDK_ROOT'):
                error('Environment is not well set')

        if rev < rev_gyp_defines or repo_type == 'chrome-android' and not args.chrome_android_apk and ver_ge(ver_gyp_defines, ver):
            setenv('GYP_DEFINES', 'werror= disable_nacl=1 enable_svg=0')
        else:
            setenv('GYP_DEFINES', 'OS=%s werror= disable_nacl=1 enable_svg=0' % target_os)

    print '''
========== Configuration Begin ==========
PATH=%(path)s
http_proxy=%(http_proxy)s
https_proxy=%(http_proxy)s
no_proxy=%(no_proxy)s
========== Configuration End ==========
    ''' % {'path': getenv('PATH'), 'http_proxy': getenv('http_proxy'), 'https_proxy': getenv('https_proxy'), 'no_proxy': getenv('no_proxy')}

    # Setup test_suite
    for command in _setup_list('test_command'):
        test_suite[command] = []
        for suite in _setup_list(command + '_suite'):
            test_suite[command].append(suite)


def buildid(force=False):
    if not args.buildid and not force:
        return

    # get the target arch
    execute('unzip "%s" -d temp' % chrome_android_apk, show_command=True)
    target_arch_temp = ''
    for key in target_arch_info:
        if os.path.exists('temp/lib/' + target_arch_info[key][TARGET_ARCH_INFO_INDEX_ABI]):
            target_arch_temp = key
            break
    if target_arch_temp == '':
        error('Arch is not supported for ' + todo)
    execute('rm -rf temp', show_command=False)

    (ver_temp, ver_type_temp, build_id_temp) = _chrome_android_get_info(target_arch_temp, chrome_android_apk)
    info('build id is ' + build_id_temp)
    dir_todo = '%s/%s/%s-%s' % (chrome_android_dir_server_todo, target_arch_temp, ver_temp, ver_type_temp)
    dirs_check = [
        dir_todo,
        '%s/android-%s-chrome/%s-%s' % (dir_server_chromium, target_arch_temp, ver_temp, ver_type_temp),
        '%s/android-%s-chrome/archive/%s-%s' % (dir_server_chromium, target_arch_temp, ver_temp, ver_type_temp),
    ]
    for dir_check in dirs_check:
        print dir_check
        if os.path.exists(dir_todo):
            error('The todo directory already exists at ' + dir_check)

    os.makedirs(dir_todo)
    execute('mv "%s" %s/Chrome.apk' % (chrome_android_apk, dir_todo))
    execute('echo "phase=buildid\nbuild-id=%s" >%s/README' % (build_id_temp, dir_todo), show_command=False)


def init(force=False):
    if not args.init and not force:
        return

    if repo_type == 'chrome-android':
        execute('gclient config https://src.chromium.org/chrome/releases/' + ver, abort=True)
        execute('echo "target_os = [\'android\']" >> .gclient', abort=True)
        _update_phase(get_caller_name())


def revert(force=False):
    if not args.revert and not force:
        return

    _run_gclient('revert')


def fetch(force=False):
    if not args.fetch and not force:
        return

    _run_gclient('fetch')


def sync(force=False):
    if not args.sync and not force:
        return

    # Judge if the repo is managed or not
    managed = False
    f = open('.gclient')
    lines = f.readlines()
    f.close()
    pattern = re.compile('managed.*(True|False)')
    for line in lines:
        match = pattern.search(line)
        if match and match.group(1) == 'True':
                managed = True

    if not managed:
        backup_dir(dir_src)
        execute('git pull --rebase origin master')
        restore_dir()

    cmd_type = 'sync'
    if rev != REV_MAX:
        cmd_type += ' --revision src@' + _get_hash()
    _run_gclient(cmd_type)

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def runhooks(force=False):
    if not args.runhooks and not force:
        return

    _run_gclient('runhooks')

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def patch(force=False):
    if not args.patch and not force:
        return

    apply_patch(patches, dir_patches)


def prebuild(force=False):
    global chrome_android_soname

    if not args.prebuild and not force:
        return

    if repo_type == 'chrome-android':
        build_id = _chrome_android_get_build_id()
        if build_id == '':
            return

        dir_prebuilt = '%s/prebuilt-%s' % (dir_src, target_arch)
        if not os.path.exists(dir_prebuilt):
            os.mkdir(dir_prebuilt)

        backup_dir(dir_prebuilt)
        cmd = 'wget -c -i http://storage.googleapis.com/chrome-browser-components/' + build_id + '/index.html'
        execute(cmd, interactive=True, abort=True)

        dir_release = dir_src + '/out-' + target_arch + '/out/Release'
        ensure_dir(dir_release)
        cmd = 'cp *.a ' + dir_release
        execute(cmd, abort=True)

        chrome_android_soname = _get_soname()

        restore_dir()

        _update_phase(get_caller_name())


def makefile(force=False):
    if not args.makefile and not force:
        return

    backup_dir(dir_src)
    if target_os == 'android':

        if target_arch == 'x86':
            target_arch_temp = 'ia32'
        elif target_arch == 'x86_64':
            target_arch_temp = 'x64'
        else:
            target_arch_temp = target_arch

        if repo_type == 'chrome-android':
            if chrome_android_soname == '':
                error('Please download prebuilt first')
            # gyp file must be in src dir, and contained in one level of directory

            cmd = 'GYP_DEFINES="%s libpeer_target_type=loadable_module host_os=linux" CHROMIUM_GYP_FILE="prebuilt-%s/%s_target.gyp"' % (getenv('GYP_DEFINES'), target_arch, chrome_android_soname) + ' build/gyp_chromium -Dtarget_arch='
            if ver_ge(ver_no_android_gyp, ver):
                cmd += target_arch
            else:
                cmd += target_arch_temp
        else:
            # We can't omit this step as android_gyp is a built-in command, instead of environmental variable.
            if rev < rev_envsetup:
                cmd = 'source build/android/envsetup.sh --target-arch=' + target_arch + ' && android_gyp -Dwerror= -Duse_goma=0'
            elif rev < rev_no_android_gyp:
                cmd = 'source build/android/envsetup.sh && android_gyp -Dwerror= -Duse_goma=0 -Dtarget_arch=' + target_arch_temp
            else:
                cmd = 'build/gyp_chromium -Dwerror= -Duse_goma=0 -Dtarget_arch=' + target_arch_temp
    else:
        cmd = 'build/gyp_chromium -Dwerror='

    if not args.just_out:
        cmd += ' --generator-output out-' + target_arch

    if re.search('source', cmd):
        cmd = bashify(cmd)
    result = execute(cmd, interactive=True, dryrun=False)
    restore_dir()
    if result[0]:
        error('Fail to generate makefile')

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def build(force=False):
    if not args.build and not force:
        return

    need_makefile = False
    if not args.build_skip_mk:
        need_makefile = True
    if not _has_dir_out_build_type():
        need_makefile = True

    build_fail_max = args.build_fail_max

    if repo_type == 'chrome-android':
        need_makefile = False
        build_fail_max = 1

    print '== Build Environment =='
    print 'Directory of root: ' + dir_root
    print 'Build type: ' + build_type
    print 'Build system: Ninja'
    print 'Generate makefile: ' + str(need_makefile)
    print 'Host OS: ' + host_os
    print 'Target OS: ' + target_os.capitalize()
    print '======================='

    name_func = get_caller_name()
    timer_start(name_func)

    if need_makefile:
        makefile(force=True)

    cmd_ninja = 'ninja -k' + build_fail_max + ' -j' + number_cpu + ' -C ' + dir_out_build_type
    if target_os == 'android' and target_module == 'webview':
        cmd_ninja += ' android_webview_apk libwebviewchromium'
    elif target_os == 'android' and target_module == 'content_shell':
        cmd_ninja += ' content_shell_apk'
    elif target_os == 'android' and target_module == 'chrome':
        if chrome_android_soname == '':
            error('Please download prebuilt first')
        cmd_ninja += ' lib%s_prebuilt' % chrome_android_soname
    else:
        cmd_ninja += ' ' + target_module

    if args.build_verbose:
        cmd_ninja += ' -v'

    cmd_ninja += ' 2>&1 |tee -a ' + file_log
    result = execute(cmd_ninja, interactive=True)
    timer_end(name_func)
    if result[0]:
        error('Failed to execute command: ' + cmd_ninja)

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def postbuild(force=False):
    if not args.postbuild and not force:
        return

    if repo_type == 'chrome-android':
        dir_out = dir_src + '/out-' + target_arch + '/out'
        dir_chrome = chrome_android_dir_server_root + '/Chrome'
        if target_arch == 'arm':
            target_arch_temp = 'armeabi-v7a'
        else:
            target_arch_temp = target_arch
        dir_chrome_lib = dir_chrome + '/lib/%s' % target_arch_temp

        # unpack
        execute('java -jar %s/apktool.jar d %s/Chrome.apk -o %s' % (dir_tool, chrome_android_dir_server_root, dir_chrome), interactive=True, abort=True)
        # rename
        execute('python %s/prebuilt-%s/change_chromium_package.py -u %s' % (dir_src, target_arch, dir_chrome), interactive=True, abort=True)

        # replace libchrome(view).so
        result = execute('ls %s/libchrome*.so' % dir_chrome_lib, return_output=True)
        file_chrome = result[1].split('/')[-1].strip('\n')
        backup_dir(dir_out + '/Release/lib')
        ## backup the one with symbol
        execute('cp -f lib*prebuilt.so %s/%s' % (chrome_android_dir_server_root, file_chrome), interactive=True, abort=True, dryrun=False)
        ## copy, strip and replace
        execute('cp -f lib*prebuilt.so %s' % (file_chrome), interactive=True, abort=True, dryrun=False)
        execute(dir_tool + '/' + target_arch_strip[target_arch] + ' ' + file_chrome, abort=True, dryrun=False)
        execute('cp -f %s %s/' % (file_chrome, dir_chrome_lib), interactive=True, abort=True)
        restore_dir()

        # replace libpeerconnection.so
        cmd = 'cp -f %s/prebuilt-%s/libpeerconnection_prebuilt.so %s/libpeerconnection.so' % (dir_src, target_arch, dir_chrome_lib)
        execute(cmd, interactive=True, abort=True)

        # repackage the new chromium.apk
        # --zipalign: can be found in SDK
        backup_dir(chrome_android_dir_server_root)
        execute('java -jar %s/apktool.jar b Chrome -o Chromium_unaligned.apk' % dir_tool, interactive=True, abort=True)
        execute('jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore %s/debug.keystore -storepass android Chromium_unaligned.apk androiddebugkey' % dir_tool, interactive=True, abort=True)
        execute('%s/zipalign -f -v 4 Chromium_unaligned.apk Chromium.apk' % dir_tool, interactive=True, abort=True)
        execute('rm -f Chromium_unaligned.apk', abort=True)
        restore_dir()

        _update_phase(get_caller_name())


def verify(force=False):
    if not args.verify and not force:
        return

    if repo_type == 'chrome-android':
        #_chrome_android_get_info(target_arch, chrome_android_dir_server_root + '/Chromium.apk', bypass=True)
        _update_phase(get_caller_name())


def backup(force=False):
    if not args.backup and not force:
        return

    if repo_type == 'chrome-android':
        if host_name == 'wp-03':
            dir_chrome = 'chromium/android-%s-chrome/%s-%s' % (target_arch, ver, ver_type)
            execute('smbclient %s -N -c "prompt; recurse; mkdir %s;"' % (path_server_backup, dir_chrome))
            backup_dir(chrome_android_dir_server_root)
            if os.path.exists('Chrome.apk'):
                backup_smb(path_server_backup, dir_chrome, 'Chrome.apk')
                backup_smb(path_server_backup, dir_chrome, 'Chromium.apk')
                backup_smb(path_server_backup, dir_chrome, 'README')
            else:
                backup_smb(path_server_backup, dir_chrome, 'Null.apk')
            restore_dir()

        _update_phase(get_caller_name())


def notify(force=False):
    if not args.notify and not force:
        return

    if repo_type == 'chrome-android':
        content = '''
Browser Team is excited to announce the %s %s release of Chrome %s for Android has been prepared for you at %s/android-%s-chrome/%s-%s. Enjoy it!
        ''' % (target_arch, ver_type, ver, path_web_chromium, target_arch, ver, ver_type)
        send_mail('webperf@intel.com', 'yang.gu@intel.com', 'Chrome for Android New Release', content, type='html')

        _update_phase(get_caller_name())
        execute('mv %s %s/android-%s-chrome/%s-%s' % (chrome_android_dir_server_root, dir_server_chromium, target_arch, ver, ver_type))


def phase_continue():
    if not args.phase_continue:
        return

    if repo_type == 'chrome-android':
        if not os.path.exists(chrome_android_file_readme):
            error('Could not find README ' + chrome_android_file_readme)

        phase = _chrome_android_get_phase()
        if phase == '':
            error('Could not find correct phase')

        while True:
            phase_next = chrome_android_phase_all[chrome_android_phase_all.index(phase) + 1]
            info('Begin to run phase ' + phase_next)
            globals()[phase_next](force=True)
            if phase_next == chrome_android_phase_all[-1]:
                return
            phase_new = _chrome_android_get_phase()
            if phase == phase_new:
                error('phase %s has not changed its phase' % phase_next)
            phase = phase_new


def run():
    if not args.run:
        return()

    if target_os == 'linux':
        option = ' --flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + dir_root + '/user-data'

        if args.run_GPU:
            option += ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

        if args.run_debug_renderer:
            if build_type == 'release':
                warning('Debugger should run with debug version. Switch to it automatically')
            option = option + ' --renderer-cmd-prefix="xterm -title renderer -e gdb --args"'

        cmd = dir_out_build_type + '/chrome ' + option
    else:
        cmd = dir_src + '/build/android/adb_run_content_shell'

    if args.run_option:
        cmd += ' ' + args.run_option

    execute(cmd)


def owner():
    if not args.owner:
        return()

    backup_dir(dir_src)
    files = commands.getoutput('git diff --name-only HEAD origin/master').split('\n')
    owner_file_map = {}  # map from OWNERS file to list of modified files
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

    restore_dir()


def layout():
    if not args.layout:
        return()

    backup_dir(dir_src + '/out/Release')
    if os.path.isdir('content_shell'):
        execute('rm -rf content_shell_dir')
        execute('mv content_shell content_shell_dir')
    restore_dir()

    backup_dir(dir_src)
    execute('ninja -C out/Release content_shell')
    execute('webkit/tools/layout_tests/run_webkit_tests.sh ' + args.layout_test)
    restore_dir()


def test_build(force=False):
    if not args.test_build and not force:
        return

    name_func = get_caller_name()
    timer_start(name_func)

    results = {}
    for command in test_suite:
        results[command] = []
        # test command specific build
        _test_build_name(command, 'md5sum forwarder2')

        for suite in test_suite[command]:
            if command == 'gtest':
                if suite in ['breakpad_unittests', 'sandbox_linux_unittests']:
                    name = suite + '_stripped'
                else:
                    name = suite + '_apk'
            elif command == 'instrumentation':
                if suite == 'ContentShellTest':
                    name = 'content_shell_apk content_shell_test_apk'
                elif suite == 'ChromeShellTest':
                    name = 'chrome_shell_apk chrome_shell_test_apk'
                elif suite == 'AndroidWebViewTest':
                    name = 'android_webview_apk android_webview_test_apk'
                elif suite == 'MojoTest':
                    name = 'mojo_test_apk'

            result = _test_build_name(command, name)
            if result:
                info('Succeeded to build ' + suite)
                results[command].append('PASS')
            else:
                error('Failed to build ' + suite, abort=False)
                results[command].append('FAIL')

    timer_end(name_func)

    return results


def test_run(force=False):
    if not args.test_run and not force:
        return

    if not os.path.exists(dir_test):
        os.mkdir(dir_test)

    number_device = len(devices)
    if number_device < 1:
        error('Please ensure test device is connected')

    # Build test
    if args.test_drybuild:
        results = {}
        for command in test_suite:
            results[command] = []
            for suite in test_suite[command]:
                results[command].append('PASS')
    else:
        results = test_build(force=True)

    pool = Pool(processes=number_device)
    for index, device in enumerate(devices):
        pool.apply_async(_test_run_device, (index, results))
    pool.close()
    pool.join()


def analyze():
    if not args.analyze:
        return

    analyze_issue(dir_chromium=dir_root, arch='x86_64', date=20140624)


########## Internal function begin ##########
def _test_build_name(command, name):
    cmd = 'ninja -j' + number_cpu + ' -C ' + dir_out_build_type + ' ' + name
    result = execute(cmd, interactive=True)
    if result[0]:
        return False
    else:
        return True


def _test_run_device(index_device, results):
    timer_start('test_run_' + str(index_device))

    device = devices[index_device]
    device_name = devices_name[index_device]
    device_type = devices_type[index_device]
    dir_test_device_name = dir_test_timestamp + '-' + device_name

    connect_device(device)

    if not os.path.exists(dir_test_device_name):
        os.mkdir(dir_test_device_name)

    if not args.test_dryrun:
        # Ensure screen stays on
        execute(adb(cmd='shell svc power stayon usb', device=device))

        # Try to unlock the screen if needed
        execute(adb(cmd='shell input keyevent 82', device=device))

        # Fake /storage/emulated/0
        cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount', device=device) + ' && ' + adb(cmd='shell "mount -o rw,remount rootfs / && chmod 777 /mnt/sdcard && cd /storage/emulated && ln -s legacy 0"', device=device)
        result = execute(cmd)
        if result[0]:
            error('Failed to fake /storage/emulated/0, which is critical for test')
        for command in test_suite:
            for index, suite in enumerate(test_suite[command]):
                if results[command][index] == 'FAIL':
                    continue

                if command == 'instrumentation':
                    # Install packages before running
                    if suite == 'ContentShellTest':
                        apks = ['org.chromium.content_shell_apk', 'ContentShell.apk']
                    elif suite == 'ChromeShellTest':
                        apks = ['org.chromium.chrome.shell', 'ChromeShell.apk']
                    elif suite == 'AndroidWebViewTest':
                        apks = ['org.chromium.android_webview.shell', 'AndroidWebView.apk']
                    elif suite == 'MojoTest':
                        apks = []

                    if apks:
                        _install_apk(device=device, apks=apks, force=True)

                    # push test data
                    #cmd = adb(cmd='push ', device=device)

                    #if suite == 'ContentShellTest':
                    #    cmd += 'src/content/test/data/android/device_files /storage/emulated/0/content/test/data'
                    #elif suite == 'ChromeShellTest':
                    #    cmd += 'src/chrome/test/data/android/device_files /storage/emulated/0/chrome/test/data'
                    #if suite == 'AndroidWebViewTest':
                    #    cmd += 'src/android_webview/test/data/device_files /storage/emulated/0/chrome/test/data/webview'

                    #execute(cmd)

                if args.just_out:
                    cmd = ''
                else:
                    cmd = 'CHROMIUM_OUT_DIR=out-' + target_arch + '/out '

                cmd += dir_src + '/build/android/test_runner.py ' + command

                if command == 'gtest':
                    cmd += ' -s ' + suite
                elif command == 'instrumentation':
                    cmd += ' --test-apk ' + suite

                if args.test_debug:
                    if command == 'gtest':
                        cmd += ' -a --wait-for-debugger'
                    elif command == 'instrumentation':
                        cmd += ' -w'

                if command == 'gtest':
                    if args.test_debug:
                        cmd += ' -t 600'
                    else:
                        cmd += ' -t 60'

                if suite == 'ContentShellTest':
                    cmd += ' --test_data content:content/test/data/android/device_files'
                elif suite == 'ChromeShellTest':
                    cmd += ' --test_data chrome:chrome/test/data/android/device_files'  # --host-driven-root?
                elif suite == 'AndroidWebViewTest':
                    cmd += ' --test_data webview:android_webview/test/data/device_files'
                elif suite == 'MojoTest':
                    cmd += ''

                cmd += ' --num_retries 1'

                if args.test_filter:
                    test_filter_str = args.test_filter
                else:
                    (test_filter_str, count_test_filter) = _calc_test_filter(device_type, target_arch, suite)
                if test_filter_str != '*':
                    cmd += ' -f "' + test_filter_str + '"'
                # Below is needed to make sure our filter can work together with Google filter
                if command == 'instrumentation':
                    cmd += ' -A Smoke,SmallTest,MediumTest,LargeTest,EnormousTest'
                cmd += ' -d ' + device + ' --' + build_type
                if args.test_verbose:
                    cmd += ' -v'
                cmd += ' 2>&1 | tee ' + dir_test_device_name + '/' + suite + '.log'
                result = execute(cmd, interactive=True)
                if result[0]:
                    warning('Failed to run "' + suite + '"')
                else:
                    info('Succeeded to run "' + suite + '"')

    timer_end('test_run_' + str(index_device))
    # Generate report
    html = _test_gen_report(index_device, results)
    file_html = dir_test_device_name + '/report.html'
    file_report = open(file_html, 'w')
    file_report.write(html)
    file_report.close()

    if args.test_formal:
        # Backup
        backup_dir(dir_test)
        backup_smb('//wp-03.sh.intel.com/chromium-x64', 'test', timestamp + '-' + device_name)
        restore_dir()

        # Send mail
        _test_sendmail(index_device, html)


def _test_sendmail(index_device, html):
    report_name = 'Chromium Tests Report'
    device_name = devices_name[index_device]
    if args.test_to:
        to = args.test_to.split(',')
    else:
        to = 'webperf@intel.com'

    send_mail('webperf@intel.com', to, report_name + '-' + timestamp + '-' + device_name, html, type='html')


def _test_gen_report(index_device, results):
    device = devices[index_device]
    device_name = devices_name[index_device]
    device_type = devices_type[index_device]
    dir_test_device_name = dir_test_timestamp + '-' + device_name

    html_start = '''
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=windows-1252">
    <style type="text/css">
      table {
        border: 2px solid black;
        border-collapse: collapse;
        border-spacing: 0;
        text-align: center;
      }

      table tr td {
        border: 1px solid black;
      }
    </style>
  </head>
  <body>
    <div id="main">
      <div id="content">
        <div>
          <h2 id="Environment">Environment</h2>
          <ul>
            <li>Chromium Revision: ''' + str(rev) + '''</li>
            <li>Target Device: ''' + device_name + '''</li>
            <li>Target Image: ''' + android_get_info(key='ro.build.display.id', device=device) + '''</li>
            <li>Build Duration: ''' + timer_diff('build') + '''</li>
            <li>Test Build Duration: ''' + timer_diff('test_build') + '''</li>
            <li>Test Run Duration: ''' + timer_diff('test_run_' + str(index_device)) + '''</li>
          </ul>

          <h2>Details</h2>
    '''

    html_end = '''
          <h2>Log</h2>
          <ul>
            <li>http://wp-03.sh.intel.com/chromium-x64/test/''' + timestamp + '-' + device_name + '''</li>
          </ul>
        </div>
      </div>
    </div>
  </body>
</html>
    '''

    html = html_start
    for command in test_suite:
        html += '''
     <h3>%s</h3>
        ''' % command

        html += '''
      <table>
        <tbody>
          <tr>
            <td> <strong>Test Case Category</strong>  </td>
            <td> <strong>Build Status</strong>  </td>
            <td> <strong>Run Status</strong>  </td>
            <td> <strong>All</strong> </td>
            <td> <strong>Pass</strong> </td>
            <td> <strong>Skip</strong> </td>
            <td> <strong>Fail</strong> </td>
          </tr>
        '''

        for index, suite in enumerate(test_suite[command]):
            bs = results[command][index]
            suite_log = dir_test_device_name + '/' + suite + '.log'
            ut_all = '0'
            ut_pass = '0'
            ut_fail = '0'

            if bs == 'FAIL' or not os.path.exists(suite_log):
                rs = 'FAIL'
            else:
                ut_result = open(dir_test_device_name + '/' + suite + '.log', 'r')
                lines = ut_result.readlines()
                pattern_all = '\[==========\] (\d*) test'
                pattern_pass = '\[  PASSED  \] (\d*) test'
                pattern_fail = '\[  FAILED  \] (\d*) test'
                need_skip = True
                for line in lines:
                    if need_skip and re.search('Main  Summary', line):
                        need_skip = False
                    if need_skip:
                        continue

                    match = re.search(pattern_all, line)
                    if match:
                        ut_all = match.group(1)
                        continue

                    match = re.search(pattern_pass, line)
                    if match:
                        ut_pass = match.group(1)
                        continue

                    match = re.search(pattern_fail, line)
                    if match:
                        ut_fail = match.group(1)
                        continue

            if int(ut_all) == int(ut_pass):
                rs = 'PASS'
            else:
                rs = 'FAIL'

            (test_filter_str, count_test_filter) = _calc_test_filter(device_type, target_arch, suite)
            if count_test_filter > 0:
                ut_all = str(int(ut_all) + count_test_filter)

            ut_skip = str(count_test_filter)

            # Generate the html
            ut_tr_start = '''<tr>'''
            ut_bs_td_start = '''<td>'''
            ut_rs_td_start = '''<td>'''
            ut_td_end = '''</td>'''

            if bs == 'PASS':
                ut_bs_td_start = '''<td style='color:green'>'''
                if rs == 'PASS':
                    ut_tr_start = '''<tr style='color:green'>'''
                elif rs == 'FAIL':
                    ut_rs_td_start = '''<td style='color:red'>'''
            elif bs == 'FAIL':
                ut_bs_td_start = '''<td style='color:red'>'''

            ut_row = ut_tr_start + '''
                         <td> <strong>''' + suite + ''' <strong></td> ''' + ut_bs_td_start + bs + ut_td_end + ut_rs_td_start + rs + ut_td_end + '''
                         <td>''' + ut_all + '''</td>
                         <td>''' + ut_pass + '''</td>
                         <td>''' + ut_skip + '''</td>
                         <td>''' + ut_fail + '''</td></tr>'''
            html += ut_row
        html += '''
        </tbody>
      </table>
        '''

    html += html_end
    return html


def _hack_app_process():
    for device in devices:
        if not execute_adb_shell("test -d /system/lib64", device=device):
            continue

        for file in ['am', 'pm']:
            execute(adb('pull /system/bin/' + file + ' /tmp/' + file))
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount') + ' && ' + adb(cmd='push /tmp/' + file + ' /system/bin/')
                execute(cmd)


def _setup_list(var):
    if var in args_dict and args_dict[var]:
        if args_dict[var] == 'all':
            list_temp = eval(var + '_default')
        else:
            list_temp = eval('args.' + var).split(',')
    else:
        if (var + '_default') in globals():
            list_temp = eval(var + '_default')
        else:
            list_temp = []
    return list_temp


def _run_gclient(cmd_type):
    cmd = 'gclient ' + cmd_type
    if cmd_type != 'runhooks' and cmd_type != 'fetch':
        cmd += ' -n'
    cmd += ' -j' + number_cpu

    if repo_type == 'chrome-android' and cmd_type == 'runhooks' and ver_ge(ver_envsetup, ver):
        cmd = 'source src/build/android/envsetup.sh --target-arch=' + target_arch + ' && ' + cmd

    if re.search('source', cmd):
        cmd = bashify(cmd)
    result = execute(cmd, interactive=True)
    if result[0]:
        error('Failed to execute cmd: ' + cmd)


def _has_dir_out_build_type():
    if not os.path.exists(dir_out_build_type):
        warning(dir_out_build_type + ' directory doesn\'t exist. Will create the directory for you and perform a clean build')
        os.makedirs(dir_out_build_type)
        return False

    return True


def _get_filter_count():
    if test_filter[0:3] == '*:-':
        filters = test_filter.split(':')
        return len(filters) - 1
    else:
        return 0


def _need_device():
    if args.test_run:
        return True

    return False


def _calc_test_filter(device_type, target_arch, suite):
    filter_temp = []

    if suite in test_filter[(device_type, target_arch)]:
        filter_temp += test_filter[(device_type, target_arch)][suite]

    if suite in test_filter[(device_type, 'all')]:
        filter_temp += test_filter[(device_type, 'all')][suite]

    if suite in test_filter[('all', target_arch)]:
        filter_temp += test_filter[('all', target_arch)][suite]

    if suite in test_filter[('all', 'all')]:
        filter_temp += test_filter[('all', 'all')][suite]

    count_test_filter = len(filter_temp)

    if count_test_filter > 0:
        test_filter_str = '*:-' + ':'.join(filter_temp)
    else:
        test_filter_str = '*'

    return (test_filter_str, count_test_filter)


def _get_hash():
    if rev == REV_MAX:
        error('_get_hash should not be called for REV_MAX')

    backup_dir(dir_src)
    hash_temp = _get_hash_one()
    if hash_temp != 0:
        return hash_temp

    execute('git fetch')
    hash_temp = _get_hash_one()
    restore_dir()
    if hash_temp != 0:
        return hash_temp

    error('Could not find hash for revision ' + str(rev))


# Return 0 if failed to find
def _get_hash_one():
    execute('git log origin master >git_log')
    f = open('git_log')
    lines = f.readlines()
    f.close()

    pattern_hash = re.compile('^commit (.*)')
    pattern_rev = re.compile('git-svn-id: .*@(.*) (.*)')
    for line in lines:
        match = pattern_hash.search(line)
        if match:
            hash_temp = match.group(1)
            continue

        match = pattern_rev.search(line)
        if match:
            rev_temp = int(match.group(1))
            if rev_temp == rev:
                return hash_temp
            elif rev_temp < rev:
                return 0


def _install_apk(device, apks, force=False):
    if not args.install and not force:
        return

    if not target_os == 'android':
        return

    cmd = 'python %s/build/android/adb_install_apk.py --apk_package %s --%s' % (dir_src, ' '.join(apks), build_type)
    if not args.just_out:
        cmd = 'CHROMIUM_OUT_DIR=out-' + target_arch + '/out ' + cmd
    if device != '':
        cmd += ' -d ' + device
    result = execute(cmd, interactive=True)

    if result[0]:
        error('Failed to install packages')


def _get_soname():
    if not repo_type == 'chrome-android':
        soname = ''
    else:
        dir_prebuilt = '%s/prebuilt-%s' % (dir_src, target_arch)
        result = execute('ls %s/*.gyp' % dir_prebuilt, return_output=True)
        if result[0] == 0:
            file_gyp = result[1].split('/')[-1].strip('\n')
            pattern = re.compile('(.*)_target')
            match = pattern.search(file_gyp)
            soname = match.group(1)
        else:
            soname = ''

    return soname


def _chrome_android_get_readme_info(key):
    f = open(chrome_android_file_readme)
    lines = f.readlines()
    f.close()
    value = ''
    pattern = re.compile(key + '=(.*)')
    for line in lines:
        match = pattern.search(line)
        if match:
            value = match.group(1)
            break

    return value


def _chrome_android_get_build_id():
    return _chrome_android_get_readme_info('build-id')


def _chrome_android_get_phase():
    return _chrome_android_get_readme_info('phase')


def _chrome_android_get_info(target_arch, file_apk, bypass=False):
    from selenium import webdriver
    from selenium.webdriver.support.wait import WebDriverWait

    target_arch_device = _get_target_arch_device()
    if target_arch not in target_arch_device:
        android_start_emu(target_arch)
        target_arch_device = _get_target_arch_device()
    if not target_arch in target_arch_device:
        error('Failed to get device for target arch ' + target_arch)

    device = target_arch_device[target_arch]
    info('Use device %s with target_arch %s' % (device, target_arch))
    android_unlock_screen(device)
    chrome_android_cleanup(device)

    execute(adb(cmd='install -r "%s"' % file_apk, device=device), interactive=True, dryrun=False)
    ver_type_temp = chrome_android_get_ver_type(device)
    if ver_type_temp == '':
        error('Failed to install package')

    if bypass:
        ver_temp = ''
        build_id_temp = ''
        execute_adb_shell(cmd='am start -n %s/%s -d "chrome://version"' % (chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG], chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_ACT]), device=device)
    else:
        #The following code does not work for com.example.chromium as webdriver.Remote() would hang.
        #adb shell input tap 400 1040
        #adb shell input tap 400 1070
        if has_process('chromedriver'):
            execute('sudo killall chromedriver', show_command=False)
        subprocess.Popen(dir_tool + '/chromedriver', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)  # Sleep a bit to make sure driver is ready
        env_http_proxy = getenv('http_proxy')
        unsetenv('http_proxy')
        capabilities = {
            'chromeOptions': {
                'androidPackage': chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG],
                'androidDeviceSerial': device,
            }
        }
        activity = chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_ACT]
        if not activity == '':
            capabilities['chromeOptions']['androidActivity'] = activity
        driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)
        driver.get('chrome://version')
        WebDriverWait(driver, 30, 1).until(_has_element_ver)
        pattern_version = re.compile('(Chrome|Chrome Beta|Example Chromium) (\d+\.\d+\.\d+\.\d+)')
        match = pattern_version.search(driver.find_elements_by_class_name('version')[0].get_attribute('innerText'))
        ver_type_str = match.group(1)
        if ver_type_str == 'Chrome':
            ver_type_temp = 'stable'
        elif ver_type_str == 'Chrome Beta':
            ver_type_temp = 'beta'
        elif ver_type_str == 'Example Chromium':
            ver_type_temp = 'example'
        ver_temp = match.group(2)
        pattern_build_id = re.compile('Build ID\s+(.*)')
        match = pattern_build_id.search(driver.find_elements_by_id('build-id-section')[0].get_attribute('innerText'))
        build_id_temp = match.group(1)
        driver.quit()
        setenv('http_proxy', env_http_proxy)
    execute(adb('uninstall ' + chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG], device=device))

    return (ver_temp, ver_type_temp, build_id_temp)


def _update_phase(phase):
    pattern = re.compile('phase=(.*)')
    for line in fileinput.input(chrome_android_file_readme, inplace=1):
        match= pattern.search(line)
        if match:
            phase_old = match.group(1)
            if chrome_android_phase_all.index(phase_old) + 1 != chrome_android_phase_all.index(phase):
                error('Phase can not be set discontinuously')
            line = 'phase=' + phase + '\n'
        sys.stdout.write(line)


# get one device for each target_arch
def _get_target_arch_device():
    (devices, devices_name, devices_type, devices_target_arch) = setup_device()
    target_arch_device = {}
    for index, device in enumerate(devices):
        target_arch_temp = devices_target_arch[index]
        if not target_arch_temp in target_arch_device:
            target_arch_device[target_arch_temp] = devices[index]

    return target_arch_device


def _has_element_ver(driver):
    if driver.find_elements_by_class_name('version'):
        return True
    else:
        return False
########## Internal function end ##########


if __name__ == '__main__':
    parse_arg()
    setup()
    buildid()
    init()
    # gclient
    revert()
    fetch()
    sync()
    runhooks()
    # basic
    patch()
    prebuild()
    makefile()
    build()
    postbuild()
    verify()
    backup()
    notify()
    phase_continue()
    run()
    # test
    test_build()
    test_run()
    # misc
    analyze()
    owner()
    layout()
