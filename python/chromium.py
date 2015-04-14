#!/usr/bin/env python

# steps to perf:
# 1. push share/android/tool/perf to target machine /system/bin/perf
# 2. designate perf on host machine
#    /workspace/project/linux-kernel/3.19.2/tools/perf/perf and /usr/bin/perf are similar.
#    We can also use perf from aosp /workspace/project/aosp-gminl/out/host/linux-x86/bin/perfhost


import fileinput
from multiprocessing import Pool
from util import *

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
dir_out_relative = ''  # out-x86
dir_out_build_type = ''  # /workspace/project/chromium-android/src/out-x86/Release
dir_test_timestamp = ''  # /workspace/project/chromium-android/test

name_file = sys._getframe().f_code.co_filename

devices_id = []
devices_product = []
devices_type = []
devices_arch = []
devices_mode = []

# <contrib>
cmd_git_log = 'git log --since 2012-01-01'
str_commit = 'commit (.*)'
authors = ['yang.gu@intel.com', 'yunchao.he@intel.com', 'qiankun.miao@intel.com']
MAX_LEN_REV = 6
# all vers that are roll
repo_rollset = {}
# all info about roll
# chromium_rev, repo_name, chromium_author, chromium_date, chromium_subject, chromium_hash, hash_start, hash_end
repo_rolls = {}
# rolls and our contribution
# author, date, subject, hash
repo_commits = {}
REPO_COMMIT_INDEX_AUTHOR = 0
REPO_COMMIT_INDEX_DATE = 1
REPO_COMMIT_INDEX_SUBJECT = 2
REPO_COMMIT_INDEX_HASH = 3
REPO_COMMIT_INDEX_REV = 4
# our contribution with roll info
# chromium: 0-5
# other: chromium_rev, repo_name, chromium_author, chromium_date, chromium_subject, chromium_hash, repo_author, repo_date, repo_subject, repo_hash, repo_rev
contribs = []
CONTRIB_INDEX_CHROMIUM_REV = 0
CONTRIB_INDEX_REPO_NAME = 1
CONTRIB_INDEX_DIRECTION = 2
CONTRIB_INDEX_CHROMIUM_AUTHOR = 3
CONTRIB_INDEX_CHROMIUM_DATE = 4
CONTRIB_INDEX_CHROMIUM_SUBJECT = 5
CONTRIB_INDEX_CHROMIUM_HASH = 6
CONTRIB_INDEX_REPO_AUTHOR = 7
CONTRIB_INDEX_REPO_DATE = 8
CONTRIB_INDEX_REPO_SUBJECT = 9
CONTRIB_INDEX_REPO_HASH = 10
CONTRIB_INDEX_REPO_REV = 11

repo_path = {
    'webkit': 'third_party/WebKit',
    'skia': 'third_party/skia',
}
# </contrib>

# rev related
rev = 0
rev_hash = {}

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

# From this rev, clang becomes default compiler.
rev_clang = 287416

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
chrome_android_phase_all = ['buildid', 'init', 'sync', 'runhooks', 'prebuild', 'patch', 'makefile', 'build', 'postbuild', 'verify', 'backup', 'notify']
ver = ''
ver_type = ''
chrome_android_soname = ''
dir_server_chrome_android_todo_comb = ''
chrome_android_file_readme = ''

test_command_default = [
    'gtest',
    'instrumentation',
    #'linker',
    #'uiautomator',
    #'monkey',
    #'perf'
]

gtest_suite_default = []
# instrumentation_suite_default:
# Use the description key directly as below.
#   { test_apk : {target, name, apk, apk_package, test_apk, test_data, isolate_file_path, host_driven_root, ...} }
instrumentation_suite_default = {}

test_suite = {}

