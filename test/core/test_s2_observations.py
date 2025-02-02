import os

try:
    import gdal
    import osr
except ImportError:
    from osgeo import gdal, osr

from multiply_core.util import Reprojection, FileRef
from multiply_core.observations import S2Observations, S2ObservationsCreator, extract_angles_from_metadata_file, \
    extract_tile_id
import urllib.request
import zipfile

test_data_save_path = '/tmp/test_data.zip'
if not os.path.exists(test_data_save_path):
    urllib.request.urlretrieve('https://github.com/QCDIS/multiply-core/raw/master/test/test_data.zip', test_data_save_path)
    with zipfile.ZipFile(test_data_save_path, 'r') as zip_ref:
        zip_ref.extractall('/tmp')
    zip_ref.close()
base_path = '/tmp/test_data/'


S2_BASE_FILE = base_path + 'S2A_MSIL1C_20170605T105031_N0205_R051_T30SWJ_20170605T105303-ac'
assert os.path.exists(S2_BASE_FILE)

S2_AWS_BASE_FILE = base_path + 'product_in_aws_format/'
assert os.path.exists(S2_AWS_BASE_FILE)
S2_METADATA_FILE = base_path + 'S2A_MSIL1C_20170605T105031_N0205_R051_T30SWJ_20170605T105303-ac/MTD_TL.xml'
assert os.path.exists(S2_METADATA_FILE)
S2_AWS_METADATA_FILE = base_path + 'product_in_aws_format/metadata.xml'
assert os.path.exists(S2_AWS_METADATA_FILE)
FAULTY_BASE_FILE = base_path + 'faulty_product/'
assert os.path.exists(FAULTY_BASE_FILE)
METADATA_FILE_WITH_FAULTY_TILE_ID = base_path + 'faulty_product/metadata.xml'
assert os.path.exists(METADATA_FILE_WITH_FAULTY_TILE_ID)
MISSING_TILE_ID_BASE_FILE = base_path + 'product_without_tile_id/'
assert os.path.exists(MISSING_TILE_ID_BASE_FILE)
METADATA_FILE_WITHOUT_TILE_ID = base_path + 'product_without_tile_id/metadata.xml'
assert os.path.exists(METADATA_FILE_WITHOUT_TILE_ID)
EMULATOR_FOLDER = base_path + 'emulator_folder/'
EPSG_32232_WKT = 'PROJCS["WGS 72 / UTM zone 32N",GEOGCS["WGS 72",DATUM["World Geodetic System 1972",' \
                 'SPHEROID["WGS 72",6378135.0,298.26,AUTHORITY["EPSG","7043"]],' \
                 'TOWGS84[0.0,0.0,4.5,0.0,0.0,0.554,0.219],AUTHORITY["EPSG","6322"]],PRIMEM["Greenwich",0.0,' \
                 'AUTHORITY["EPSG","8901"]],UNIT["degree",0.017453292519943295],AXIS["Geodetic longitude",' \
                 'EAST],AXIS["Geodetic latitude",NORTH],AUTHORITY["EPSG","4322"]],' \
                 'PROJECTION["Transverse_Mercator",AUTHORITY["EPSG","9807"]],PARAMETER["central_meridian",9.0],' \
                 'PARAMETER["latitude_of_origin",0.0],PARAMETER["scale_factor",0.9996],' \
                 'PARAMETER["false_easting",500000.0],PARAMETER["false_northing",0.0],UNIT["m",1.0],' \
                 'AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32232"]]'

__author__ = "Tonio Fincke (Brockmann Consult GmbH)"


def test_bands_per_observation():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    assert s2_observations.bands_per_observation == 10

    s2_observations = _get_observations(S2_BASE_FILE)
    assert s2_observations.bands_per_observation == 10


def test_aws_s2_get_band_data():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    s2_observation_data = s2_observations.get_band_data(3)
    _assert_aws_s2_observation_data(s2_observation_data)


def test_s2_get_band_data():
    s2_observations = _get_observations(S2_BASE_FILE)
    s2_observation_data = s2_observations.get_band_data(3)
    _assert_s2_observation_data(s2_observation_data)


def test_extract_angles_from_metadata_file():
    angles = extract_angles_from_metadata_file(S2_AWS_METADATA_FILE)
    assert 61.3750584241536 == angles[0]
    assert 160.875894634785 == angles[1]

    angles = extract_angles_from_metadata_file(S2_METADATA_FILE)
    assert 22.010357062494 == angles[0]
    assert 134.259951372444 == angles[1]


def test_extract_tile_id_from_metadata_file():
    tile_id = extract_tile_id(S2_AWS_METADATA_FILE)
    assert 'S2A_OPER_MSI_L1C_TL_SGS__20170112T163115_A008142_T29SQB_N02.04' == tile_id

    tile_id = extract_tile_id(S2_METADATA_FILE)
    assert 'S2A_OPER_MSI_L1C_TL_SGS__20170605T143900_A010201_T30SWJ_N02.05' == tile_id


