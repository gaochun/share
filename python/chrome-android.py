# Preparation:
# pip install selenium
# create x86 and arm emulator (use host GPU)

import urllib2
from util import *
from chromium import ver_info
from chromium import VER_INFO_INDEX_TYPE
from chromium import VER_INFO_INDEX_STAGE
from chromium import VER_INFO_INDEX_BUILD_ID
from chromium import target_arch_index
from chromium import chrome_android_dir_server_todo

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

# apk tool is downloaded from https://code.google.com/p/android-apktool/downloads/list
# http://connortumbleson.com/apktool/test_versions

# tools: android-sdk-linux/build-tools/20.0.0

dir_root = ''
vers = []
ver_types = []
target_archs = []
pkg_name = {
    'stable': 'com.android.chrome',
    'beta': 'com.chrome.beta',
    'example': 'com.example.chromium',
}

# download: download Chrome.apk and put into todo
# buildid: install Chrome.apk to device to check version, version type, arch, and create README to record build id and stage.
# init: init the source code repo. depends on ver.
# sync: sync source code. depends on ver.
# runhooks: runhooks to make source code directory ready to build. depends on ver and parts of them rely on target_arch.
# prebuild: extra things to prepare for prebuild. depends on ver and target_arch.
# makefile: generate makefile. depends on ver and target_arch.
# build: build. depends on ver and target_arch.
# postbuild: generate new package, so with symbol, etc. depends on ver, target_arch and ver_type.
# verify: install new package to device to verify its correctness.  depends on ver, target_arch and ver_type.
# notify: send out email notification.  depends on ver, target_arch and ver_type.
phase_all = ['buildid', 'init', 'sync', 'runhooks', 'prebuild', 'makefile', 'build', 'postbuild', 'verify', 'backup', 'notify']


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
    parser.add_argument('--phase', dest='phase', help='phase, including ' + ','.join(phase_all), default='all')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--buildid', dest='buildid', help='buildid', action='store_true')
    parser.add_argument('--check', dest='check', help='check', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, vers, ver_types, target_archs

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


def buildid(force=False):
    if not args.buildid and not force:
        return

    # find a device for each target_arch
    (devices, devices_name, devices_type, devices_target_arch) = setup_device()
    target_arch_device = {}
    for index, device in enumerate(devices):
        target_arch_temp = devices_target_arch[index]
        if not target_arch_temp in target_arch_device:
            target_arch_device[target_arch_temp] = devices[index]

    if not os.path.exists(chrome_android_dir_server_todo):
        os.makedirs(chrome_android_dir_server_todo)
        return
    backup_dir(chrome_android_dir_server_todo)
    files_todo = os.listdir('.')
    for file_todo in files_todo:
        # skip the directory
        if not os.path.isfile(file_todo):
            continue
        # get the target arch
        execute('unzip "%s" -d temp' % file_todo, show_command=True)
        if os.path.exists('temp/lib/armeabi-v7a'):
            target_arch_temp = 'arm'
        elif os.path.exists('temp/lib/x86'):
            target_arch_temp = 'x86'
        else:
            error('Arch is not supported for ' + todo)
        execute('rm -rf temp', show_command=False)

        # get the version type
        if target_arch_temp not in target_arch_device:
            android_start_emu(target_arch_temp)
            (devices, devices_name, devices_type, devices_target_arch) = setup_device()
            target_arch_device = {}
            for index, device in enumerate(devices):
                target_arch_temp = devices_target_arch[index]
                if not target_arch_temp in target_arch_device:
                    target_arch_device[target_arch_temp] = devices[index]
            if not target_arch_temp not in target_arch_device:
                continue

        device = target_arch_device[target_arch_temp]
        android_unlock_screen(target_arch_device[target_arch_temp])
        chrome_android_cleanup(device)
        execute(adb(cmd='install -r "%s"' % file_todo, device=device), interactive=True, dryrun=False)
        ver_type_temp = chrome_android_get_ver_type(device)
        # get version and build id
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

        driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)
        driver.get('chrome://version')
        WebDriverWait(driver, 30, 1).until(_has_element_ver)

        pattern_version = re.compile('(Chrome|Chrome Beta) (\d+\.\d+\.\d+\.\d+)')
        match = pattern_version.search(driver.find_elements_by_class_name('version')[0].get_attribute('innerText'))
        ver_temp = match.group(2)

        pattern_build_id = re.compile('Build ID\s+(.*)')
        match = pattern_build_id.search(driver.find_elements_by_id('build-id-section')[0].get_attribute('innerText'))
        build_id_temp = match.group(1)
        driver.quit()
        execute(adb('uninstall ' + chrome_android_ver_type_info[ver_type_temp][CHROME_ANDROID_VER_TYPE_INFO_INDEX_PKG], device=device))

        setenv('http_proxy', env_http_proxy)

        dir_todo = '%s/%s-%s' % (target_arch_temp, ver_temp, ver_type_temp)
        if os.path.exists(dir_todo):
            warning('The todo directory already exists for ' + file_todo)
            continue
        os.makedirs(dir_todo)
        execute('mv "%s" %s/Chrome.apk' % (file_todo, dir_todo))
        execute('echo "phase=buildid\nbuild-id=%s" >%s/README' % (build_id_temp, dir_todo), show_command=False)


