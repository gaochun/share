# todo
# logger
# try with cron jobs

# write down how to config
# Preparation:
# pip install selenium
# create x86 and arm emulator (use host GPU)
# history in readme
# apk tool is downloaded from https://code.google.com/p/android-apktool/downloads/list
# http://connortumbleson.com/apktool/test_versions
# 32761AAE6636D2A3

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import urllib2
from util import *

dir_root = ''
vers = []
ver_types = []
target_archs = []


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Script about chrome for android',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --ver 36.0.1985.81 --ver-type stable --target-arch x86
''')
    parser.add_argument('--ver', dest='ver', help='version', default='all')
    parser.add_argument('--ver-type', dest='ver_type', help='ver type', default='all')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', default='all')
    parser.add_argument('--run', dest='run', help='run', action='store_true')
    parser.add_argument('--buildid', dest='buildid', help='buildid', action='store_true')
    parser.add_argument('--check', dest='check', help='check', action='store_true')
    parser.add_argument('--backup', dest='backup', help='backup', action='store_true')
    parser.add_argument('--download', dest='download', help='download', action='store_true')

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    global dir_root, vers, ver_types, target_archs

    dir_root = get_symbolic_link_dir()

    if args.ver_type == 'all':
        ver_types = ['stable', 'beta']
    else:
        ver_types = args.ver_type.split(',')

    if args.target_arch == 'all':
        target_archs = ['x86', 'arm']
    else:
        target_archs = args.target_arch.split(',')


def run(force=False):
    if not args.run and not force:
        return

    if not os.path.exists(chrome_android_dir_server_todo):
        os.makedirs(chrome_android_dir_server_todo)
        return

    cmd_common = python_chromium + ' --repo-type chrome-android --target-os android --target-module chrome'
    backup_dir(chrome_android_dir_server_todo)
    todos = os.listdir('.')
    execute('rm -rf temp')
    for todo in todos:
        if os.path.isfile(todo):
            cmd = cmd_common + ' --dir-root ' + chrome_android_dir_server_todo
            cmd += ' --chrome-android-apk ' + todo
            cmd += ' --buildid'
            execute(cmd, interactive=True)
        elif os.path.isdir(todo):
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


def check():
    if not args.check:
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
    info('The following combos need to be downloaded: ' + ','.join(str(i) for i in combos_new))


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


def download():
    if not args.download:
        return

    dir_download = chrome_android_dir_server_todo + '/download'
    execute('rm -rf %s/*' % dir_download)

    # download the apk
    env_http_proxy = getenv('http_proxy')
    unsetenv('http_proxy')
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['ignore-certificate-errors', 'disable-default-apps', 'user-data-dir'])
    options.add_argument('user-data-dir=%s' % (dir_tool + '/chrome-profile'))
    options.add_argument('start-maximized')
    driver = webdriver.Chrome(executable_path=dir_tool + '/chromedriver', chrome_options=options, service_args=['--verbose', '--log-path=/dev/null'])
    driver.get('https://play.google.com/store/apps/details?id=com.android.chrome')
    WebDriverWait(driver, 30, 1).until(_has_element)
    mouse_move(1370, 70)
    mouse_click()
    while True:
        files = os.listdir(dir_download)
        if files and not re.search('crdownload', files[0]):
            break
        time.sleep(3)
    driver.quit()
    setenv('http_proxy', env_http_proxy)

    # check with existed build
    apk_new = files[0]
    dirs_check = os.listdir(dir_server_chromium + '/android-arm-chrome') + os.listdir(chrome_android_dir_server_todo + '/arm')
    pattern = '\d+\.\d+\.(\d+)\.(\d+)'
    for dir_check in dirs_check:
        match = re.search(pattern, dir_check)
        if not match:
            continue

        ver_build_patch = match.group(1) + match.group(2)
        if ver_build_patch == apk_new:
            info('The downloaded apk ' + apk_new + ' has been there at ' + dir_check)
            execute('rm -f %s/%s' % (dir_download, apk_new))
            return

    content = 'A new Chrome for Android apk %s has been found at Google Play.' % apk_new
    send_mail('webperf@intel.com', 'yang.gu@intel.com', 'New Chrome for Android at Google Play', content, type='html')
    execute('mv %s/%s %s' % (dir_download, apk_new, chrome_android_dir_server_todo), dryrun=False)
    run(force=True)


def _has_element(driver):
    if driver.find_elements_by_class_name('document-title'):
        return True
    else:
        return False


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
    backup()
    download()
