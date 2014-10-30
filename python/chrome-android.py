# Preparation:
# Emulator: Used for build id and verification. Download the adt, and create x86 and arm emulators (use host GPU)
# Webdriver: Used for build id and verification. pip install selenium, and download chromedriver
# Apk tool: Download it from http://connortumbleson.com/apktool/test_versions
# Download:
#    Install Chrome
#    Set its download directory as /workspace/server/chromium/android-chrome-todo/download
#    Open it with google-chrome --user-data-dir=/workspace/tool/arm/chrome-profile
#    Open it with google-chrome --user-data-dir=/workspace/tool/x86/chrome-profile
#    Install extension SwitchySharp
#    Install extension at share/python/apk-downloader
#    Login extension with: webperf0@gmail.com and 32761AAE6636D2A3(arm)/376FCD341892D871(x86) as device id.

from selenium import webdriver
import urllib2
from util import *

dir_root = dir_project + '/chrome-android'
vers = []
ver_types = []
target_archs = []
run_act = 0

ACT_DOWNLOAD = 1 << 0
ACT_FILE = 1 << 1
ACT_DIR = 1 << 2
ACT_CHECK = 1 << 3
ACT_ALL = ACT_DOWNLOAD | ACT_FILE | ACT_DIR | ACT_CHECK

cmd_common = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome'

