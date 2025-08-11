"""
validator_template.py
---------------------
Каркас GeoValidator із готовими заглушками під усі правила
(A1…G2).  Скопіюйте файл, реалізуйте перевірки поетапно.
Потребує GDAL/OGR та Shapely ≥2.0
"""



from __future__ import annotations
import math
from typing import Any, Callable, Dict, List, Sequence, Optional
from osgeo import ogr
from shapely.geometry import shape as _shape
from shapely.validation import explain_validity

from itertools import combinations
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

Result = Dict[str, Any]
ResultList = List[Result]

from osgeo import ogr
from shapely.geometry import shape, Polygon, LineString, Point, MultiPolygon, mapping
from shapely import wkb
from shapely.validation import explain_validity
import math
import numpy as np

from PyQt5.QtWidgets import QDockWidget, QWidget, QPushButton, QVBoxLayout

import shapely.geometry

from shapely import from_wkt

from osgeo import gdal
from shapely.wkt import loads as wkt_loads
from qgis.utils import iface
from qgis.core import QgsFeature, QgsMapLayerType, QgsMapLayer, QgsVectorLayer,\
    QgsProviderRegistry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgisInterface
from typing import cast

import json
from shapely import from_geojson          # Shapely ≥ 2.0

#from .sidefunctions import log


