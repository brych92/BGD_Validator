import json, os

from osgeo import ogr

from qgis.core import QgsProviderRegistry

# Можливі помилки
# Об'єкт з id "0" має помилку: "segments 142 and 229 of line 0 intersect at 33.5424, 48.2325"
# value is not unique'
from checker_class import EDRA_exchange_layer_checker, EDRA_validator

from qgis.core import QgsVectorLayer, QgsVectorFileWriter

def get_real_layer_name(layer):
    if layer.providerType() == "postgres":
        uri = layer.dataProvider().uri()
        source_layer_name = uri.table()
        source_layer_name = source_layer_name.strip("''")
    elif layer.providerType() == "ogr":
        uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        if uri_components["layerName"]:
            source_layer_name = uri_components["layerName"]
        else:
            directory, filename_with_extension = os.path.split(uri_components["path"])
            source_layer_name, extension = os.path.splitext(filename_with_extension)
    else:
        raise Error("Не зміг визначити імя джерела для шару {layer.name()}")
        source_layer_name = ''
        
    return source_layer_name




def get_layer_list_for_validator(selected_layers):
    layers_dict = {}
    for layer in selected_layers:
        # print(type(x))
        uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        
        path_to_layer = uri_components['path']
        
        layer_name = layer.name()#get_real_layer_name(layer)
        print(f'Назва {layer_name} {path_to_layer}')
        driver_name = layer.dataProvider().storageType()
        
        layer_crs = layer.crs().authid()
        
        layers_dict[layer.id()] = {'layer_crs': layer_crs, 'layer_name': layer_name, 'path': path_to_layer, 'driver_name': driver_name} 
        
    return layers_dict

def get_json_info_files(structure_bgd_file_path, domains_bgd_file_path):
    
    with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
        structure_json = json.loads(f.read())
        
    with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
        domains_json = json.loads(f.read())
        
    
        
def run_validator(layers_dict, ):
    all_layers_check_result_dict = {}
    all_layers_check_result_dict['layers'] = {}
    all_layers_check_result_dict['exchange_format_error'] = []
    all_layers_check_result_dict['missing_layers'] = []
    
    for layer_id in layers_dict:
        #driver = ogr.GetDriverByName(layers_dict[layer_id]['driver_name'])
        dataSource = ogr.Open(layers_dict[layer_id]['path'], 0) # 0 means read-only. 1 means writeable.

        layer = dataSource.GetLayer()
        
        layer_exchange_group = 'EDRA'
        layer_exchange_name = layers_dict[layer_id]['layer_real_name']
        
        
        structure_bgd_file_path = 'C:/Users/brych/OneDrive/Документы/01 Робота/98 Сторонні проекти/ua mbd team/Плагіни/Перевірка на МБД/BGD_Validator/EDRA_structure/structure_bgd3.json'
        domains_bgd_file_path = 'C:/Users/brych/OneDrive/Документы/01 Робота/98 Сторонні проекти/ua mbd team/Плагіни/Перевірка на МБД/BGD_Validator/EDRA_structure/domain.json'
        
        with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
            structure_json = json.loads(f.read())
        
        with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
            domains_json = json.loads(f.read())
            
        if layer is not None:
            layer_EDRA_valid_class = EDRA_validator(layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json)
        
        

        validate_checker = EDRA_exchange_layer_checker(layer_EDRA_valid_class, layers_dict[layer_id], layer_id, required_crs='')
        validate_result = validate_checker.run()
        
        all_layers_check_result_dict['layers'][list(validate_result.keys())[0]] = validate_result[list(validate_result.keys())[0]]
        
    return all_layers_check_result_dict
        
        
#selected_layers = iface.layerTreeView().selectedLayersRecursive()

#print(run_validator(get_layer_list_for_validator(selected_layers)))