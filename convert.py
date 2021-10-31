import click
import sys
import numpy as np

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

def auto_square_fix(coords, normal):
    edges = []
    for (idx, v) in enumerate(coords):
        prev_v = coords[((idx - 1) + len(coords)) % len(coords)]
        e = v - prev_v
        e = e - np.dot(e, normal) * normal
        edges.append(e)

    def find_best_edge(key):
        best = None
        best_val = 0
        for e in edges:
            val = key(e)
            if best is None or val > best_val:
                best = e
                best_val = val
        return best

    THRESHOLD_DEG = 3.0
    THRESHOLD_SIN = np.sin(THRESHOLD_DEG / 180.0 * np.pi)

    def vert_edge_score(e):
        l = np.linalg.norm(e)
        horiz = np.linalg.norm(e[:2])
        if horiz / l > THRESHOLD_SIN: return -1
        return l / (horiz + 1e-6)

    vertical_edge = find_best_edge(vert_edge_score)
    vertical_edge /= np.linalg.norm(vertical_edge)

    def horiz_edge_score(e):
        l = np.linalg.norm(e)
        if abs(np.dot(e, vertical_edge) / l) > THRESHOLD_SIN: return -1
        return l / (abs(e[2]) + 1e-6)

    horizontal_edge = find_best_edge(horiz_edge_score)
    horizontal_edge /= np.linalg.norm(horizontal_edge)

    #horizontal_edge = horizontal_edge - np.dot(horizontal_edge, vertical_edge) * vertical_edge
    #horizontal_edge /= np.linalg.norm(horizontal_edge)

    if max(np.linalg.norm(vertical_edge[:2]), abs(horizontal_edge[2])) > THRESHOLD_SIN:
        return None

    THRESHOLD_M = 1.0
    origin = coords[0]

    xy_coords = []
    for c in coords:
        c1 = c - origin
        x = np.dot(c1, horizontal_edge)
        y = np.dot(c1, vertical_edge)
        z = np.dot(c1, normal)
        if abs(z) > THRESHOLD_M: return None
        xy_coords.append((x, y))

    x0 = min([x for x, y in xy_coords])
    x1 = max([x for x, y in xy_coords])
    y0 = min([y for x, y in xy_coords])
    y1 = max([y for x, y in xy_coords])

    for x, y in xy_coords:
        diff_x = min(abs(x - x0), abs(x - x1))
        diff_y = min(abs(y - y0), abs(y - y1))
        diff = min(diff_x, diff_y)
        if diff > THRESHOLD_M: return None

    xy_coords = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]

    triangles = [[0, 1, 2], [2, 3, 0]]
    vertices = []
    for x, y in xy_coords:
        v = origin + x * horizontal_edge + y * vertical_edge
        vertices.append(v.tolist())

    return vertices, triangles

def linear_ring_to_triangles(coords):
    coords = remove_recurring(coords)

    if len(coords) < 3: return [], []

    coords = np.array(coords)

    origin = np.mean(coords, axis=0)
    C = np.dot((coords - origin).transpose(), coords - origin)
    u, s, vh = np.linalg.svd(C)
    t1 = u[:, 0]
    t2 = u[:, 1]
    normal = u[:, 2]

    # in th Espoo dataset, a large percentage of walls (and other surfaces)
    # seem to be missing vertices. A crude attempt to fix this by fixing all
    # things that look like a (part of) a rectangular wall to rectangles
    auto_fixed = auto_square_fix(coords, normal)
    if auto_fixed is not None:
        return auto_fixed

    # return [], [] # show only auto-fixed walls

    xy_coords = []
    seg = []

    for i, c in enumerate(coords):
        seg.append([i, (i+1) % len(coords)])
        c1 = c - origin
        x = np.dot(c1, t1)
        y = np.dot(c1, t2)
        # print(c, (x,y))
        xy_coords.append([x, y])

    if len(coords) == 3:
        vertices_xy = xy_coords
        triangles = [[0, 1, 2]]
    else:
        import thirdparty.tripy
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
    orig_vertices_map = {}
    for idx, c in enumerate(xy_coords):
        orig_vertices_map[tuple(c)] = idx

    for c in vertices_xy:
        c = tuple(c)
        if c in orig_vertices_map:
            # supports also non-planar surfaces and can help to avoid
            # adding numerical errors
            v = coords[orig_vertices_map[c]]
        else:
            # sys.stderr.write('synth vertex\n')
            x, y = c
            v = origin + x * t1 + y * t2
        vertices.append(v)

    return vertices, triangles

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
        # if len(poly.findall('.//gml:innerBoundaryIs', ns)) > 0: continue
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
