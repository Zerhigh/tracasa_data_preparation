import pandas as pd
import rasterio
import geopandas as gpd
import pathlib
from pathlib import Path

import tqdm
from rasterio.windows import Window
import shapely


tracasa_base = Path('/data/USERS/shollend/tracasa_test')
tracasa_img = tracasa_base / "tracasa_S2_SR.tif"

#data_ = [gpd.read_file(tracasa_base / file) for file in tracasa_base.glob('*.gpkg')]
#data = pd.concat(data_, axis=0)
data = gpd.read_file(tracasa_base / 'test.gpkg')

with rasterio.open(tracasa_img, 'r') as src:
    intersected = []
    for i, row in tqdm.tqdm(data.iterrows()):
        geom = row['geometry']
        y, x = src.index(geom.centroid.x, geom.centroid.y)
        window = Window(x - 512 // 2, y - 512 // 2, 512, 512)

        # window = rasterio.windows.from_bounds(*geom.bounds, transform=src.transform)
        subimg = src.read(window=window)
        b, h, w = subimg.shape
        if h == 512 and w == 512:
            intersected.append(row)
            profile = src.profile.copy()
            trafo = rasterio.windows.transform(window, src.transform)
            profile.update({'height': h,
                            'width': w,
                            'transform': trafo})

            with rasterio.open(tracasa_base / 'images' / f'S2_{row["id"]}.tif', 'w', **profile) as dst:
                dst.write(subimg)

                tile_coords = [(0, 0), (0, 256), (256, 0), (256, 256)]

                for i, (top, left) in enumerate(tile_coords):
                    img_tile = subimg[:, top:top + 256, left:left + 256]
                    window_tile = Window(left, top, 256, 256)
                    trafo_tile = rasterio.windows.transform(window_tile, dst.transform)

                    profile_tile = profile.copy()
                    profile_tile.update({'height': 256,
                                        'width': 256,
                                        'transform': trafo_tile})

                    with rasterio.open(tracasa_base / 'split_images' / f'S2_{i}_{row["id"]}.tif', 'w', **profile_tile) as tile_dst:
                        tile_dst.write(img_tile)

    intersected_val = gpd.GeoDataFrame(intersected, crs=data.crs)
    intersected_val.to_file(tracasa_base / 'intersected_test.gpkg', driver='GPKG')