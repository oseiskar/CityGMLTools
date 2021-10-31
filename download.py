import click
import requests

@click.group()
@click.option('--url', required=True)
@click.option('--verbose/--no-verbose', default=False)
@click.pass_context
def cli(ctx, url, verbose):
    ctx.ensure_object(dict)
    def get_url(params):
        if verbose:
            print(url, params)
        r = requests.get(url, params=params)
        return r
    ctx.obj['get'] = get_url

@cli.command(name = 'GetFeature')
@click.pass_context
@click.argument('typeName')
@click.option('--maxFeatures', type=int, default=1000)
@click.option('--latitude', type=float, default=None)
@click.option('--longitude', type=float, default=None)
@click.option('--radius', type=float, default=None)
@click.option('--coordinateSystem', default='WGS84')
def GetFeature(ctx, typename, maxfeatures, latitude, longitude, radius, coordinatesystem):
    p = {
        'request': 'GetFeature',
        'TYPENAME': typename,
        'OUTPUTFORMAT': 'GML2'
    }

    if radius is not None:
        import coordinates
        lng0, lat0, lng1, lat1 = coordinates.radius_to_bounding_box(latitude, longitude, radius, coordinatesystem)
        p['BBOX'] = ','.join([str(round(s)) for s in (lng0, lat0, lng1, lat1)])
        # if coordinatesystem != 'WGS84': p['BBOX'] += ',' + coordinatesystem

    if maxfeatures > 0:
        p['maxFeatures'] = maxfeatures
    r = ctx.obj['get'](p)
    print(r.text)

@cli.command(name = 'GetCapabilities')
@click.pass_context
def GetCapabilities(ctx):
    r = ctx.obj['get']({ 'request': 'GetCapabilities' })
    print(r.text)

if __name__ == '__main__':
    cli(obj={})
