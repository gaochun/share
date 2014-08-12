import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import re


class Benchmark(object):
    def __init__(self, driver, case):
        self.driver = driver
        self.case = case
        self.case.metric = self.CONFIG['metric']

        config_path = self.CONFIG['path']
        if case.path == 'external':
            self.path = config_path['external']
        if case.path == 'internal':
            self.path = 'http://wp-01.sh.intel.com/' + config_path['internal']
        elif case.path == 'local':
            #self.path = 'file:///' + PROJECT_PATH + 'third_party/WebBench/' + config_path['internal']
            self.path = 'file:///data/local/tmp/' + config_path['local']
        else:
            self.path = self.case.path

        #run_times = self.case.run_times
        #for i in range(run_times):
        #self.driver.maximize_window()

        driver.get(self.path)
        WebDriverWait(driver, case.timeout_start, case.period_start_check).until(self.is_started)
        self.config(driver)
        WebDriverWait(driver, case.timeout_finish, case.period_finish_check).until(self.is_finished)

    def is_started(self, driver):
        return True

    def config(self, driver):
        pass

    def is_finished(self, driver):
        time.sleep(3)
        return True

    def get_result(self, driver):
        return 0.0

    def get_result_one(self, driver):
        return '0.0'

    def get_result_periodic(self, driver, count=3, period=3):
        result = 0.0
        for i in range(1, count + 1):
            time.sleep(period)
            result_one = self.get_result_one(driver)
            print result_one
            result += (float(result_one) - result) / i

        return round(result, 2)