devices_id = []


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --ver-type stable --target-arch x86
''')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--run-act', dest='run_act', help='run act', type=int, default=ACT_ALL)
    parser.add_argument('--check', dest='check', help='check if there is new apk', action='store_true')
    parser.add_argument('--download', dest='download', help='download apk from google play', action='store_true')
    parser.add_argument('--download_type', dest='download_type', help='version type to download', default='all')
    parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
    parser.add_argument('--backup-ver', dest='backup_ver', help='backup versions less than the designated')
    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')
    parser.add_argument('--analyze', dest='analyze', help='analyze test tombstone', action='store_true')
    parser.add_argument('--analyze-type', dest='analyze_type', help='type to analyze', choices=['tombstone', 'anr'], default='tombstone')
    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global vers, ver_types, target_archs, run_act
    global dir_root, log, timestamp

    (timestamp, dir_root, log) = setup_common(args, _teardown)

    if args.ver_type == 'all':
        ver_types = ['stable', 'beta']
    else:
        ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['x86', 'arm']
    else:
        target_archs = args.target_arch.split(',')

    for target_arch in target_archs:
        dir_temp = dir_server_chromium + '/android-%s-chrome/archive' % target_arch
        if not os.path.exists(dir_temp):
            os.makedirs(dir_temp)

    ensure_dir(dir_server_chrome_android_todo)
    run_act = args.run_act


def run(force=False, act=ACT_ALL):
    if not args.run and not force:
        return

    if act & ACT_DOWNLOAD:
        download(force=True)

    if act & ACT_FILE:
        _handle_todo_file()

    if act & ACT_DIR:
        _handle_todo_dir()

    if act & ACT_CHECK:
        check(force=True)


def download(force=False):
    if not args.download and not force:
        return

    dir_download = dir_server_chrome_android_todo + '/download'
    ensure_dir(dir_download)
    execute('rm -rf %s/*' % dir_download)

    dir_trash = dir_server_chrome_android_todo + '/trash'
    ensure_dir(dir_trash)

    # download the apk
    for target_arch in target_arch_chrome_android:
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['user-data-dir', 'ignore-certificate-errors', 'disable-default-apps'])
        options.add_argument('user-data-dir=%s' % (dir_tool + '/' + target_arch + '/chrome-profile'))
        driver = webdriver.Chrome(executable_path=dir_tool + '/chromedriver', chrome_options=options, service_args=['--verbose', '--log-path=%s/chromedriver-%s.log' % (dir_share_ignore_log, timestamp)])

        if args.download_type == 'all' or args.download_type == 'stable':
            driver.get('https://play.google.com/store/apps/details?id=' + chromium_android_info['chrome_stable'][CHROMIUM_ANDROID_INFO_INDEX_PKG])
        time.sleep(3)
        if args.download_type == 'all' or args.download_type == 'beta':
            driver.get('https://play.google.com/store/apps/details?id=' + chromium_android_info['chrome_beta'][CHROMIUM_ANDROID_INFO_INDEX_PKG])

        finished = False
        while not finished:
            finished = True
            files = os.listdir(dir_download)
            if not files:
                finished = False
            else:
                for f in files:
                    if re.search('crdownload', f):
                        finished = False
                        break

            if not finished:
                time.sleep(3)

        driver.quit()

    execute('mv %s/* %s' % (dir_download, dir_server_chrome_android_todo), dryrun=False)


def check(force=False):
    if not args.check and not force:
        return

    info('Begin to check..')
    content = ''
    subject = ''

    # get all the combos
    url = 'http://www.hiapphere.org/app-chrome_beta'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        warning('Failed to open ' + url)
        return

    html = u.read()
    pattern = re.compile('Version(\d+\.\d+\.\d+\.\d+)')
    vers_all = pattern.findall(html)
    combos_all = []
    for ver in vers_all:
        if ver_cmp(ver, '33.0.1750.132') < 0:
            continue
        for target_arch in target_arch_chrome_android:
            combos_all.append((target_arch, ver))

    # get all combos done
    combos_done = []
    for target_arch in target_arch_chrome_android:
        dirs_done = os.listdir(dir_server_chromium + '/android-%s-chrome' % target_arch)
        dirs_done += os.listdir(dir_server_chromium + '/android-%s-chrome/archive' % target_arch)
        combos_done += _get_combos(dirs_done, target_arch)

    # get all combos todo
    combos_todo = []
    for target_arch in target_arch_chrome_android:
        dirs_todo = os.listdir(dir_server_chrome_android_todo + '/%s' % target_arch)
        combos_todo += _get_combos(dirs_todo, target_arch)

    combos_new = sorted(list_diff(combos_all, list_union(combos_done, combos_todo)))

    if len(combos_new):
        subject += ' download required'
        content += 'The following combos need to be downloaded: ' + ','.join(str(i) for i in combos_new) + '<br>'
    else:
        subject += ' download clean'

    if len(combos_todo):
        subject += ' build required'
        content += 'The following combos need to be built: ' + ','.join(str(i) for i in combos_todo) + '<br>'
    else:
        subject += ' build clean'

    info(content)
    if host_name == 'wp-03':
        to = ['yang.gu@intel.com', 'zhiqiangx.yu@intel.com']
        send_mail('webperf@intel.com', to, 'Chrome for Android -' + subject, content, type='html')


def backup():
    if not args.backup:
        return

    for target_arch in target_arch_chrome_android:
        dirs = os.listdir(dir_server_chromium + '/android-%s-chrome' % target_arch)
        for dir_temp in dirs:
            if dir_temp == 'archive':
                continue

            info_temp = dir_temp.split('-')
            ver_temp = info_temp[0]
            ver_type_temp = info_temp[1]

            dir_chrome = 'chromium/android-%s-chrome/%s-%s' % (target_arch, ver_temp, ver_type_temp)
            execute('smbclient %s -N -c "prompt; recurse; mkdir %s;"' % (path_server_backup, dir_chrome))
            backup_dir(dir_server + '/' + dir_chrome)
            if os.path.exists('Chrome.apk'):
                backup_smb(path_server_backup, dir_chrome, 'Chrome.apk')
                backup_smb(path_server_backup, dir_chrome, 'Chromium.apk')
                backup_smb(path_server_backup, dir_chrome, 'README')
            else:
                backup_smb(path_server_backup, dir_chrome, 'Null.apk')
            restore_dir()


def backup_ver():
    if not args.backup_ver:
        return

    dirs = os.listdir('.')
    for dir_ver in dirs:
        if re.match('\d+\.\d+\.\d+\.\d+', dir_ver) and ver_cmp(dir_ver, args.backup_ver) <= 0:
            execute('tar zcf %s.tar.gz %s' % (dir_ver, dir_ver))
            backup_smb(path_server_backup, 'chromium', '%s.tar.gz' % dir_ver)


def analyze():
    if not args.analyze:
        return

    _setup_device()
    lines = analyze_file(device_id=devices_id[0], type=args.analyze_type)
    dirs_symbol = []
    pattern = re.compile('libchrome\.(.*)\.so')
    for line in lines:
        match = pattern.search(line)
        if match:
            ver_part = match.group(1)
            break

    dir_android_chrome = dir_server_chromium + '/android-x86-chrome'
    dirs = os.listdir(dir_android_chrome)
    for d in dirs:
        if re.search(ver_part, d):
            dirs_symbol.append(dir_android_chrome + '/' + d)
            break

    get_symbol(lines, dirs_symbol)


def _setup_device():
    global devices_id, devices_product, devices_type, devices_arch, devices_mode

    if devices_id:
        return

    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device()


def _get_combos(dirs_check, target_arch):
    combos = []
    pattern = re.compile('(\d+\.\d+\.\d+\.\d+)-(stable|beta)')

    for dir_check in dirs_check:
        match = pattern.search(dir_check)
        if not match:
            continue
        ver_temp = match.group(1)

        combos.append((target_arch, ver_temp))

    return combos


def _handle_todo_file():
    backup_dir(dir_server_chrome_android_todo)
    todos = os.listdir('.')
    for todo in todos:
        if os.path.isfile(todo):
            cmd = cmd_common + ' --dir-root ' + dir_server_chrome_android_todo
            cmd += ' --chrome-android-apk "' + todo + '"'
            cmd += ' --buildid'
            execute(cmd, interactive=True)

    restore_dir()


def _handle_todo_dir():
    backup_dir(dir_server_chrome_android_todo)
    todos = os.listdir('.')
    for todo in todos:
        if os.path.isdir(todo):
            target_arch_temp = todo
            if target_arch_temp not in target_arch_all:
                continue

            dirs_todo = os.listdir(dir_server_chrome_android_todo + '/' + target_arch_temp)
            for dir_todo in dirs_todo:
                info = dir_todo.split('-')
                ver_temp = info[0]
                ver_type_temp = info[1]

                cmd = cmd_common + ' --dir-root ' + dir_root + '/' + ver_temp
                cmd += ' --target-arch ' + target_arch_temp
                cmd += ' --ver ' + ver_temp
                cmd += ' --ver-type ' + ver_type_temp
                cmd += ' --phase-continue'

                execute(cmd, interactive=True)
    restore_dir()


def _teardown():
    pass


if __name__ == "__main__":
    parse_arg()
    setup()
    run(act=run_act)
    check()
    download()
    backup()
    backup_ver()
    analyze()
