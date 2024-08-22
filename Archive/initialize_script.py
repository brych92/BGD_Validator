import json, os
from importlib import reload

from osgeo import ogr

from qgis.core import QgsProviderRegistry

import checker_class
reload(checker_class)
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
        
    
        
def run_validator(layers:dict, structure_path:str, domains_path:str):
    """
    Запустити валідатор для шарів.

    Args:
        layers (dict): Словник шарів. Кожен шар - це словник з ключами:
            - layer_crs (str): Система координат шару.
            - layer_name (str): Ім'я шару.
            - path (str): Шлях до шару.
            - driver_name (str): Ім'я драйвера, який використовувався для відкриття шару.
        structure_path (str): Шлях до файлу структури.
        domains_path (str): Шлях до файлу доменів.

    Returns:
        dict: Словник з результатами валідатору.
            - layers (dict): Словник результатів валідатору для кожного шару.
            - exchange_format_error (list): Список шарів з помилками формату обміну.
            - missing_layers (list): Список відсутніх шарів.
    """


    all_layers_check_result_dict = {}
    all_layers_check_result_dict['layers'] = {}
    all_layers_check_result_dict['exchange_format_error'] = []
    all_layers_check_result_dict['missing_layers'] = []
    
    for id in layers:
        dataSource = ogr.Open(layers[id]['path'], 0) # 0 means read-only. 1 means writeable.

        layer = dataSource.GetLayer()
        
        group = 'EDRA'
        layer_real_name = layers[id]['layer_real_name']
        
        with open(structure_path, 'r', encoding='utf-8') as f: 
            structure = json.loads(f.read())
        
        with open(domains_path, 'r', encoding='utf-8') as f: 
            domains = json.loads(f.read())
            
        if layer is None:
            raise AttributeError(f'Не вдалося відкрити шар {layers[id]["path"]}')
        
        layer_EDRA_valid_class = EDRA_validator(
            layer = layer,
            layer_exchange_group=group,
            layer_exchange_name=layer_real_name,
            structure_json=structure,
            domains_json=domains)
        
        validate_checker = EDRA_exchange_layer_checker(
            layer_EDRA_valid_class = layer_EDRA_valid_class,
            layer_props = layers[id],
            layer_id = id)
        
        validate_result = validate_checker.run()
        
        all_layers_check_result_dict['layers'][list(validate_result.keys())[0]] = validate_result[list(validate_result.keys())[0]]
        
    return all_layers_check_result_dict
        
        