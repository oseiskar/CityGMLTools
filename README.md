# Usage

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
      --coordinateSystem=EPSG:3879 < data/dataset.xml > data/dataset.obj
