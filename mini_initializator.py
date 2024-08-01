import json 


from osgeo import ogr

from checker_class import EDRA_validator, EDRA_exchange_layer_checker


domains_bgd_file_path = r'/home/bohdan/Programming/ПЛАГІН/domain.json'
structure_bgd_file_path = r'/home/bohdan/Programming/ПЛАГІН/structure_bgd3.json'
        
with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
    structure_json = json.loads(f.read())
        
with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
    domains_json = json.loads(f.read())


layer_exchange_group = 'EDRA'

path_to_layer = r'/home/bohdan/Programming/ПЛАГІН/buildings_polygon.geojson'


driver = ogr.GetDriverByName('GeoJSON')
dataSource = driver.Open(path_to_layer, 0) # 0 means read-only. 1 means writeable.

layer = dataSource.GetLayer()

layer_exchange_name = 'buildings_polygon'

layer_EDRA_valid_class = EDRA_validator(layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json)

validate_checker = EDRA_exchange_layer_checker(layer_EDRA_valid_class, {'layer_name': layer_exchange_name, 'name': layer_exchange_name, 'driver_name': 'GeoJSON', 'path': path_to_layer}, '1')

print(validate_checker.run())

#print([ogr.GeometryTypeToName(layer_EDRA_valid_class.layer.GetGeomType()).replace(' ', ''), layer_EDRA_valid_class.required_geometry_type])

#print(layer_EDRA_valid_class.compare_object_geometry_type(ogr.GeometryTypeToName(layer_EDRA_valid_class.layer.GetGeomType()).replace(' ', ''), layer_EDRA_valid_class.required_geometry_type))

#print(layer_EDRA_valid_class.check_fields_type_and_names(layer_EDRA_valid_class.layerDefinition))

