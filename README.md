# CityGML conversion tools (Espoo)

The main purpose of this repository is allowing conversions of this 3D model data
of the city of Espoo https://kartat.espoo.fi/3D/citymodel_en.html to a commonly
understood 3D format and coordinate system, using Open Source tools.

The first implementation converts to Wafefront OBJ format, which can be viewed
with, e.g., this online tool: https://3dviewer.net/.
The result is in ENU coordinates defined at the given origin.

The code includes some hacks (like `--auto-fix-walls`) that may not be required with
other CityGML datasets. Compatibility with other CityGML datasets is currently unknown.
On the other hand, other tools such as https://github.com/tudelft3d/CityGML2OBJs,
which did not work with the Espoo dataset, may work with those.

## Usage

 1. Optional but recommended: virtualenv
    * (once) Set up virtualenv: `python3 -m venv venv`
    * (every time): Activate: `venv/bin/activate`
 2. (once) Install: `pip install -r requirements.txt`

## Downloading

List available datasets

    python download.py --url=https://example.com/wfs.ashx GetCapabilities

Look at the `FeatureType/Name` fields in the result XML, something like `example_namespace:example_name`.

Download a particular dataset

    mkdir -p data
    python download.py --url=... GetFeature \
        "example_namespace:example_name" --maxFeatures=100 > data/dataset.xml

## Conversions

Example:

    python convert.py to_obj 6673665.767760608 25489120.986737024 \
      --auto-fix-walls \
      --coordinateSystem=EPSG:3879 < data/dataset.xml > data/dataset.obj

If the imported area is large (several kilometers in diameter), consider also
using `--accurate-enu`, which should correctly handle the curvature of the Earth
and other effects of similar magnitude, which are less accurately modeled in
the default mode, `--fast-enu`.
