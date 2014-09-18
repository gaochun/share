from benchmark import *


class canvasmark(Benchmark):
    CONFIG = {
        'name': 'canvasmark',
        'metric': 'Score',
        'path': {
            'external': 'http://www.kevs3d.co.uk/dev/canvasmark/',
            'internal': 'webbench/canvasmark/'
        },
        'version': '2013'
    }

    def __init__(self, driver, case):
        super(canvasmark, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_id('canvas')
        if self.e:
            time.sleep(10)
            return True
        else:
            return False

    def act0(self, driver):
        self.e.click()

    def cond1(self, driver):
        self.e = driver.find_element_by_id('results').text
        if self.e:
            return True
        else:
            return False

    def act1(self, driver):
        self.result.append(self.e.split()[2])
