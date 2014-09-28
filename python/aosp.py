#!/usr/bin/env python

# todo:
# flash_image for upstream

# Build:
# Check tag info from http://source.android.com/source/build-numbers.html
# Download proprietary drivers from https://developers.google.com/android/nexus/drivers, and put them into related directory under /workspace/topic/aosp/driver.
# jdk must be 1.6.0.45 for 4.4 build, and JAVA_HOME should be set correctly.

# Build time:
# upstream 4.4: 1 hour

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import fileinput

dir_root = ''
dir_chromium = ''
dir_out = ''
dir_script = sys.path[0]
dir_backup = ''

# no need of concrete device
targets_arch = []
targets_type = []
targets_module = []
# concrete device
devices = []
devices_product = []
devices_type = []
devices_arch = []
devices_mode = []

chromium_version = ''
ip = '192.168.42.1'
timestamp = ''
use_upstream_chromium = False
variant = ''
product_brand = ''
product_name = ''

# variable product: out/target/product/asus_t100_64p|baytrail_64p
# variable combo: lunch asus_t100_64p-userdebug|aosp_baytrail_64p-eng
# out/dist asus_t100_64p-bootloader-eng.gyagp|aosp_baytrail_64p-bootloader-userdebug.gyagp
repo_type = ''  # upstream, stable, mcg, gminl, irdakk, gminl64
repo_branch = ''
# stable from 20140624, combo changed to asus_t100-userdebug, etc.
repo_ver = '0.0'

patches_build_common = {
    # Emulator
    #'build/core': ['0001-Emulator-Remove-opengl-from-blacklist-to-enable-gpu.patch'],
    #'device/generic/goldfish': ['0001-Emulator-Make-the-size-of-cb_handle_t-same-for-32-64.patch'],
    #'frameworks/base': ['0001-Emulator-Enable-HWUI.patch'],
}

patches_build_upstream_chromium = {
    'external/chromium_org/src/tools/gyp': ['0001-Cherrypick-android-Support-host-multilib-builds.patch'],
    'frameworks/webview': ['0001-Fix-WebView-crash-on-startup-due-to-missing-resource.patch'],
}

patches_build_aosp_chromium = {}


