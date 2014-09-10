from benchmark import *


class canvasmark(Benchmark):
    CONFIG = {
        'name': 'CanvasMark',
        'metric': 'Score',
        'path': {
            'external': 'http://www.kevs3d.co.uk/dev/canvasmark/index.html?auto=true',
            'internal': 'webbench/CanvasMark/index.html?auto=true'
        },
        'version': '2013'
    }

    def __init__(self, driver, case):
        super(canvasmark, self).__init__(driver, case)

    def cond0(self, driver):
        try:
            alert = driver.switch_to_alert()
            self.e = alert.text
            return True
        except:
            return False

    def act0(self, driver):
        self.result.append(self.e)