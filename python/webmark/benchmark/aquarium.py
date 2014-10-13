from benchmark import *


class aquarium(Benchmark):
    CONFIG = {
        'category': category_info['webgl'],
        'name': 'Aquarium',
        'metric': metric_info['fps'],
        'path': {
            'external': 'http://webglsamples.googlecode.com/hg/aquarium/aquarium.html',
            'internal': 'webbench/webgl/webglsamples/aquarium/aquarium.html'
        },
    }

    def __init__(self, driver, case):
        super(aquarium, self).__init__(driver, case)

    def cond0(self, driver):
        self.e = driver.find_element_by_id('fps')
        if self.e:
            return True
        else:
            return False

    def act0(self, driver):
        self.result = self.get_result_periodic(driver)

    def get_result_one(self, driver):
        return self.e.get_attribute('innerText')
