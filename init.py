import sys
import imp
sys.path.append(r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator')

#del ResultWindow

#from qgis.utils import iface

import ResultWindow, resultStructure, initialize_script, StartWindow
#from initialize_script import run_validator, get_layer_list_for_validator
from initialize_script import run_validator, get_layer_list_for_validator
imp.reload(ResultWindow) #юзається шоб скинути кеш скрипта коли ти шось там міняєш
imp.reload(resultStructure)#юзається шоб скинути кеш скрипта коли ти шось там міняєш
imp.reload(initialize_script)#юзається шоб скинути кеш скрипта коли ти шось там міняєш
from ResultWindow import *
from initialize_script import EDRA_validator
from StartWindow import startWindow




#from resultStructure import result

selected_layers = iface.layerTreeView().selectedLayersRecursive()


#result = run_validator(get_layer_list_for_validator(selected_layers))

#window = ResultWindow(result, parent=iface.mainWindow())

window = startWindow(parent=iface.mainWindow())

window.show()