def test_extract_tile_id_from_metadata_file_when_id_is_missing():
    tile_id = extract_tile_id(METADATA_FILE_WITHOUT_TILE_ID)
    assert tile_id is None


def test_can_read():
    file_ref = FileRef(url=FAULTY_BASE_FILE, start_time='2017-09-10', end_time='2017-09-10',
                       mime_type='unknown mime type')
    assert not S2ObservationsCreator.can_read([file_ref])
    file_ref = FileRef(url=MISSING_TILE_ID_BASE_FILE, start_time='2017-09-10', end_time='2017-09-10',
                       mime_type='unknown mime type')
    assert not S2ObservationsCreator.can_read([file_ref])
    file_ref = FileRef(url=S2_AWS_BASE_FILE, start_time='2017-09-10', end_time='2017-09-10',
                       mime_type='unknown mime type')
    assert S2ObservationsCreator.can_read([file_ref])
    file_ref = FileRef(url=S2_BASE_FILE, start_time='2017-06-05', end_time='2017-06-05',
                       mime_type='unknown mime type')
    assert S2ObservationsCreator.can_read([file_ref])


def test_s2_data_type():
    s2_observations = _get_observations(S2_BASE_FILE)
    assert 'S2_L2' == s2_observations.data_type


def test_aws_s2_data_type():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    assert 'AWS_S2_L2' == s2_observations.data_type


def test_s2_bands_per_observation():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    assert 10 == s2_observations.bands_per_observation

    s2_observations = _get_observations(S2_BASE_FILE)
    assert 10 == s2_observations.bands_per_observation


def test_aws_s2_get_band_data_by_name():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    s2_observation_data = s2_observations.get_band_data_by_name('B05_sur.tif')
    _assert_aws_s2_observation_data(s2_observation_data)


def test_s2_get_band_data_by_name():
    s2_observations = _get_observations(S2_AWS_BASE_FILE)
    s2_observation_data = s2_observations.get_band_data_by_name('B05_sur.tif')
    _assert_s2_observation_data(s2_observation_data)


def test_s2_get_band_data_by_name_full():
    s2_observations = _get_observations(S2_BASE_FILE)
    s2_observation_data = s2_observations.get_band_data_by_name('T30SWJ_20170605T105031_B05_sur.tif')
    _assert_s2_observation_data(s2_observation_data)


def _get_observations(url: str):
    destination_srs = osr.SpatialReference()
    destination_srs.ImportFromWkt(EPSG_32232_WKT)
    bounds_srs = osr.SpatialReference()
    bounds_srs.SetWellKnownGeogCS('EPSG:4326')
    bounds = [7.8, 53.5, 8.8, 53.8]
    reprojection = Reprojection(bounds=bounds, x_res=50, y_res=100, destination_srs=destination_srs,
                                bounds_srs=bounds_srs, resampling_mode=None)
    file_ref = FileRef(url=url, start_time='2017-09-10', end_time='2017-09-10',
                       mime_type='unknown mime type')
    return S2Observations([file_ref], reprojection, emulator_folder=EMULATOR_FOLDER)


def _assert_aws_s2_observation_data(s2_observation_data):
    assert (327, 1328) == s2_observation_data.observations.shape
    assert 4, len(s2_observation_data.metadata.keys())
    assert 'sza' in s2_observation_data.metadata.keys()
    assert 61.3750584241536, s2_observation_data.metadata['sza']
    assert 'saa' in s2_observation_data.metadata.keys()
    assert 160.875894634785, s2_observation_data.metadata['saa']
    assert 'vza' in s2_observation_data.metadata.keys()
    assert 2.776727292381147, s2_observation_data.metadata['vza']
    assert 'vaa' in s2_observation_data.metadata.keys()
    assert 177.40153095962427, s2_observation_data.metadata['vaa']
    assert (327, 1328) == s2_observation_data.mask.shape
    assert (434256, 434256) == s2_observation_data.uncertainty.shape


def _assert_s2_observation_data(s2_observation_data):
    assert (327, 1328) == s2_observation_data.observations.shape
    assert 4, len(s2_observation_data.metadata.keys())
    assert 'sza' in s2_observation_data.metadata.keys()
    assert 61.3750584241536, s2_observation_data.metadata['sza']
    assert 'saa' in s2_observation_data.metadata.keys()
    assert 160.875894634785, s2_observation_data.metadata['saa']
    assert 'vza' in s2_observation_data.metadata.keys()
    assert 2.776727292381147, s2_observation_data.metadata['vza']
    assert 'vaa' in s2_observation_data.metadata.keys()
    assert 177.40153095962427, s2_observation_data.metadata['vaa']
    assert (327, 1328) == s2_observation_data.mask.shape
    assert (434256, 434256) == s2_observation_data.uncertainty.shape
