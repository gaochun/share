# Preparation:
# Emulator: Used for build id and verification. Download the adt, and create x86 and arm emulators (use host GPU)
# Webdriver: Used for build id and verification. pip install selenium, and download chromedriver
# Apk tool: Download it from http://connortumbleson.com/apktool/test_versions
# Download:
#    Install Chrome
#    Set its download directory as /workspace/server/chromium/android-chrome-todo/download
#    Open it with google-chrome --user-data-dir /workspace/tool/chrome-profile
#    Install extension SwitchySharp
#    Install extension at share/python/apk-downloader
#    Login extension with: webperf0@gmail.com and 32761AAE6636D2A3 as device id.

from selenium import webdriver
import urllib2
from util import *

dir_root = dir_project + '/chrome-android'
dir_log = dir_root + '/log'
vers = []
ver_types = []
target_archs = []

ACT_CHECK = 1 << 0
ACT_FILE = 1 << 1
ACT_DIR = 1 << 2
ACT_ALL = ACT_CHECK | ACT_FILE | ACT_DIR


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --ver-type stable --target-arch x86
''')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--check', dest='check', help='check if there is new apk', action='store_true')
    parser.add_argument('--download', dest='download', help='download apk from google play', action='store_true')
    parser.add_argument('--download_type', dest='download_type', help='version type to download', default='all')
    parser.add_argument('--backup', dest='backup', help='backup', action='store_true')

    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global vers, ver_types, target_archs

    if not os.path.exists(dir_log):
        os.mkdir(dir_log)

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


def run(force=False, act=ACT_ALL):
    if not args.run and not force:
        return

    if act & ACT_CHECK:
        check(force=True)

    if not os.path.exists(chrome_android_dir_server_todo):
        os.makedirs(chrome_android_dir_server_todo)
        return

    cmd_common = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome'
    backup_dir(chrome_android_dir_server_todo)
    todos = os.listdir('.')
    execute('rm -rf temp', show_command=False)
    for todo in todos:
        if os.path.isfile(todo) and act & ACT_FILE:
            cmd = cmd_common + ' --dir-root ' + chrome_android_dir_server_todo
            cmd += ' --chrome-android-apk ' + todo
            cmd += ' --buildid'
            execute(cmd, interactive=True)
        elif os.path.isdir(todo) and act & ACT_DIR:
            target_arch_temp = todo
            if target_arch_temp not in target_arch_all:
                continue

            dirs_todo = os.listdir(chrome_android_dir_server_todo + '/' + target_arch_temp)
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


def check(force=False):
    if not args.check and not force:
        return

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
        if not ver_ge(ver, '33.0.1750.132'):
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
        dirs_todo = os.listdir(chrome_android_dir_server_todo + '/%s' % target_arch)
        combos_todo += _get_combos(dirs_todo, target_arch)

    combos_new = sorted(list_diff(combos_all, list_union(combos_done, combos_todo)))
    if len(combos_new):
        content = 'The following combos need to be downloaded: ' + ','.join(str(i) for i in combos_new)
        info(content)
        send_mail('webperf@intel.com', 'yang.gu@intel.com', 'New Chrome for Android at Google Play', content, type='html')
    else:
        info('Great! All the known versions have been built')


def download():
    if not args.download:
        return

    dir_download = chrome_android_dir_server_todo + '/download'
    if not os.path.exists(dir_download):
        os.mkdir(dir_download)
    execute('rm -rf %s/*' % dir_download)

    dir_trash = chrome_android_dir_server_todo + '/trash'
    if not os.path.exists(dir_trash):
        os.mkdir(dir_trash)

    # download the apk
    env_http_proxy = getenv('http_proxy')
    unsetenv('http_proxy')
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['user-data-dir', 'ignore-certificate-errors', 'disable-default-apps'])
    options.add_argument('user-data-dir=%s' % (dir_tool + '/chrome-profile'))
    driver = webdriver.Chrome(executable_path=dir_tool + '/chromedriver', chrome_options=options, service_args=['--verbose', '--log-path=%s/log/chromedriver.log' % dir_root])

    if args.download_type == 'all' or args.download_type == 'stable':
        driver.get('https://play.google.com/store/apps/details?id=' + chromium_android_info['chrome_stable'][CHROMIUM_ANDROID_INFO_INDEX_PKG])
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
    setenv('http_proxy', env_http_proxy)

    execute('mv %s/* %s' % (dir_download, chrome_android_dir_server_todo), dryrun=False)
    run(force=True, act=(ACT_FILE | ACT_DIR))


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


if __name__ == "__main__":
    parse_arg()
    setup()
    run()
    check()
    download()
    backup()
