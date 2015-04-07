#/usr/bin/python

# Post-execution steps for a development machine:
# Set vnc connection
# Install display card driver, slickedit, sublime text.
# Set keyboard shortcut: 'nautilus /workspace' -> ctrl+alt+E
# Set input method: gnome-session-properties


from util import *
is_sylk = True
pkg_chromium = 'google-chrome-stable'
pkgs_common = [
    'tsocks', 'privoxy',
    'apache2',
    'apt-file',
    'zsh',
    'git', 'git-svn', 'subversion',
    'gparted',
    'gnome-shell',
    'vim',
    'ssh',
    'most',
    'binutils',
    'vnc4server',
    'cmake',
    'hibernate',
    'python-dev', 'python-psutil',
    'ccache',
    'alacarte',
    'libicu-dev',
    # <chromium>
    'libspeechd-dev', 'libgdk-pixbuf2.0-dev', 'libgtk2.0-dev', 'libdrm-dev', 'libgnome-keyring-dev', 'libgconf2-dev', 'libudev-dev',
    'libpci-dev', 'linux-tools-generic', 'binutils-dev', 'libelf-dev', 'gperf', 'bison', 'python-pip',
    'module-assistant', 'autoconf', 'automake', 'libnss3-dev', 'ant', 'libcups2-dev', 'libasound2-dev', 'libxss-dev', 'libxtst-dev',
    'libpulse-dev', 'libexif-dev', 'libkrb5-dev', 'libcap-dev', 'linux-libc-dev:i386',
    'libc6-dev-i386', 'g++-multilib',  # clang build
    'zlib1g:i386',  # apk build, used by aapt
    # </chromium>
    'postfix',  # smtp server
    'android-tools-adb',
    'dos2unix',
    'lib32z1',
    'openjdk-7-jdk',
    'dconf-editor',
    'dnsmasq',
    #'lighttpd',
    'meld',

    # Package used at home
    'openconnect', 'python-zsi', 'openssh-server', 'vpnc',

    # adb
    'libc6:i386', 'libc++-dev',  # 'stdlibc++6:i386',
]


