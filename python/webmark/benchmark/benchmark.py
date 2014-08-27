import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
import sys
sys.path.append(sys.path[0] + '/..')
from util import *


class Benchmark(object):
    def __init__(self, driver, case):
        self.driver = driver
        self.result = []
        self.state = 0

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
            'name': '',
            'metric': 'fps',
            'version': '1.0',
            'path_type': 'internal',
            'timeout': 90,
            'sleep': 3,
            'times_run': 1,
            'times_skip': 0,
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
            self.__dict__[key] = 'http://wp-01.sh.intel.com:8000/' + self.__dict__[key]
        elif self.path_type == 'local':
            self.__dict__[key] = 'file:///data/local/tmp/' + self.__dict__[key]

    def get_result(self, driver):
        return self.result

    def get_result_one(self, driver):
        return '0.0'

    def get_result_periodic(self, driver, count=3, period=3):
        result = 0.0
        for i in range(1, count + 1):
            time.sleep(period)
            result_one = self.get_result_one(driver)
            result += (float(result_one) - result) / i

        return round(result, 2)

    # Each specific benchmark only returns result in string format, we will convert them to float here.
    def run(self):
            times_run = self.times_run
            times_skip = self.times_skip
            driver = self.driver

            results = []
            for i in range(times_run):
                driver.get(self.path)
                WebDriverWait(driver, self.timeout, self.sleep).until(self._is_finished)
                if times_skip > 0:
                    times_skip = times_skip - 1
                    continue
                result = self.get_result(driver)
                info('Single result: ' + ','.join(result))
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
                results_average.append(results_total[i] / count_results)

            return 'Result: %s,%s,[%s]' % (self.name, self.version, ','.join(str(x) for x in results_average))

    def _is_finished(self, driver):
        if self.states[self.state][0](driver):
            act = self.states[self.state][1]
            if act:
                act(driver)
            self.state += 1
            if self.state == len(self.states):
                return True

        return False
