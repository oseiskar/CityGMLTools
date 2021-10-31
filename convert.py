import click
import sys

def remove_recurring(coords):
    if len(coords) < 2: return coords
    r = []
    prev_ct = None
    for idx, c in enumerate(coords):
        ct = tuple(list(c))
        if ct != prev_ct:
            r.append(c)
        else:
            sys.stderr.write('WARN: removed recurring vertex at idx %d/%d\n' % (idx+1, len(coords)))
        prev_ct = ct
    if prev_ct == tuple(list(coords[0])):
        # sys.stderr.write('removed recurring last vertex\n')
        r = r[:-1]
    return r

def linear_ring_to_triangles(coords):
    coords = remove_recurring(coords)

    if len(coords) < 3: return [], []
    import numpy as np
    import thirdparty.tripy

    v0, v1, v2 = [np.array(v) for v in coords[:3]]
    e1 = v0 - v1
    e2 = v2 - v1
    normal = np.cross(e1, e2)
    # print(normal)
    l = np.linalg.norm(normal)
    if l < 1e-6: return [], []
    normal = normal / l
    # coords.append(coords[0])

    t1 = e1 / np.linalg.norm(e1)
    t2 = np.cross(t1, normal)
    # print(t1, t2, np.dot(t1, t2))

    origin = v1

    xy_coords = []
    seg = []

    for i, c in enumerate(coords):
        seg.append([i, (i+1) % len(coords)])
        c1 = c - origin
        x = np.dot(c1, t1)
        y = np.dot(c1, t2)
        # print(c, (x,y))
        xy_coords.append([x, y])

    # some data just seems to be missing
    # bounding_box = False
    bounding_box = abs(normal[2]) < 0.1 and len(coords) <= 4

    if bounding_box:
        x0 = min([x for x, y in xy_coords])
        x1 = max([x for x, y in xy_coords])
        y0 = min([y for x, y in xy_coords])
        y1 = max([y for x, y in xy_coords])
        xy_coords = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        # could also use tripy but faster if we don't
        vertices_xy = xy_coords
        triangles = [[0, 1, 2], [2, 3, 0]]
    elif len(coords) == 3:
        vertices_xy = xy_coords
        triangles = [[0, 1, 2]]
    else:
        triangles = []
        vertices_xy = []
        vertices_map = {}
        for tri in thirdparty.tripy.earclip(xy_coords):
            index_tri = []
            for v_xy in tri:
                if v_xy not in vertices_map:
                    vertices_map[v_xy] = len(vertices_xy)
                    vertices_xy.append(v_xy)
                index_tri.append(vertices_map[v_xy])
            triangles.append(index_tri)

    vertices = []
    for x, y in vertices_xy:
        v = origin + x * t1 + y * t2
        vertices.append(v.tolist())

    return vertices, triangles

    #t = triangle.triangulate({ 'vertices': xy_coords, 'segments': seg })
    #vertices = []
    #for x, y in t['vertices'].tolist():
    #    v = origin + x * t1 + y * t2
    #    # print((x,y), v)
    #    vertices.append(v.tolist())
    #return vertices, t['triangles'].tolist()

    #vertices = coords
    #triangles = triangle.delaunay(xy_coords)
    #return vertices, triangles.tolist()

def cityglm_to_obj(s, origin_latitude, origin_longitude, origin_altitude, coordinateSystem='WGS84', target='bldg:outerBuildingInstallation'):
    import coordinates
    to_wgs = coordinates.conversions_wgs84(coordinateSystem)[0]
    to_enu = coordinates.wgs_to_enu_simple(*to_wgs(origin_latitude, origin_longitude))

    import xml.etree.ElementTree as ET
    root = ET.fromstring(s)
    # totally idiotic to have to list these here as they are found in XML file itself
    ns = {
        'wfs': "http://www.opengis.net/wfs",
        'gml': "http://www.opengis.net/gml",
        'ogc': "http://www.opengis.net/ogc",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'bldg': "http://www.opengis.net/citygml/building/2.0",
        'core': "http://www.opengis.net/citygml/2.0",
        'gen': "http://www.opengis.net/citygml/generics/2.0",
        'app': "http://www.opengis.net/citygml/appearance/2.0",
        'xlink': "http://www.w3.org/1999/xlink",
        'xAL': "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
    }

    vertex_rows = []
    line_rows = []

    for poly in root.findall('.//gml:Polygon', ns):
        if len(poly.findall('.//gml:innerBoundaryIs', ns)) > 0: continue
        for coords in poly.findall('.//gml:outerBoundaryIs//gml:coordinates', ns):
            xyz = []
            vertex_idx_offset = len(vertex_rows) + 1 # 1-based indices
            groups = coords.text.split()
            if len(groups[0].split(',')) < 3: continue
            for coord in groups:
                lng_orig, lat_orig, alt_orig = [float(x) for x in coord.split(',')]
                lat_wgs, lng_wgs, alt_wgs = to_wgs(lat_orig, lng_orig, alt_orig)
                x, y = to_enu(lat_wgs, lng_wgs)
                xyz.append([x, y, alt_wgs])

            vertices, triangles = linear_ring_to_triangles(xyz)
            #vertices = xyz
            #triangles = [list(range(len(xyz)))]
            for (x, y, z) in vertices:
                vertex_rows.append("v %f %f %f" % (x, y, z))

            for tri in triangles:
                idxs = [str(i + vertex_idx_offset) for i in tri]
                assert(len(idxs) == 3)
                line_rows.append('f ' + ' '.join(idxs))

    for r in vertex_rows:
        print(r)
    for r in line_rows:
        print(r)

@click.group()
def cli():
    pass

@cli.command(name = 'to_obj')
@click.argument('latitude', type=float)
@click.argument('longitude', type=float)
@click.option('--altitude', type=float, default=0)
@click.option('--coordinateSystem', default='WGS84')
def to_obj(latitude, longitude, altitude, coordinatesystem):
    cityglm_to_obj(sys.stdin.read(), latitude, longitude, altitude, coordinatesystem)

if __name__ == '__main__':
    cli()