class GeoValidator:
    # ------------------------------------------------------------------ init
    ogr_geometry_types = {
        0: 'wkbUnknown',
        1: 'wkbPoint',
        2: 'wkbLineString',
        3: 'wkbPolygon',
        4: 'wkbMultiPoint',
        5: 'wkbMultiLineString',
        6: 'wkbMultiPolygon',
        7: 'wkbGeometryCollection',
        100: 'wkbNone',

        # 2.5D варіанти
        101: 'wkbPoint25D',
        102: 'wkbLineString25D',
        103: 'wkbPolygon25D',
        104: 'wkbMultiPoint25D',
        105: 'wkbMultiLineString25D',
        106: 'wkbMultiPolygon25D',
        107: 'wkbGeometryCollection25D',
        
        # Новіші типи (GDAL 2+)
        16: 'wkbCircularString',
        17: 'wkbCompoundCurve',
        18: 'wkbCurvePolygon',
        19: 'wkbMultiCurve',
        20: 'wkbMultiSurface',
        21: 'wkbCurve',
        22: 'wkbSurface',
        23: 'wkbPolyhedralSurface',
        24: 'wkbTIN',
        25: 'wkbTriangle',

        # 2.5D версії новіших типів (як правило, код + 1000)
        1001: 'wkbCircularString25D',
        1002: 'wkbCompoundCurve25D',
        1003: 'wkbCurvePolygon25D',
        1004: 'wkbMultiCurve25D',
        1005: 'wkbMultiSurface25D',
        1006: 'wkbCurve25D',
        1007: 'wkbSurface25D',
        1008: 'wkbPolyhedralSurface25D',
        1009: 'wkbTIN25D',
        1010: 'wkbTriangle25D'
    }

    def __init__(
        self,
        *,
        checks: Optional[Sequence[str]] = None,
        tolerance: float = 1e-8,
        expected_types: list[str] = None,
        expected_crs: Optional[str] = None,
        allow_z: bool = False,
        name: Optional[str] = None
    ) -> None:
        self.tol = tolerance
        self.expected_types = expected_types
        self.expected_crs = expected_crs
        self.allow_z = allow_z
        self.checks = checks


        self.brake_points = ["C1", "C2", "С3", "C4"]
        # if checks is None:
        #     log(f"Правила перевірки не вказані при ініціалізації класу GeoValidator({name})")
        # if expected_crs is None:
        #     log(f"Очікуваний CRS не вказаний при ініціалізації класу GeoValidator({name})")
        # if expected_types is None:
        #     log(f"Очікуваний тип геометрій не вказаний при ініціалізації класу GeoValidator({name})")
        # if allow_z is None:
        #     log(f"Значення allow_z не вказано при ініціалізації класу GeoValidator({name})")


        # ---------- РЕЄСТР: код → метод ------------------------------------
        self._registry: Dict[str, Callable[[ogr.Feature], ResultList]] = {
            "C1": self._is_none, # Перевірка на None
            "C2": self._is_empty, # Перевірка на порожню геометрію
            "C3": self._is_correct_type, # Перевірка на тип геометрії
            "C4": self._is_correct_length_area, # Перевірка на довжину/площу геометрій
            "A1": self._check_A1, # Перевірка на самоперетинення
            "A2": self._check_A2,
            "A3": self._check_A3,
            "A4": self._check_A4,
            "A5": self._check_A5,
            "A6": self._check_A6,
            "B1": self._check_B1,
            "B2": self._check_B2,
            "B3": self._check_B3,
            "B4": self._check_B4,
            "C5": self._check_C5,
            "C6": self._check_C6,
            "D1": self._check_D1,
            "D2": self._check_D2,
            "D3": self._check_D3,
            "D4": self._check_D4,
            "E1": self._check_E1,
            "E2": self._check_E2,
            "E3": self._check_E3,
            "E4": self._check_E4,
            "F1": self._check_F1,
            "F2": self._check_F2,
            "F3": self._check_F3,
            "F4": self._check_F4,
            "G1": self._check_G1,
            "G2": self._check_G2,
        }

        self.active = set(checks) if checks else set(self._registry)

    # -------------------------------------------------------- helper convert
    def _to_shapely(self, ogr_geom: ogr.Geometry) -> shapely.geometry.base.BaseGeometry:
        """OGR → Shapely geometry (коректне перетворення)."""
        if ogr_geom is None:
            return None
        return wkb.loads(bytes(ogr_geom.ExportToWkb()))

    # -------------------------------------------------------- public methods
    def validate_feature(self, ogr_feature: ogr.Feature) -> ResultList:
        results: ResultList = []
        for code in self._registry.keys():#self.active:
            try:
                #print(f"Перевіряю {code}")
                check_result = self._registry[code](ogr_feature)
                #print(check_result)
                results.append(check_result)
                if code in self.brake_points and check_result['result'] == 'NOK':
                    return results
            except NotImplementedError:
                #print(f"Перевірка {code} не реалізована")
                # ще не реалізовано — пропускаємо
                continue
            except Exception as exc:
                results.append({
                    "check": code,
                    "result": "ERR",
                    "message": f"{exc}",
                    "error_coords": []
                })
                if code in self.brake_points:
                    return results
        
        return results
    
    #--- Z. Вхідні перевірки -----------------------------------------------
    def _is_none(self, feat: ogr.Feature) -> ResultList:
        print('is none here')
        geom = feat.GetGeometryRef()
        if geom is None:
            return {
                "check": "C1",
                "result": "NOK"
            }
        return {
                "check": "C1",
                "result": "OK"
            }
    
    def _is_empty(self, feat: ogr.Feature) -> ResultList:
        geom = feat.GetGeometryRef()
        if geom.IsEmpty():
            return {
                "check": "C2",
                "result": "NOK"
            }
        return {
                "check": "C2",
                "result": "OK"
            }
    
    def _is_correct_type(self, feat: ogr.Feature) -> ResultList:
        if self.expected_types is None:
            raise ValueError("При ініціалізації перевірки не вказано очікуваних типів геометрій")
        if len(self.expected_types) == 0:
            return {
                "check": "C3",
                "result": "OK",
                "message": "При ініціалізації перевірки не вказано очікуваних типів геометрій"
            }
        #треба перевірити чи хаває якщо в мультигеометрії є одна точка і лінія ітд
        geom = cast(ogr.Geometry, feat.GetGeometryRef())
        geom_type = geom.GetGeometryName()
        print(f"Перевіряємо тип геометрії: {geom_type} по відповідності з {self.expected_types}")
        if geom_type in self.expected_types:
            return {
                "check": "C3",
                "result": "OK"
            }
        return {
                "check": "C3",
                "result": "NOK"
            }

    def _is_correct_length_area(self, feat: ogr.Feature) -> ResultList:
        geom = cast(ogr.Geometry, feat.GetGeometryRef())
        geom_type = geom.GetGeometryName()
        if geom_type in ['POINT','MULTIPOINT']:
            return {
                "check": "C4",
                "result": "OK"
            }
        shp_geom = self._to_shapely(geom)
        if geom_type in ['LINESTRING','MULTILINESTRING']:
            if shp_geom.length < self.tol:
                return {
                    "check": "C4",
                    "result": "NOK"
                }
            else:
                return {
                    "check": "C4",
                    "result": "OK"
                }
        
        if geom_type in ['POLYGON','MULTIPOLYGON']:
            if shp_geom.area < self.tol*self.tol:
                return {
                    "check": "C4",
                    "result": "NOK"
                }
            else:
                return {
                    "check": "C4",
                    "result": "OK"
                }
        
        raise  ValueError(f"Валідатор не може перевірити геометрію типу: {geom_type}")
        
    # ===================================================== RULE TEMPLATES ==
    # --- A. ТОПОЛОГІЯ -------------------------------------------------------
    # Self‑intersection
    def _check_A1(self, ogr_feature: ogr.Feature) -> ResultList:
        """
        Повертає список координат усіх точок самоперетину для LineString.
        
        Parameters
        ----------
        ogr_geom : ogr.Geometry
            OGR-геометрія типу LineString.
            
        Returns
        -------
        List[Tuple[float, float]]
            Список (x, y) всіх точок, де лінія перетинає сама себе.
        """
        def segmantize_line(geom: LineString) -> List[LineString]:
            segments = []
            if len(geom.coords) < 2:
                raise ValueError("Помилка розмірності частини геометрії. LineString має мати мінімум дві точки")
            for i in range(len(geom.coords) - 1):
                segments.append(LineString([geom.coords[i], geom.coords[i+1]]))            
            return segments

        def get_segments_intersection(segments:List[LineString])->list:
            intersection_list = []
            for i, j in combinations(range(len(segments)), 2):
                if abs(i - j) <= 1:  # Пропускаємо сусідні відрізки
                    continue
                seg1, seg2 = segments[i], segments[j]
                if seg1.intersects(seg2):
                    intersection = seg1.intersection(seg2)
                    if intersection.geom_type == "Point":
                        intersection_list.append((intersection.x, intersection.y))
                    else:
                        coords = shapely.get_coordinates(intersection)
                        points = [(point[0], point[1]) for point in coords]
                        intersection_list.extend(points)
            
            return intersection_list

        result = {
            "check": "A1",
            'result': 'NOK',
            'exceptions': [],
            'error_coords': [],
            }
        
        if ogr_feature.GetGeometryRef() is None or ogr_feature.GetGeometryRef().IsEmpty():
            raise AttributeError(f"Обєкт не має геометрії")
        
        if ogr_feature.geometry().GetGeometryType() not in [ogr.wkbLineString25D, ogr.wkbLineString, ogr.wkbLineStringM, ogr.wkbLineStringZM, ogr.wkbMultiLineString, ogr.wkbMultiLineString25D, ogr.wkbMultiLineStringM, ogr.wkbMultiLineStringZM]:
            raise AttributeError(f"Обєкт не є LineString, насправді({ogr_feature.geometry().GetGeometryName()})")
            
        ogr_geom = cast(ogr.Geometry, ogr_feature.geometry())
        
        if ogr_geom.GetPointCount() == 1:
            raise AttributeError(f"Обєкт має тільки одну точку")
        
        if ogr_geom.GetGeometryCount() > 0:
            segments = []
            for i in range(ogr_geom.GetGeometryCount()):
                geom_part = ogr_geom.GetGeometryRef(i)
                
                shp_geom = self._to_shapely(geom_part)
                segments.extend(segmantize_line(shp_geom))
                
            error_coords = get_segments_intersection(segments)
            
            if len(error_coords) > 0:
                result['result'] = 'NOK'
                result['error_coords'] = error_coords
            
            return result

        else:
            if ogr_geom.GetPointCount() == 1:
                raise ValueError(f"Обєкт {ogr_feature.GetFID()}({ogr_feature.GetField('name')}) має лише одну точку")

            if ogr_geom.GetPointCount() >= 3:
                result['result'] = 'OK'
                return result
                
            shp_geom = self._to_shapely(ogr_geom)

            # Перевіряємо, чи лінія не має самоперетинів
            if shp_geom.is_simple:
                result['result'] = 'OK'
                return result
            
            error_coords = get_segments_intersection(segmantize_line(shp_geom))
            result['result'] = 'NOK' if len(error_coords) > 0 else 'OK'
            result['error_coords'] = error_coords
            return result

    
    def _check_A2(self, feat): raise NotImplementedError  # Overlaps
    def _check_A3(self, feat): raise NotImplementedError  # Gaps
    def _check_A4(self, feat): raise NotImplementedError  # Unclosed ring
    def _check_A5(self, feat): raise NotImplementedError  # Duplicate vertices
    def _check_A6(self, feat): raise NotImplementedError  # Dangling line

    # --- B. КООРДИНАТИ ------------------------------------------------------
    def _check_B1(self, feat): raise NotImplementedError  # Invalid / NaN coord
    def _check_B2(self, feat): raise NotImplementedError  # Wrong vertex order
    def _check_B3(self, feat): raise NotImplementedError  # Too close vertices
    def _check_B4(self, feat): raise NotImplementedError  # Bad Z value

    # --- C. ТИП / РОЗМІРНІСТЬ ----------------------------------------------
    def _check_C1(self, feat): raise NotImplementedError  # Zero length/area
    def _check_C2(self, feat): raise NotImplementedError  # Type mismatch
    def _check_C3(self, feat): raise NotImplementedError  # no_geometry
    def _check_C4(self, feat): raise NotImplementedError  # empty_geometry
    def _check_C5(self, feat): raise NotImplementedError  # Invalid part count
    def _check_C6(self, feat): raise NotImplementedError  # Mixed types

    # --- D. АНОМАЛІЇ ФОРМИ --------------------------------------------------
    def _check_D1(self, feat): raise NotImplementedError  # Spikes
    def _check_D2(self, feat): raise NotImplementedError  # Kinks
    def _check_D3(self, feat): raise NotImplementedError  # Over‑detailed
    def _check_D4(self, feat): raise NotImplementedError  # Collapsed edges

    # --- E. CRS / КОНТЕКСТ --------------------------------------------------
    def _check_E1(self, feat): raise NotImplementedError  # CRS mismatch
    def _check_E2(self, feat): raise NotImplementedError  # Out of bounds
    def _check_E3(self, feat): raise NotImplementedError  # Undefined CRS
    def _check_E4(self, feat): raise NotImplementedError  # Mixed layer CRS

    # --- F. АТРИБУТИ ↔ ГЕОМЕТРІЯ -------------------------------------------
    def _check_F1(self, feat): raise NotImplementedError  # Area/length mismatch
    def _check_F2(self, feat): raise NotImplementedError  # Mandatory field null
    def _check_F3(self, feat): raise NotImplementedError  # Domain violation
    def _check_F4(self, feat): raise NotImplementedError  # ID not unique

    # --- G. CROSS‑LAYER -----------------------------------------------------
    def _check_G1(self, feat): raise NotImplementedError  # Must be within
    def _check_G2(self, feat): raise NotImplementedError  # Must not overlap


