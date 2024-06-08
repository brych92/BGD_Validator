import sys
import imp
sys.path.append(r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator')

#del ResultWindow

import ResultWindow, resultStructure
imp.reload(ResultWindow)
imp.reload(resultStructure)
from ResultWindow import *
from resultStructure import result

window = ResultWindow(result)
window.show()