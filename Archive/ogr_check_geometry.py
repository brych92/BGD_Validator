import os
from osgeo import ogr

print(bool(None))

path_to_file = '/home/bohdan/Programming/ПЛАГІН/Рядове межа (копія).geojson'

driver = ogr.GetDriverByName('GeoJSON')

dataSource = driver.Open(path_to_file, 0) # 0 means read-only. 1 means writeable.

print(type(dataSource))

# Check to see if shapefile is found.
if dataSource is None:
    print('Could not open %s' % (path_to_file))
else:
    print('Opened %s' % (path_to_file))
    layer = dataSource.GetLayer()
    #print(layer.GetName())
    #print(ogr.GeometryTypeToName(layer.GetGeomType()))
    featureCount = layer.GetFeatureCount()

    layerDefinition = layer.GetLayerDefn()
    
    for i in range(layerDefinition.GetFieldCount()):
        layerDefinition.GetFieldDefn(i).SetNullable(0)
        layerDefinition.GetFieldDefn(i).SetUnique(0)

    for feature in layer:
        #print(ogr.GeometryTypeToName(feature.geometry().GetGeometryType()))

        for i in range(layerDefinition.GetFieldCount()):
            
            print(feature[i])
            print(f'null {feature.IsFieldNull(i)}')
            print(f'unique {feature.IsFieldSetAndNotNull(i)}')
        #print(feature.Validate())

    # layer_field_names = []
    
    #     print(f'nullable {layerDefinition.GetFieldDefn(i).IsNullable()}')
    #     print(f'unique {layerDefinition.GetFieldDefn(i).IsUnique()}')
        
    print(layer_field_names)