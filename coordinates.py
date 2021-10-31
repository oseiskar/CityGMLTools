import click

def conversions_wgs84(spec):
    if spec.lower() == 'wgs84':
        identity = lambda x, y, z: (x, y, z)
        return identity, identity

    from pyproj import CRS, Transformer
    crs = CRS.from_string(spec)

    def build_transform(trans):
        def transform(x, y, z = None):
            if z is None:
                z0 = 0
            else:
                z0 = z
            x1, y1, z1 = trans.transform(x, y, z0)
            if z is None:
                return (x1, y1)
            return (x1, y1, z1)

        return transform

    to_wgs = build_transform(Transformer.from_crs(crs, crs.geodetic_crs))
    from_wgs = build_transform(Transformer.from_crs(crs.geodetic_crs, crs))
    return to_wgs, from_wgs

def radius_to_bounding_box(latitude, longitude, radius_meters, coordinateSystem='WGS84'):
    import pymap3d

    to_wgs, from_wgs = conversions_wgs84(coordinateSystem)
    lat_wgs, lng_wgs = to_wgs(latitude, longitude)

    f = lambda x, y: pymap3d.enu2geodetic(x, y, 0, lat_wgs, lng_wgs, 0)
    lng0_wgs, lng1_wgs, lat0_wgs, lat1_wgs = [
        f(x * radius_meters, y * radius_meters)[idx]
        for (x, y, idx) in [
            [-1, 0, 1],
            [1, 0, 1],
            [0, -1, 0],
            [0, 1, 0]
        ]
    ]

    lat0, lng0 = from_wgs(lat0_wgs, lng0_wgs)
    lat1, lng1 = from_wgs(lat1_wgs, lng1_wgs)

    return (lng0, lat0, lng1, lat1)

def wgs_to_enu_simple(lat0, lng0):
    import math
    EARTH_CIRCUMFERENCE_EQUATORIAL = 40075.017e3
    EARTH_CIRCUMFERENCE_POLAR = 40007.863e3
    METERS_PER_LAT_DEG = EARTH_CIRCUMFERENCE_POLAR / 360.0
    m_per_lng_deg = math.cos(lat0 * math.pi / 180.0) * EARTH_CIRCUMFERENCE_EQUATORIAL / 360.0

    def wgs_to_enu(lat, lng):
        x = m_per_lng_deg * (lng - lng0)
        y = METERS_PER_LAT_DEG * (lat - lat0)
        return x, y

    return wgs_to_enu

@click.group()
@click.option('--coordinateSystem', default='WGS84')
@click.pass_context
def cli(ctx, coordinatesystem):
    ctx.ensure_object(dict)
    ctx.obj['transform'] = conversions_wgs84(coordinatesystem)

@cli.command(name = 'single')
@click.argument('from_or_to', type=click.Choice(['from_wgs', 'to_wgs'], case_sensitive=False))
@click.argument('latitude', type=float)
@click.argument('longitude', type=float)
@click.option('--altitude', type=float, default=None)
@click.pass_context
def single(ctx, from_or_to, latitude, longitude, altitude):
    to_wgs, from_wgs = ctx.obj['transform']
    func = { 'from_wgs': from_wgs, 'to_wgs': to_wgs }[from_or_to]
    print(func(latitude, longitude, altitude))

if __name__ == '__main__':
    cli(obj={})
