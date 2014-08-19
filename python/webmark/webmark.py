# TODO:
# move chromedriver.log to test dir

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import json
from selenium import webdriver

logger = ''
dir_root = ''
dir_test = ''
device = ''


class Format:
    NAME = 0
    REQUIRED = 1  # (O)ptional or (M)andatory
    TYPE = 2  # A for Array, O for Object, P for Property

    @staticmethod
    def format_has_member(format, member):
        for f in format:
            if f[Format.NAME] == member or f[Format.NAME] == '*':
                return f
        return None

    @staticmethod
    def format(instance):
        # Check if all mandatory members in FORMAT are satisfied
        for format in instance.FORMAT:
            if format[Format.REQUIRED] == 'M' and not format[Format.NAME] in instance.data:
                logger.error(format[Format.NAME] + ' is not defined in ' + instance.__class__.__name__)
                quit()

        for member in instance.data:
            # Check all members in instance are recognized
            format = Format.format_has_member(instance.FORMAT, member)
            if not format:
                logger.warning('Can not recognize ' + ' in ' + instance.__class__.__name__)
                continue

            if format[Format.NAME] == '*':
                format_name = member
            else:
                format_name = format[Format.NAME]
            format_type = format[Format.TYPE]
            instance_data = instance.data[format_name]
            if format_type == 'P':
                instance.__dict__[format_name] = instance_data
            elif format_type == 'O':
                instance.__dict__[format_name] = eval(format_name.capitalize())(instance_data)
            elif format_type == 'A':
                for element in instance_data:
                    instance.__dict__[format_name].append(eval(format_name.capitalize()[:-1])(element))