repo_type_info = {
    'default': {
        'rev': chromium_rev_max,
        'dir_patches': dir_share_python,
        'patches': {},
        # (device_type, target_arch): {}
        # device_type can be 'baytrail', 'generic'
        'test_filter': {},
    },
    'feature': {
        'dir_patches': dir_share_python + '/chromium-patches',
        'patches': {
            'src': [
                #'0001-Enlarge-kThreadLocalStorageSize-to-satisfy-test.patch',
            ],
        },
        'test_filter': {
            ('all', 'all'): {},
            ('all', 'x86_64'): {},
            ('all', 'x86'): {},
            ('baytrail', 'all'): {
                'base_unittests': [
                    # Child process can not be terminated correctly.
                    # This seems not due to action_max_timeout() is not enough.
                    # Root cause is unknown.
                    'ProcessUtilTest.GetTerminationStatusCrash',
                ],
                'gl_tests': [
                    # Status: TODO - timeout
                    'GLReadbackTest.ReadPixelsWithPBOAndQuery',
                ],
                'media_unittests': [
                    # Status: TODO
                    'YUVConvertTest.YUVAtoARGB_MMX_MatchReference',
                    'MediaDrmBridgeTest.IsKeySystemSupported_Widevine',
                    'MediaDrmBridgeTest.IsSecurityLevelSupported_Widevine',
                    # regression
                    'MediaSourcePlayerTest.A_StarvationDuringEOSDecode',  # message_loop_.Run();
                    'MediaSourcePlayerTest.DemuxerConfigRequestedIfInPrefetchUnit0',
                    'MediaSourcePlayerTest.DemuxerConfigRequestedIfInPrefetchUnit1',  # decoder not request new data.
                    'MediaSourcePlayerTest.DemuxerConfigRequestedIfInUnit0AfterPrefetch',
                    'MediaSourcePlayerTest.DemuxerConfigRequestedIfInUnit1AfterPrefetch',  # decoder not request new data.
                    'MediaSourcePlayerTest.PrerollContinuesAcrossReleaseAndStart',  # 419122. disable in upstream.
                ],
                'net_unittests': [
                    # Status: TODO
                    'CertNetFetcherImplTest.Cache',  # new added case from #324261. have not confirmed the cause.
                ],
                # content_gl_tests is disabled in upstream
                'content_gl_tests': [
                    # Intel gfx bug related to glReadPixels with format BGRA
                    'GLHelperTest.BGRASyncReadbackTest',
                    'GLHelperTest.BGRAASyncReadbackTest',
                    'GLHelperPixelTest.CropScaleReadbackAndCleanTextureTest',
                ],
                'ContentShellTest': [
                    # Status: TODO
                    'TransitionTest#testTransitionElementsFetched',
                ],
                'AndroidWebViewTest': [
                    # Status: TODO
                    'AwSettingsTest#testZeroLayoutHeightDisablesViewportQuirkWithTwoViews',
                    'KeySystemTest#testSupportPlatformKeySystem',
                    'KeySystemTest#testSupportWidevineKeySystem',
                    'AndroidScrollIntegrationTest#testJsScrollFromBody',
                    'AndroidScrollIntegrationTest#testJsScrollReflectedInUi',
                    'AndroidScrollIntegrationTest#testPinchZoomUpdatesScrollRangeSynchronously',
                    'AwQuotaManagerBridgeTest#testDeleteOriginWithAppCache',  # pass if run alone
                ],
                'ChromeShellTest': [
                    # Status: TODO
                ],
                # MojoTest is disabled in upstream
                'MojoTest': [
                    # TODO
                    'CoreImplTest#testDataPipeCreation',
                    'CoreImplTest#testSharedBufferCreation',
                ]
            },
            ('baytrail', 'x86_64'): {
                'media_unittests': [
                    # can not create Drm Service from system.
                    'MediaDrmBridgeTest.CreateWithoutSessionSupport_Widevine',
                    'MediaDrmBridgeTest.SetSecurityLevel_Widevine',
                ]
            },
            ('baytrail', 'x86'): {
                'AndroidWebViewTest': [
                    # Status: TODO
                    'CommandLineTest#testSetupCommandLine',
                ],
                'ChromeShellTest': [
                    # Status: TODO
                    'InstallerDelegateTest#testRunnableRaceCondition',
                    'DistilledPagePrefsTest#testSingleObserverTheme',
                    'ContextMenuTest#testCopyImageURL',
                ]
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
    parser = argparse.ArgumentParser(description='Script about Chromium',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --revert -s --patch -b
  python %(prog)s --batch-build
  python %(prog)s --batch-build
  python %(prog)s --revert --sync --patch
  python %(prog)s --batch-build --test-run
  python %(prog)s --batch-test
  python %(prog)s --test-dryrun --time-fixed
  python %(prog)s --test-to yang.gu@intel.com --test-case 'webkit_compositor_bindings_unittests' --test-run
  python %(prog)s --instrumentation-suite ContentShellTest --test-run --test-command instrumentation --test-formal --test-to yang.gu@intel.com

  gclient:
  python %(prog)s --revert
  python %(prog)s --fetch
  python %(prog)s --sync --rev 270000
  python %(prog)s --sync --repo_type feature
  python %(prog)s --sync --repo_type feature
  python %(prog)s --runhooks

  build:
  python %(prog)s -b --target-module webview_shell // out/Release/lib/libstandalonelibwebviewchromium.so->Release/android_webview_apk/libs/x86/libstandalonelibwebviewchromium.so
  python %(prog)s -b --target-module chrome

  run:
  python %(prog)s --run --build-type release
  python %(prog)s --run --run-option=--enable-logging=stderr
  python %(prog)s --run --run-option--enable-logging=stderr
  python %(prog)s --run '--run-option --enable-logging=stderr'
  python %(prog)s --run --run-debug-render
  python %(prog)s --run --run-option 'http://browsermark.rightware.com'

  debug & perf:
  python %(prog)s --perf --target-module chrome_shell --process render --perf-second 5 --perf-binary-host /usr/bin/perf

  misc:
  python %(prog)s --owner
  python %(prog)s --backup-test content_gl_tests --time-fixed
  python %(prog)s --run --run-link http://wp-02.sh.intel.com/media/vpx/vpx.html --debug --debug-process render

  chrome-android:
  python %(prog)s --repo-type chrome-android --target-os android --target-module chrome --dir-root /workspace/project/chrome-android/37.0.2062.94 --target-arch x86 --ver 37.0.2062.94 --ver-type beta --phase-continue

  crontab -e
  0 1 * * * cd /workspace/project/chromium64-android && python %(prog)s -s --extra-path=/workspace/project/depot_tools
''')
    group_common = parser.add_argument_group('common')
    group_common.add_argument('--repo-type', dest='repo_type', help='repo type. default for upstream, feature for feature test, chrome-android for "Chrome for Android"', default='default')
    #dir: <arch>-<target-os>/out/<build_type>, example: x86-linux/Release
    group_common.add_argument('--target-os', dest='target_os', help='target os', choices=['android', 'linux'], default='android')
    group_common.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'arm', 'x86_64', 'arm64'], default='x86')
    group_common.add_argument('--target-module', dest='target_module', help='target module to build, choices can be chrome, webview_shell, \
        content_shell, chrome_shell, chromedriver, cpu_features, system_webview_apk, android_webview_telemetry_shell_apk, etc.', default='chrome_shell')
    group_common.add_argument('--device-id', dest='device_id', help='device id list separated by ","', default='')
    group_common.add_argument('--just-out', dest='just_out', help='stick to out, instead of out-x86_64', action='store_true')
    group_common.add_argument('--rev', dest='rev', type=int, help='revision')
    group_common.add_argument('--hash-webkit', dest='hash_webkit', help='hash of webkit')
    group_common.add_argument('--hash-skia', dest='hash_skia', help='hash of skia')
    group_common.add_argument('--ver', dest='ver', help='ver for chrome-android')
    group_common.add_argument('--ver-type', dest='ver_type', help='ver type, stable or beta')
    group_common.add_argument('--chrome-android-apk', dest='chrome_android_apk', help='chrome android apk')
    group_common.add_argument('--phase-end', dest='phase_end', help='phase which running end with')
    group_common.add_argument('--phase-continue', dest='phase_continue', help='run all left phases', action='store_true')
    group_common.add_argument('--build-type', dest='build_type', help='build type', choices=['release', 'debug'], default='release')
    group_common.add_argument('--profile', dest='profile', help='profile by adding profiling=1 into GYP_DEFINES', action='store_true')
    group_common.add_argument('--process', dest='process', help='process, browser, render, gpu', default='browser')
    group_common.add_argument('--debug', dest='debug', help='debug', action='store_true')
    group_common.add_argument('--perf', dest='perf', help='perf', action='store_true')
    group_common.add_argument('--perf-second', dest='perf_second', help='perf second', default='10')
    group_common.add_argument('--perf-binary-host', dest='perf_binary_host', help='perf binary host', default='/usr/bin/perf')
    group_common.add_argument('--perf-arg-host', dest='perf_arg_host', help='perf arg host, can be --stdio, -G', default='')
    group_common.add_argument('--perf-dryrun', dest='perf_dryrun', help='without actual run of perf on target', action='store_true')
    group_common.add_argument('--trace', dest='trace', help='trace', action='store_true')
    group_common.add_argument('--trace-second', dest='trace_second', help='trace second', default='10')

    group_gclient = parser.add_argument_group('gclient')
    group_gclient.add_argument('--revert', dest='revert', help='revert', action='store_true')
    group_gclient.add_argument('--fetch', dest='fetch', help='fetch', action='store_true')
    group_gclient.add_argument('--cleanup', dest='cleanup', help='cleanup', action='store_true')
    group_gclient.add_argument('--sync', dest='sync', help='sync to a specific rev if designated, otherwise, sync to upstream', action='store_true')
    # -f has similar capability to reset local non-committed changes
    group_gclient.add_argument('--sync-reset', dest='sync_reset', help='sync reset, and reset local changes', action='store_true')
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
    group_basic.add_argument('--build-fail-max', dest='build_fail_max', help='allow n build failures before it stops', type=int, default=1)
    group_basic.add_argument('--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')
    group_basic.add_argument('--build-asan', dest='build_asan', help='enable asan by adding asan=1 into GYP_DEFINES', action='store_true')
    group_basic.add_argument('--postbuild', dest='postbuild', help='postbuild', action='store_true')
    group_basic.add_argument('--verify', dest='verify', help='verify', action='store_true')
    group_basic.add_argument('--backup', dest='backup', help='backup', action='store_true')
    group_basic.add_argument('--notify', dest='notify', help='notify', action='store_true')
    group_basic.add_argument('--install', dest='install', help='install module', action='store_true')
    group_basic.add_argument('--run', dest='run', help='run', action='store_true')
    group_basic.add_argument('--run-link', dest='run_link', help='link to run with', default='')
    group_basic.add_argument('--run-option', dest='run_option', help='option to run')
    group_basic.add_argument('--run-gpu', dest='run_GPU', help='enable GPU acceleration', action='store_true')
    group_basic.add_argument('--run-debug-render', dest='run_debug_render', help='run gdb before render starts', action='store_true')

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
    group_misc.add_argument('--analyze-type', dest='analyze_type', help='type to analyze', choices=['tombstone', 'anr'], default='tombstone')
    group_misc.add_argument('--owner', dest='owner', help='find owner for latest commit', action='store_true')
    group_misc.add_argument('--layout', dest='layout', help='layout test')
    group_misc.add_argument('--backup-test', dest='backup_test', help='backup test, so that bug can be easily reproduced by others')
    group_misc.add_argument('--contrib', dest='contrib', help='upstream contribution', action='store_true')
    group_misc.add_argument('--contrib-norevert', dest='contrib_norevert', help='only keep last roll', action='store_true')
    group_misc.add_argument('--contrib-serialize', dest='contrib_serialize', help='contrib serialize', action='store_true')

    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_src, dir_out_relative, dir_out_build_type, dir_test, dir_test_timestamp
    global target_os, target_arch, target_module
    global test_suite, build_type, rev, dir_patches, patches, test_filter, repo_type
    global ver, ver_type, chrome_android_soname, dir_server_chrome_android_todo_comb, chrome_android_file_readme, chrome_android_apk
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)
    if args.perf or args.trace:
        args.profile = True

    target_arch = args.target_arch
    if not args.target_module:
        if target_os == 'linux':
            target_module = 'chrome'
        elif target_os == 'android':
            target_module = 'webview_shell'
    else:
        target_module = args.target_module

    dir_src = dir_root + '/src'
    build_type = args.build_type
    if args.just_out:
        dir_out_relative = 'out'
    else:
        dir_out_relative = 'out-' + target_arch
        if args.profile:
            dir_out_relative += '-profile'

    dir_out_build_type = dir_src + '/' + dir_out_relative + '/' + build_type.capitalize()

    dir_test = dir_root + '/test'
    dir_test_timestamp = dir_test + '/' + timestamp

    repo_type = args.repo_type

    # set repo_type related global variables
    for key in repo_type_info['default']:
        if repo_type == 'default' or repo_type not in repo_type_info or key not in repo_type_info[repo_type]:
            globals()[key] = repo_type_info['default'][key]
        else:
            globals()[key] = repo_type_info[repo_type][key]

    if repo_type == 'chrome-android':
        rev = 0
    elif args.rev:
        rev = args.rev
    else:
        rev = chromium_rev_max

    for cmd in ['adb', 'git', 'gclient']:
        result = execute('which ' + cmd, show_cmd=False)
        if result[0]:
            error('Could not find ' + cmd + ', and you may use --path-extra to designate it')

    setenv('GYP_GENERATORS', 'ninja')

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

    # repo type specific variables
    if repo_type == 'chrome-android':
        if args.chrome_android_apk:
            chrome_android_apk = args.chrome_android_apk
        else:
            ver = args.ver
            ver_type = args.ver_type
            chrome_android_soname = _get_soname()
            dir_server_chrome_android_todo_comb = dir_server_chrome_android_todo + '/' + target_arch + '/' + ver + '-' + ver_type
            chrome_android_file_readme = dir_server_chrome_android_todo_comb + '/README'

    gyp_defines = ''
    if target_os == 'windows':
        gyp_defines += 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"'
        setenv('GYP_MSVS_VERSION', '2010e')
        setenv('GYP_MSVS_OVERRIDE_PATH', 'd:/user/ygu5/project/chromium/win_toolchain')
        setenv('WDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/WDK')
        setenv('DXSDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/DXSDK')
        setenv('WindowsSDKDir', 'd:/user/ygu5/project/chromium/win_toolchain/win8sdk')
    elif target_os == 'linux':
        gyp_defines += 'werror= disable_nacl=1 component=shared_library enable_svg=0'
        setenv('CHROME_DEVEL_SANDBOX', '/usr/local/sbin/chrome-devel-sandbox')
    elif target_os == 'android':
        if repo_type != 'chrome-android' and rev < rev_envsetup:
            backup_dir(dir_src)
            shell_source('build/android/envsetup.sh --target-arch=' + target_arch, use_bash=True)
            restore_dir()
            if not getenv('ANDROID_SDK_ROOT'):
                error('Environment is not well set')

        if repo_type != 'chrome-android' and rev < rev_gyp_defines or repo_type == 'chrome-android' and not args.chrome_android_apk and ver_cmp(ver, ver_gyp_defines) < 0:
            gyp_defines += 'werror= disable_nacl=1 enable_svg=0'
        else:
            gyp_defines += 'OS=%s werror= disable_nacl=1 enable_svg=0' % target_os

    if args.profile:
        gyp_defines += ' profiling=1'

    if args.build_asan:
        gyp_defines += ' asan=1'

    setenv('GYP_DEFINES', gyp_defines)
    setenv('NO_AUTH_BOTO_CONFIG', dir_share_linux_config + '/boto.conf')

    if args.test_build or args.test_run or args.test_drybuild or args.test_dryrun:
        _get_suite_default()
        # Setup test_suite
        for command in _setup_list('test_command'):
            test_suite[command] = []
            for suite in _setup_list(command + '_suite'):
                test_suite[command].append(suite)


def buildid(force=False):
    global chrome_android_apk
    if not args.buildid and not force:
        return

    if os.path.exists('lib'):
        is_gms = True
    else:
        is_gms = False

    # repack gms apk and lib to google play apk
    if is_gms:
        dir_chromium = 'Chrome2'
        name_apk = 'Chrome2'
        execute('rm -rf %s' % dir_chromium)
        execute('java -jar %s d Chrome.apk -o %s' % (path_share_apktool, dir_chromium), interactive=True, abort=True)
        execute('cp -rf lib %s' % dir_chromium)
        execute('java -jar %s b %s -o %s_unaligned.apk' % (path_share_apktool, name_apk, name_apk), interactive=True, abort=True)
        execute('jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore %s/debug.keystore -storepass android %s_unaligned.apk androiddebugkey' % (dir_share_linux_tool, name_apk), interactive=True, abort=True)
        execute('%s/zipalign -f -v 4 %s_unaligned.apk %s.apk' % (dir_share_linux_tool, name_apk, name_apk), interactive=True, abort=True)
        execute('rm -f %s_unaligned.apk' % name_apk, abort=True)
        chrome_android_apk = name_apk + '.apk'

    # get the target arch
    target_arch_temp = ''
    if is_gms:
        path_lib = 'lib'
    else:
        execute('rm -rf tmp')
        execute('unzip "%s" -d tmp' % chrome_android_apk, show_cmd=True)
        path_lib = 'tmp/lib'
    for key in target_arch_info:
        if os.path.exists(path_lib + '/' + target_arch_info[key][TARGET_ARCH_INFO_INDEX_ABI]):
            target_arch_temp = key
            break
    if not is_gms:
        execute('rm -rf tmp', show_cmd=False)
    if target_arch_temp == '':
        error('Arch is not supported for ' + todo)

    # emulator would behave abnormally after several services. So we just start a new one for each round.
    (result, ver_temp, ver_type_temp, build_id_temp) = _chrome_android_get_info(target_arch_temp, chrome_android_apk)
    info('build id is ' + build_id_temp)
    dir_todo = '%s/%s/%s-%s' % (dir_server_chrome_android_todo, target_arch_temp, ver_temp, ver_type_temp)
    dirs_check = [
        dir_todo,
        '%s/android-%s-chrome/%s-%s' % (dir_server_chromium, target_arch_temp, ver_temp, ver_type_temp),
        '%s/android-%s-chrome/archive/%s-%s' % (dir_server_chromium, target_arch_temp, ver_temp, ver_type_temp),
    ]
    for dir_check in dirs_check:
        if os.path.exists(dir_check):
            if is_gms:
                execute('mv %s ../../trash' % dir_root)
            else:
                execute('mv "%s" ../trash' % chrome_android_apk)
            error('The apk %s/%s-%s has been tracked, so will be moved to trash' % (target_arch_temp, ver_temp, ver_type_temp))

    os.makedirs(dir_todo)
    execute('chmod +r "%s"' % chrome_android_apk)
    if is_gms:
        execute('mv "%s" %s/gms' % (dir_root, dir_todo))
        execute('mv %s/gms/%s.apk %s/Chrome.apk' % (dir_todo, name_apk, dir_todo))
    else:
        execute('mv "%s" %s/Chrome.apk' % (chrome_android_apk, dir_todo))
    execute('echo "phase=buildid\nbuild-id=%s" >%s/README' % (build_id_temp, dir_todo), show_cmd=False)


def init(force=False):
    if not args.init and not force:
        return

    if repo_type == 'chrome-android':
        if ver_cmp(ver, '37.0.2062.117') < 0:
            execute('gclient config https://src.chromium.org/chrome/releases/' + ver, abort=True)
            execute('echo "target_os = [\'android\']" >> .gclient', abort=True)
        _update_phase(get_caller_name())


def cleanup(force=False):
    if not args.cleanup and not force:
        return

    _run_gclient('cleanup')


def fetch(force=False):
    if not args.fetch and not force:
        return

    _run_gclient('fetch')


def revert(force=False):
    if not args.revert and not force:
        return

    _run_gclient('revert')


def runhooks(force=False):
    if not args.runhooks and not force:
        return

    _run_gclient('runhooks')

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def sync(force=False):
    if not args.sync and not force:
        return

    if repo_type == 'chrome-android' and ver_cmp(ver, '37.0.2062.117') >= 0:
        if not os.path.exists(dir_src):
            backup_dir(dir_project_chrome_android + '/chromium-android/src')
            execute('git pull && gclient sync -f -j16 && git fetch --tags', interactive=True, abort=True)
            restore_dir()
            execute('cp -rf %s/chromium-android/. %s' % (dir_project_chrome_android, dir_root), interactive=True, abort=True)
            backup_dir(dir_src)
            result = execute('git checkout -f -B %s tags/%s && gclient sync --with_branch_heads -j16 -f -n' % (ver, ver), interactive=True, abort=True)
            if result[0]:
                error('Could not check out source code of version %s' % ver)
            restore_dir()
    else:
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

        cmd_extra = ''
        if args.rev:
            hash_temp = chromium_get_rev_hash(dir_src, rev)
            if not hash_temp:
                error('Could not find hash for rev ' + str(rev))
            cmd_extra = '--revision src@' + hash_temp
        _run_gclient(cmd_type='sync', cmd_extra=cmd_extra)
        if args.hash_webkit:
            backup_dir(dir_src + '/third_party/WebKit')
            execute('git reset --hard %s' % args.hash_webkit)
            restore_dir()
        if args.hash_skia:
            backup_dir(dir_src + '/third_party/skia')
            execute('git reset --hard %s' % args.hash_skia)
            restore_dir()

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())


def prebuild(force=False):
    global chrome_android_soname

    if not args.prebuild and not force:
        return

    if repo_type == 'chrome-android':
        build_id = _chrome_android_get_build_id()
        if build_id == '':
            return

        dir_prebuilt = '%s/prebuilt-%s' % (dir_src, target_arch)
        ensure_dir(dir_prebuilt)
        backup_dir(dir_prebuilt)
        cmd = 'wget -c -i http://storage.googleapis.com/chrome-browser-components/' + build_id + '/index.html'
        execute(cmd, interactive=True, abort=True)

        dir_release = dir_src + '/out-' + target_arch + '/Release'
        ensure_dir(dir_release)
        cmd = 'cp *.a ' + dir_release
        execute(cmd, abort=True)

        chrome_android_soname = _get_soname()

        restore_dir()

        _update_phase(get_caller_name())


def patch(force=False):
    global patches, dir_patches
    if not args.patch and not force:
        return

    if repo_type == 'chrome-android':
        dir_patches = dir_share_python + '/chrome-android'
        patches = {}
        if ver_cmp(ver, '38') > 0 and ver_cmp(ver, '39') < 0:
            patches['src'] = ['0001-Fix-spdy-crash.patch']

    apply_patch(patches, dir_patches)

    if repo_type == 'chrome-android':
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
            if ver_cmp(ver, ver_no_android_gyp) < 0:
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
        cmd += ' -Goutput_dir=%s' % dir_out_relative

    if re.search('source', cmd):
        cmd = bashify_cmd(cmd)
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
    print 'GYP_DEFINES: ' + getenv('GYP_DEFINES')
    print 'Host OS: ' + host_os
    print 'Target OS: ' + target_os.capitalize()
    print '======================='

    if repo_type != 'chrome-android' and rev >= rev_clang and not os.path.exists('src/third_party/llvm-build'):
        info('From revision %s, llvm is used for build. Now will download it for you.' % rev_clang)
        execute('src/tools/clang/scripts/update.sh')

    name_func = get_caller_name()
    timer_start(name_func)

    if need_makefile:
        makefile(force=True)

    cmd_ninja = 'ninja -k' + str(build_fail_max) + ' -j' + str(count_cpu_build) + ' -C ' + dir_out_build_type
    if target_os == 'android' and target_module == 'webview_shell':
        cmd_ninja += ' android_webview_apk libwebviewchromium'
    elif target_os == 'android' and target_module == 'content_shell':
        cmd_ninja += ' content_shell_apk'
    elif target_os == 'android' and target_module == 'chrome_shell':
        cmd_ninja += ' chrome_shell_apk'
    elif target_os == 'android' and target_module == 'chrome':
        if chrome_android_soname == '':
            error('Please download prebuilt first')
        cmd_ninja += ' lib%s_prebuilt' % chrome_android_soname
    else:
        cmd_ninja += ' ' + target_module

    if args.build_verbose:
        cmd_ninja += ' -v'

    result = execute(cmd_ninja, interactive=True, file_log=log)
    timer_stop(name_func)
    if result[0]:
        error('Failed to execute command: ' + cmd_ninja)

    if repo_type == 'chrome-android':
        result = execute('ls %s/lib/lib*prebuilt.so' % dir_out_build_type)
        if result[0]:
            error('Failed to execute build')
        _update_phase(get_caller_name())


def postbuild(force=False):
    if not args.postbuild and not force:
        return

    if repo_type == 'chrome-android':
        # get combs
        combs = []
        if ver_type == 'stable':
            name_app = 'Chromium'
            name_pkg = 'com.android.chromium'
        else:
            name_app = 'Chromium Beta'
            name_pkg = 'com.chromium.beta'
        combs.append([name_app, name_pkg, 'Chromium'])

        # align package name with Google
        if ver_type == 'stable':
            name_app = 'Chromium2'
            name_pkg = 'com.android.chrome'
        else:
            name_app = 'Chromium2 Beta'
            name_pkg = 'com.chrome.beta'
        combs.append([name_app, name_pkg, 'Chromium2'])

        # get target_arch_temp for directory name that holds libchrome
        if target_arch == 'arm':
            target_arch_temp = 'armeabi-v7a'
        else:
            target_arch_temp = target_arch

        for line in fileinput.input('%s/prebuilt-%s/change_chromium_package.py' % (dir_src, target_arch), inplace=1):
            # hack the script to allow same package name with Google
            if re.search('\'com.android.chrome\'', line) and line.lstrip()[0] != '#':
                line = line.replace('\'com.android.chrome\'', '#\'com.android.chrome\'')
            elif re.search('\'com.chrome.beta\'', line) and line.lstrip()[0] != '#':
                line = line.replace('\'com.chrome.beta\'', '#\'com.chrome.beta\'')

            # "snapshot" can not be found in latest AndroidManifest.xml. Just ignore it here.
            # Note that we rely on later script to change all the authorities in AndroidManifest.xml,
            # so we don't need to add others here.
            elif re.search('android:authorities="\%\(package\)s.snapshot', line) and line.lstrip()[0] != '#':
                line = '#' + line
            sys.stdout.write(line)

        for comb in combs:
            name_app = comb[0]
            name_pkg = comb[1]
            name_apk = comb[2]

            dir_chromium = '%s/%s' % (dir_server_chrome_android_todo_comb, name_apk)
            dir_chromium_lib = dir_chromium + '/lib/%s' % target_arch_temp

            # unpack
            execute('rm -rf %s' % dir_chromium)
            execute('java -jar %s d %s/Chrome.apk -o %s' % (path_share_apktool, dir_server_chrome_android_todo_comb, dir_chromium), interactive=True, abort=True)

            # replace libchrome(view).so
            ## get the name
            result = execute('ls -r -S %s/libchrome*.so' % dir_chromium_lib, return_output=True)
            file_libchrome = result[1].split('/')[-1].strip('\n')
            backup_dir(dir_out_build_type + '/lib')
            ## backup the one with symbol, which should be done only once
            path_file_libchrome = '%s/%s' % (dir_server_chrome_android_todo_comb, file_libchrome)
            result = execute('ls lib*prebuilt.so', return_output=True)
            file_libchrome_prebuilt = result[1].split('/')[-1].strip('\n')
            # backup the file with symbol
            if not is_same_file(file_libchrome_prebuilt, path_file_libchrome):
                execute('cp -f %s %s' % (file_libchrome_prebuilt, path_file_libchrome), interactive=True, abort=True, dryrun=False)
                execute(dir_share_linux_tool + '/' + target_arch_strip[target_arch] + ' ' + file_libchrome_prebuilt + ' -o ' + file_libchrome, abort=True, dryrun=False)
            if not os.path.exists(file_libchrome):
                execute(dir_share_linux_tool + '/' + target_arch_strip[target_arch] + ' ' + file_libchrome_prebuilt + ' -o ' + file_libchrome, abort=True, dryrun=False)
            # replace the file without symbol
            execute('cp -f %s %s/%s' % (file_libchrome, dir_chromium_lib, file_libchrome), interactive=True, abort=True)
            restore_dir()

            # replace libpeerconnection.so
            cmd = 'cp -f %s/prebuilt-%s/libpeerconnection_prebuilt.so %s/libpeerconnection.so' % (dir_src, target_arch, dir_chromium_lib)
            execute(cmd, interactive=True, abort=True)

            # change app name and package name to avoid conflict
            # This has to be done before the hack of AndroidManifest.xml
            execute('python %s/prebuilt-%s/change_chromium_package.py -u %s -a %s -p %s' % (dir_src, target_arch, dir_chromium, name_app, name_pkg), interactive=True, abort=True)

            # hack the AndroidManifest.xml to avoid provider conflict, permission conflict
            for line in fileinput.input('%s/AndroidManifest.xml' % dir_chromium, inplace=1):
                for name_pkg_old in ['com.example.chromium', 'com.android.chrome', 'com.chrome.beta']:
                    if re.search(name_pkg_old, line):
                        line = line.replace(name_pkg_old, name_pkg)
                sys.stdout.write(line)

            # repackage the new apk
            # --zipalign: can be found in SDK
            backup_dir(dir_server_chrome_android_todo_comb)
            execute('java -jar %s b %s -o %s_unaligned.apk' % (path_share_apktool, name_apk, name_apk), interactive=True, abort=True)
            execute('jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore %s/debug.keystore -storepass android %s_unaligned.apk androiddebugkey' % (dir_share_linux_tool, name_apk), interactive=True, abort=True)
            execute('%s/zipalign -f -v 4 %s_unaligned.apk %s.apk' % (dir_share_linux_tool, name_apk, name_apk), interactive=True, abort=True)
            execute('rm -f %s_unaligned.apk' % name_apk, abort=True)
            restore_dir()
        _update_phase(get_caller_name())


def verify(force=False):
    if not args.verify and not force:
        return

    if repo_type == 'chrome-android':
        _chrome_android_get_info(target_arch, dir_server_chrome_android_todo_comb + '/Chromium.apk', bypass=True)
        if os.path.exists(dir_server_chrome_android_todo_comb + '/Chromium2.apk'):
            _chrome_android_get_info(target_arch, dir_server_chrome_android_todo_comb + '/Chromium2.apk', bypass=True)
        _update_phase(get_caller_name())


def backup(force=False):
    if not args.backup and not force:
        return

    if repo_type == 'chrome-android':
        if host_name == 'wp-03':
            dir_chrome = 'chromium/android-%s-chrome/%s-%s' % (target_arch, ver, ver_type)
            execute('smbclient %s -N -c "prompt; recurse; mkdir %s;"' % (path_server_backup, dir_chrome))
            backup_dir(dir_server_chrome_android_todo_comb)
            if os.path.exists('Chrome.apk'):
                backup_smb(path_server_backup, dir_chrome, 'Chrome.apk')
                backup_smb(path_server_backup, dir_chrome, 'Chromium.apk')
                if os.path.exists('Chromium2.apk'):
                    backup_smb(path_server_backup, dir_chrome, 'Chromium2.apk')
                backup_smb(path_server_backup, dir_chrome, 'README')
            else:
                backup_smb(path_server_backup, dir_chrome, 'Null.apk')
            restore_dir()

        _update_phase(get_caller_name())


def notify(force=False):
    if not args.notify and not force:
        return

    if repo_type == 'chrome-android':
        _update_phase(get_caller_name())
        dir_server_chrome_android_comb = '%s/android-%s-chrome/%s-%s' % (dir_server_chromium, target_arch, ver, ver_type)
        ensure_nodir(dir_server_chrome_android_comb)
        execute('mv %s %s/android-%s-chrome/%s-%s' % (dir_server_chrome_android_todo_comb, dir_server_chromium, target_arch, ver, ver_type))

        target_arch_done = {}
        all_done = True
        for target_arch_temp in target_arch_chrome_android:
            target_arch_done[target_arch_temp] = os.path.exists('%s/android-%s-chrome/%s-%s' % (dir_server_chromium, target_arch_temp, ver, ver_type))
            if not target_arch_done[target_arch_temp]:
                all_done = False

        if all_done:
            subject = 'Chrome for Android New Release %s-%s' % (ver, ver_type)
            content = 'Browser Team is excited to announce the %s release of Chrome %s for Android has been prepared for you!<br>' % (ver_type, ver)
            for target_arch_temp in target_arch_chrome_android:
                content += '%s version: %s/android-%s-chrome/%s-%s.<br>' % (target_arch_temp, path_web_chrome_android, target_arch_temp, ver, ver_type)
            content += 'Enjoy them!<br>'
        else:
            subject = 'Chrome for Android New Release %s-%s-%s' % (target_arch, ver, ver_type)
            content = 'New Chrome for Android has been prepared at %s/android-%s-chrome/%s-%s.' % (path_web_chrome_android, target_arch, ver, ver_type)
        if host_name == 'wp-03':
            send_mail('webperf@intel.com', ['yang.gu@intel.com', 'zhiqiangx.yu@intel.com'], subject, content, type='html')


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
            if args.phase_end and phase_next == args.phase_end:
                return
            phase_new = _chrome_android_get_phase()
            if phase == phase_new:
                error('phase %s has not changed its phase' % phase_next)
            phase = phase_new


def install():
    if not args.install:
        return

    _setup_device()
    device_id = devices_id[0]

    apk = chromium_android_info[target_module][CHROMIUM_ANDROID_INFO_INDEX_APK]
    _install_apk(apk=apk, device_id=device_id)


def run():
    if not args.run:
        return()

    if target_os == 'linux':
        option = ' --flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + dir_root + '/user-data'

        if args.run_GPU:
            option += ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

        if args.run_debug_render:
            if build_type == 'release':
                warning('Debugger should run with debug version. Switch to it automatically')
            option = option + ' --renderer-cmd-prefix="xterm -title renderer -e gdb --args"'

        cmd = dir_out_build_type + '/chrome ' + option
        if args.run_option:
            cmd += ' ' + args.run_option

        execute(cmd, interactive=True)

    elif target_os == 'android':
        _setup_device()
        device_id = devices_id[0]
        chromium_run_module(device_id=device_id, module_name=target_module, url=args.run_link)


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

    backup_dir(dir_src + '/Release')
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
                name = instrumentation_suite_default[suite]['target']

            result = _test_build_name(command, name)
            if result:
                info('Succeeded to build ' + suite)
                results[command].append('PASS')
            else:
                error('Failed to build ' + suite, abort=False)
                results[command].append('FAIL')

    timer_stop(name_func)

    return results


def test_run(force=False):
    if not args.test_run and not force:
        return

    ensure_dir(dir_test)
    _setup_device()
    number_device = len(devices_id)
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
    for index, device_id in enumerate(devices_id):
        pool.apply_async(_test_run_device, (index, results))
    pool.close()
    pool.join()


def analyze():
    if not args.analyze:
        return

    analyze_issue(dir_chromium=dir_root, type=args.analyze_type, ver='2.0')


def backup_test():
    if not args.backup_test:
        return

    test = args.backup_test
    files_backup = {
        'build/android': [
            'build/android/test_runner.py',
            'build/android/lighttpd_server.py',
            'build/android/pylib',
        ],
        'build': 'build/util',
        'third_party': 'third_party/android_testrunner',
        'third_party/android_tools/sdk/build-tools/20.0.0': 'third_party/android_tools/sdk/build-tools/20.0.0/aapt',
        'out/Release': [
            dir_out_build_type + '/md5sum_bin_host',
            dir_out_build_type + '/md5sum_dist',
        ],
        'out/Release/%s_apk' % test: dir_out_build_type + '/%s_apk/%s-debug.apk' % (test, test),
    }

    dir_backup = timestamp + '-' + args.backup_test
    backup_files(files_backup=files_backup, dir_backup=dir_backup, dir_src=dir_src)


def contrib():
    global repo_rollset, repo_rolls, repo_commits, contribs

    if not args.contrib:
        return

    ensure_file(path_share_ignore_chromium_contrib)
    if args.contrib_serialize:
        f = open(path_share_ignore_chromium_contrib)
        repo_rollset = pickle.load(f)
        repo_rolls = pickle.load(f)
        repo_commits = pickle.load(f)
        f.close()
    else:
        f = open(path_share_ignore_chromium_contrib, 'w')
        f.seek(0)
        f.truncate()
        f.close()

        _get_repo_rolls()
        _get_repo_commits()

    # only handle revert in repo, not chromium
    _get_repo_contrib()
    if args.contrib_norevert:
        # (backward, forward)
        repo_pairs = {}
        repo_topair = {}
        indice = []
        for repo in repo_path:
            repo_pairs[repo] = []
            repo_topair[repo] = 0
        for index, contrib in enumerate(contribs):
            if contrib[CONTRIB_INDEX_DIRECTION] == 'backward':
                repo_pairs[repo].append([index, -1, contrib[CONTRIB_INDEX_REPO_HASH], contrib[CONTRIB_INDEX_REPO_REV]])
                repo_topair[repo] += 1
            elif repo_topair[repo] > 0:
                pairs = repo_pairs[repo]
                for pair in pairs:
                    if pair[1] == -1 and contrib[CONTRIB_INDEX_REPO_HASH] == pair[2] and contrib[CONTRIB_INDEX_REPO_REV] == pair[3]:
                        pair[1] = index
                        repo_topair[repo] -= 1
                        indice.append(pair[0])
                        indice.append(pair[1])
                        break

        indice = sorted(indice, reverse=True)

        for index in indice:
            del contribs[index]

    _get_chromium_contrib()

    contribs = sorted(contribs, key=lambda x: x[0], reverse=True)

    for contrib in contribs:
        print '\t'.join(contrib)


def debug():
    if not args.debug:
        return

    _setup_device()
    device_id = devices_id[0]
    dir_symbol = '%s/%s/%s/lib' % (dir_src, dir_out_relative, build_type.capitalize())
    dir_src_tmp = 'src'
    pid = chromium_get_pid(device_id, target_module, args.process)
    chromium_gdb_module(device_id, target_module, target_arch, pid, dir_src=dir_src_tmp, dir_symbol=dir_symbol, dir_out=dir_out_relative, pull_lib=False)


def perf():
    if not args.perf:
        return

    _setup_device()
    device_id = devices_id[0]

    # For perf data collection
    dryrun = args.perf_dryrun

    # run perf
    pid = chromium_get_pid(device_id, target_module, args.process)
    cmd = adb('shell perf record -g -p %s -o /data/local/tmp/perf.data sleep %s' % (pid, args.perf_second), device_id=device_id)
    execute(cmd, dryrun=dryrun)

    backup_dir(dir_share_ignore_chromium)
    # pull perf data
    cmd = adb('pull /data/local/tmp/perf.data', device_id=device_id)
    execute(cmd, dryrun=dryrun)

    # create symbol dir
    dir_symbol = dir_share_ignore_chromium + '/symbol'
    dir_lib_host = '%s%s/lib/%s' % (dir_symbol, chromium_android_info[target_module][CHROMIUM_ANDROID_INFO_INDEX_DIRLIB], target_arch)
    ensure_dir(dir_lib_host)

    # symbolic link to real symbol file
    copy_file(dir_out_build_type + '/lib', chromium_get_soname(target_module), dir_lib_host, is_sylk=True)

    # generate perf report
    cmd = '%s report' % args.perf_binary_host
    if args.perf_arg_host:
        cmd += ' ' + args.perf_arg_host
    else:
        cmd += ' -g'
    cmd += ' -i %s/perf.data --symfs %s' % (dir_share_ignore_chromium, dir_symbol)
    execute(cmd, interactive=True)

    restore_dir()


def trace():
    if not args.trace:
        return

    _setup_device()
    device_id = devices_id[0]

    backup_dir(dir_src)
    cmd = 'CHROMIUM_OUT_DIR=%s build/android/adb_profile_chrome -d %s --trace-flow --browser %s --time %s' % (device_id, dir_out_relative, target_module, args.trace_second)
    result = execute(cmd, return_output=True)
    match = re.search('file\://(.*)', result[1])
    execute('google-chrome ' + match.group(1))
    restore_dir()


########## Internal function begin ##########
def _get_suite_default():
    global gtest_suite_default, instrumentation_suite_default

    # gtest
    f = open('src/build/android/pylib/gtest/gtest_config.py')
    lines = f.readlines()
    f.close()
    i = 0

    suite_config = {
        'EXPERIMENTAL_TEST_SUITES': False,
        'STABLE_TEST_SUITES': True,
    }

    while i < len(lines):
        for suite, is_enabled in suite_config.iteritems():
            if is_enabled and re.match(suite, lines[i]):
                len_old = len(gtest_suite_default)
                i = i + 1
                while not re.match(']', lines[i]):
                    match = re.search('\'(.*)\'', lines[i])
                    if match:
                        gtest_suite_default.append(match.group(1))
                    i = i + 1

                if len(gtest_suite_default) == len_old:
                    error('Could not find suite ' + suite)
        i = i + 1
    if len(gtest_suite_default) == 0:
        error('Could not find suite for gtest')

    # instrumentation
    f = open('src/build/android/buildbot/bb_device_steps.py')
    lines = f.readlines()
    f.close()

    arguments = []
    i = 0
    while i < len(lines):
        # parse the key of arguments of description
        if re.match('def I\(', lines[i]):
            flag_done = False
            while not flag_done:
                if re.search('\)\:', lines[i]):
                    flag_done = True

                line_temp = lines[i].replace('def I(', '').replace('):', '')
                line_temp = line_temp.replace('\n', '').replace(' ', '')
                keys = line_temp.split(',')
                for k in keys:
                    if len(k) == 0:
                        continue
                    if re.search('=', k):
                        arguments.append(k.split('=')[0])
                    else:
                        arguments.append(k)
                i = i + 1

            if len(arguments) == 0:
                error('Could not parse the arguments of instrumentation')

        # parse the value of arguments of description
        if re.match('INSTRUMENTATION_TESTS =', lines[i]):
            i = i + 1  # start from next line
            len_old = len(instrumentation_suite_default)

            count = 0
            test_temp = {}
            while not re.match('    \]\)', lines[i]):
                if re.search('I\(', lines[i]):
                    # reset variables
                    count = 0
                    test_temp = {}

                line_temp = lines[i]
                replacement = ['\n', 'I(', ')', ' ', '\'', ',', 'None']
                for r in replacement:
                    if r in line_temp:
                        line_temp = line_temp.replace(r, '')

                if re.search('=', line_temp):
                    key = line_temp.split('=')[0]
                    value = line_temp.split('=')[1]
                    test_temp[key] = value
                else:
                    key = arguments[count]
                    test_temp[key] = line_temp

                if re.search('\),', lines[i]):
                    # finish parsing one group then set target
                    name = test_temp['name']
                    name = name.replace('WebView', 'Webview')
                    name = (re.sub('([A-Z])', lambda p: '_' + p.group(1).lower(), name)).lstrip('_')
                    target = name + '_apk' + ' ' + name + '_test_apk'
                    test_temp['target'] = target
                    instrumentation_suite_default[test_temp['test_apk']] = test_temp

                count = count + 1
                i = i + 1

            # finish parsing of loop outside
            break
        i = i + 1

    if len(instrumentation_suite_default) == len_old:
        error('Could not find suite for instrumentation')


def _test_build_name(command, name):
    cmd = 'ninja -j' + str(count_cpu_build) + ' -C ' + dir_out_build_type + ' ' + name
    result = execute(cmd, interactive=True)
    if result[0]:
        return False
    else:
        return True


def _test_run_device(index_device, results):
    timer_start('test_run_' + str(index_device))
    _setup_device()
    device_id = devices_id[index_device]
    device_product = devices_product[index_device]
    device_type = devices_type[index_device]
    dir_test_device_product = dir_test_timestamp + '-' + device_product

    connect_device(device_id=device_id)

    if not os.path.exists(dir_test_device_product):
        os.mkdir(dir_test_device_product)

    if not args.test_dryrun:
        # Ensure screen stays on
        execute(adb(cmd='shell svc power stayon usb', device_id=device_id))

        # Try to unlock the screen if needed
        execute(adb(cmd='shell input keyevent 82', device_id=device_id))

        android_ensure_root(device_id)

        # Set system time to current time
        execute(adb(cmd='shell date -s %s' % get_datetime(format='%Y%m%d.%H%M%S'), device_id=device_id))

        # Fake /storage/emulated/0
        cmd = adb(cmd='shell "mount -o rw,remount rootfs / && cd /storage/emulated && rm -f 0 && ln -s legacy 0"', device_id=device_id)
        result = execute(cmd)
        if result[0]:
            error('Failed to fake /storage/emulated/0, which is critical for test')
        for command in test_suite:
            for index, suite in enumerate(test_suite[command]):
                if results[command][index] == 'FAIL':
                    continue

                if command == 'instrumentation':
                    # Install packages before running
                    apk = instrumentation_suite_default[suite]['apk']
                    _install_apk(apk=apk, device_id=device_id)

                    # push test data
                    #cmd = adb(cmd='push ', device_id=device_id)

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
                    cmd = 'CHROMIUM_OUT_DIR=%s ' % dir_out_relative

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

                if suite in instrumentation_suite_default and 'isolate_file_path' in instrumentation_suite_default[suite]:
                    cmd += ' --isolate_file_path ' + instrumentation_suite_default[suite]['isolate_file_path']

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
                cmd += ' -d ' + device_id + ' --' + build_type
                if args.test_verbose:
                    cmd += ' -v'
                result = execute(cmd, interactive=True, file_log=dir_test_device_product + '/' + suite + '.log')
                if result[0]:
                    warning('Failed to run "' + suite + '"')
                else:
                    info('Succeeded to run "' + suite + '"')

    timer_stop('test_run_' + str(index_device))
    # Generate report
    html = _test_gen_report(index_device, results)
    file_html = dir_test_device_product + '/report.html'
    file_report = open(file_html, 'w')
    file_report.write(html)
    file_report.close()

    if args.test_formal:
        # Backup
        backup_dir(dir_test)
        backup_smb('//wp-03.sh.intel.com/chromium-test', 'feature', timestamp + '-' + device_product)
        restore_dir()

        # Send mail
        _test_sendmail(index_device, html)


def _test_sendmail(index_device, html):
    report_name = 'Chromium Tests Report'
    device_product = devices_product[index_device]
    if args.test_to:
        to = args.test_to.split(',')
    else:
        to = 'webperf@intel.com'

    send_mail('webperf@intel.com', to, report_name + '-' + timestamp + '-' + device_product, html, type='html')


def _test_gen_report(index_device, results):
    _setup_device()
    device_id = devices_id[index_device]
    device_product = devices_product[index_device]
    device_type = devices_type[index_device]
    dir_test_device_product = dir_test_timestamp + '-' + device_product

    _setup_rev()

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
            <li>Host Machine: ''' + host_name + '''</li>
            <li>Target Device: ''' + device_product + '''</li>
            <li>Target Image: ''' + android_get_build_desc(device_id=device_id) + '''</li>
            <li>Build Duration: ''' + str(timer_diff('build')) + '''</li>
            <li>Test Build Duration: ''' + str(timer_diff('test_build')) + '''</li>
            <li>Test Run Duration: ''' + str(timer_diff('test_run_' + str(index_device))) + '''</li>
          </ul>

          <h2>Details</h2>
    '''

    html_end = '''
          <h2>Log</h2>
          <ul>
            <li>http://wp-03.sh.intel.com/chromium-test/feature/''' + timestamp + '-' + device_product + '''</li>
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
            log_suite = dir_test_device_product + '/' + suite + '.log'
            ut_all = '0'
            ut_pass = '0'
            ut_fail = '0'

            if bs == 'FAIL' or not os.path.exists(log_suite):
                rs = 'FAIL'
            else:
                ut_result = open(log_suite, 'r')
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
    _setup_device()
    for device_id in devices_id:
        if not execute_adb_shell("test -d /system/lib64", device_id=device_id):
            continue

        for file in ['am', 'pm']:
            execute(adb(cmd='pull /system/bin/' + file + ' /tmp/' + file, device_id=device_id))
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                android_ensure_root(device_id)
                execute(adb(cmd='push /tmp/' + file + ' /system/bin/', device_id=device_id))


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


# cleanup, fetch, revert, runhooks, sync
def _run_gclient(cmd_type, cmd_extra=''):
    cmd = 'gclient ' + cmd_type
    if cmd_extra:
        cmd += ' ' + cmd_extra
    if cmd_type == 'revert' or cmd_type == 'sync':
        cmd += ' -n'

    if cmd_type == 'sync' and args.sync_reset:
        cmd += ' -R'
    cmd += ' -j' + str(count_cpu_build)

    if repo_type == 'chrome-android' and cmd_type == 'runhooks' and ver_cmp(ver, ver_envsetup) < 0:
        cmd = 'source src/build/android/envsetup.sh --target-arch=' + target_arch + ' && ' + cmd

    if re.search('source', cmd):
        cmd = bashify_cmd(cmd)
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


def _install_apk(apk, device_id):
    if not target_os == 'android':
        return

    cmd = 'python %s/build/android/adb_install_apk.py --keep_data --%s' % (dir_src, build_type)
    if not args.just_out:
        cmd = 'CHROMIUM_OUT_DIR=%s ' % dir_out_relative + cmd
    if device_id != '':
        cmd += ' -d ' + device_id

    cmd += ' ' + apk
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

    target_arch_device_id = _get_target_arch_device_id()
    if target_arch not in target_arch_device_id:
        android_start_emu(target_arch)
        target_arch_device_id = _get_target_arch_device_id()
    if target_arch not in target_arch_device_id:
        error('Failed to get device for target arch ' + target_arch)

    device_id = target_arch_device_id[target_arch]
    info('Use device %s with target_arch %s' % (device_id, target_arch))
    android_unlock_screen(device_id)
    chrome_android_cleanup(device_id)

    execute(adb(cmd='install -r "%s"' % file_apk, device_id=device_id), interactive=True, dryrun=False)
    # used to install gms apk and lib
    #if os.path.exists('lib'):
    #    execute(adb(cmd='push %s/lib/%s /data/app-lib/com.android.chrome-1' % (dir_root, target_arch), device_id=device_id))
    chromium_android_type = chrome_android_get_ver_type(device_id)
    if chromium_android_type == '':
        error('Failed to install package')

    if bypass:
        ver_temp = ''
        ver_type_temp = ''
        build_id_temp = ''
        result = execute_adb_shell(cmd='am start -n %s/%s -d "chrome://version"' % (chromium_android_info[chromium_android_type][CHROMIUM_ANDROID_INFO_INDEX_PKG], chromium_android_info[chromium_android_type][CHROMIUM_ANDROID_INFO_INDEX_ACT]), device_id=device_id, show_cmd=True)
    else:
        #The following code does not work for com.example.chromium as webdriver.Remote() would hang.
        #adb shell input tap 400 1040
        #adb shell input tap 400 1070
        if has_process('chromedriver'):
            execute('sudo killall chromedriver', show_cmd=False)
        subprocess.Popen(path_share_chromedriver, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)  # Sleep a bit to make sure driver is ready
        env_http_proxy = getenv('http_proxy')
        unsetenv('http_proxy')
        capabilities = get_capabilities(device_id, chromium_android_type)
        driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)
        driver.get('chrome://version')
        WebDriverWait(driver, 30, 1).until(_has_element_ver)
        ver_str = driver.find_elements_by_class_name('version')[0].get_attribute('innerText')

        match = re.search('(\d+\.\d+\.\d+\.\d+)', ver_str)
        if match:
            ver_temp = match.group(1)
        else:
            error('Could not find the correct version')

        if re.search('Beta', ver_str, re.IGNORECASE):
            ver_type_temp = 'beta'
        elif re.search('example', ver_str, re.IGNORECASE):
            ver_type_temp = 'example'
        else:
            ver_type_temp = 'stable'

        pattern_build_id = re.compile('Build ID\s+(.*)')
        match = pattern_build_id.search(driver.find_elements_by_id('build-id-section')[0].get_attribute('innerText'))
        if match:
            build_id_temp = match.group(1)
        else:
            error('Could not find the correct build id')
        driver.quit()
        setenv('http_proxy', env_http_proxy)
        result = True
    execute(adb('uninstall ' + chromium_android_info[chromium_android_type][CHROMIUM_ANDROID_INFO_INDEX_PKG], device_id=device_id))

    return (result, ver_temp, ver_type_temp, build_id_temp)


def _update_phase(phase):
    has_error = False
    pattern = re.compile('phase=(.*)')
    for line in fileinput.input(chrome_android_file_readme, inplace=1):
        match = pattern.search(line)
        if match:
            phase_old = match.group(1)
            if chrome_android_phase_all.index(phase_old) + 1 != chrome_android_phase_all.index(phase):
                has_error = True
            else:
                line = 'phase=' + phase + '\n'
        sys.stdout.write(line)
    if has_error:
        error('Phase can not be set discontinuously')


# get one device for each target_arch
def _get_target_arch_device_id():
    _setup_device()
    target_arch_device_id = {}
    for index, device_id in enumerate(devices_id):
        target_arch_temp = devices_arch[index]
        if target_arch_temp not in target_arch_device_id:
            target_arch_device_id[target_arch_temp] = devices_id[index]

    return target_arch_device_id


def _has_element_ver(driver):
    if driver.find_elements_by_class_name('version'):
        return True
    else:
        return False


def _setup_device():
    global devices_id, devices_product, devices_type, devices_arch, devices_mode

    if devices_id:
        return

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device(devices_id_limit=args.device_id)


def _setup_rev():
    global rev

    if rev == chromium_rev_max:
        rev = chromium_get_rev_max(dir_src=dir_src, need_fetch=False)


# <contrib>
def _git_match(lines, index, hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp):
    line = lines[index].strip()

    # hash
    match = re.match(str_commit, line)
    if match:
        hash_tmp = match.group(1)

    # author
    match = re.match('Author:', lines[index])
    if match:
        match = re.search('<(.*@.*)@.*>', line)
        if match:
            author_tmp = match.group(1)
        else:
            match = re.search('(\S+@\S+)', line)
            if match:
                author_tmp = match.group(1)
                author_tmp = author_tmp.lstrip('<')
                author_tmp = author_tmp.rstrip('>')
            else:
                author_tmp = line.rstrip('\n').replace('Author:', '').strip()
                warning('The author %s is in abnormal format' % author_tmp)

    # update author for commit bot
    match = re.match('Author: (.*)', line)
    if match and match.group(1) in authors and author_tmp not in authors:
        author_tmp = match.group(1)

    # date & subject
    match = re.match('Date:(.*)', line)
    if match:
        date_tmp = match.group(1).strip()
        index += 2
        subject_tmp = lines[index].strip()

    # rev
    match = re.match('git-svn-id: .*@(.*) .*', line)
    if match:
        rev_tmp = match.group(1)
    match = re.match('Cr-Commit-Position: refs/heads/master@{#(.*)}', line)
    if match:
        rev_tmp = match.group(1)

    return (hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp)


def _is_hash(ver):
    if len(ver) > MAX_LEN_REV:
        return True

    return False


# get all rolls hash or svn id into repo_rollset
# get all rolls into repo_rolls
# hash is for git, rev is for svn, ver for either.
def _get_repo_rolls():
    global repo_rollset, repo_rolls

    for repo in repo_path:
        repo_rollset[repo] = []
        repo_rolls[repo] = []

    repos = repo_path.keys()

    backup_dir(dir_src)

    result = execute('git log -p DEPS', show_cmd=False, return_output=True)
    lines = result[1].split('\n')

    index = 0
    is_roll = False
    repo_tmp = ''
    hash_begin = ''
    hash_end = ''
    rev_begin = ''
    rev_end = ''

    while True:
        if index >= len(lines) or re.match(str_commit, lines[index]):
            if index != 0 and is_roll:
                # For rev before 241675, many skia hash values are not correct. So we prefer to use svn rev
                if int(rev_tmp) <= '241675':
                    if not rev_begin or not rev_end:
                        if not hash_begin or not hash_end:
                            print rev_tmp
                            error('Both hash_begin and hash_end should be valid')
                        ver_begin = hash_begin
                        ver_end = hash_end
                    else:
                        ver_begin = rev_begin
                        ver_end = rev_end
                else:
                    if not hash_begin or not hash_end:
                        if not rev_begin or not rev_end:
                            print rev_tmp
                            error('Both rev_begin and rev_end should be valid')
                        ver_begin = rev_begin
                        ver_end = rev_end
                    else:
                        ver_begin = hash_begin
                        ver_end = hash_end

                if ver_begin not in repo_rollset[repo_tmp]:
                    repo_rollset[repo_tmp].append(ver_begin)
                if ver_end not in repo_rollset[repo_tmp]:
                    repo_rollset[repo_tmp].append(ver_end)

                repo_rolls[repo_tmp].append([rev_tmp, repo_tmp, author_tmp, date_tmp, subject_tmp, hash_tmp, ver_begin, ver_end])

            if index >= len(lines):
                break

            # reset
            hash_tmp = ''
            author_tmp = ''
            date_tmp = ''
            subject_tmp = ''
            rev_tmp = ''

            is_roll = False
            repo_tmp = ''
            hash_begin = ''
            hash_end = ''
            rev_begin = ''
            rev_end = ''

        (hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp) = _git_match(lines, index, hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp)

        # 291561 changes from svn id to git hash
        # 194995 fix a typo
        # 116215 fix "103944444444" -> "103944"
        if rev_tmp in ['291561', '194995', '116215']:
            index += 1
            continue

        # smaller than r15949, it's not easy to get ver_begin and ver_end
        if rev_tmp and int(rev_tmp) <= 15949:
            break

        line = lines[index].strip()
        # skia: It is a mess here. skia_revision may contain svn id or hash. skia_hash only contains hash. svn id and hash may appear at same time
        # we can get svn id or hash from webkit_revision
        for repo in repos:
            strs_ver = [
                '  (?:\'|")%s_(?:revision|hash)(?:\'|"): (?:\'|")(\S+)(?:\'|"),' % repo,
                '    "http://skia.googlecode.com/svn/trunk/src@(\S+)"',
                '    "http://skia.googlecode.com/svn/trunk@(\S+)"'
            ]
            for str_ver in strs_ver:
                match = re.match('-' + str_ver, line)
                if match:
                    if _is_hash(match.group(1)):
                        hash_begin = match.group(1)
                    else:
                        rev_begin = match.group(1)

                match = re.match('\+' + str_ver, line)
                if match:
                    # This is a bug for chromium r116206 (bed92ce4a201fa067d7f3ac566eb30e06e40ec4e)
                    if match.group(1) == '103944444444':
                        rev_end = '103944'
                    # r79257 forgot to delete old svn id
                    elif match.group(1) == '81851':
                        rev_end = match.group(1)
                        rev_begin = '81791'
                    elif _is_hash(match.group(1)):
                        hash_end = match.group(1)
                    else:
                        rev_end = match.group(1)

                    is_roll = True
                    repo_tmp = repo

        index += 1

    restore_dir()

    f = open(path_share_ignore_chromium_contrib, 'a+')
    pickle.dump(repo_rollset, f)
    pickle.dump(repo_rolls, f)
    f.close()


def _is_roll(repo, hash_tmp, rev_tmp):
    for repo_tmp in repo_rollset:
        if repo_tmp != repo:
            continue

        rolls = repo_rollset[repo]
        for roll in rolls:
            if not _is_hash(roll) and rev_tmp == roll:
                return True
            if _is_hash(roll) and hash_tmp.startswith(roll):
                return True

    return False


# get commits, either contributed by us, or roll, in cared repos
def _get_repo_commits():
    global repo_commits, repo_rollset

    for repo in repo_path:
        repo_commits[repo] = []

    for repo in repo_path:
        path = repo_path[repo]
        backup_dir(dir_src + '/' + path)
        result = execute(cmd_git_log, show_cmd=False, return_output=True)
        lines = result[1].split('\n')

        index = 0

        while True:
            if index >= len(lines) or re.match(str_commit, lines[index].strip()):
                if index != 0 and (author_tmp in authors or _is_roll(repo, hash_tmp, rev_tmp)):
                    repo_commits[repo].append([author_tmp, date_tmp, subject_tmp, hash_tmp, rev_tmp])
                if index >= len(lines):
                    break
                # reset
                hash_tmp = ''
                author_tmp = ''
                date_tmp = ''
                subject_tmp = ''
                rev_tmp = ''

            (hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp) = _git_match(lines, index, hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp)
            index += 1

        restore_dir()

    f = open(path_share_ignore_chromium_contrib, 'a+')
    pickle.dump(repo_commits, f)
    f.close()


def _update_roll(chromium_rev, repo, chromium_author, chromium_date, chromium_subject, chromium_hash, ver_begin, ver_end):
    global contribs

    if _is_hash(ver_begin) ^ _is_hash(ver_end):
        print ver_begin, ver_end
        error('ver_begin and ver_end should have same length')

    if not _is_hash(ver_begin):
        if int(ver_begin) < int(ver_end):
            direction = 'forward'
        else:
            direction = 'backward'
    else:
        result = execute('git rev-list --count %s..%s' % (ver_begin, ver_end), return_output=True, show_cmd=False)
        if result[1].strip('\n') != '0':
            direction = 'forward'
        else:
            direction = 'backward'

    if direction == 'forward':
        ver_begin_tmp = ver_begin
        ver_end_tmp = ver_end
    else:
        ver_begin_tmp = ver_end
        ver_end_tmp = ver_begin

    commits = repo_commits[repo]
    check = False
    for commit in commits:
        hash_tmp = commit[REPO_COMMIT_INDEX_HASH]
        rev_tmp = commit[REPO_COMMIT_INDEX_REV]

        if not _is_hash(ver_begin_tmp):
            if rev_tmp and int(rev_tmp) <= int(ver_end_tmp):
                check = True
            if rev_tmp and int(rev_tmp) <= int(ver_begin_tmp):
                return
        else:
            if hash_tmp.startswith(ver_end_tmp):
                check = True
            if hash_tmp.startswith(ver_begin_tmp):
                return

        if check:
            author_tmp = commit[REPO_COMMIT_INDEX_AUTHOR]
            if author_tmp in authors:
                contribs.append([chromium_rev, repo, direction, chromium_author, chromium_date, chromium_subject, chromium_hash, author_tmp, commit[REPO_COMMIT_INDEX_DATE], commit[REPO_COMMIT_INDEX_SUBJECT], hash_tmp, commit[REPO_COMMIT_INDEX_REV]])


def _get_repo_contrib():
    for repo in repo_rolls:
        backup_dir(dir_src + '/' + repo_path[repo])
        rolls = repo_rolls[repo]
        for roll in rolls:
            _update_roll(roll[0], roll[1], roll[2], roll[3], roll[4], roll[5], roll[6], roll[7])
        restore_dir()


# can be done earlier as it has no dependence with others
def _get_chromium_contrib():
    global contribs

    backup_dir(dir_src)
    result = execute(cmd_git_log, show_cmd=False, return_output=True)
    lines = result[1].split('\n')

    index = 0
    while True:
        if index >= len(lines) or re.match(str_commit, lines[index]):
            if index != 0 and author_tmp in authors:
                contribs.append([rev_tmp, 'chromium', 'forward', author_tmp, date_tmp, subject_tmp, hash_tmp])
            if index >= len(lines):
                break
            # reset
            hash_tmp = ''
            author_tmp = ''
            date_tmp = ''
            subject_tmp = ''
            rev_tmp = ''

        (hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp) = _git_match(lines, index, hash_tmp, author_tmp, subject_tmp, date_tmp, rev_tmp)
        index += 1

    restore_dir()
# </contrib>


def _teardown():
    pass
########## Internal function end ##########


if __name__ == '__main__':
    parse_arg()
    setup()
    buildid()
    init()
    # gclient
    revert()
    fetch()
    cleanup()
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
    install()
    run()

    # test
    test_build()
    test_run()

    # misc
    analyze()
    owner()
    layout()
    backup_test()

    debug()
    perf()
    trace()

    contrib()
