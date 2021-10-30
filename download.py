import click
import requests

@click.group()
@click.option('--url', required=True)
@click.pass_context
def cli(ctx, url):
    ctx.ensure_object(dict)
    ctx.obj['url'] = url

@cli.command(name = 'GetFeature')
@click.pass_context
@click.argument('typeName')
@click.option('--maxFeatures', type=int, default=1000)
def GetFeature(ctx, typename, maxfeatures):
    p = {
        'request': 'GetFeature',
        'TYPENAME': typename
    }
    if maxfeatures > 0:
        p['maxFeatures'] = maxfeatures
    r = requests.get(ctx.obj['url'], params=p)
    print(r.text)

@cli.command(name = 'GetCapabilities')
@click.pass_context
def GetCapabilities(ctx):
    r = requests.get(ctx.obj['url'], params={ 'request': 'GetCapabilities' })
    print(r.text)

if __name__ == '__main__':
    cli(obj={})