class Case:
    FORMAT = [
        ['name', 'M', 'P'],
        ['*', 'O', 'P']
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

    def run(self, driver):
        name = self.name
        exec 'from benchmark.' + name.lower() + ' import ' + name
        benchmark = eval(name)(driver, self)
        logger.info(benchmark.run())


class Proxy:
    FORMAT = [
        ['type', 'O', 'P'],
        ['http', 'O', 'P'],
        ['noproxy', 'O', 'P']
    ]

    def __init__(self, data=json.loads('{}')):
        self.data = data
        Format.format(self)

        if not hasattr(self, 'type'):
            self.type = 'manual'
            self.http = 'http://proxy.pd.intel.com:911'
            self.noproxy = 'localhost,127.0.0.1,*.intel.com'


class Module:
    FORMAT = [
        ['target_os', 'M', 'P'],
        ['name', 'M', 'P'],
        ['path', 'M', 'P'],
        ['mode', 'O', 'P'],
        ['proxy', 'O', 'O'],
        ['switches', 'O', 'P'],
        ['driver', 'O', 'P']
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

        if not hasattr(self, 'mode'):
            self.mode = 'browser'

        if not hasattr(self, 'proxy'):
            self.proxy = Proxy()

        if not hasattr(self, 'switches'):
            if self.target_os == 'linux' and self.name == 'chrome':
                self.switches = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'
            elif self.target_os == 'android' and self.name == 'content_shell':
                self.switches = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'

        if not hasattr(self, 'driver'):
            if self.target_os == 'linux' and self.name == 'chrome':
                self.driver = 'driver/chromedriver'
            elif self.target_os == 'android' and self.name == 'content_shell':
                self.driver = 'driver/chromedriver'


class Suite:
    FORMAT = [
        ['module', 'M', 'O'],
        ['cases', 'M', 'A'],
        ['name', 'O', 'P'],
        ['description', 'O', 'P']
    ]

    def __init__(self, data):
        self.cases = []
        self.data = data
        Format.format(self)

    def run(self):
        # driver_name = self.module.name.capitalize() + 'Driver'
        # exec 'from driver.' + driver_name.lower() + ' import ' + driver_name
        # self.driver = eval(driver_name)(self.module)

        # Handle app mode
        if self.module.mode == 'app':
            app_path = dir_root + '/hosted_app'
            self.extension = self.driver.install_extension(app_path)
            self.driver.get('chrome:newtab')
            handles = self.driver.window_handles
            self.driver.find_element_by_xpath("//div[@title='Hosted App Benchmark']").click()
            self.driver.switch_to_new_window(handles)

        # Install module if needed
        if self.module.path:
            result = execute('adb install -r ' + self.module.path, interactive=True)
            if result[0]:
                error('Can not install ' + self.module.path)

        capabilities = {}
        capabilities['chromeOptions'] = {}
        capabilities['chromeOptions']['androidPackage'] = chromium_android_info[args.target_module][CHROMIUM_ANDROID_INFO_INDEX_PKG]
        capabilities['chromeOptions']['androidUseRunningApp'] = args.use_running_app
        capabilities['chromeOptions']['args'] = ['--disable-web-security']
        capabilities['chromeOptions']['androidDeviceSerial'] = device

        driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)

        for i in range(len(self.cases)):
            self.cases[i].run(driver)

        # self.extension.uninstall()
        driver.quit()


class WebMark:
    FORMAT = [
        ['suites', 'M', 'A']
    ]

    def __init__(self):
        self.start_time = time.time()
        logger.info('Start of ' + self.__class__.__name__ + '.')

        # Parse
        if args.config:
            if not os.path.isfile(config_file):
                logger.error(config_file + ' is not a valid file.')
                return [1, '']
            f = file(config_file)
            self.data = json.load(f)
            f.close()
        else:
            target_module = args.target_module
            target_os = args.target_os

            # TODO: Handle other comb here
            if target_os == 'linux' and target_module == 'chrome':
                path = args.target_module_path
                module_file = os.path.basename(path)
                rev = module_file.replace('.tar.gz', '')
                execute('cp ' + path + ' ' + dir_test)
                backup_dir(dir_test)
                execute('tar zxf ' + module_file)
                execute('rm -f ' + module_file)
                target_module_path = dir_test + '/' + rev + '/chrome'
                restore_dir()
            elif target_os == 'android':
                target_module_path = args.target_module_path
                # module_file = os.path.basename(target_module_path)
                # execute('adb install -r ' + target_module_path)

            benchmark = args.benchmark
            if args.benchmark_config:
                benchmark_config = ', ' + args.benchmark_config
            else:
                benchmark_config = ''
            self.data = json.loads('''
{
  "suites": [
    {
      "module": {
        "name": "%s",
        "target_os": "%s",
        "path": "%s"
      },
      "cases": [
        {"name": "%s"%s}
      ]
    }
  ]
}
            ''' % (target_module, target_os, target_module_path, benchmark, benchmark_config))

        self.suites = []
        Format.format(self)

        # Start patrol
        if host_os == 'windows':
            exec 'from common.patrol import Patrol'
            self.patrol = Patrol()

        # Run
        for i in range(len(self.suites)):
            self.suites[i].run()

    def __del__(self):
        self.stop_time = time.time()
        logger.info('End of ' + self.__class__.__name__ + '. Total elapsed time: ' + str(int(self.stop_time - self.start_time)) + ' seconds')


def parse_arg():
    global args
    parser = argparse.ArgumentParser(description='Automation tool to measure the performance of browser and web runtime with benchmarks',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --target-os android --target-arch x86 --target-module content_shell --benchmark fishietank --benchmark-config '"fish_count": 10, "path": "internal"'
  python %(prog)s --target-os android --target-arch x86 --target-module content_shell --benchmark browsermark --benchmark-config '"username": "xxx", "password": "xxx"'
  python %(prog)s --config config.json

''')
    parser.add_argument('--target-os', dest='target_os', help='target os', choices=target_os_all, default='android')
    parser.add_argument('--target-arch', dest='target_arch', help='target arch', choices=target_arch_all, default='x86')
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all, default='content_shell')
    parser.add_argument('--target-module-path', dest='target_module_path', help='target module path', default='')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', default='sunspider')
    parser.add_argument('--benchmark-config', dest='benchmark_config', help='benchmark config')
    parser.add_argument('--use-running-app', dest='use_running_app', help='use running app', action='store_true', default=False)
    parser.add_argument('--device', dest='device', help='device')
    parser.add_argument('--config', dest='config', help='config file to put in all the configurations')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(0)


def setup():
    global dir_root, dir_test, device, logger

    dir_root = get_symbolic_link_dir()
    dir_test = dir_root + '/test'
    if not os.path.exists(dir_test):
        os.mkdir(dir_test)

    if has_process('chromedriver'):
        execute('sudo killall chromedriver', show_command=False)
    subprocess.Popen(dir_webmark + '/driver/chromedriver', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Sleep a bit to make sure driver is ready
    time.sleep(1)

    unsetenv('http_proxy')

    (devices, devices_name, devices_type, devices_target_arch) = setup_device()

    if len(devices) == 0:
        error('No device is connected')
    if len(devices) > 1 and not args.device:
        error('More than one device is connected')
    if args.device:
        if args.device != devices[0]:
            error('Please ensure device is connected')
        device = args.device
    else:
        device = devices[0]

    logger = get_logger(name='webmark', dir_log=dir_root + '/log')

if __name__ == '__main__':
    parse_arg()
    setup()
    WebMark()
