from __future__ import print_function
import os
import numpy as np
import math

SRTM_DICT = {'SRTM1': 3601, 'SRTM3': 1201}

# Get the type of SRTM files
SRTM_TYPE = os.getenv('SRTM_TYPE', 'SRTM1')
SAMPLES = SRTM_DICT[SRTM_TYPE]

# put uncompressed hgt files in HGT_DIR, defaults to 'hgt'
HGTDIR = os.getenv('HGT_DIR', 'hgt')


def get_elevation(lat, lon):
    hgt_file = get_file_name(lat, lon)
    if hgt_file:
        return read_elevation_from_file(hgt_file, lat, lon)
    # Treat it as data void as in SRTM documentation
    # if file is absent
    return -32768
def bilinear_interpolation(x, y, points):
    '''Interpolate (x,y) from values associated with four points.

    The four points are a list of four triplets:  (x, y, value).
    The four points can be in any order.  They should form a rectangle.

         bilinear_interpolation(12, 5.5,
        ...                        [(10, 4, 100),
        ...                         (20, 4, 200),
        ...                         (10, 6, 150),
        ...                         (20, 6, 300)])
        165.0

    '''
    # See formula at:  http://en.wikipedia.org/wiki/Bilinear_interpolation

    points = sorted(points)               # order points by x, then by y
    (x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

    if x1 != _x1 or x2 != _x2 or y1 != _y1 or y2 != _y2:
        raise ValueError('points do not form a rectangle')
    if not x1 <= x <= x2 or not y1 <= y <= y2:
        raise ValueError('(x, y) not within the rectangle')

    return (q11 * (x2 - x) * (y2 - y) +
            q21 * (x - x1) * (y2 - y) +
            q12 * (x2 - x) * (y - y1) +
            q22 * (x - x1) * (y - y1)
           ) / ((x2 - x1) * (y2 - y1) + 0.0)
def read_elevation_from_file(hgt_file, lat, lon):
    with open(hgt_file, 'rb') as hgt_data:
        # HGT is 16bit signed integer(i2) - big endian(>)
        elevations = np.fromfile(
            hgt_data,  # binary data
            np.dtype('>i2'),  # data type
            SAMPLES * SAMPLES  # length
        ).reshape((SAMPLES, SAMPLES))

        lat_row =round((lat - int(lat)) * (SAMPLES - 1),4)
        lat_bottom = math.floor(lat_row)
        if lat_row == lat_bottom:
            lat_top = lat_row
        else:
            lat_top = math.ceil(lat_row)
        lon_row = -round((lon - int(lon)) * (SAMPLES - 1),4)
        lon_right = math.ceil(lon_row)
        if lon_right == lon_row:
            lon_left = lon_right
        else:
            lon_left = math.floor(lon_row)
            lat_bottom = SAMPLES - 1 - lat_bottom
        lat_top = SAMPLES - 1 - lat_top
        ind_lat = lat_row - int(lat_row)
        ind_lon = lon_row - int(lon_row)
        n = [(0, 0, elevations[int(lat_top),int(lon_left)]),(1, 0, elevations[int(lat_bottom),int(lon_left)]),(0, 1, elevations[int(lat_top),int(lon_right)]),(1, 1, elevations[int(lat_bottom),int(lon_right)]),]
        x = bilinear_interpolation(ind_lat, ind_lon, n)

        return x
def get_file_name(lat, lon):
    """
    Returns filename such as N27E086.hgt, concatenated
    with HGTDIR where these 'hgt' files are kept
    """
    if lat >= 0:
        ns = 'N'
    elif lat < 0:
        ns = 'S'

    if lon >= 0:
        ew = 'E'
    elif lon < 0:
        ew = 'W'

    hgt_file = "%(ns)s%(lat)02d%(ew)s%(lon)03d.hgt" % \
               {'lat': abs(lat), 'lon': abs(lon)+1, 'ns': ns, 'ew': ew} # N,W
    hgt_file_path = os.path.join(HGTDIR, hgt_file)
    if os.path.isfile(hgt_file_path):
        return hgt_file_path
    else:
        return None

if __name__ == '__main__':
    print('Elevation: %f' % get_elevation(43.524, -85.7523))

