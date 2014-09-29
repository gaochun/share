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
device_config = False
file_result = ''


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
        self.dryrun = args.dryrun
        Format.format(self)

    def run(self, driver):
        name = self.name
        exec 'from benchmark.' + name.lower() + ' import ' + name
        benchmark = eval(name)(driver, self)
        result = benchmark.run()
        execute('echo "' + result + '" >>' + file_result, show_cmd=False)
        logger.info('Result: ' + result)


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


class Target:
    FORMAT = [
        ['os', 'M', 'P'],
        ['arch', 'M', 'P'],
        ['module', 'M', 'P'],
        ['module_path', 'O', 'P'],
        ['module_mode', 'O', 'P'],
        ['module_proxy', 'O', 'O'],
        ['module_switches', 'O', 'P'],
        ['module_driver', 'O', 'P']
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

        if not hasattr(self, 'module_mode'):
            self.module_mode = 'browser'

        if not hasattr(self, 'module_proxy'):
            self.module_proxy = Proxy()

        if not hasattr(self, 'module_switches'):
            if self.os == 'linux' and self.module == 'chrome':
                self.module_switches = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'
            elif self.os == 'android' and self.module == 'content_shell':
                self.module_switches = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'

        if not hasattr(self, 'module_driver'):
            if self.os == 'linux' and self.module == 'chrome':
                self.module_driver = 'driver/chromedriver'
            elif self.os == 'android' and self.module == 'content_shell':
                self.module_driver = 'driver/chromedriver'


class Suite:
    FORMAT = [
        ['target', 'M', 'O'],
        ['cases', 'M', 'A'],
        ['name', 'O', 'P'],
        ['description', 'O', 'P']
    ]

    def __init__(self, data):
        self.cases = []
        self.data = data
        Format.format(self)

    def run(self):
        # driver_name = self.target.name.capitalize() + 'Driver'
        # exec 'from driver.' + driver_name.lower() + ' import ' + driver_name
        # self.driver = eval(driver_name)(self.target)

        # Handle app mode
        if self.target.module_mode == 'app':
            app_path = dir_root + '/hosted_app'
            self.extension = self.driver.install_extension(app_path)
            self.driver.get('chrome://newtab')
            handles = self.driver.window_handles
            self.driver.find_element_by_xpath("//div[@title='Hosted App Benchmark']").click()
            self.driver.switch_to_new_window(handles)

        # Install target if needed
        if hasattr(self.target, 'module_path') and self.target.module_path:
            result = execute('adb install -r ' + self.target.module_path, interactive=True)
            if result[0]:
                error('Can not install ' + self.target.module_path)

        capabilities = get_capabilities(device, self.target.module, args.use_running_app, ['--disable-web-security'])

        if args.dryrun:
            driver = None
        else:
            driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)

        for i in range(len(self.cases)):
            self.cases[i].run(driver)

        # self.extension.uninstall()
        if not args.dryrun:
            driver.quit()


class WebMark:
    FORMAT = [
        ['suites', 'M', 'A']
    ]

    def __init__(self):
        timer_start(self.__class__.__name__)

        # Parse
        if args.config:
            file_config = args.config
            if not os.path.isfile(file_config):
                error(file_config + ' is not a valid file.')
            f = file(file_config)
            self.data = json.load(f)
            f.close()
        else:
            target_os = args.target_os
            target_arch = args.target_arch
            target_module = args.target_module
            target_module_path = args.target_module_path

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
      "target": {
        "os": "%s",
        "arch": "%s",
        "module": "%s",
        "module_path": "%s"
      },
      "cases": [
        {"name": "%s"%s}
      ]
    }
  ]
}
            ''' % (target_os, target_arch, target_module, target_module_path, benchmark, benchmark_config))

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
        timer_stop(self.__class__.__name__)
        logger.info('Total elapsed time for execution: ' + timer_diff(self.__class__.__name__))


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
    parser.add_argument('--target-module', dest='target_module', help='target module', choices=target_module_all, default='chrome_stable')
    parser.add_argument('--target-module-path', dest='target_module_path', help='target module path', default='')
    parser.add_argument('--benchmark', dest='benchmark', help='benchmark', default='sunspider')
    parser.add_argument('--benchmark-config', dest='benchmark_config', help='benchmark config')
    parser.add_argument('--use-running-app', dest='use_running_app', help='use running app', action='store_true', default=False)
    parser.add_argument('--config', dest='config', help='config file to put in all the configurations')
    parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true', default=False)

    parser.add_argument('--device', dest='device', help='device')
    parser.add_argument('--device-config', dest='device_config', help='need device config or not', action='store_true')
    parser.add_argument('--governor', dest='governor', help='governor')
    parser.add_argument('--freq', dest='freq', type=int, help='freq')
    parser.add_argument('--ver-driver', dest='ver_driver', help='version of chromedriver', default='')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(0)


def setup():
    global dir_root, dir_test, device, device_product, logger
    global device_config, file_result

    dir_root = get_symbolic_link_dir()
    dir_test = dir_root + '/test'
    if not os.path.exists(dir_test):
        os.mkdir(dir_test)

    if args.ver_driver:
        chrome_driver = 'chromedriver-' + args.ver_driver
    else:
        chrome_driver = 'chromedriver'

    if has_process(chrome_driver):
        execute('sudo killall %s' % chrome_driver, show_cmd=False)
    subprocess.Popen(dir_webmark + '/driver/' + chrome_driver, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Sleep a bit to make sure driver is ready
    time.sleep(1)

    unsetenv('http_proxy')
    (devices, devices_product, devices_type, devices_arch, devices_mode) = setup_device()

    if len(devices) == 0:
        warning('No device is connected')
        android_start_emu('x86')
    if len(devices) > 1 and not args.device:
        error('More than one device is connected')
    if args.device:
        if args.device != devices[0]:
            error('Please ensure device is connected')
        device = args.device
    else:
        device = devices[0]

    device_product = devices_product[0]

    datetime = get_datetime()
    logger = get_logger(tag='webmark', dir_log=dir_webmark_log, datetime=datetime)
    ensure_dir(dir_webmark_result)
    file_result = dir_webmark_result + '/' + datetime

    if args.device_config:
        device_config = True

    if device_config:
        governor = args.governor
        freq = args.freq
        android_config_device(device=device, device_product=device_product, default=False, governor=governor, freq=freq)


def teardown():
    if device_config:
        android_config_device(device=device, device_product=device_product, default=True)

if __name__ == '__main__':
    parse_arg()
    setup()
    WebMark()
    teardown()