def get_ogr_layer(layer: QgsMapLayer)->gdal.Dataset:
    layerPath = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())['path']
    dataSource = cast(gdal.Dataset, ogr.Open(layerPath, 0))
    return dataSource


def decribe_geom(ogr_feature: QgsFeature) -> None: 
    ogr_geom = cast(ogr.Geometry, ogr_feature.geometry())
    if ogr_feature.GetFieldIndex("name") != -1:
        name = ogr_feature.GetField('name')
    else:
        name = ''
    print(f"{'='*50}\r\n\tReport for feature {ogr_feature.GetFID()}({name})\r\n{'='*50}")
    
    print(f"\tGeometry object: {ogr_geom}")
    print(f"\tGeometry WKT type: {ogr_geom.GetGeometryName()}")
    print(f"\tGeometry geom type: {GeoValidator.ogr_geometry_types[ogr_geom.GetGeometryType()]}({ogr_geom.GetGeometryType()})")
    print(f"\tGeometry geom count: {ogr_geom.GetGeometryCount()}")
    if ogr_geom.GetGeometryCount() > 0: 
        for i in range(ogr_geom.GetGeometryCount()): 
            print(f"\t\tGeometry ref {i}: {ogr_geom.GetGeometryRef(i)}")
            print(f"\t\tGeometry ref {i} type: {ogr_geom.GetGeometryRef(i).GetGeometryName()}")
            print(f"\t\tGeometry ref {i} geom type: {GeoValidator.ogr_geometry_types[ogr_geom.GetGeometryRef(i).GetGeometryType()]}({ogr_geom.GetGeometryRef(i).GetGeometryType()})")
            print(f"\t\tGeometry ref {i} geom count: {ogr_geom.GetGeometryRef(i).GetGeometryCount()}")
            if ogr_geom.GetGeometryRef(i).GetGeometryCount() > 0:
                for j in range(ogr_geom.GetGeometryRef(i).GetGeometryCount()):
                    print(f"\t\t\tGeometry ref {i} geom ref {j}: {ogr_geom.GetGeometryRef(i).GetGeometryRef(j)}")
                    print(f"\t\t\tGeometry ref {i} geom ref {j} type: {ogr_geom.GetGeometryRef(i).GetGeometryRef(j).GetGeometryName()}")
                    print(f"\t\t\tGeometry ref {i} geom ref {j} geom type: {ogr_geom.GetGeometryRef(i).GetGeometryRef(j).GetGeometryType()}")
    
    print(f"\tGeometry get linear geom: {ogr_geom.GetLinearGeometry()}")
    print(f"\tGeometry point count: {ogr_geom.GetPointCount()}")
    
    print(f"\tGeometry WKT: {ogr_geom.ExportToWkt()}")
    

