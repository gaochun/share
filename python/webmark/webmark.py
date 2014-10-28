# TODO:
# move chromedriver.log to test dir

import sys
sys.path.append(sys.path[0] + '/..')
from util import *
import json
from selenium import webdriver

logger = ''
device_arch = ''


def parse_arg():
    global args, args_dict
    parser = argparse.ArgumentParser(description='Automation tool to measure the performance of browser and web runtime with benchmarks',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog='''
examples:
  python %(prog)s --config config.json
  python %(prog)s --analyze all
  python %(prog)s --module-os android --module-arch x86 --module-name content_shell --case fishietank --case-config '"count_fish": 10, "path": "internal"'
''')

    parser.add_argument('--config', dest='config', help='config file to put in all the configurations')

    group_device = parser.add_argument_group('device')
    group_device.add_argument('--device-id', dest='device_id', help='device id separated by comma')
    group_device.add_argument('--device-freq', dest='device_freq', type=int, help='device freq')
    group_device.add_argument('--device-governor', dest='device_governor', help='device governor')
    group_module = parser.add_argument_group('module')
    group_module.add_argument('--module-arch', dest='module_arch', help='module arch')
    group_module.add_argument('--module-driver', dest='module_driver', help='module driver')
    group_module.add_argument('--module-mode', dest='module_mode', help='module mode')
    group_module.add_argument('--module-name', dest='module_name', help='module name', default='chrome_stable')
    group_module.add_argument('--module-os', dest='module_os', help='module os')
    group_module.add_argument('--module-path', dest='module_path', help='module path')
    group_module.add_argument('--module-proxy', dest='module_proxy', help='module proxy')
    group_module.add_argument('--module-switch', dest='module_switch', help='module switch')
    group_module.add_argument('--module-version', dest='module_version', help='module version')

    group_case = parser.add_argument_group('case')
    group_case.add_argument('--case-name', dest='case_name', help='case name')
    group_case.add_argument('--case-config', dest='case_config', help='case config')

    # cmdline only
    parser.add_argument('--driver-log', dest='driver_log', help='log of chromedriver', action='store_true')
    parser.add_argument('--driver-verbose', dest='driver_verbose', help='verbose log of chromedriver', action='store_true')
    parser.add_argument('--use-running-app', dest='use_running_app', help='use running app', action='store_true', default=False)
    parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true', default=False)
    parser.add_argument('--analyze', dest='analyze', help='file to analyze')

    add_argument_common(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(0)


def setup():
    global dir_root, log, timestamp, logger, dryrun, baseline
    global devices_id, devices_product, devices_arch

    (timestamp, dir_root, log) = setup_common(args, _teardown)
    unsetenv('http_proxy')
    logger = get_logger(tag='webmark', dir_log=dir_share_ignore_webmark_log, datetime=timestamp)
    dryrun = args.dryrun
    baseline = Baseline()
    ensure_dir(dir_share_ignore_webmark_download)
    ensure_dir(dir_share_ignore_webmark_result)

    # driver
    if args.module_driver:
        chrome_driver = args.module_driver
    else:
        chrome_driver = 'chromedriver'

    if has_process(chrome_driver):
        execute('sudo killall %s' % chrome_driver, show_cmd=False)

    cmd = dir_webmark + '/driver/' + chrome_driver
    if args.driver_log:
        cmd += ' --log-path ' + dir_share_ignore_webmark_log + '/chromedriver-' + timestamp + '.log'
    if args.driver_verbose:
        cmd += ' --verbose'
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Sleep a bit to make sure driver is ready
    time.sleep(1)

    # device
    if args.device_id:
        devices_id_limit = args.device_id.split(',')
    else:
        devices_id_limit = []
    (devices_id, devices_product, devices_type, devices_arch, devices_mode) = setup_device(devices_id_limit=devices_id_limit)
    if len(devices_id) == 0:
        error('No device is connected')


def run():
    if not args.config and not args.case_name:
        return

    Webmark()


def analyze(files_result):
    if not files_result:
        return

    if files_result == 'all':
        files_result_todo = os.listdir(dir_share_ignore_webmark_result)
    else:
        files_result_todo = files_result.split(',')

    for file_result in files_result_todo:
        if file_result[0] != '/':
            file_result = dir_share_ignore_webmark_result + '/' + file_result

        # get baseline_suite
        baseline_suite = ''
        fr = open(file_result)
        lines = fr.readlines()
        fr.close()

        for line in lines:
            if re.search('"device":', line):
                device = json.loads(line.replace('"device":', ''))
            elif re.search('"module"', line):
                module = json.loads(line.replace('"module":', ''))
        for index in range(len(baseline.suites)):
            suite_temp = baseline.suites[index]
            device_temp = suite_temp.device
            module_temp = suite_temp.module
            if device_temp.product == device['product'] and \
                    device_temp.arch == device['arch'] and \
                    device_temp.governor == device['governor'] and \
                    device_temp.freq == device['freq'] and \
                    module_temp.name == module['name'] and \
                    module_temp.arch == module['arch'] and \
                    module_temp.os == module['os']:
                break
        if index >= len(baseline.suites):
            warning('There is no baseline found for %s' % file_result)
            continue
        baseline_suite = baseline.suites[index]

        # analyze
        for line in fileinput.input(file_result, inplace=1):
            if not re.search('"device"', line) and not re.search('"module"', line):
                # get case info
                case = {}
                results = line.split(',')
                for index, item in enumerate(webmark_format):
                    if item == 'metric':
                        case['metric'] = results[index]
                    elif item == 'name':
                        case['name'] = results[index]
                    elif item == 'result':
                        case['result'] = float(results[index])
                    elif item == 'version':
                        case['version'] = results[index]

                baseline_result = 0
                for baseline_case in baseline_suite.cases:
                    if baseline_case.name == case['name'] and ('version' not in case or baseline_case.version == case['version']):
                        baseline_result = float(baseline_case.result)
                        break
                if baseline_result < 0.01:
                    analysis = '?'
                else:
                    diff = round(abs(case['result'] - baseline_result) / baseline_result, 2) * 100
                    if diff > 5:
                        if re.search('\+', case['metric']):
                            if case['result'] < baseline_result:
                                change = '-'
                            else:
                                change = '+'
                        else:
                            if case['result'] > baseline_result:
                                change = '-'
                            else:
                                change = '+'

                        analysis = '%s%s%%' % (change, diff)
                    else:
                        analysis = '='

                if results[-1][0] in ['+', '-', '=', '?']:  # has analyzed
                    line = line.replace(results[-1], analysis) + '\n'
                else:
                    line = line.rstrip('\n') + ',' + analysis + '\n'

            sys.stdout.write(line)


def _teardown():
    pass


class Webmark:
    FORMAT = [
        ['suites', 'M', 'A'],
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
            data = {
                'device': {},
                'module': {}
            }

            for c in [Device, Module]:
                for m in [x[0] for x in c.FORMAT]:
                    name_arg = '%s_%s' % (c.__name__.lower(), m)
                    if name_arg in args_dict and args_dict[name_arg]:
                        data[c.__name__.lower()][m] = args_dict[name_arg]

            if args.case_config:
                case_config = ', ' + args.case_config
            else:
                case_config = ''

            json_string = '''
{
  "suites": [
    {
      "device": %s,
      "module": %s,
      "cases": [
        {"name": "%s"%s}
      ]
    }
  ]
}
            ''' % (json.dumps(data['device']), json.dumps(data['module']), args.case_name, case_config)
            self.data = json.loads(json_string)

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


class Baseline:
    FORMAT = [
        ['suites', 'M', 'A'],
    ]

    def __init__(self):
        file_baseline = 'baseline.json'
        if not os.path.isfile(file_baseline):
            error(file_baseline + ' is not a valid file.')
        f = file(file_baseline)
        self.data = json.load(f)
        f.close()
        self.suites = []
        Format.format(self)


class Suite:
    FORMAT = [
        ['cases', 'M', 'A'],
        ['description', 'O', 'P'],
        ['device', 'M', 'O'],
        ['name', 'O', 'P'],
        ['module', 'M', 'O'],

    ]

    def __init__(self, data):
        self.data = data
        self.cases = []
        Format.format(self)

    def run(self):
        device = self.device
        module = self.module

        # Handle app mode
        if module.mode == 'app':
            app_path = dir_root + '/hosted_app'
            self.extension = self.driver.install_extension(app_path)
            self.driver.get('chrome://newtab')
            handles = self.driver.window_handles
            self.driver.find_element_by_xpath("//div[@title='Hosted App Benchmark']").click()
            self.driver.switch_to_new_window(handles)

        # install module
        if hasvalue(module, 'path'):
            if module.path == 'auto':
                if module.name == 'chrome_stable' or module.name == 'chrome_beta':
                    module_path = path_web_chrome_android + '/%s-%s-chrome/%s-%s/Chrome.apk' % (module.os, module.arch, module.version, module.name.replace('chrome_', ''))
                elif module.name == 'content_shell':
                    module_path = path_web_webcatch + '/%s-%s-%s/%s.apk' % (module.os, module.arch, module.name, module.version)
                else:
                    error('module path is not correct')
            else:
                module_path = module.path
            if re.match('http', module_path):
                backup_dir(dir_share_ignore_webmark_download)
                if module.os == 'android':
                    module_file = '%s-%s-%s-%s.apk' % (module.os, module.arch, module.name, module.version)
                    if not os.path.exists(module_file):
                        result = execute('wget %s -O %s' % (module_path, module_file), dryrun=False)
                        if result[0]:
                            error('Failed to download ' + module_path)
                    module_path = dir_share_ignore_webmark_download + '/' + module_file
                restore_dir()

            chrome_android_cleanup(device.id)
            result = execute('adb install -r ' + module_path, interactive=True)
            if result[0]:
                error('Can not install ' + module_path)

        # change freq
        if hasvalue(device, 'governor') and hasvalue(device, 'freq'):
            android_config_device(device_id=device.id, device_product=device.product, default=False, governor=device.governor, freq=device.freq)

        # generate result file
        timestamp_temp = get_datetime()
        file_result = dir_share_ignore_webmark_result + '/%s-%s-%s-%s-%s-%s-%s.txt' % (timestamp_temp, device.product, device.arch, module.os, module.arch, module.name, module.version)
        logger.info('Use result file ' + file_result)
        fw = open(file_result, 'w')
        ## write config
        data = {
            'device': {},
            'module': {}
        }
        for i in [device, module]:
            for m in [x[0] for x in i.FORMAT]:
                data[i.__class__.__name__.lower()][m] = getattr(i, m)
        config = '"device": %s\n"module": %s\n' % (json.dumps(data['device']), json.dumps(data['module']))
        fw.write(config)

        # write performance data
        capabilities = get_capabilities(device.id, module.name, args.use_running_app, ['--disable-web-security'])
        for i in range(len(self.cases)):
            if dryrun:
                driver = None
            else:
                driver = webdriver.Remote('http://127.0.0.1:9515', capabilities)
            result = self.cases[i].run(driver)
            fw.write(result + '\n')
            logger.info('Result: ' + result)

            if not dryrun:
                driver.quit()
        fw.close()
        analyze(file_result)

        # restore freq
        if hasvalue(device, 'governor') and hasvalue(device, 'freq'):
            android_config_device(device_id=device.id, device_product=device.product, default=True)

        # uninstall module
        if hasvalue(module, 'path'):
            chrome_android_cleanup(device.id, module_name=module.name)


class Device:
    FORMAT = [
        ['arch', 'O', 'P'],
        ['id', 'O', 'P'],
        ['freq', 'O', 'P', 0],
        ['governor', 'O', 'P'],
        ['product', 'O', 'P'],
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

        if self.id:
            for index, device_id in enumerate(devices_id):
                if device_id != self.id:
                    continue
                self.arch = devices_arch[index]
                self.product = devices_product[index]
            if not hasvalue(self, 'arch'):
                error('The designated device %s is not found' % self.id)
        elif not self.arch and not self.product:
            self.id = devices_id[0]
            self.arch = devices_arch[0]
            self.product = devices_product[0]


class Module:
    FORMAT = [
        ['arch', 'O', 'P'],
        ['driver', 'O', 'P'],
        ['mode', 'O', 'P'],
        ['name', 'M', 'P'],
        ['os', 'O', 'P'],
        ['path', 'O', 'P'],
        ['proxy', 'O', 'O'],
        ['switch', 'O', 'P'],
        ['version', 'O', 'P', '0'],
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)

        if not hasvalue(self, 'mode'):
            self.mode = 'browser'

        if not hasvalue(self, 'proxy'):
            self.proxy = Proxy()

        if not hasvalue(self, 'switch'):
            if self.os == 'linux' and self.name == 'chrome':
                self.switch = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'
            elif self.os == 'android' and self.name == 'content_shell':
                self.switch = '--flag-switches-begin --enable-experimental-web-platform-features --flag-switches-end --disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=./'

        if not hasvalue(self, 'driver'):
            if self.os == 'linux' and self.name == 'chrome':
                self.driver = 'driver/chromedriver'
            elif self.os == 'android' and self.name == 'content_shell':
                self.driver = 'driver/chromedriver'


class Proxy:
    FORMAT = [
        ['http', 'O', 'P'],
        ['noproxy', 'O', 'P'],
        ['type', 'O', 'P'],
    ]

    def __init__(self, data=json.loads('{}')):
        self.data = data
        Format.format(self)

        if not hasvalue(self, 'type'):
            self.type = 'manual'
            self.http = 'http://proxy.pd.intel.com:911'
            self.noproxy = 'localhost,127.0.0.1,*.intel.com'


class Case:
    FORMAT = [
        ['name', 'M', 'P'],
        ['*', 'O', 'P'],
    ]

    def __init__(self, data):
        self.data = data
        Format.format(self)
        self.dryrun = dryrun

    def run(self, driver):
        name = self.name
        exec 'from benchmark.' + name.lower() + ' import ' + name
        benchmark = eval(name)(driver, self)
        return benchmark.run()


class Format:
    NAME = 0
    REQUIRED = 1  # (O)ptional or (M)andatory
    TYPE = 2  # A for Array, O for Object, P for Property
    DEFAULT = 3

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
                logger.warning('Can not recognize ' + member + ' in ' + instance.__class__.__name__)
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

        # set default
        for format in instance.FORMAT:
            format_name = format[Format.NAME]
            if not hasattr(instance, format_name):
                if len(format) > Format.DEFAULT:
                    instance.__dict__[format_name] = format_type = format[Format.DEFAULT]
                else:
                    format_type = format[Format.TYPE]
                    if format_type == 'P':
                        instance.__dict__[format_name] = ''
                    elif format_type == 'O':
                        instance.__dict__[format_name] = None
                    elif format_type == 'A':
                        instance.__dict__[format_name] = []


if __name__ == '__main__':
    parse_arg()
    setup()
    run()
    analyze(args.analyze)