def run():
    if not args.run:
        return

    buildid(force=True)

    dirs_target_arch = os.listdir(chrome_android_dir_server_todo)
    for target_arch_temp in dirs_target_arch:
        # skip the file
        if os.path.isfile(target_arch_temp):
            continue
        if target_arch_temp not in target_arch_all:
            continue

        dirs_todo = os.listdir(chrome_android_dir_server_todo + '/' + target_arch_temp)
        for dir_todo in dirs_todo:
            info = dir_todo.split('-')
            ver_temp = info[0]
            ver_type_temp = info[1]
            file_readme = chrome_android_dir_server_todo + '/' + target_arch_temp + '/' + dir_todo + '/README'
            if not os.path.exists(file_readme):
                warning('Could not find README in ' + dir_todo)
                continue
            f = open(file_readme)
            lines = f.readlines()
            f.close()

            pattern = re.compile('phase=(.*)')
            match = pattern.search(lines[0])
            if not match:
                warning('Could not find phase in README of ' + dir_todo)
                continue

            phase = match.group(1)
            index_phase = phase_all.index(phase)
            for index in range(index_phase + 1, len(phase_all)):
                phase_temp = phase_all[index]
                cmd = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome --' + phase_temp
                cmd += ' --dir-root ' + dir_root + '/' + ver_temp
                cmd += ' --target-arch ' + target_arch_temp
                cmd += ' --ver-type ' + ver_type_temp
                if phase_temp == 'build':
                    cmd += ' --build-skip-mk --build-fail-max 1'
                result = execute(cmd, interactive=True)
                if result[0]:
                    warning('Failed to finish phase %s for %s %s' % (phase_temp, target_arch_temp, dir_todo))
                    break


def check():
    if not args.check:
        return

    _check_track()

    # Check how many builds left
    combos_incomplete = []
    for target_arch, ver, ver_type in [(target_arch, ver, ver_type) for target_arch in target_archs for ver in vers for ver_type in ver_types]:
        if ver_info[ver][VER_INFO_INDEX_BUILD_ID][target_arch_index[target_arch]] == '':
            continue

        if ver_type not in ver_info[ver][VER_INFO_INDEX_TYPE]:
            continue

        dir_server_ver = dir_server_chromium + '/android-%s-chrome/%s-%s' % (target_arch, ver, ver_type)
        if not os.path.exists(dir_server_ver):
            combos_incomplete.append((ver, ver_type, target_arch))
        else:
            backup_dir(dir_server_ver)
            if not os.path.exists('Chromium.apk') or not os.path.exists('Chrome.apk') or ver_ge(ver, '34.0.0.0') and execute('ls *.so', show_command=False)[0]:
                combos_incomplete.append((ver, ver_type, target_arch))
            restore_dir()

    if len(combos_incomplete) > 0:
        info('The following builds are not complete: ' + str(combos_incomplete))
    else:
        info('All the tracked versions are complete')

    # Check if some stage is marked wrongly
    vers_incomplete = []
    for combo in combos_incomplete:
        ver = combo[0]
        if ver not in vers_incomplete:
            vers_incomplete.append(ver)

    vers_stage_error = []
    for ver in ver_info:
        if ver_info[ver][VER_INFO_INDEX_STAGE] == 'end' and ver in vers_incomplete:
            vers_stage_error.append(ver)

    if len(vers_stage_error) > 0:
        info('The following versions has incorrect stage: ' + ','.join(vers_stage_error))
    else:
        info('The stage of all versions are marked correctly')


def _has_element_ver(driver):
    if driver.find_elements_by_class_name('version'):
        return True
    else:
        return False


def _check_track():
    url = 'http://www.hiapphere.org/app-chrome_beta'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        warning('Failed to open ' + url)
        return

    html = u.read()
    pattern = re.compile('Version(\d+\.\d+\.\d+\.\d+)')
    vers_exist = pattern.findall(html)
    vers_track = ver_info.keys()
    vers_miss = []
    ver_min = vers_track[-1]
    for ver in vers_exist:
        if ver_ge(ver, ver_min) and ver not in vers_track:
            vers_miss.append(ver)

    if len(vers_miss) > 0:
        info('Please add following versions to ver_info: ' + ','.join(vers_miss))
    else:
        info('All existed versions have been fully tracked')


if __name__ == "__main__":
    parse_arg()
    setup()
    buildid()
    run()
    check()
