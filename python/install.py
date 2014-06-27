#/usr/bin/python

# Post-execution steps for a development machine:
# sudo /workspace/project/chromium/git_upstream/src/build/install-build-deps.sh.
# Install display card driver, slickedit, sublime text.
# Set keyboard shortcut: 'nautilus /workspace' -> ctrl+alt+E
# Set input method: gnome-session-properties


from util import *

username = getenv('USER')

pkgs_common = [
    'tsocks', 'privoxy',
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
    # required by Chromium build
    'libspeechd-dev', 'libgdk-pixbuf2.0-dev', 'libgtk2.0-dev', 'libdrm-dev', 'libgnome-keyring-dev', 'libgconf2-dev', 'libudev-dev',
    'libpci-dev', 'linux-tools-generic', 'binutils-dev', 'libelf-dev', 'gperf', 'gcc-4.7-multilib', 'g++-4.7-multilib', 'bison', 'python-pip',
    'module-assistant', 'autoconf', 'automake', 'libnss3-dev', 'ant', 'libcups2-dev', 'libasound2-dev', 'libxss-dev', 'libxtst-dev',
    'libpulse-dev',
    'postfix',  # smtp server
    'android-tools-adb',
    'dos2unix',
    'lib32z1',
    'openjdk-7-jdk',

    # Package used at home
    'openconnect',
    'python-zsi',
    'openssh-server',
]


def handle_option():
    global args
    parser = argparse.ArgumentParser(description='Script to install system',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
Examples:
  python %(prog)s
  python %(prog)s
''')
    args = parser.parse_args()


def setup():
    backup_dir(dir_python)


def patch_sudo():
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


def upgrade():
    if not has_recent_change('/var/lib/apt/lists'):
        execute('python upgrade.py -t basic', interactive=True)


def install_pkg(pkgs):
    for pkg in pkgs:
        if package_installed(pkg):
            info('Package ' + pkg + ' was already installed')
        else:
            info('Package ' + pkg + ' is installing...')
            result = execute('sudo apt-get install -y ' + pkg, interactive=True)
            if result[0]:
                warning('Package ' + pkg + ' installation failed')


def install_chromium():
    if package_installed('google-chrome-unstable'):
        return

    execute('python upgrade.py -t chrome', interactive=True)
    install_pkg(['google-chrome-unstable'])

    # Install Chrome, which needs to use tsocks
    result = execute('sudo apt-key list | grep 7FAC5991')
    if result[0]:
        info('Get the key for Chrome...')

        # To get the key: tsocks wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub
        cmd = 'cat ' + dir_linux + '/chrome_key_pub.txt | sudo apt-key add -'
        result = execute(cmd)
        if result[0]:
            error('Key for Chrome has not been added correctly')
    else:
        info('Key for Chrome has been added')


if __name__ == '__main__':
    handle_option()
    setup()
    patch_sudo()  # This should be done first
    upgrade()
    install_pkg(pkgs_common)

    if username == 'gyagp':
        # This takes quite a long time
        #execute('sudo apt-file update', interactive=True)
        is_sylk = True
    else:
        is_sylk = False

    copy_file(dir_linux + '/.zshrc', dir_home, is_sylk=is_sylk)
    execute('sudo chsh -s /bin/zsh ' + username)
    copy_file(dir_linux + '/.gitconfig', dir_home, is_sylk=is_sylk)
    copy_file(dir_linux + '/.bashrc', dir_home, is_sylk=is_sylk)
    copy_file(dir_linux + '/.gdbinit', dir_home, is_sylk=is_sylk)
    copy_file(dir_linux + '/.vimrc', dir_home, is_sylk=is_sylk)
    copy_file(dir_linux + '/subversion/servers', '/etc/subversion', is_sylk=is_sylk)
    copy_file(dir_linux + '/privoxy/config', '/etc/privoxy', is_sylk=is_sylk)
    copy_file(dir_linux + '/tsocks.conf', '/etc', is_sylk=is_sylk)

    #install_chromium() # This requires tsocks

    # Chromium build
    copy_file('/usr/include/x86_64-linux-gnu/asm', '/usr/include', is_sylk=True)
