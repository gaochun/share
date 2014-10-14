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
        self.run_fail = False
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
            'version': 'NA',
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
            self.__dict__[key] = path_web_benchmark + '/' + self.__dict__[key]
        elif self.path_type == 'local':
            self.__dict__[key] = 'file:///data/local/tmp/' + self.__dict__[key]

    def get_result(self, driver):
        if self.dryrun:
            return ['60.0']
        elif self.run_fail:
            return ['-1.0']
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
                    try:
                        WebDriverWait(driver, self.timeout, self.sleep).until(self._is_finished)
                    except:
                        self.run_fail = True
                if times_skip > 0:
                    times_skip = times_skip - 1
                    continue
                result = self.get_result(driver)
                info('Round result: ' + ','.join(result))
                results.append([float(x) for x in result])
                if self.run_fail:
                    break

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

            outputs = []
            for item in webmark_format:
                if item == 'category':
                    outputs.append(self.category)
                elif item == 'name':
                    outputs.append(self.name)
                elif item == 'version':
                    outputs.append(self.version)
                elif item == 'metric':
                    outputs.append(self.metric)
                elif item == 'result':
                    outputs.append(','.join(str(x) for x in results_average))
            return ','.join(outputs)

    def inject_jperf(self, driver):
        if self.path_type == 'internal':
            js = path_web_webbench + '/jperf/jperf.js'
        else:
            js = 'https://raw.githubusercontent.com/gyagp/webbench/master/jperf/jperf.js'
        self.inject_js(driver, js)

    def inject_js(self, driver, js):
        script = '''
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = '%s';
    document.head.appendChild(script);
        ''' % js
        driver.execute_script('{' + script + '}')
        time.sleep(3)

    def _is_finished(self, driver):
        if self.states[self.state][0](driver):
            act = self.states[self.state][1]
            if act:
                act(driver)
            self.state += 1
            if self.state == len(self.states):
                return True
        return False


class CssBenchmark(Benchmark):
    def inject_css_fps(self, driver):
        self.inject_jperf(driver)
        script = '''
    var cssFpsElement = document.createElement('div');
    var style = 'float:left; width:800px; height:30px: color:red;';
    cssFpsElement.setAttribute('style', style);
    cssFpsElement.setAttribute('id', 'css-fps');
    cssFpsElement.innerHTML = 'Recent FPS: 0, Average FPS: 0';
    document.body.appendChild(cssFpsElement);

    var cssFpsMeter = new window.jPerf.CSSFPSMeter();
    cssFpsMeter.start();
    document.addEventListener('CSSFPSReport',
      function(event) {
        cssFpsElement.innerHTML = 'Recent FPS: ' + event.recentFPS + ', Average FPS: ' + event.averageFPS;
      },
      false
    );
        '''
        driver.execute_script(script)

    def get_css_fps(self, driver):
        match = re.search('Average FPS: (.*)', driver.find_element_by_id('css-fps').get_attribute('innerText'))
        return match.group(1)