def parse_arg():
    global args
    parser = argparse.ArgumentParser(description='Script to set up a machine',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Examples:
  python %(prog)s --default
''')
    parser.add_argument('--default', dest='default', help='default setup', action='store_true')
    parser.add_argument('--time', dest='time', help='set system time and hardware clock time with "MM/dd/yyyy hh:mm:ss" format')
    parser.add_argument('--update-system', dest='update_system', help='update system', action='store_true')
    parser.add_argument('--update-force', dest='update_force', help='avoid the check of recent update and update anyway', action='store_true')
    parser.add_argument('--cleanup', dest='cleanup', help='cleanup and release more disk space', action='store_true')
    parser.add_argument('--install-chromium', dest='install_chromium', help='install chromium', action='store_true')
    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        quit()


def setup():
    for machine in machines:
        if host_name == machine[MACHINES_INDEX_HOSTNAME]:
            break
    else:
        if not confirm('Your machine is not officially supported. Are you sure to proceed?'):
            return

    backup_dir(dir_share_python)


def patch_sudo(force=False):
    if not force:
        return

    file_name = '10_' + username + '_sudo'
    sudo_file = '/etc/sudoers.d/' + file_name

    if os.path.exists(sudo_file):
        info('You already set sudo without password before')
    else:
        execute('sudo echo "' + username + ' ALL=NOPASSWD:ALL" >' + file_name)
        execute('chmod 0440 ' + file_name)
        execute('sudo chown root:root ' + file_name)
        result = execute('sudo mv ' + file_name + ' ' + sudo_file)
        if result[0] == 0:
            info('Now you can sudo without password')
            # No need to run following command to take effect
            #execute('/etc/init.d/sudo restart')
        else:
            warning('Failed to enable sudo')


def time():
    if not args.time:
        return

    execute('sudo date -s "%s"' % args.time)
    execute('sudo hwclock --set --date="%s"' % args.time)


def update(force=False):
    if not args.update_system and not force:
        return

    if force:
        if has_recent_change('/var/lib/apt/lists') and not args.update_force:
            info('Packages have been upgraded recently')
        else:
            execute('sudo apt-get update && sudo apt-get --force-yes -y dist-upgrade', interactive=True)
            # This takes quite a long time
            #execute('sudo apt-file update', interactive=True)

    if args.update_system:
        execute('sudo update-manager -d', interactive=True)


def install_pkg(force=False):
    global pkgs_common

    if not force:
        return

    execute('sudo apt-mark hold ' + pkg_chromium, show_cmd=False)

    ver_gcc_result = execute('ls -l /usr/bin/gcc', show_cmd=False, return_output=True)
    match = re.match('.+gcc-(.+)', ver_gcc_result[1])
    if match:
        ver_gcc = match.group(1)
        pkgs_common.append('gcc-%s-multilib' % ver_gcc)
        pkgs_common.append('g++-%s-multilib' % ver_gcc)

    for pkg in pkgs_common:
        _install_one_pkg(pkg)

    execute('sudo apt-mark unhold ' + pkg_chromium, show_cmd=False)


def _install_one_pkg(pkg):
    if not package_installed(pkg):
        info('Package ' + pkg + ' is installing...')
        result = execute('sudo apt-get install --force-yes -y ' + pkg, interactive=True)
        if result[0]:
            warning('Package ' + pkg + ' installation failed')


def install_chromium():
    if not args.install_chromium:
        return

    if package_installed(pkg_chromium):
        return

    if not os.path.islink(dir_share_linux_config + '/apt/addon.list'):
        copy_file(dir_share_linux_config + '/apt', 'addon.list', '/etc/apt/sources.list.d', is_sylk=is_sylk)
        execute('sudo apt-get update')
        _install_one_pkg('google-chrome-stable')


def config_before_update():
    copy_file(dir_share_linux_config + '/apt', 'apt.conf', '/etc/apt', is_sylk=is_sylk)
    copy_file(dir_share_linux_config + '/apt', 'sources.list', '/etc/apt', is_sylk=is_sylk)


def config_after_update():
    # Change default shell
    execute('sudo chsh -s /bin/zsh ' + username, show_cmd=False)

    copy_file(dir_share_linux_config, 'bashrc', dir_home, '.bashrc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'gdbinit', dir_home, '.gdbinit', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'gitconfig', dir_home, '.gitconfig', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'vimrc', dir_home, '.vimrc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'zshrc', dir_home, '.zshrc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'privoxy-config', '/etc/privoxy', 'config', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'subversion-servers', '/etc/subversion', 'servers', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'ssh-config', dir_home + '/.ssh', 'config', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'tsocks.conf', '/etc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, 'proxychains.conf', '/etc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config, '51-android.rules', '/etc/udev/rules.d', is_sylk=is_sylk)

    copy_file(dir_share_linux_config, 'androidtool.cfg', dir_home + '/.android', is_sylk=is_sylk)

    copy_file(dir_share_linux_config + '/dnsmasq', 'dnsmasq.conf', '/etc', is_sylk=is_sylk)
    copy_file(dir_share_linux_config + '/hostapd', 'hostapd.conf', '/etc/hostapd', is_sylk=is_sylk)

    copy_file(dir_share_python, 'aosp.py', dir_project + '/aosp', is_sylk=is_sylk)
    copy_file(dir_share_python, 'aosp.py', dir_project + '/aosp-gminl', is_sylk=is_sylk)
    copy_file(dir_share_python, 'aosp.py', dir_project + '/aosp-stable', is_sylk=is_sylk)

    copy_file(dir_share_python, 'chromium.py', dir_project + '/chromium-linux', is_sylk=is_sylk)
    copy_file(dir_share_python, 'chromium.py', dir_project + '/chromium-android', is_sylk=is_sylk)

    copy_file(dir_share_python, 'skia.py', dir_project + '/skia', is_sylk=is_sylk)

    copy_file(dir_share_web, 'dashboard.html', dir_server_dashboard, is_sylk=is_sylk)

    # sublime
    for version in ['2', '3']:
        copy_file(dir_share_common + '/sublime/%s' % version, 'Preferences.sublime-settings', dir_home + '/.config/sublime-text-%s/Packages/User' % version, is_sylk=is_sylk)
        copy_file(dir_share_common + '/sublime/%s' % version, 'SublimeLinter.sublime-settings', dir_home + '/.config/sublime-text-%s/Packages/User' % version, is_sylk=is_sylk)

    # Chromium build
    copy_file('/usr/include/x86_64-linux-gnu', 'asm', '/usr/include', is_sylk=is_sylk)

    # apache2
    dir_share_linux_config_apache2 = dir_share_linux_config + '/apache2'
    dir_etc_apache2 = '/etc/apache2'
    copy_file(dir_share_linux_config_apache2, 'apache2.conf', dir_etc_apache2, is_sylk=is_sylk)
    copy_file(dir_share_linux_config_apache2, '.htaccess', '/workspace/server', is_sylk=is_sylk)
    copy_file(dir_share_linux_config_apache2 + '/conf-available', 'fqdn.conf', dir_etc_apache2 + '/conf-available', is_sylk=is_sylk)
    copy_file(dir_etc_apache2 + '/conf-available', 'fqdn.conf', dir_etc_apache2 + '/conf-enabled', is_sylk=is_sylk)
    copy_file(dir_etc_apache2 + '/sites-available', '000-default.conf', dir_etc_apache2 + '/sites-enabled', is_sylk=is_sylk)

    if host_name in ['ubuntu-ygu5-01', 'ubuntu-ygu5-02', 'wp-01']:
        copy_file(dir_share_linux_config_apache2, 'ports-8888.conf', dir_etc_apache2, 'ports.conf', is_sylk=is_sylk)
    else:
        copy_file(dir_share_linux_config_apache2, 'ports-80.conf', dir_etc_apache2, 'ports.conf', is_sylk=is_sylk)

    if host_name == 'wp-02':
        copy_file(dir_share_linux_config_apache2 + '/sites-available', '000-benchmark.conf', dir_etc_apache2 + '/sites-available', '000-default.conf', is_sylk=is_sylk)
        copy_file(dir_share_linux_config_apache2 + '/sites-available', '001-browsermark.conf', dir_etc_apache2 + '/sites-available', is_sylk=is_sylk)
        copy_file(dir_etc_apache2 + '/sites-available', '001-browsermark.conf', dir_etc_apache2 + '/sites-enabled', is_sylk=is_sylk)
    elif host_name in ['ubuntu-ygu5-01', 'ubuntu-ygu5-02', 'wp-01']:
        copy_file(dir_share_linux_config_apache2 + '/sites-available', '000-default-8888.conf', dir_etc_apache2 + '/sites-available', '000-default.conf', is_sylk=is_sylk)
    else:
        copy_file(dir_share_linux_config_apache2 + '/sites-available', '000-default-80.conf', dir_etc_apache2 + '/sites-available', '000-default.conf', is_sylk=is_sylk)


def cleanup():
    if not args.cleanup:
        return

    # cache for old package
    execute('sudo apt-get autoclean')
    # cache for all package
    execute('sudo apt-get clean')
    # orphan package
    execute('sudo apt-get -y autoremove', interactive=True)

    # ~/.debug, ~/.flasher ~/.cache

    cmd_kernel = "dpkg -l linux-* | awk '/^ii/{ print $2}' | grep -v -e `uname -r | cut -f1,2 -d'-'` | grep -e [0-9] | grep -E '(image|headers)' | xargs sudo apt-get"
    cmd_kernel_dryrun = cmd_kernel + ' --dry-run remove'
    cmd_kernel += ' -y purge'
    execute(cmd_kernel_dryrun, interactive=True)

    if confirm('Are you sure to remove above kernels?'):
        execute(cmd_kernel, interactive=True)


def proxy():
    # proxies in linux/config
    # [http/socks5] gitconfig
    # [http] androidtool.cfg
    # [http] apt.conf
    # [http] boto.conf
    # [http] subversion-servers
    # [http] privoxy-config
    # [all] zshrc

    # proxies in python script
    # [http] util.py
    pass


if __name__ == '__main__':
    parse_arg()
    setup()
    patch_sudo(force=args.default)  # This should be done first
    time()
    config_before_update()
    update(force=args.default)
    install_pkg(force=args.default)
    install_chromium()
    config_after_update()
    cleanup()
    proxy()
