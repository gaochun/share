#!/usr/bin/env python

# Build:
# Check tag info from http://source.android.com/source/build-numbers.html
# Download proprietary drivers from https://developers.google.com/android/nexus/drivers, and put them into related directory under /workspace/topic/android/backup/vendor.
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
dir_backup = 'backup'
target_archs = []
target_devices_type = []
target_modules = []
devices = []
devices_name = []
devices_type = []
devices_target_arch = []
chromium_version = ''
ip = '192.168.42.1'
timestamp = ''
use_upstream_chromium = False
file_log = ''
variant = ''

# variable product: out/target/product/asus_t100_64p|baytrail_64p
# variable combo: lunch asus_t100_64p-userdebug|aosp_baytrail_64p-eng
# out/dist asus_t100_64p-bootloader-eng.gyagp|aosp_baytrail_64p-bootloader-userdebug.gyagp
repo_type = ''  # upstream, stable, mcg, gmin
repo_branch = ''
# stable from 20140624, combo changed to asus_t100-userdebug, etc.
repo_date = 0

codename = {
    'nexus4': 'mako',
    'nexus5': 'hammerhead',
}

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
  python %(prog)s --target-device-type generic --backup --backup-skip-server --time-fixed
''')

    parser.add_argument('--init', dest='init', help='init', action='store_true')
    parser.add_argument('--repo-type', dest='repo_type', help='repo type')
    parser.add_argument('--repo-branch', dest='repo_branch', help='repo branch', default='master')
    parser.add_argument('--revert', dest='revert', help='revert', action='store_true')
    parser.add_argument('--sync', dest='sync', help='sync code for android, chromium and intel', choices=['all', 'aosp', 'chromium'])
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
    parser.add_argument('--extra-path', dest='extra_path', help='extra path for execution, such as path for depot_tools')
    parser.add_argument('--hack-app-process', dest='hack_app_process', help='hack app_process', action='store_true')
    parser.add_argument('--time-fixed', dest='time_fixed', help='fix the time for test sake. We may run multiple tests and results are in same dir', action='store_true')
    parser.add_argument('--dir-root', dest='dir_root', help='set root directory')
    parser.add_argument('--cts-run', dest='cts_run', help='package to run with cts, such as android.webkit, com.android.cts.browserbench')

    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=['x86', 'x86_64', 'all'], default='x86_64')
    parser.add_argument('--target-device-type', dest='target_device_type', help='target device, can be t100, generic, mrd7, nexus4, nexus5, nexus7', choices=['baytrail', 'generic'], default='baytrail')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=['libwebviewchromium', 'webview', 'browser', 'cts', 'system', 'all'], default='system')
    parser.add_argument('--variant', dest='variant', help='variant', choices=['user', 'userdebug', 'eng'])

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()


def setup():
    global dir_root, dir_chromium, dir_out, target_archs, target_devices_type, target_modules, chromium_version
    global devices, devices_name, devices_type, devices_target_arch, timestamp, use_upstream_chromium, patches_build
    global repo_type, repo_date, file_log, variant

    if args.dir_root:
        dir_root = args.dir_root
    elif os.path.islink(sys.argv[0]):
        dir_root = get_symbolic_link_dir()
    else:
        dir_root = os.path.abspath(os.getcwd())

    dir_chromium = dir_root + '/external/chromium_org'
    dir_out = dir_root + '/out'

    (devices, devices_name, devices_type, devices_target_arch) = setup_device()

    os.chdir(dir_root)

    if not os.path.exists('.repo'):
        if not args.repo_type:
            error('Please designate repo type')
        repo_type = args.repo_type
    else:
        (repo_type, repo_date) = _get_repo_info()

    if args.time_fixed:
        timestamp = get_datetime(format='%Y%m%d')
    else:
        timestamp = get_datetime()

    # Set path
    path = os.getenv('PATH')
    path += ':/usr/bin:/usr/sbin'
    if args.extra_path:
        path += ':' + args.extra_path
    if repo_type == 'gmin':
        path = '/workspace/software/make-3.81:' + path
    setenv('PATH', path)

    for cmd in ['adb', 'git', 'gclient']:
        result = execute('which ' + cmd, show_command=False)
        if result[0]:
            error('Could not find ' + cmd + ', and you may use --extra-path to designate it')

    set_proxy()

    if args.target_arch == 'all':
        target_archs = ['x86_64', 'x86']
    else:
        target_archs = args.target_arch.split(',')

    if args.target_device_type == 'all':
        target_devices_type = ['baytrail', 'generic']
    else:
        target_devices_type = args.target_device_type.split(',')

    if args.target_module == 'all':
        target_modules = ['system']
    else:
        target_modules = args.target_module.split(',')

    if os.path.exists(dir_chromium + '/src'):
        chromium_version = 'cr36'
    else:
        chromium_version = 'cr30'

    if os.path.exists('external/chromium_org/src'):
        use_upstream_chromium = True

    if use_upstream_chromium:
        patches_build = dict(patches_build_common, **patches_build_upstream_chromium)
    else:
        patches_build = dict(patches_build_common, **patches_build_aosp_chromium)

    file_log = dir_root + '/log-' + timestamp + '.txt'

    # Set up JDK
    backup_dir(dir_python)
    if repo_type == 'gmin':
        execute('python version.py -t java -s jdk1.6.0_45')
    else:
        execute('python version.py -t java -s java-7-openjdk-amd64')
    restore_dir()

    if args.variant:
        variant = args.variant
    else:
        if repo_type == 'upstream':
            variant = 'userdebug'
        else:
            variant = 'eng'


def init():
    if not args.init:
        return()

    if repo_type == 'stable':
        file_repo = 'http://android.intel.com/repo'
    elif repo_type == 'upstream':
        file_repo = 'https://storage.googleapis.com/git-repo-downloads/repo'

    execute('curl --noproxy intel.com %s >./repo' % file_repo, interactive=True)
    execute('chmod +x ./repo')

    if repo_type == 'stable':
        cmd = './repo init -u ssh://android.intel.com/a/aosp/platform/manifest -b abt/private/topic/aosp_stable/master'
    elif repo_type == 'upstream':
        cmd = './repo init -u https://android.googlesource.com/platform/manifest -b ' + args.repo_branch

    execute(cmd, interactive=True)
    execute('./repo sync -c -j16')
    execute('./repo start temp --all')


def sync():
    if not args.sync:
        return()

    if args.sync == 'all' or args.sync == 'aosp':
        info('Syncing aosp...')
        _sync_repo(dir_root, './repo sync -c -j16')

    if (args.sync == 'all' or args.sync == 'chromium') and os.path.exists(dir_chromium + '/src'):
        info('Syncing chromium...')
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

    for arch, device_type, module in [(arch, device_type, module) for arch in target_archs for device_type in target_devices_type for module in target_modules]:
        name_build = get_caller_name() + '-' + arch + '-' + device_type + '-' + module
        timer_start(name_build)

        combo = _get_combo(arch, device_type)
        if repo_type == 'upstream':
            dir_backup = '/workspace/topic/android/backup'
            dir_backup_driver = dir_backup + '/vendor'
            # Check proprietary binaries.
            dir_backup_spec_driver = dir_backup_driver + '/' + device + '/' + version + '/vendor'
            if not os.path.exists(dir_backup_spec_driver):
                error('Proprietary binaries do not exist')
                quit()
            execute('rm -rf vendor')
            execute('cp -rf ' + dir_backup_spec_driver + ' ./')

        if not args.build_skip_mk and os.path.exists(dir_root + '/external/chromium_org/src'):
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86'
            if arch == 'x86_64':
                cmd += ' && ' + dir_root + '/external/chromium_org/src/android_webview/tools/gyp_webview linux-x86_64'
            cmd = bashify(cmd)
            execute(cmd, interactive=True)

        if module == 'system' or module == 'cts':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && make '
            if module == 'system':
                cmd += 'dist'
            else:
                cmd += module
        elif module == 'browser' or module == 'webview' or module == 'libwebviewchromium':
            cmd = '. build/envsetup.sh && lunch ' + combo + ' && '
            if args.build_no_dep:
                cmd += 'mmm '
            else:
                cmd += 'mmma '

            if module == 'browser':
                cmd += 'packages/apps/Browser'
            elif module == 'webview':
                cmd += 'frameworks/webview'
            elif module == 'libwebviewchromium':
                cmd += 'external/chromium_org'

        if args.build_showcommands:
            cmd += ' showcommands'
        cmd += ' -j16 2>&1 |tee -a ' + file_log
        cmd = bashify(cmd)
        result = execute(cmd, interactive=True, dryrun=False)
        if result[0]:
            error('Failed to build %s %s %s' % (arch, device_type, module))

        if module == 'system' and device_type == 'generic':
            cmd = bashify('. build/envsetup.sh && lunch ' + combo + ' && external/qemu/android-rebuild.sh')
            result = execute(cmd, interactive=True)
            if result[0]:
                error('Failed to build %s emulator' % arch)

        timer_end(name_build)
        info('Time for ' + name_build + ': ' + timer_diff(name_build))


def backup():
    if not args.backup:
        return

    for arch, device_type, module in [(arch, device_type, module) for arch in target_archs for device_type in target_devices_type for module in target_modules]:
        _backup_one(arch, device_type, module)


def burn_image():
    if not args.burn_image:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail can burn the image')

    connect_device()

    arch = target_archs[0]
    device_type = target_devices_type[0]
    img = dir_out + '/target/product/' + get_product(arch, device_type, date=repo_date) + '/live.img'
    if not os.path.exists(img):
        error('Could not find the live image to burn')

    sys.stdout.write('Are you sure to burn live image to ' + args.burn_image + '? [yes/no]: ')
    choice = raw_input().lower()
    if choice not in ['yes', 'y']:
        return

    execute('sudo dd if=' + img + ' of=' + args.burn_image + ' && sync', interactive=True)


def flash_image():
    if not args.flash_image:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail can burn the image')

    connect_device()
    arch = target_archs[0]
    device_type = target_devices_type[0]
    path_fastboot = dir_linux + '/fastboot'

    # Prepare image
    if repo_type == 'stable':
        dir_extract = '/tmp/' + timestamp
        execute('mkdir ' + dir_extract)
        backup_dir(dir_extract)

        if args.file_image:
            if re.match('http', args.file_image):
                execute('wget ' + args.file_image, dryrun=False)
            else:
                execute('mv ' + args.file_image + ' ./')

            if args.file_image[-6:] == 'tar.gz':
                execute('tar zxf ' + args.file_image.split('/')[-1])
                execute('mv */* ./')
                result = execute('ls *.tgz', return_output=True)
                file_image = dir_extract + '/' + result[1].rstrip('\n')
            else:
                file_image = args.file_image.split('/')[-1]
        else:
            if repo_date >= 20140624:
                file_image = dir_root + '/out/dist/%s-om-factory.tgz' % get_product(arch, device_type, date=repo_date)
            else:
                file_image = dir_root + '/out/dist/aosp_%s-om-factory.tgz' % get_product(arch, device_type, date=repo_date)

        if not os.path.exists(file_image):
            error('File ' + file_image + ' used to flash does not exist, please have a check', abort=False)
            return

        execute('tar xvf ' + file_image, interactive=True)

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

    # Flash image
    # This command would not return so we have to use timeout here
    execute('timeout 5s ' + adb(cmd='reboot bootloader'))
    sleep_sec = 3
    is_connected = False
    for i in range(0, 60):
        if not connect_device(mode='bootloader'):
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            continue
        else:
            is_connected = True
            break

    if not is_connected:
        error('Can not connect to device in bootloader')

    if repo_type == 'gmin' or repo_type == 'upstream':
        combo = _get_combo(arch, device_type)
        cmd = bashify('. build/envsetup.sh && lunch ' + combo + ' && fastboot -t 192.168.42.1 -w flashall')
        execute(cmd, interactive=True)
    else:

        execute('./flash-all.sh -t ' + ip, interactive=True, dryrun=False)
        execute('rm -rf ' + dir_extract, dryrun=False)

        # This command would not return so we have to use timeout here
        cmd = 'timeout 10s %s -t %s reboot' % (path_fastboot, ip)
        execute(cmd)

        restore_dir()

    # Wait until system is up
    is_connected = False
    for i in range(0, 60):
        if not connect_device():
            info('Sleeping %s seconds' % str(sleep_sec))
            time.sleep(sleep_sec)
            continue
        else:
            is_connected = True
            break

    if not is_connected:
        error('Can not connect to device after system boots up')

    # It will take about 45s to boot to GUI
    info('Sleeping 60 seconds until system fully boots up..')
    time.sleep(60)

    if repo_type == 'stable':
        android_keep_screen_on()
        android_unlock_screen()
        # Remove guide screen
        android_tap()
        # After system boots up, it will show guide screen and never lock or turn off screen.
        android_set_screen_lock_none()
        android_set_display_sleep_30mins()


def start_emu():
    if not args.start_emu:
        return

    for arch in target_archs:
        product = get_product(arch, 'generic', date=repo_date)
        if args.dir_emu:
            dir_backup = args.dir_emu
        else:
            result = execute('ls -t -d --group-directories-first backup/*generic*', return_output=True)
            dir_backup = dir_root + '/' + result[1].split('\n')[0]
        backup_dir(dir_backup)

        if not os.path.exists(dir_root + '/sdcard-%s.img' % arch):
            error('Please put sdcard.img into ' + dir_root)

        if not os.path.exists('system-images/aosp_%(arch)s/userdata-qemu.img' % {'arch': arch}):
            execute('cp system-images/aosp_%(arch)s/userdata.img system-images/aosp_%(arch)s/userdata-qemu.img' % {'arch': arch})

        if arch == 'x86_64':
            gpu_type = 'on'
            file_emu = 'emulator64-x86'
        else:
            gpu_type = 'off'
            file_emu = 'emulator-x86'

        cmd = '''
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:%(dir_backup)s/emulator-linux/lib \
%(dir_backup)s/emulator-linux/%(file_emu)s -verbose -show-kernel -no-snapshot -gpu %(gpu_type)s -memory 512 \
-skin HVGA \
-skindir %(dir_backup)s/platforms/skins \
-kernel %(dir_backup)s/system-images/aosp_%(arch)s/kernel-qemu \
-ramdisk %(dir_backup)s/system-images/aosp_%(arch)s/ramdisk.img \
-sysdir %(dir_backup)s/system-images/aosp_%(arch)s \
-system %(dir_backup)s/system-images/aosp_%(arch)s/system.img \
-datadir %(dir_backup)s/system-images/aosp_%(arch)s \
-data %(dir_backup)s/system-images/aosp_%(arch)s/userdata-qemu.img \
-cache %(dir_backup)s/system-images/aosp_%(arch)s/cache.img \
-initdata %(dir_backup)s/system-images/aosp_%(arch)s/userdata.img \
-sdcard %(dir_root)s/sdcard-%(arch)s.img \
''' % {'dir_root': dir_root, 'dir_backup': dir_backup, 'product': product, 'arch': arch, 'gpu_type': gpu_type, 'file_emu': file_emu}

        execute(cmd, interactive=True)
        restore_dir()


def analyze():
    if not args.analyze:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    arch = target_archs[0]
    connect_device()
    analyze_issue(dir_aosp=dir_root, arch=arch, type=args.analyze, date=repo_date)


def push():
    if not args.push:
        return

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail is supported to analyze')

    arch = target_archs[0]
    device_type = target_devices_type[0]

    connect_device()

    if args.target_module == 'all':
        modules = ['libwebviewchromium', 'webview']
    else:
        modules = args.target_module.split(',')

    cmd = adb(cmd='root') + ' && ' + adb(cmd='remount') + ' && ' + adb(cmd='push out/target/product/%s' % get_product(arch, device_type, date=repo_date))

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


def hack_app_process():
    if not args.hack_app_process:
        return

    for device in devices:
        connect_device(device)
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
                cmd = adb(cmd='root', device=device) + ' && ' + adb(cmd='remount', device=device) + ' && ' + adb('push /tmp/' + file + ' /system/bin/')
                execute(cmd)


def cts_run():
    if not args.cts_run:
        return

    connect_device()

    if len(target_archs) > 1:
        error('You need to specify the target arch')

    if len(target_devices_type) > 1 or target_devices_type[0] != 'baytrail':
        error('Only baytrail can run cts')

    arch = target_archs[0]
    device_type = target_devices_type[0]

    combo = _get_combo(arch, device_type)
    cmd = bashify('. build/envsetup.sh && lunch ' + combo + ' && cts-tradefed run cts -p ' + args.cts_run)
    execute(cmd, interactive=True)


def _sync_repo(dir, cmd):
    backup_dir(dir)
    result = execute(cmd + ' 2>&1 |tee -a ' + file_log, interactive=True)
    if result[0]:
        error('Failed to sync ' + dir)
    restore_dir()


def _get_combo(arch, device_type):
    if repo_type == 'upstream':
        combo = 'full_' + codename[device_type] + '-' + variant
    elif device_type == 'generic':
        combo_prefix = 'aosp_'
        combo_suffix = '-' + variant
        combo = combo_prefix + arch + combo_suffix
    elif device_type == 'baytrail':
        if repo_type == 'stable' and repo_date >= 20140624 or repo_type == 'gmin':
            combo_prefix = 'asus_t100'
            combo_suffix = '-' + variant

            if arch == 'x86_64':
                combo = combo_prefix + '_64p' + combo_suffix
            elif arch == 'x86':
                combo = combo_prefix + combo_suffix
        else:
            combo_prefix = 'aosp_'
            combo_suffix = '-' + variant
            if arch == 'x86_64':
                combo = combo_prefix + device_type + '_64p' + combo_suffix
            elif arch == 'x86':
                combo = combo_prefix + device_type + combo_suffix

    return combo


# All valid combination:
# 1. x86_64, baytrail, webview
# 2. x86_64, baytrail, system
# 3. x86, baytrail, system
# 4. x86_64, generic, system
# 5. x86, generic, system
# (x86_64, generic, webview) is same as 1
# (x86, baytrail, webview) is included in 1
# (x86, generic, webview) is included in 1

def _backup_one(arch, device_type, module):
    product = get_product(arch, device_type, date=repo_date)

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
            if repo_date >= 20140624:
                prefix = ''
            else:
                prefix = 'aosp_'
            backup_files = {
                '.': [
                    'out/dist/%s%s-om-factory.tgz' % (prefix, get_product(arch, device_type, date=repo_date)),
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

        # TODO: Backup image for upstream
        #dest_dir = dir_backup_img + get_datetime() + '-' + device + '-' + variant + '/'
        #os.mkdir(dest_dir)
        #execute('cp ' + root_dir + 'out/target/product/' + device_code_name + '/*.img ' + dest_dir)

    name = timestamp + '-' + arch + '-' + device_type + '-' + module + '-' + chromium_version
    dir_backup_one = dir_backup + '/' + name
    if not os.path.exists(dir_backup_one):
        os.makedirs(dir_backup_one)
    backup_dir(dir_backup_one)
    info('Begin to backup to ' + dir_backup_one)
    for dir_dest in backup_files:
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)

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
        backup_smb('//wp-03.sh.intel.com/aosp', 'aosp-stable/temp', name_tar, dryrun=False)
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


# Now support:
# google, upstream
# intel, stable
# intel, mcg
def _get_repo_info():
    f = open('.repo/manifests.git/config')
    lines = f.readlines()
    f.close()

    for line in lines:
        if re.search('merge =', line):
            if re.search('aosp_stable', line):
                repo_type = 'stable'
            elif re.search('merge = master', line):
                repo_type = 'upstream'
            elif re.search('platform/android/r44c-stable', line):
                repo_type = 'mcg'
            elif re.search('gmin', line):
                repo_type = 'gmin'
            else:
                error('Could not find repo branch')

    if repo_type == 'stable' and os.path.exists('device/intel/baytrail/asus_t100'):
        repo_date = 20140624
    else:
        repo_date = 20140101

    return (repo_type, repo_date)


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
    burn_image()
    flash_image()
    start_emu()
    analyze()
    push()
    hack_app_process()
    cts_run()