def parse_arg():
    global args

    parser = argparse.ArgumentParser(description='Script to sync, build Android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s -s all -b --disable-2nd-arch --patch
  python %(prog)s -b --build-skip-mk --disable-2nd-arch
  python %(prog)s -b --disable-2nd-arch  --build-skip-mk --target-module libwebviewchromium --build-no-dep
  python %(prog)s --target-type generic --backup --backup-skip-server --time-fixed
  python %(prog)s --build --target-type flo --version KTU84P
''')

    parser.add_argument('--init', dest='init', help='init', action='store_true')
    parser.add_argument('--repo-type', dest='repo_type', help='repo type')
    parser.add_argument('--repo-branch', dest='repo_branch', help='repo branch', default='master')
    parser.add_argument('--revert', dest='revert', help='revert', action='store_true')
    parser.add_argument('--sync', dest='sync', help='sync code for android', action='store_true')
    parser.add_argument('--sync-chromium', dest='sync_chromium', help='sync code for chromium', action='store_true')
    parser.add_argument('--patch', dest='patch', help='patch', action='store_true')
    parser.add_argument('--build', dest='build', help='build', action='store_true')
    parser.add_argument('--build-showcommands', dest='build_showcommands', help='build with detailed command', action='store_true')
    parser.add_argument('--build-skip-mk', dest='build_skip_mk', help='skip the generation of makefile', action='store_true')
    parser.add_argument('--build-no-dep', dest='build_no_dep', help='use mmma or mmm', action='store_true')
    parser.add_argument('--disable-2nd-arch', dest='disable_2nd_arch', help='disable 2nd arch, only effective for baytrail', action='store_true')
    parser.add_argument('--burn-image', dest='burn_image', help='burn live image')
    parser.add_argument('--flash-image', dest='flash_image', help='flash the boot and system', action='store_true')
    parser.add_argument('--file-image', dest='file_image', help='image tgz file')
    parser.add_argument('--backup', dest='backup', help='backup output to both local and samba server', action='store_true')
    parser.add_argument('--backup-skip-server', dest='backup_skip_server', help='only local backup', action='store_true')
    parser.add_argument('--start-emu', dest='start_emu', help='start the emulator. Copy sdcard.img to dir_root and rename it as sdcard-<arch>.img', action='store_true')
    parser.add_argument('--dir-emu', dest='dir_emu', help='emulator dir')
    parser.add_argument('--analyze', dest='analyze', help='analyze tombstone or ANR file')
    parser.add_argument('--push', dest='push', help='push updates to system', action='store_true')
    parser.add_argument('--remove-out', dest='remove_out', help='remove out dir before build', action='store_true')
    parser.add_argument('--hack-app-process', dest='hack_app_process', help='hack app_process', action='store_true')
    parser.add_argument('--cts-run', dest='cts_run', help='package to run with cts, such as android.webkit, com.android.cts.browserbench')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'all'], default='x86_64')
    parser.add_argument('--target-type', dest='target_type', help='target type, can be baytrail for t100, generic, mrd7, mako for nexus4, hammerhead for nexus5, flo for nexus7', default='baytrail')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=['libwebviewchromium', 'webview', 'browser', 'cts', 'system', 'all'], default='system')

    parser.add_argument('--variant', dest='variant', help='variant', choices=['user', 'userdebug', 'eng'], default='userdebug')
    parser.add_argument('--version', dest='version', help='version, KTU84P for 4.4.4, master')

    parser.add_argument('--product-brand', dest='product_brand', help='product brand', choices=['ecs', 'fxn'], default='ecs')
    parser.add_argument('--product-name', dest='product_name', help='product name', choices=['e7', 'anchor8'], default='e7')

    add_argument_common(parser)

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global targets_arch, targets_type, targets_module
    global dir_chromium, dir_out, dir_backup, chromium_version
    global use_upstream_chromium, patches_build
    global repo_type, repo_ver, variant
    global product_brand, product_name
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)

    dir_chromium = dir_root + '/external/chromium_org'
    dir_out = dir_root + '/out'
    dir_backup = dir_root + '/backup'
    variant = args.variant
    product_brand = args.product_brand
    product_name = args.product_name

    if not os.path.exists('.repo'):
        if not args.repo_type:
            error('Please designate repo type')
        repo_type = args.repo_type
    else:
        (repo_type, repo_ver) = _get_repo_info()
    info('repo type is ' + repo_type)
    info('repo version is ' + repo_ver)

    for cmd in ['adb', 'git', 'gclient']:
        result = execute('which ' + cmd, show_cmd=False)
        if result[0]:
            error('Could not find ' + cmd + ', and you may use --path-extra to designate it')

    if args.target_arch == 'all':
        targets_arch = ['x86_64', 'x86']
    else:
        targets_arch = args.target_arch.split(',')

    if args.target_type == 'all':
        targets_type = ['baytrail', 'generic']
    else:
        targets_type = args.target_type.split(',')

    if args.target_module == 'all':
        targets_module = ['system']
    else:
        targets_module = args.target_module.split(',')

    if os.path.exists(dir_chromium + '/src'):
        chromium_version = 'cr36'
    else:
        chromium_version = 'cr30'

    if os.path.exists(dir_chromium + '/src'):
        use_upstream_chromium = True

    if use_upstream_chromium:
        patches_build = dict(patches_build_common, **patches_build_upstream_chromium)
    else:
        patches_build = dict(patches_build_common, **patches_build_aosp_chromium)


def init():
    if not args.init:
        return()

    if repo_type == 'upstream':
        file_repo = 'https://storage.googleapis.com/git-repo-downloads/repo'
    elif repo_type == 'stable' or repo_type == 'gminl' or repo_type == 'gminl64':
        file_repo = 'http://android.intel.com/repo'
    elif repo_type == 'irdakk':
        file_repo = 'https://buildbot-otc.jf.intel.com/repo.otc'
    execute('curl -k --noproxy intel.com %s >./repo' % file_repo, interactive=True)
    execute('chmod +x ./repo')

    if repo_type == 'upstream':
        cmd = './repo init -u https://android.googlesource.com/platform/manifest -b ' + args.repo_branch
    elif repo_type == 'stable':
        cmd = './repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/private/topic/aosp_stable/master'
    elif repo_type == 'gminl':
        cmd = './repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/topic/gmin/l-dev/master'
    elif repo_type == 'gminl64':
        cmd = './repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/topic/gmin/l-dev/aosp/64bit/master'
    elif repo_type == 'irdakk':
        cmd = 'repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b irda/kitkat/master'
    execute(cmd, interactive=True)

    execute('./repo sync -c -j16', interactive=True)
    execute('./repo start temp --all')


def sync():
    if not args.sync:
        return()

    _sync_repo(dir_root, './repo sync -c -j16')

    if args.sync_chromium and os.path.exists(dir_chromium + '/src'):
        _sync_repo(dir_chromium, 'GYP_DEFINES="OS=android werror= disable_nacl=1 enable_svg=0" gclient sync -f -n -j16')


def revert():
    if not args.revert:
        return()

    execute('./repo forall -vc "git reset --hard"', interactive=True)


def patch(patches, force=False):
    if not args.patch and not force:
        return

    for dir_repo in patches:
        if not os.path.exists(dir_repo):
            continue

        for patch in patches[dir_repo]:
            path_patch = dir_script + '/patches/' + patch
            if _patch_applied(dir_repo, path_patch):
                info('Patch ' + patch + ' was applied before, so is just skipped here')
            else:
                backup_dir(dir_repo)
                cmd = 'git am ' + path_patch
                result = execute(cmd, show_progress=True)
                restore_dir()
                if result[0]:
                    error('Fail to apply patch ' + patch, error_code=result[0])


def remove_out():
    if not args.remove_out:
        return

    execute('rm -rf out', dryrun=False)


def build():
    if not args.build:
        return

    # Set up JDK
    backup_dir(dir_python)
    if repo_type == 'irdakk' or repo_type == 'upstream' and ver_cmp(repo_ver, '5.0') < 0:
        execute('python version.py -t java -s jdk1.6.0_45')
    else:
        execute('python version.py -t java -s java-7-openjdk-amd64')
    restore_dir()

    # make
    if repo_type == 'irdakk' or repo_type == 'upstream' and ver_cmp(repo_ver, '5.0') < 0:
        make = dir_tool + '/make-3.81/make'
    else:
        make = 'make'

    for target_arch, target_type, target_module in [(target_arch, target_type, target_module) for target_arch in targets_arch for target_type in targets_type for target_module in targets_module]:
        name_build = get_caller_name() + '-' + target_arch + '-' + target_type + '-' + target_module
        timer_start(name_build)

        combo = _get_combo(target_arch, target_type)
        if repo_type == 'upstream':
            dir_driver_upstream = '/workspace/topic/aosp/driver'
            # Check proprietary binaries.
            dir_driver_upstream_one = dir_driver_upstream + '/' + target_type + '/' + args.version + '/vendor'
            if not os.path.exists(dir_driver_upstream_one):
                error('Proprietary binaries do not exist')
            execute('rm -rf vendor')
            execute('cp -rf ' + dir_driver_upstream_one + ' ./')

        if not args.build_skip_mk and os.path.exists(dir_root + '/external/chromium_org/src'):
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86'
            if target_arch == 'x86_64':
                cmd += ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86_64'
            cmd = bashify_cmd(cmd)
            execute(cmd, interactive=True)

        if target_module == 'system' or target_module == 'cts':
            cmd = '. build/envsetup.sh && lunch %s && %s ' % (combo, make)
            if target_module == 'system':
                cmd += 'dist'
            else:
                cmd += target_module
        elif target_module == 'browser' or target_module == 'webview' or target_module == 'libwebviewchromium':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && '
            if args.build_no_dep:
                cmd += 'mmm '
            else:
                cmd += 'mmma '

            if target_module == 'browser':
                cmd += 'packages/apps/Browser'
            elif target_module == 'webview':
                cmd += 'frameworks/webview'
            elif target_module == 'libwebviewchromium':
                cmd += 'external/chromium_org'

        if args.build_showcommands:
            cmd += ' showcommands'
        cmd += ' -j16 2>&1 |tee -a ' + log
        cmd = bashify_cmd(cmd)
        result = execute(cmd, interactive=True, dryrun=False)
        if result[0]:
            error('Failed to build %s %s %s' % (target_arch, target_type, target_module))

        if target_module == 'system' and target_type == 'generic':
            cmd = bashify_cmd('. build/envsetup.sh && lunch ' + combo + ' && external/qemu/android-rebuild.sh')
            result = execute(cmd, interactive=True)
            if result[0]:
                error('Failed to build %s emulator' % target_arch)

        timer_stop(name_build)
        info('Time for ' + name_build + ': ' + timer_diff(name_build))


def backup():
    if not args.backup:
        return

    for target_arch, target_type, target_module in [(target_arch, target_type, target_module) for target_arch in targets_arch for target_type in targets_type for target_module in targets_module]:
        _backup_one(target_arch, target_type, target_module)


def hack_app_process():
    if not args.hack_app_process:
        return

    _setup_device()

    for device in devices:
        connect_device(device=device)
        if not execute_adb_shell("test -d /system/lib64", device=device):
            continue

        for file in ['am', 'pm']:
            cmd = adb('pull /system/bin/' + file + ' /tmp/' + file)
            execute(cmd)
            need_hack = False
            for line in fileinput.input('/tmp/' + file, inplace=1):
                if re.search('app_process ', line):
                    line = line.replace('app_process', 'app_process64')
                    need_hack = True
                sys.stdout.write(line)

            if need_hack:
                android_ensure_root(device)
                cmd = adb(cmd='push /tmp/' + file + ' /system/bin/', device=device)
                execute(cmd)


def flash_image():
    if not args.flash_image:
        return

    _setup_device()

    if len(devices) < 1:
        error('You must have device connected')

    device_arch = devices_arch[0]
    device_type = devices_type[0]
    device = devices[0]
    path_fastboot = dir_linux + '/fastboot'

    if repo_type != 'upstream':
        dir_extract = '/tmp/' + timestamp
        ensure_dir(dir_extract)
        backup_dir(dir_extract, verbose=True)

    # extract image
    if repo_type != 'upstream':
        if args.file_image:
            if re.match('http', args.file_image):
                execute('wget ' + args.file_image, dryrun=False)
            else:
                execute('cp ' + args.file_image + ' ./')

            if args.file_image[-6:] == 'tar.gz':
                execute('tar zxf ' + args.file_image.split('/')[-1])
                execute('mv */* ./')
                result = execute('ls *.tgz', return_output=True)
                file_image = dir_extract + '/' + result[1].rstrip('\n')
            else:
                file_image = args.file_image.split('/')[-1]
        else:
            if repo_type == 'stable':
                if ver_cmp(repo_ver, '2.0') >= 0:
                    file_image = dir_root + '/out/dist/%s-om-factory.tgz' % get_product(device_arch, device_type, ver=repo_ver)
                else:
                    file_image = dir_root + '/out/dist/aosp_%s-om-factory.tgz' % get_product(device_arch, device_type, ver=repo_ver)
            elif repo_type == 'irdakk':
                file_image = dir_root + '/out/target/product/irda/irda-ktu84p-factory.tgz'
            elif repo_type == 'gminl':
                file_image = dir_root + '/out/target/product/%s_%s/%s_%s-lmp-factory.tgz' % (product_brand, product_name, product_brand, product_name)
            elif repo_type == 'gminl64':
                file_image = dir_root + '/out/target/product/%s_%s_64p/%s_%s_64p-lmp-factory.tgz' % (product_brand, product_name, product_brand, product_name)

        if not os.path.exists(file_image):
            error('File ' + file_image + ' used to flash does not exist, please have a check', abort=False)
            return

        execute('tar xvf ' + file_image, interactive=True, dryrun=False)

    # hack the script
    if repo_type == 'stable':
        # Hack flash-all.sh to skip sleep and use our own fastboot
        for line in fileinput.input('flash-all.sh', inplace=1):
            if re.search('sleep', line):
                line = line.replace('sleep', '#sleep')
            elif re.match('fastboot', line):
                line = dir_linux + '/' + line
            # We can not use print here as it will generate blank line
            sys.stdout.write(line)
        fileinput.close()

        # Hack gpt.ini for fast userdata erasion
        result = execute('ls *.ini', return_output=True)
        file_gpt = result[1].rstrip('\n')
        for line in fileinput.input(file_gpt, inplace=1):
            if re.search('len = -1', line):
                line = line.replace('-1', '2000')
            # We can not use print here as it will generate blank line
            sys.stdout.write(line)
        fileinput.close()

    # enter fastboot mode
    android_enter_fastboot(device=device)

    # flash image
    if repo_type == 'upstream':
        combo = _get_combo(device_arch, device_type)
        cmd = bashify_cmd('. build/envsetup.sh && lunch ' + combo + ' && fastboot -w flashall')
        execute(cmd, interactive=True, dryrun=False)
    elif repo_type == 'irdakk' or repo_type == 'gminl' or repo_type == 'gminl64':
        execute('./flash-base.sh', interactive=True, dryrun=False)
        execute('./flash-all.sh', interactive=True, dryrun=False)
        execute('timeout 10s %s -s %s reboot' % (path_fastboot, device))
        execute('rm -rf ' + dir_extract, dryrun=False)
    elif repo_type == 'stable':
        execute('./flash-all.sh -t ' + ip, interactive=True, dryrun=False)
        execute('timeout 10s %s -t %s reboot' % (path_fastboot, ip))
        execute('rm -rf ' + dir_extract, dryrun=False)

    if repo_type != 'upstream':
        restore_dir()

    # wait until system boots up
    if repo_type == 'stable':
        is_connected = False
        sleep_sec = 3
        for i in range(0, 60):
            if not connect_device(device=device):
                info('Sleeping %s seconds' % str(sleep_sec))
                time.sleep(sleep_sec)
                continue
            else:
                is_connected = True
                break

        if not is_connected:
            error('Can not connect to device after system boots up')
        else:
            info('Sleeping 150 seconds until system fully boots up..')
            time.sleep(150)

        android_keep_screen_on()
        android_unlock_screen()
        # Remove guide screen
        android_tap(683, 384)
        android_tap()
        # After system boots up, it will show guide screen and never lock or turn off screen.
        android_set_screen_lock_none()
        android_set_display_sleep_30mins()


def start_emu():
    if not args.start_emu:
        return

    _setup_device()

    for device_arch in devices_arch:
        product = get_product(device_arch, 'generic', ver=repo_ver)
        if args.dir_emu:
            dir_backup_emu = args.dir_emu
        else:
            result = execute('ls -t -d --group-directories-first backup/*generic*', return_output=True)
            dir_backup_emu = dir_root + '/' + result[1].split('\n')[0]
        backup_dir(dir_backup_emu)

        if not os.path.exists(dir_root + '/sdcard-%s.img' % device_arch):
            error('Please put sdcard.img into ' + dir_root)

        if not os.path.exists('system-images/aosp_%(device_arch)s/userdata-qemu.img' % {'device_arch': device_arch}):
            execute('cp system-images/aosp_%(device_arch)s/userdata.img system-images/aosp_%(device_arch)s/userdata-qemu.img' % {'device_arch': device_arch})

        if device_arch == 'x86_64':
            gpu_type = 'on'
            file_emu = 'emulator64-x86'
        else:
            gpu_type = 'off'
            file_emu = 'emulator-x86'

        cmd = '''
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:%(dir_backup_emu)s/emulator-linux/lib \
%(dir_backup_emu)s/emulator-linux/%(file_emu)s -verbose -show-kernel -no-snapshot -gpu %(gpu_type)s -memory 512 \
-skin HVGA \
-skindir %(dir_backup_emu)s/platforms/skins \
-kernel %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/kernel-qemu \
-ramdisk %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/ramdisk.img \
-sysdir %(dir_backup_emu)s/system-images/aosp_%(device_arch)s \
-system %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/system.img \
-datadir %(dir_backup_emu)s/system-images/aosp_%(device_arch)s \
-data %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/userdata-qemu.img \
-cache %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/cache.img \
-initdata %(dir_backup_emu)s/system-images/aosp_%(device_arch)s/userdata.img \
-sdcard %(dir_root)s/sdcard-%(device_arch)s.img \
''' % {'dir_root': dir_root, 'dir_backup_emu': dir_backup_emu, 'product': product, 'device_arch': device_arch, 'gpu_type': gpu_type, 'file_emu': file_emu}

        execute(cmd, interactive=True)
        restore_dir()


def analyze():
    if not args.analyze:
        return

    _setup_device()

    if len(devices_arch) > 1:
        error('You need to specify the device arch')

    if len(devices_type) > 1 or devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    analyze_issue(dir_aosp=dir_root, type=args.analyze, ver=repo_ver)


def push():
    if not args.push:
        return

    _setup_device()

    if len(devices_arch) > 1:
        error('You need to specify the target arch')

    if len(devices_type) > 1 or devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    device_arch = devices_arch[0]
    device_type = devices_type[0]
    device = devices[0]

    if args.target_module == 'all':
        modules = ['libwebviewchromium', 'webview']
    else:
        modules = args.target_module.split(',')

    android_ensure_root(device)
    cmd = adb(cmd='push out/target/product/%s' % get_product(device_arch, device_type, ver=repo_ver), device=device)

    for module in modules:
        if module == 'browser':
            cmd += '/system/app/Browser.apk /system/app'
        if module == 'libwebviewchromium':
            cmd += '/obj/lib/libwebviewchromium.so /system/lib64'
        elif module == 'webview':
            cmd += '/system/framework/webviewchromium.jar /system/framework'

    result = execute(cmd)
    if result[0]:
        error('Failed to push binaries to system')

    if len(modules) == 1 and modules[0] == 'browser':
        pass
    elif len(modules) > 0:
        cmd = adb(cmd='shell stop') + ' && ' + adb(cmd='shell start')
        execute(cmd)


def cts_run():
    if not args.cts_run:
        return

    _setup_device()

    if len(devices_arch) > 1:
        error('You need to specify the device arch')

    if len(devices_type) > 1 or devices_type[0] != 'baytrail':
        error('Only baytrail can run cts')

    device_arch = devices_arch[0]
    device_type = devices_type[0]

    combo = _get_combo(device_arch, device_type)
    cmd = bashify_cmd('. build/envsetup.sh && lunch ' + combo + ' && cts-tradefed run cts -p ' + args.cts_run)
    execute(cmd, interactive=True)


def _sync_repo(dir, cmd):
    backup_dir(dir)
    result = execute(cmd + ' 2>&1 |tee -a ' + log, interactive=True, dryrun=False)
    if result[0]:
        error('Failed to sync ' + dir)
    restore_dir()


def _get_combo(device_arch, device_type):
    if repo_type == 'upstream':
        combo = 'aosp_' + device_type + '-' + variant
    elif repo_type == 'irdakk':
        combo = 'irda-%s' % variant
    elif repo_type == 'gminl':
        if not product_brand or not product_name:
            error('Please designate product brand and name')
        combo = '%s_%s-%s' % (product_brand, product_name, variant)
    elif repo_type == 'gminl64':
        combo = '%s_%s_64p-%s' % (product_brand, product_name, variant)
    elif repo_type == 'stable':
        if device_type == 'generic':
            combo_prefix = 'aosp_'
            combo_suffix = '-' + variant
            combo = combo_prefix + device_arch + combo_suffix
        elif device_type == 'baytrail':
            if repo_type == 'stable' and ver_cmp(repo_ver, '2.0') >= 0:
                combo_prefix = 'asus_t100'
                combo_suffix = '-' + variant

                if device_arch == 'x86_64':
                    combo = combo_prefix + '_64p' + combo_suffix
                elif device_arch == 'x86':
                    combo = combo_prefix + combo_suffix
            else:
                combo_prefix = 'aosp_'
                combo_suffix = '-' + variant
                if device_arch == 'x86_64':
                    combo = combo_prefix + device_type + '_64p' + combo_suffix
                elif device_arch == 'x86':
                    combo = combo_prefix + device_type + combo_suffix

    return combo


# All valid combination for stable:
# 1. x86_64, baytrail, webview
# 2. x86_64, baytrail, system
# 3. x86, baytrail, system
# 4. x86_64, generic, system
# 5. x86, generic, system
# (x86_64, generic, webview) is same as 1
# (x86, baytrail, webview) is included in 1
# (x86, generic, webview) is included in 1

def _backup_one(arch, device_type, module):
    if repo_type == 'upstream':
        pass
        #dest_dir = dir_backup_img + get_datetime() + '-' + device + '-' + variant + '/'
        #os.mkdir(dest_dir)
        #execute('cp ' + root_dir + 'out/target/product/' + device_code_name + '/*.img ' + dest_dir)
    elif repo_type == 'irdakk':
        backup_files = {'.': 'out/target/product/irda/irda-ktu84p-factory.tgz'}
    elif repo_type == 'gminl':
        backup_files = {'.': 'out/target/product/%s_%s/%s_%s-lmp-factory.tgz' % (product_brand, product_name, product_brand, product_name)}
    elif repo_type == 'gminl64':
        backup_files = {'.': 'out/target/product/%s_%s_64p/%s_%s_64p-lmp-factory.tgz' % (product_brand, product_name, product_brand, product_name)}
    elif repo_type == 'stable':
        product = get_product(arch, device_type, ver=repo_ver)

        if module == 'webview':
            if arch == 'x86_64':
                libs = ['lib64', 'lib']
            elif arch == 'x86':
                libs = ['lib']

            backup_files = {
                'out/target/product/' + product + '/system/framework': 'out/target/product/' + product + '/system/framework/webviewchromium.jar',
                'out/target/product/' + product + '/system/framework/webview': 'out/target/product/' + product + '/system/framework/webview/paks',
            }

            for lib in libs:
                backup_files['out/target/product/' + product + '/system/' + lib] = [
                    'out/target/product/' + product + '/system/' + lib + '/libwebviewchromium_plat_support.so',
                    'out/target/product/' + product + '/system/' + lib + '/libwebviewchromium.so'
                ]

        else:  # module == 'system'
            if device_type == 'baytrail':
                if ver_cmp(repo_ver, '2.0') >= 0:
                    prefix = ''
                else:
                    prefix = 'aosp_'
                backup_files = {
                    '.': [
                        'out/dist/%s%s-om-factory.tgz' % (prefix, get_product(arch, device_type, ver=repo_ver)),
                    ],
                }
            elif device_type == 'generic':
                backup_files = {
                    'platforms': 'development/tools/emulator/skins',
                    'emulator-linux': 'external/qemu/objs/*',
                    'system-images/aosp_%s/system' % arch: 'out/target/product/generic_%s/system/*' % arch,
                    'system-images/aosp_%s' % arch: [
                        'out/target/product/generic_%s/cache.img' % arch,
                        'out/target/product/generic_%s/userdata.img' % arch,
                        'out/target/product/generic_%s/ramdisk.img' % arch,
                        'out/target/product/generic_%s/system.img' % arch,
                        'prebuilts/qemu-kernel/%s/kernel-qemu' % arch,
                    ],
                }

    name = timestamp + '-' + repo_type
    if repo_type == 'stable':
        name += '-' + arch + '-' + device_type + '-' + module + '-' + chromium_version
    elif repo_type == 'gminl':
        name += '-' + product_brand + '-' + product_name
    dir_backup_one = dir_backup + '/' + name
    ensure_dir(dir_backup_one)
    backup_dir(dir_backup_one)
    info('Begin to backup to ' + dir_backup_one)
    for dir_dest in backup_files:
        ensure_dir(dir_dest)

        if isinstance(backup_files[dir_dest], str):
            files = [backup_files[dir_dest]]
        else:
            files = backup_files[dir_dest]

        for file in files:
            if not os.path.exists(dir_root + '/' + file):
                warning(dir_root + '/' + file + ' could not be found')
            execute('cp -rf ' + dir_root + '/' + file + ' ' + dir_dest)
    restore_dir()

    if not args.backup_skip_server:
        backup_dir(dir_backup)
        name_tar = name + '-' + host_name + '.tar.gz'
        execute('tar zcf ' + name_tar + ' ' + name)
        backup_smb('//wp-03.sh.intel.com/aosp', '%s/temp' % repo_type, name_tar, dryrun=False)
        restore_dir()


def _ensure_exist(file):
    if not os.path.exists(file):
        execute('mv -f %s.bk %s' % (file, file))


def _ensure_nonexist(file):
    if os.path.exists(file):
        execute('mv -f %s %s.bk' % (file, file))


def _patch_cond(cond_true, patches):
    if cond_true:
        patch(patches, force=True)
    else:
        _patch_remove(patches)


def _patch_remove(patches):
    dir_repo = patches.keys()[0]
    path_patch = dir_script + '/patches/' + patches.values()[0][0]

    if not _patch_applied(dir_repo, path_patch):
        return

    if not _patch_applied(dir_repo, path_patch, count=1):
        error('Can not revert the patch to enable 2nd arch')

    backup_dir(dir_repo)
    execute('git reset --hard HEAD^')
    restore_dir()


def _get_repo_info():
    f = open('.repo/manifests.git/config')
    lines = f.readlines()
    f.close()

    repo_ver = '0.0'
    pattern = re.compile('merge = (.*)')
    for line in lines:
        match = pattern.search(line)
        if match:
            merge = match.group(1)
            if merge == 'master':
                repo_type = 'upstream'
                repo_ver = '99.0.0.0'
            elif merge == 'android-4.4.4_r1':
                repo_type = 'upstream'
                repo_ver = '4.4.4.1'
            elif merge == 'abt/private/topic/aosp_stable/master':
                repo_type = 'stable'
                if os.path.exists('device/intel/baytrail/asus_t100'):
                    repo_ver = '2.0'
                else:
                    repo_ver = '1.0'
            elif merge == 'platform/android/r44c-stable':
                repo_type = 'mcg'
            elif merge == 'abt/topic/gmin/l-dev/master':
                repo_type = 'gminl'
            elif merge == 'abt/topic/gmin/l-dev/aosp/64bit/master':
                repo_type = 'gminl64'
            elif merge == 'irda/kitkat/master':
                repo_type = 'irdakk'
            else:
                error('Could not find repo branch')

    return (repo_type, repo_ver)


def _teardown():
    pass


def _setup_device():
    global devices, devices_product, devices_type, devices_arch, devices_mode

    if devices:
        return

    if repo_type == 'stable':
        connect_device()
    (devices, devices_product, devices_type, devices_arch, devices_mode) = setup_device()

if __name__ == "__main__":
    parse_arg()
    setup()
    init()
    revert()
    sync()
    patch(patches_build)
    remove_out()
    build()
    backup()

    hack_app_process()
    flash_image()
    start_emu()
    analyze()
    push()
    cts_run()