iface.mainWindow().findChild(QDockWidget, 'PythonConsole').console.shellOut.clearConsole()

validator = GeoValidator(
    expected_crs = iface.activeLayer().crs(),
    expected_types=[], #['POINT', 'MULTIPOINT'],
    tolerance=0.01
    )

selected_layers = []

for layer in iface.layerTreeView().selectedLayersRecursive():
    if layer.type() == QgsMapLayerType.VectorLayer and layer.featureCount() > 0:
        selected_layers.append(layer)

for layer in selected_layers:
    ogr_layer = get_ogr_layer(layer)
    #print(f"Перевіряю {ogr.GeometryTypeToName(ogr_layer.GetLayer().GetGeomType())}")

    for ogr_feature in ogr_layer.GetLayer():
        ogr_feature = cast(ogr.Feature, ogr_feature)
        #decribe_geom(ogr_feature)
        if ogr_feature.GetFieldIndex("name") != -1:
            name = ogr_feature.GetField('name')
        else:
            name = ''
        errors = validator.validate_feature(ogr_feature)
        print(f"\n\t{name}({ogr_feature.GetFID()}):\n{json.dumps(errors, indent=2, ensure_ascii=False)}")
        # print(f"{json.dumps(errors, indent=2, ensure_ascii=False)}") #errors)