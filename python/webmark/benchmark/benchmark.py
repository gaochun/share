import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
import sys
sys.path.append(sys.path[0] + '/..')
from util import *

category_info = {
    'comprehensive': 'Comprehensive',
    'js': 'JavaScript',
    'canvas2d': 'Canvas2D',
    'webgl': 'WebGL',
    'css': 'CSS',
    'webaudio': 'WebAudio',
    'webvideo': 'WebVideo',
    'webtouch': 'WebTouch',
    'fileop': 'FileOperation',
    'localstorage': 'LocalStorage',
    'render': 'PageRendering',
}

metric_info = {
    'score': 'Score(+)',
    'fps': 'FPS(+)',
    'ms': 'ms(-)',
    's': 's(-)'
}


class Benchmark(object):
    def __init__(self, driver, case):
        self.driver = driver

        # handle states
        funcs = [func for func in dir(self) if callable(getattr(self, func))]
        self.states = []
        count = 0
        pattern_cond = re.compile('cond(\d+)')
        for func in funcs:
            match = pattern_cond.match(func)
            if match:
                count_temp = int(match.group(1))
                if count_temp > count:
                    count = count_temp
        for i in range(count + 1):
            self.states.append([getattr(self, 'cond' + str(i)), getattr(self, 'act' + str(i))])

        # handle general members
        config = self.CONFIG
        members = {
            'category': '',
            'name': '',
            'version': '',
            'metric': '',
            'path_type': 'internal',
            'timeout': 90,
            'sleep': 3,
            'times_run': 1,
            'times_skip': 0,
            'dryrun': False,
        }
        for key in members:
            if key == 'name':
                if key in config:
                    self.__dict__[key] = config[key]
                else:
                    self.__dict__[key] = getattr(case, key)
                continue

            if hasattr(case, key):
                self.__dict__[key] = getattr(case, key)
            elif key in config:
                self.__dict__[key] = config[key]
            else:
                self.__dict__[key] = members[key]

        # handle path
        key = 'path'
        if hasattr(case, key):
            self.__dict__[key] = getattr(case, key)
        elif key in config:
            if self.version in config[key]:
                self.__dict__[key] = config[key][self.version][self.path_type]
            else:
                self.__dict__[key] = config[key][self.path_type]
        if self.path_type == 'internal':
            self.__dict__[key] = 'http://wp-02.sh.intel.com/' + self.__dict__[key]
        elif self.path_type == 'local':
            self.__dict__[key] = 'file:///data/local/tmp/' + self.__dict__[key]

    def get_result(self, driver):
        if self.dryrun:
            return ['60']
        else:
            return self.result

    def get_result_one(self, driver):
        return '0.0'

    def get_result_periodic(self, driver, count=5, period=3):
        result = 0.0
        for i in range(1, count + 1):
            time.sleep(period)
            result_one = self.get_result_one(driver)
            info('Periodic result: ' + result_one)
            result += (float(result_one) - result) / i

        return [str(round(result, 2))]

    # Each specific benchmark only returns result in string format, we will convert them to float here.
    def run(self):
            info('Begin to run "%s" version "%s"' % (self.name, self.version))
            times_run = self.times_run
            times_skip = self.times_skip
            driver = self.driver

            results = []
            for i in range(times_run):
                self.result = []
                self.state = 0
                if not self.dryrun:
                    driver.get(self.path)
                    WebDriverWait(driver, self.timeout, self.sleep).until(self._is_finished)
                if times_skip > 0:
                    times_skip = times_skip - 1
                    continue
                if self.dryrun:
                    result = ['60']
                else:
                    result = self.get_result(driver)
                info('Round result: ' + ','.join(result))
                results.append([float(x) for x in result])

            count_results = len(results)
            if count_results == 0:
                error('There is no result for ' + self.name)

            results_total = results[0]
            count_result = len(results[0])
            for i in range(1, count_results):
                for j in range(count_result):
                    results_total[j] += results[i][j]

            results_average = []
            for i in range(count_result):
                results_average.append(round(results_total[i] / count_results, 2))

            return '%s,%s,%s,%s,%s' % (self.category, self.name, self.version, self.metric, ','.join(str(x) for x in results_average))

    def _is_finished(self, driver):
        if self.states[self.state][0](driver):
            act = self.states[self.state][1]
            if act:
                act(driver)
            self.state += 1
            if self.state == len(self.states):
                return True

        return False
