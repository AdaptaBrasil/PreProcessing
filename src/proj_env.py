"""Ignore PROJ/GDAL data paths left by a PostgreSQL/PostGIS install.

The PostGIS installer on Windows sets PROJ_LIB and GDAL_DATA system-wide,
pointing at its own (older) proj.db. rasterio, pyproj and pyogrio then load
that database instead of their bundled one and fail with errors such as
"The EPSG code is unknown ... DATABASE.LAYOUT.VERSION.MINOR = 2 whereas a
number >= 6 is expected".

Importing this module removes those variables from *this process only*
(PostGIS itself is unaffected). It must be imported before rasterio,
pyproj, geopandas or fiona. Variables pointing anywhere else are kept.
"""

import os

for _name in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    if "postgresql" in os.environ.get(_name, "").lower():
        del os.environ[_name]
