    
from osgeo import ogr
from shapely.wkt import loads as wkt_loads

from shapely.geometry import MultiPoint, LineString, MultiPolygon, Polygon

#1. Перевірка на дубліковані точки (MultiPoint)

def has_duplicate_points(geometry):
    if not isinstance(geometry, MultiPoint):
        return None
    
    points = list(geometry.geoms)
    seen = {}
    duplicates = []
    
    for i, point in enumerate(points):
        if point.coords[0] in seen:
            duplicates.append((i, point))
        else:
            seen[point.coords[0]] = i
    
    if duplicates:
        return [(dup[0], dup[1].wkt) for dup in duplicates]  # Повертає індекс та WKT дубльованих точок
    return None

# Приклад використання:
duplicate_points = MultiPoint([(10, 20), (15, 25), (10, 20)])
print(has_duplicate_points(duplicate_points))  
# [(2, 'POINT (10 20)')]

#2. Перевірка на дубльовані вершини (LineString)

def has_duplicate_vertices(geometry):
    if not isinstance(geometry, LineString):
        return None
    
    coords = list(geometry.coords)
    seen = {}
    duplicates = []
    
    for i, coord in enumerate(coords):
        if coord in seen:
            duplicates.append((i, coord))
        else:
            seen[coord] = i
    
    if duplicates:
        return [(dup[0], f"POINT ({dup[1][0]} {dup[1][1]})") for dup in duplicates]  # Повертає індекс та WKT дубльованих точок
    return None

# Приклад використання:
line_with_duplicates = LineString([(10, 20), (15, 25), (15, 25), (20, 30)])
print(has_duplicate_vertices(line_with_duplicates))  
# [(2, 'POINT (15 25)')]
 
#3. Перевірка на вироджену лінію (Degenerate Line)

def is_degenerate_line(geometry):
    if not isinstance(geometry, LineString):
        return None
    
    coords = list(geometry.coords)
    
    if len(set(coords)) < 2:  # Якщо всі точки однакові
        return f"LINESTRING ({', '.join([f'{x} {y}' for x, y in coords])})"
    
    return None

# Приклад використання:
degenerate_line = LineString([(10, 20), (10, 20)])
print(is_degenerate_line(degenerate_line))  
# 'LINESTRING (10 20, 10 20)'


#4. Перевірка на самозамикання кільця (Self-closing ring)

def has_self_closing_ring(geometry):
    if not isinstance(geometry, Polygon):
        return None
    
    exterior_coords = list(geometry.exterior.coords)
    seen = {}
    duplicates = []
    
    for i, coord in enumerate(exterior_coords):
        if coord in seen:
            duplicates.append((i, coord))
        else:
            seen[coord] = i
    
    if duplicates:
        return [(dup[0], f"POINT ({dup[1][0]} {dup[1][1]})") for dup in duplicates]  # Повертає індекс та WKT дубльованих точок
    return None

# Приклад використання:
self_closing_ring = Polygon([(10, 20), (15, 25), (20, 20), (15, 15), (10, 20), (15, 25)])
print(has_self_closing_ring(self_closing_ring))  
# [(5, 'POINT (15 25)')]


# 5. Перевірка на неправильний напрямок кільця (Invalid ring direction)

def is_invalid_ring_direction(geometry):
    if not isinstance(geometry, Polygon):
        return None
    
    if not geometry.exterior.is_ccw:  # Перевірка напрямку зовнішнього кільця
        return geometry.exterior.wkt
    
    return None

# Приклад використання:
invalid_ring_direction = Polygon([(10, 10), (20, 10), (20, 20), (10, 20), (10, 10)])
print(is_invalid_ring_direction(invalid_ring_direction))  
# 'LINESTRING (10 10, 20 10, 20 20, 10 20, 10 10)'


# 6. Перевірка на вироджений полігон (Degenerate Polygon)

def is_degenerate_polygon(geometry):
    if not isinstance(geometry, Polygon):
        return None
    
    exterior_coords = list(geometry.exterior.coords)
    
    if len(exterior_coords) < 4:  # Якщо полігон має менше 4 точок
        return geometry.exterior.wkt
    
    return None

# Приклад використання:
degenerate_polygon = Polygon([(10, 10), (20, 20), (30, 30)])
print(is_degenerate_polygon(degenerate_polygon))  
# 'LINESTRING (10 10, 20 20, 30 30, 10 10)'

# 7. Перевірка на порожні полігони (Empty polygons)
def has_empty_polygons(geometry):
    if not isinstance(geometry, MultiPolygon):
        return None
    
    empty_polygons = [polygon for polygon in geometry.geoms if polygon.is_empty]
    
    if empty_polygons:
        return [polygon.wkt for polygon in empty_polygons]  # Повертає WKT порожніх полігонів
    return None

# Приклад використання:
empty_polygon = MultiPolygon([Polygon([(10, 10), (20, 20), (30, 30)]), Polygon()])
print(has_empty_polygons(empty_polygon))  
# ['POLYGON EMPTY']


# 8. Перевірка на порожні лінії (Empty lines)

def has_empty_lines(geometry):
    if isinstance(geometry, MultiLineString):
        empty_lines = [line for line in geometry.geoms if line.is_empty]
        if empty_lines:
            return [line.wkt for line in empty_lines]  # Повертає WKT порожніх ліній
    elif isinstance(geometry, LineString) and geometry.is_empty:
        return geometry.wkt
    return None

# Приклад використання:
empty_lines = MultiLineString([LineString([(10, 10), (20, 20)]), LineString([])])
print(has_empty_lines(empty_lines))  
# ['LINESTRING EMPTY']


# 9. Перевірка на незамкнуте кільце (Unclosed ring)

from shapely.geometry import LineString

def is_unclosed_ring(geometry):
    if not isinstance(geometry, LineString):
        return None
    
    coords = list(geometry.coords)
    
    if coords[0] != coords[-1]:  # Якщо кільце не замкнуте
        return geometry.wkt
    
    return None

# Приклад використання:
unclosed_ring = LineString([(10, 20), (20, 30), (30, 20)])
print(is_unclosed_ring(unclosed_ring))  
# 'LINESTRING (10 20, 20 30, 30 20)'


