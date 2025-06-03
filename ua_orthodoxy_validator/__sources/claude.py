from osgeo import ogr
from shapely.geometry import shape, Polygon, LineString, Point, MultiPolygon, mapping
from shapely import ops
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

class ShapelyGeometryValidator:
    """
    Class for validating OGR geometries using Shapely library.
    """
    
    def __init__(self, min_distance:float=0.001, max_vertices:float=100, crs:QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem('EPSG:4326')):
        """
        Initialize the validator with configurable thresholds.
        
        Args:
            min_distance (float): Minimum allowed distance between vertices
            max_vertices (int): Maximum reasonable number of vertices for simple geometries
        """
        self.min_distance = min_distance
        self.max_vertices = max_vertices
        
        self.crs = crs
            
        self.get_bounds()
        
        
        print(self.lon_bounds, self.lat_bounds)

    def get_bounds(self):
        """Get the bounds of the current CRS."""    
        original_extent = self.crs.bounds()
        if not self.crs.isGeographic():
            # Transform bounds to layer CRS
            transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'), self.crs, QgsProject.instance())
            extent = transform.transform(original_extent)
            self.lon_bounds = (extent.xMinimum(), extent.xMaximum())
            self.lat_bounds = (extent.yMinimum(), extent.yMaximum())
        else:
            self.lon_bounds = (original_extent.xMinimum(), original_extent.xMaximum())
            self.lat_bounds = (original_extent.yMinimum(), original_extent.yMaximum())
        
    def check_feature(self, feature):
        """
        Check an OGR feature for all geometry errors.
        
        Args:
            feature: OGR Feature object
            
        Returns:
            dict: Dictionary with error information
        """
        errors_list = []

        if feature is None:
            return {
                'has_error': True,
                'errors': {'error_type': 'no_feature'}
            }
            
            
        ogr_geom = cast(ogr.Geometry, feature.GetGeometryRef()) #feature.GetGeometryRef()
        if ogr_geom is None:
            return {
                'has_error': True,
                'errors': {'error_type': 'no_geometry'}
            }
        else:
            if ogr_geom.IsEmpty():
                return {
                    'has_error': True,
                    'errors': {'error_type': 'empty_geometry', 'error_coords': []}
                }
            
        # Convert OGR geometry to Shapely
        geom = from_wkt(ogr_geom.ExportToWkt())
        
        # Run all checks
        checks = [
            self.check_self_intersection,
            self.check_unclosed_polygon,
            self.check_duplicate_vertices,
            self.check_invalid_coordinates,
            self.check_vertex_order,
            self.check_too_close_vertices,
            self.check_zero_area,
            self.check_geometry_type_mismatch,
            self.check_spikes,
            self.check_kinks,
            self.check_overly_detailed,
            self.check_out_of_bounds
        ]
        
        for check in checks:
            result = check(geom)
            if result['has_error']:
                errors_list.append({'error_type': result['error_type'], 'error_coords': result['error_coords']})

        if len(errors_list) > 0:
            return {
                'has_error': True,
                'errors': errors_list
            }
        else:
            return {
                'has_error': False
            }
        
    def check_self_intersection(self, geom: shapely.geometry.base.BaseGeometry):
        """Check if a geometry intersects itself"""
        def check_segments_intersection(segments:list)->list:
            """Check if two segments intersect
            Args:
                segments (list): List of LineStrings
                
            Returns:
                list: List of intersection points
            """
            intersection_list = []
            for i in range(len(segments)-1):
                for j in range(i+1, len(segments)):
                    if segments[i].coords[0] in segments[j].coords or segments[i].coords[1] in segments[j].coords:
                        pass
                    if segments[i].intersects(segments[j]):
                        intersection_list.append(segments[i].intersection(segments[j]))
            return intersection_list
        
        def get_segments(geom: shapely.geometry.base.BaseGeometry)->list:
            segments = []
            for i in range(len(geom.coords) - 1):
                segments.append(LineString([geom.coords[i], geom.coords[i+1]]))
            return segments


        if "line" in geom.geom_type.lower():            
            if "multiline" in geom.geom_type.lower():
                self_intersections = []
                corss_intersections = []
                all_segments = []
                for geom in geom.geoms:
                    segments = get_segments(geom)
                    self_intersections.append(check_segments_intersection(segments))
                    all_segments.extend(segments)
                
                corss_intersections = [x for x in check_segments_intersection(all_segments) if x not in self_intersections]
                
                if len(self_intersections) > 0 or len(corss_intersections) > 0:
                    if len(corss_intersections) > 0:
                        error = 'cross_intersections'
                    else:
                        error = 'self_intersections'
                    return {
                        'has_error': True,
                        'error_type': error,
                        'error_coords': self_intersections + corss_intersections
                    }
                return {'has_error': False,'error_coords': []}
            
            segments = get_segments(geom)
            self_intersections = check_segments_intersection(segments)
            if len(self_intersections) > 0:
                return {
                    'has_error': True,
                    'error_type': 'self_intersections',
                    'error_coords': self_intersections
                }
            
            return {'has_error': False,'error_coords': []}

            
        if not geom.is_valid:
            reason = explain_validity(geom)
            print(reason)
            
            # Try to extract coordinates from the error reason
            if "Self-intersection" in reason:
                try:
                    # Shapely's explain_validity often includes coords like "[x y]"
                    coords_part = reason.split("[")[1].split("]")[0]
                    x, y = map(float, coords_part.split())
                    error_coords = [(x, y)]
                except (IndexError, ValueError):
                    # If extraction fails, try to get the representative point
                    try:
                        point = geom.representative_point()
                        error_coords = [(point.x, point.y)]
                    except:
                        error_coords = []
                
                return {
                    'has_error': True,
                    'error_type': 'self_intersection',
                    'error_coords': error_coords
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_unclosed_polygon(self, geom):
        """Check if a polygon is not closed"""
        if isinstance(geom, (Polygon, MultiPolygon)):
            # In Shapely, polygons are automatically closed, so we need to check the input coords
            if isinstance(geom, Polygon):
                rings = [geom.exterior] + list(geom.interiors)
            else:  # MultiPolygon
                rings = []
                for poly in geom.geoms:
                    rings.append(poly.exterior)
                    rings.extend(list(poly.interiors))
            
            for ring in rings:
                coords = list(ring.coords)
                if len(coords) >= 2:
                    if coords[0] != coords[-1]:
                        return {
                            'has_error': True,
                            'error_type': 'unclosed_polygon',
                            'error_coords': [coords[-1]]
                        }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_duplicate_vertices(self, geom):
        """Check for duplicate consecutive vertices"""
        coords = self._get_all_coords(geom)
        
        for i in range(1, len(coords)):
            prev_x, prev_y = coords[i-1]
            curr_x, curr_y = coords[i]
            
            if prev_x == curr_x and prev_y == curr_y:
                return {
                    'has_error': True,
                    'error_type': 'duplicate_vertices',
                    'error_coords': [(curr_x, curr_y)]
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_invalid_coordinates(self, geom):
        """Check for null or invalid coordinates"""
        coords = self._get_all_coords(geom)
        
        for x, y in coords:
            if (math.isnan(x) or math.isnan(y) or 
                math.isinf(x) or math.isinf(y)):
                return {
                    'has_error': True, 
                    'error_type': 'invalid_coordinates',
                    'error_coords': [(x, y)]
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_vertex_order(self, geom):
        """Check if polygon vertices are in the correct order (counter-clockwise for exterior rings)"""
        if isinstance(geom, Polygon):
            # In Shapely, the exterior should be counterclockwise and holes clockwise
            # Check if the exterior is clockwise (negative area)
            if self._is_clockwise(geom.exterior.coords):
                return {
                    'has_error': True,
                    'error_type': 'incorrect_vertex_order',
                    'error_coords': list(geom.exterior.coords)[:3]  # Return first few points
                }
                
            # Check if any interior rings are counterclockwise (positive area)
            for interior in geom.interiors:
                if not self._is_clockwise(interior.coords):
                    return {
                        'has_error': True,
                        'error_type': 'incorrect_vertex_order_hole',
                        'error_coords': list(interior.coords)[:3]  # Return first few points
                    }
                    
        elif isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                result = self.check_vertex_order(poly)
                if result['has_error']:
                    return result
        
        return {'has_error': False, 'error_coords': []}
    
    def _is_clockwise(self, coords):
        """Helper method to determine if a ring is clockwise"""
        # Use the shoelace formula to compute the signed area
        coords = list(coords)
        area = 0
        for i in range(len(coords) - 1):
            area += (coords[i+1][0] - coords[i][0]) * (coords[i+1][1] + coords[i][1])
        return area > 0  # Positive area means clockwise in Shapely's coordinate system
    
    def check_too_close_vertices(self, geom):
        """Check for vertices that are too close together"""
        coords = self._get_all_coords(geom)
        
        for i in range(1, len(coords)):
            prev_x, prev_y = coords[i-1]
            curr_x, curr_y = coords[i]
            
            # Calculate distance
            dist = math.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
            
            if 0 < dist < self.min_distance:
                return {
                    'has_error': True,
                    'error_type': 'too_close_vertices',
                    'error_coords': [(prev_x, prev_y), (curr_x, curr_y)]
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_zero_area(self, geom):
        """Check if a polygon has zero area or a line has zero length"""
        if isinstance(geom, (Polygon, MultiPolygon)):
            if geom.area < 1e-8:
                return {
                    'has_error': True,
                    'error_type': 'zero_area',
                    'error_coords': self._get_all_coords(geom)
                }
                
        elif isinstance(geom, LineString):
            if geom.length < 1e-8:
                return {
                    'has_error': True,
                    'error_type': 'zero_length',
                    'error_coords': self._get_all_coords(geom)
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_geometry_type_mismatch(self, geom):
        """Check if the geometry type matches its actual structure"""
        if isinstance(geom, Polygon):
            # A polygon should have at least 4 points (to form a triangle and close)
            if len(list(geom.exterior.coords)) < 4:
                return {
                    'has_error': True,
                    'error_type': 'geometry_type_mismatch',
                    'error_coords': list(geom.exterior.coords)
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_spikes(self, geom):
        """Check for spikes in the geometry"""
        coords = self._get_all_coords(geom)
        
        if len(coords) >= 3:
            for i in range(1, len(coords) - 1):
                prev = coords[i-1]
                curr = coords[i]
                next_pt = coords[i+1]
                
                # Calculate vectors
                v1 = (curr[0] - prev[0], curr[1] - prev[1])
                v2 = (next_pt[0] - curr[0], next_pt[1] - curr[1])
                
                # Normalize vectors
                len_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
                len_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
                
                if len_v1 > 0 and len_v2 > 0:
                    v1_norm = (v1[0]/len_v1, v1[1]/len_v1)
                    v2_norm = (v2[0]/len_v2, v2[1]/len_v2)
                    
                    # Dot product to find angle
                    dot_product = v1_norm[0] * v2_norm[0] + v1_norm[1] * v2_norm[1]
                    
                    # If dot product close to -1, vectors point in opposite directions (spike)
                    if dot_product < -0.95:  # ~170 degrees or more
                        return {
                            'has_error': True,
                            'error_type': 'spike',
                            'error_coords': [curr]
                        }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_kinks(self, geom):
        """Check for kinks (sharp angles) in the geometry"""
        coords = self._get_all_coords(geom)
        
        if len(coords) >= 3:
            for i in range(1, len(coords) - 1):
                prev = coords[i-1]
                curr = coords[i]
                next_pt = coords[i+1]
                
                # Calculate vectors
                v1 = (curr[0] - prev[0], curr[1] - prev[1])
                v2 = (next_pt[0] - curr[0], next_pt[1] - curr[1])
                
                # Normalize vectors
                len_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
                len_v2 = math.sqrt(v2[0]**2 + v2[1]**2)
                
                if len_v1 > 0 and len_v2 > 0:
                    v1_norm = (v1[0]/len_v1, v1[1]/len_v1)
                    v2_norm = (v2[0]/len_v2, v2[1]/len_v2)
                    
                    # Dot product to find angle
                    dot_product = v1_norm[0] * v2_norm[0] + v1_norm[1] * v2_norm[1]
                    
                    # If dot product close to 0, vectors are almost perpendicular (sharp angle)
                    if abs(dot_product) < 0.1:  # ~85-95 degrees
                        return {
                            'has_error': True,
                            'error_type': 'kink',
                            'error_coords': [curr]
                        }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_overly_detailed(self, geom):
        """Check if the geometry has an excessive number of vertices"""
        coords = self._get_all_coords(geom)
        
        if len(coords) > self.max_vertices:
            # Check if the geometry is actually simple (collinear points)
            is_simple = True
            for i in range(1, len(coords) - 1):
                prev = coords[i-1]
                curr = coords[i]
                next_pt = coords[i+1]
                
                # If three consecutive points are collinear, this is a sign of unnecessary detail
                if not self._are_collinear(prev, curr, next_pt):
                    is_simple = False
                    break
            
            if is_simple:
                return {
                    'has_error': True,
                    'error_type': 'overly_detailed',
                    'error_coords': [coords[0], coords[-1]]  # First and last point
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_out_of_bounds(self, geom):
        """Check if coordinates are outside valid ranges (e.g., lat/lon bounds)"""
        if self.lon_bounds is None or self.lat_bounds is None:
            return {'has_error': False, 'error_coords': []}
        coords = self._get_all_coords(geom)
        
        for x, y in coords:
            if not (self.lon_bounds[0] <= x <= self.lon_bounds[1] and 
                    self.lat_bounds[0] <= y <= self.lat_bounds[1]):
                return {
                    'has_error': True,
                    'error_type': 'out_of_bounds',
                    'error_coords': [(x, y)]
                }
        
        return {'has_error': False, 'error_coords': []}
    
    def _get_all_coords(self, geom):
        """Helper method to extract all coordinates from any Shapely geometry type"""
        if isinstance(geom, Point):
            return [(geom.x, geom.y)]
            
        elif isinstance(geom, LineString):
            return list(geom.coords)
            
        elif isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            for interior in geom.interiors:
                coords.extend(list(interior.coords))
            return coords
            
        elif hasattr(geom, 'geoms'):  # MultiPoint, MultiLineString, MultiPolygon
            coords = []
            for g in geom.geoms:
                coords.extend(self._get_all_coords(g))
            return coords
            
        return []
    
    def _are_collinear(self, p1, p2, p3, tolerance=1e-8):
        """Check if three points are collinear"""
        # Calculate the area of the triangle formed by the three points
        # If area is close to zero, points are collinear
        area = abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1])) / 2
        return area < tolerance
    
    def check_overlaps(self, features):
        """
        Check if multiple features overlap where they shouldn't
        
        Args:
            features: List of OGR Feature objects
            
        Returns:
            dict: Dictionary with error information
        """
        if len(features) < 2:
            return {'has_error': False, 'error_coords': []}
        
        # Convert OGR features to Shapely geometries
        geometries = []
        for feature in features:
            if feature is None:
                continue
                
            ogr_geom = feature.GetGeometryRef()
            if ogr_geom is None:
                continue
                
            geometries.append(shape(ogr_geom.ExportToJson()))
        
        # Check each pair for overlap
        for i in range(len(geometries)):
            for j in range(i+1, len(geometries)):
                if geometries[i].intersects(geometries[j]):
                    intersection = geometries[i].intersection(geometries[j])
                    if not intersection.is_empty:
                        # For a MultiGeometry, get the first component's coordinates
                        if hasattr(intersection, 'geoms'):
                            error_coords = self._get_all_coords(intersection.geoms[0])
                        else:
                            error_coords = self._get_all_coords(intersection)
                            
                        return {
                            'has_error': True,
                            'error_type': 'overlaps',
                            'error_coords': error_coords
                        }
        
        return {'has_error': False, 'error_coords': []}
    
    def check_gaps(self, features, tolerance=0.001):
        """
        Check for gaps between polygons that should be adjacent
        
        Args:
            features: List of OGR Feature objects
            tolerance: Maximum allowed gap distance
            
        Returns:
            dict: Dictionary with error information
        """
        if len(features) < 2:
            return {'has_error': False, 'error_coords': []}
            
        # Convert OGR features to Shapely geometries
        geometries = []
        for feature in features:
            if feature is None:
                continue
                
            ogr_geom = feature.GetGeometryRef()
            if ogr_geom is None:
                continue
                
            geom = shape(ogr_geom.ExportToJson())
            if isinstance(geom, (Polygon, MultiPolygon)):
                geometries.append(geom)
        
        if len(geometries) < 2:
            return {'has_error': False, 'error_coords': []}
            
        # Create a union of all geometries
        union = ops.unary_union(geometries)
        
        # Check for small internal rings (these are likely gaps)
        if isinstance(union, Polygon):
            for interior in union.interiors:
                # Create a polygon from the interior ring
                hole = Polygon(interior)
                if hole.area < tolerance:
                    return {
                        'has_error': True,
                        'error_type': 'gaps',
                        'error_coords': list(interior.coords)
                    }
        elif isinstance(union, MultiPolygon):
            # Find the main polygon (largest) and check its holes
            main_poly = max(union.geoms, key=lambda p: p.area)
            for interior in main_poly.interiors:
                hole = Polygon(interior)
                if hole.area < tolerance:
                    return {
                        'has_error': True,
                        'error_type': 'gaps',
                        'error_coords': list(interior.coords)
                    }
        
        return {'has_error': False, 'error_coords': []}
    
def get_ogr_layer(layer: QgsMapLayer)->gdal.Dataset:
    layerPath = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())['path']
    dataSource = cast(gdal.Dataset, ogr.Open(layerPath, 0))
    return dataSource


iface.mainWindow().findChild(QDockWidget, 'PythonConsole').console.shellOut.clearConsole()

validator = ShapelyGeometryValidator(crs = iface.activeLayer().crs())

selected_layers = []

for layer in iface.layerTreeView().selectedLayersRecursive():
    if layer.type() == QgsMapLayerType.VectorLayer and layer.featureCount() > 0:
        selected_layers.append(layer)

for layer in selected_layers:
    ogr_layer = get_ogr_layer(layer)

    for feature in ogr_layer.GetLayer():
        feature = cast(ogr.Feature, feature)
        # print(feature)
        #geom = cast(ogr.Geometry, feature.GetGeometryRef())
        # print(f"Тип геометріі: {geom.GetGeometryName()}")
        # print(f"Кількість точок: {geom.GetPointCount()}")

        # errors = validator.check_self_intersection(from_wkt(feature.GetGeometryRef().ExportToWkt()))
        errors = validator.check_feature(feature)
        print(f"\n\t{feature.GetFID()}:\n{errors}") #errors)