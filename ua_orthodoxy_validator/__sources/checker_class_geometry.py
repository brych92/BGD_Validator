from osgeo import ogr
from osgeo import gdal
import shapely.geometry
from shapely.wkt import loads as wkt_loads
from qgis.utils import iface
from qgis.core import QgsFeature, QgsMapLayerType, QgsMapLayer, QgsVectorLayer, QgsProviderRegistry
from qgis.gui import QgisInterface
from typing import cast
import shapely
from shapely.geometry import MultiPoint, LineString, MultiPolygon, Polygon

from shapely.validation import explain_validity

from claude import ShapelyGeometryValidator


def get_ogr_layer(layer: QgsMapLayer)->gdal.Dataset:
    layerPath = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())['path']
    dataSource = cast(gdal.Dataset, ogr.Open(layerPath, 0))
    return dataSource

selected_layers = []

for layer in iface.layerTreeView().selectedLayersRecursive():
    if layer.type() == QgsMapLayerType.VectorLayer and layer.featureCount() > 0:
        selected_layers.append(layer)

errors = {}

def vertex_duplicate_check(geom: ogr.Geometry)->dict:
    """Перевіряє наявність дублів точок у геометріі.

    Args:
        geom (ogr.Geometry): Геометрія.

    Returns:
        dict: Словник з помилками.
            {
            'has_error': True/False,
            'error_coords': [координати дублів],
            } 
    """    
    if geom.GetPointCount() < 2:
        return {
            'has_error': False,
            'error_coords': []
            }
    if "MULTI" in geom.GetGeometryName():
        for i in range(geom.GetGeometryCount()):
            pass
            

    if geom.GetGeometryName() != 'POLYGON':
        wkt_list = geom.ExportToWkt()
        wkt_list = wkt_list.split('(')[1].split(')')[0]
        wkt_list = wkt_list.split(', ')
        wkt_list = [tuple(wkt.split(' ')) for wkt in wkt_list]
        wkt_list = list(set(wkt_list))
        if len(wkt_list) != geom.GetPointCount():
            error_coords = [coord for coord in wkt_list if wkt_list.count(coord) > 1]
            return {
                'has_error': True,
                'error_coords': error_coords
                }
        else:
            return {
                'has_error': False,
                'error_coords': []
                }
    else:
        pass

validator = ShapelyGeometryValidator()

for layer in selected_layers:
    ogr_layer = get_ogr_layer(layer)

    for feature in ogr_layer.GetLayer():
        feature = cast(ogr.Feature, feature)
        geom = cast(ogr.Geometry, feature.GetGeometryRef())
        
        # print(f"Тип геометріі: {geom.GetGeometryName()}")
        # print(f"Кількість точок: {geom.GetPointCount()}")
        print(f"{geom.ExportToWkt()}")
    
    
    
    # print(f"Перевіряю {layer.name()}")
    # layer = cast(QgsVectorLayer, layer)
    # objects = layer.getFeatures()
    # print(f"Кількість об'єктів: {layer.featureCount()}")
    
    # for object in objects:
    #     print(f"Перевіряємо об'єкт: {object.id()}") #, object)
    #     q_geom = object.geometry()
    #     wkt_geom = q_geom.asWkt()
    #     #print(wkt_geom)

        s_geom = cast(shapely.geometry.base.BaseGeometry, wkt_loads(wkt_geom))
    #     print(f"Тип геометріі: {s_geom.geom_type}")
    #     explination = explain_validity(s_geom)
    #     if explination != "Valid Geometry":
    #         print(f"\tValidity: {explain_validity(s_geom)}")
    #         errors[f"{layer.name()} - {object.id()}"] = explination
        # print(f"\thas_m: {s_geom.has_m}")
        # print(f"\thas_z: {s_geom.has_z}")
        # print(f"\tis_empty: {s_geom.is_empty}")
        # print(f"\tis_ring: {s_geom.is_ring}")
        # print(f"\tis_simple: {s_geom.is_simple}")
        # print(f"\tis_valid: {s_geom.is_valid}")

        # if s_geom.geom_type == 'linestring':
        #     print(f"\tis_closed: {s_geom.is_closed}")

        #     print(f"\tis_ccw: {s_geom.is_ccw}")
        #     print(f"\tis_geometry: {s_geom.is_geometry}")
        #     print(f"\tis_missing: {s_geom.is_missing}")
        #     print(f"\tis_prepared: {s_geom.is_prepared}")
        #     print(f"\tis_valid_input: {s_geom.is_valid_input}")
        #     print(f"\tis_valid_reason: {s_geom.is_valid_reason}")


        #print(type(s_geom))
#print(errors)