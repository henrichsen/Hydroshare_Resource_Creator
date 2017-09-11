from datetime import datetime
import shutil
import requests
import sqlite3
import uuid
import random
import time
import xmltodict
import os
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
from django.conf import settings
from .app import HydroshareResourceCreator
import json
import logging

logger = logging.getLogger(__name__)
use_hs_client_helper = True
try:
    from tethys_services.backends.hs_restclient_helper import get_oauth_hs
except Exception as ex:
    use_hs_client_helper = False
    logger.error("tethys_services.backends.hs_restclient_helper import get_oauth_hs: " + ex.message)


def get_user_workspace(request):
    """
    Gets app workspace path.
    
    Arguments:      []
    Returns:        [workspace]
    Referenced By:  [error_report, create_ts_resource, controllers_ajax.chart_data, controllers_ajax.create_layer]
    References:     [app.HydroshareResourceCreator]
    Libraries:      []
    """

    workspace = HydroshareResourceCreator.get_user_workspace(request).path

    return workspace


def get_o_auth_hs(request):
    """
    Gets HydroShare Open Authorization.
    
    Arguments:      [request]
    Returns:        [hs]
    Referenced By:  [controllers_ajax.chart_data, controllers_ajax.create_layer]
    References:     []
    Libraries:      [HydroShareAuthOAuth2, HydroShare]
    """

    if use_hs_client_helper:
        hs = get_oauth_hs(request)
    else:
        hs_instance_name = "www"
        client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", None)
        client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", None)
        # this line will throw out from django.core.exceptions.ObjectDoesNotExist\
        # if current user is not signed in via HydroShare OAuth
        token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
        hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)
        auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
        hs = HydroShare(auth=auth, hostname=hs_hostname)

    return hs


def process_file_data(json_file):
    """
    Processes json_file data.
    
    Arguments:      [json_file]
    Returns:        [processed_file_data]
    Referenced By:  [controllers_ajax.chart_data]
    References:     []
    Libraries:      [json]
    """

    with open(json_file) as f:
        data = json.load(f)
        if type(data['timeSeriesReferenceFile']) != dict:
            data = json.loads(data["timeSeriesReferenceFile"])
            data = {"timeSeriesReferenceFile": data}

        for i in range(len(data['timeSeriesReferenceFile']['referencedTimeSeries'])):
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteName'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteName'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteCode'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteCode'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableName'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableName'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableCode'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableCode'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['networkName'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['networkName'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['refType'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['refType'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['serviceType'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['serviceType'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['returnType'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['returnType'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['latitude'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['latitude'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['longitude'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['longitude'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodDescription'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodDescription'] = 'N/A'
            if data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] == '':
                data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] = 'N/A'
        processed_file_data = data['timeSeriesReferenceFile']

        return processed_file_data


def create_ts_resource(res_data):
    """
    Parses Timeseries Layer.

    Arguments:      [file_path, title, abstract]
    Returns:        [counter]
    Referenced By:  [controllers_ajax.create_layer, create_ts_resource]
    References:     [get_user_workspace, load_into_odm2]
    Libraries:      [json, shutil, sqlite3]
    """

    refts_path = res_data['user_dir'] + '/timeseriesLayerResource.json'
    with open(refts_path, 'r') as refts_file:
        refts_data = ((refts_file.read()).encode(encoding='UTF-8')).replace("'", '"')
    series_count = 0
    json_data = json.loads(refts_data)
    json_data = json_data["timeSeriesReferenceFile"]
    layer = json_data['referencedTimeSeries']
    current_path = os.path.dirname(os.path.realpath(__file__))
    odm_master = os.path.join(current_path, "static_data/ODM2_master.sqlite")
    res_filepath = res_data['user_dir'] + '/' + res_data['res_filename'] + '.sqlite'
    shutil.copy(odm_master, res_filepath)
    parse_result = []
    for sub in layer:
        ref_type = sub['requestInfo']['refType']
        service_type = sub['requestInfo']['serviceType']
        url = sub['requestInfo']['url']
        site_code = sub['site']['siteCode']
        variable_code = sub['variable']['variableCode']
        start_date = sub['beginDate']
        end_date = sub['endDate']
        conn = sqlite3.connect(res_filepath, isolation_level=None)
        c = conn.cursor()
        data_set_info = (str(uuid.uuid1()),
                         'Multi-time series',
                         variable_code,
                         res_data['res_title'],
                         res_data['res_abstract']
                         )
        conn.commit()

        c.execute('INSERT INTO Datasets(DataSetID, DataSetUUID, DataSetTypeCV, DataSetCode, DataSetTitle, \
                  DataSetAbstract) '
                  'VALUES (NULL, ?, ?, ?, ?, ?)', data_set_info)
        if ref_type == 'WOF':
            if service_type == 'SOAP':
                odm_result = load_into_odm2(url, site_code, variable_code, start_date, end_date, res_filepath, series_count)
                parse_result.append(odm_result)
            series_count += 1

    return_obj = {
        'res_type': 'TimeSeriesResource',
        'res_filepath': res_filepath,
        'file_extension': '.sqlite',
        'series_count': series_count,
        'parse_result': parse_result
    }

    return return_obj


def update_resource():
    pass


def create_refts_resource(res_data):
    refts_path = res_data['user_dir'] + '/timeseriesLayerResource.json'
    with open(refts_path, 'r') as refts_file:
        refts_data = json.loads((refts_file.read()).encode(encoding='UTF-8'))['timeSeriesReferenceFile']
        data_symbol = refts_data['symbol']
        data_file = refts_data['fileVersion']
        data_stor = []
        for i, refts in enumerate(refts_data['referencedTimeSeries']):
            if i in res_data['selected_resources']:
                data_stor.append(refts)
        data_dic = {"referencedTimeSeries": data_stor, "fileVersion": data_file, "title": res_data['res_title'],
                    "symbol": data_symbol, "abstract": res_data['res_abstract'], 'keyWords': res_data['res_keywords']}
        refts_data.update(data_dic)
        final_dic = {"timeSeriesReferenceFile": refts_data}
        res_filepath = res_data['user_dir'] + '/' + res_data['res_filename'] + '.json.refts'
        with open(res_filepath, 'w') as res_file:
            json.dump(final_dic, res_file)

        return_obj = {'res_type': 'CompositeResource',
                      'res_filepath': res_filepath,
                      'file_extension': '.json.refts'}

        return return_obj


def load_into_odm2(url, site_code, variable_code, begin_date, end_date, odm_copy, series_number):
    """
    Loads data into ODM 2 Table.

    Arguments:      [url, site_code, variable_code, begin_date, end_date, odm_copy, series_number]
    Returns:        []
    Referenced By:  [create_ts_resource]
    References:     [connect_wsdl_url]
    Libraries:      [sqlite3, requests, xmltodict, uuid, datetime]
    """

    """ Sets up sqllite3 connect """
    sql_connect = sqlite3.connect(odm_copy, isolation_level=None)
    c = sql_connect.cursor()

    """ Sets temporary test values for the function """
    data_set_id = 1
    autho_token = ''

    """ Handles NASA data with requests  """
    if 'nasa' in url:
        headers = {'content-type': 'text/xml'}
        body = """<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" """ + \
               """xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                   <soap:Body>
                       <GetValuesObject xmlns="http://www.cuahsi.org/his/1.0/ws/">
                           <location>""" + site_code + """</location>
                        <variable>""" + variable_code + """</variable>
                        <startDate>""" + begin_date + """</startDate>
                        <endDate>""" + end_date + """</endDate>
                        <authToken>""" + autho_token + """"</authToken>
                    </GetValuesObject>
                </soap:Body>
            </soap:Envelope>"""
        response = requests.post(url, data=body, headers=headers)
        values_result = response.content
        values_result = xmltodict.parse(values_result)
        data_root = values_result["soap:Envelope"]["soap:Body"]["GetValuesObjectResponse"]["timeSeriesResponse"]
        data_type = "NASA"
    else:
        client = connect_wsdl_url(url)
        # The following line bottlenecks getting the results data.
        values_result = client.service.GetValuesObject(site_code, variable_code, begin_date, end_date, autho_token)
        with open("/home/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/tethysapp/hydroshare_resource_creator/static_data/refts_test_files/stroud_resource.wml", "w") as my_file:
            my_file.write(str(values_result))
        my_file.close()
        data_type = "OTHER"

    if data_type == "NASA" and len(data_root["timeSeries"]["values"]) == 0:
        return "No data values found."
    elif data_type != "NASA" and len(values_result.timeSeries[0].values[0]) == 0:
        return "No data values found."
    elif data_type == "NASA" and len(data_root["timeSeries"]["values"]["value"]) < 24:
        return "No sensor data found"
    elif data_type != "NASA" and len(values_result.timeSeries[0].values[0].value) < 24:
        return "No sensor data found"
    else:
        # ----------------------------------------------------------------
        # Get the SamplingFeatureInformation and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the sampling feature already exists in the database
        if data_type == "NASA":
            site_code_tup = (data_root["timeSeries"]["sourceInfo"]["siteCode"]["#text"],)
        else:
            site_code_tup = (values_result.timeSeries[0].sourceInfo.siteCode[0].value,)

        c.execute('SELECT * FROM SamplingFeatures WHERE SamplingFeatureCode = ?', site_code_tup)
        row = c.fetchone()
        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for SamplingFeature Information
            # SamplingFeatureID = Automatically generated by SQlite as autoincrement
            # SamplingFeatureUUID = Use python UUID to generate a UUID
            # SamplingFeatureTypeCV = 'Site'
            # SamplingFeatureCode = WaterML siteCode
            # SamplingFeatureName = WaterML siteName
            # SamplingFeatureDescription = NULL (doesn't exist in WaterML 1.1)
            # SamplingFeatureGeotypeCV = 'Point'
            # FeatureGeometry = Geometry representation of point using WaterML latitude and longitude
            # FeatureGeometryWKT = String Well Known Text representation of point using WaterML latitude and longitude
            # Elevation_m = WaterML elevation_m
            # ElevationDatumCV = WaterML verticalDatum
            try:
                if data_type == 'NASA':
                    elevation_m = data_root["timeSeries"]["sourceInfo"]["elevation_m"]["#text"]
                else:
                    elevation_m = values_result.timeSeries[0].sourceInfo.elevation_m
            except:
                elevation_m = None
            try:
                if data_type == 'NASA':
                    vertical_datum = data_root["timeSeries"]["sourceInfo"]["verticalDatum"]["#text"]
                else:
                    vertical_datum = values_result.timeSeries[0].sourceInfo.verticalDatum
            except:
                vertical_datum = None

            if data_type == 'NASA':
                r_site_code = data_root["timeSeries"]["sourceInfo"]["siteCode"]["#text"]
                r_site_name = data_root["timeSeries"]["sourceInfo"]["siteName"]
                r_lon = data_root["timeSeries"]["sourceInfo"]["geoLocation"]["geogLocation"]["longitude"]
                r_lat = data_root["timeSeries"]["sourceInfo"]["geoLocation"]["geogLocation"]["latitude"]
            else:
                r_site_code = values_result.timeSeries[0].sourceInfo.siteCode[0].value
                r_site_name = values_result.timeSeries[0].sourceInfo.siteName
                r_lon = values_result.timeSeries[0].sourceInfo.geoLocation.geogLocation.longitude
                r_lat = values_result.timeSeries[0].sourceInfo.geoLocation.geogLocation.latitude

            sampling_feature_info = (str(uuid.uuid1()),
                                     'Site',
                                     r_site_code,
                                     r_site_name,
                                     'Point',
                                     'POINT (' + str(r_lon) + ' ' + str(r_lat) + ')',
                                     elevation_m,
                                     vertical_datum)

            c.execute('INSERT INTO SamplingFeatures (SamplingFeatureID, SamplingFeatureUUID, '
                      'SamplingFeatureTypeCV, SamplingFeatureCode, SamplingFeatureName, SamplingFeatureDescription,'
                      'SamplingFeatureGeotypeCV, FeatureGeometry, FeatureGeometryWKT,'
                      'Elevation_m, ElevationDatumCV) VALUES (NULL,?,?,?,?,NULL,?,NULL,?,?,?)', sampling_feature_info)

            # Get the ID of the SamplingFeature I just created
            sampling_feature_id = c.lastrowid

            # ----------------------------------------------------------------
            # Get the Site information and load it into the database
            # ----------------------------------------------------------------
            # The WaterML 1.1 response doesn't have the spatial reference for the latitude and longitude
            # Insert a record into SpatialReferences to indicate that it is unknown
            spatial_reference_info = ('Unknown', 'The spatial reference is unknown')

            c.execute('INSERT INTO SpatialReferences(SpatialReferenceID, SRSCode, SRSName, SRSDescription, SRSLink) '
                      'VALUES (NULL, NULL, ?, ?, NULL)', spatial_reference_info)

            # Get the ID of the SpatialReference I just created
            spatial_reference_id = c.lastrowid

            # WaterML 1.1 ----> ODM2 Mapping for Site Information
            # SamplingFeatureID = SamplingFeatureID of the record just loaded into the SamplingFeatures table
            # SiteTypeCV = Set to the WaterML SiteType property value for the site
            # Latitude = WaterML latitude
            # Longitude = WaterML longitude
            # SpatialReferenceID = SpatialReferenceID of the record just loaded into the SpatialReferences table
            try:
                if data_type == 'NASA':
                    sitetypecv = data_root["timeSeries"]["sourceInfo"]["siteProperty"]["#text"]
                else:
                    sitetypecv = values_result.timeSeries[0].sourceInfo.siteProperty[4].value
            except:
                sitetypecv = 'unknown'
            site_info = (sampling_feature_id,
                         sitetypecv,
                         r_lat,
                         r_lon,
                         spatial_reference_id)

            c.execute('INSERT INTO Sites(SamplingFeatureID, SiteTypeCV, Latitude, Longitude, SpatialReferenceID) '
                      'VALUES (?, ?, ?, ?, ?)', site_info)
        else:  # The sampling feature and the site already exist in the database
            sampling_feature_id = row[0]

        # ----------------------------------------------------------------
        # Get the Method information and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the method already exists
        # methodDescription = (valuesResult.timeSeries[0].values[0].method[0].methodDescription,)
        # print valuesResult.timeSeries[0].values[0]
        # methodDescription = ('hi',)
        try:
            if data_type == 'NASA':
                method_description = data_root["timeSeries"]["method"]["MethodDescription"]
            else:
                method_description = values_result.timeSeries[0].values[0].method[0].methodDescription
        except:
            method_description = 'unknown'
        try:
            if data_type == 'NASA':
                method_code = data_root["timeSeries"]["method"]["methodCode"]
            else:
                method_code = values_result.timeSeries[0].values[0].method[0].methodCode
        except:
            method_code = series_number
        try:
            if data_type == 'NASA':
                method_link = data_root["timeSeries"]["method"]["methodLink"]
            else:
                method_link = values_result.timeSeries[0].values[0].method[0].methodLink
        except:
            method_link = 'unknown'
        r_method_description = (method_description,)
        c.execute('SELECT * FROM Methods WHERE MethodName = ?', r_method_description)
        row = c.fetchone()

        if row is None:
            # NOTE:  Some hard coded stuff here - MethodCode, MethodTypeCV, and MethodDescription don't exist in
            #        WaterML
            # WaterML 1.1 ----> ODM2 Mapping for Method Information
            # MethodID = Automatically generated by SQLite as autoincrement
            # MethodTypeCV = HARD CODED FOR NOW (Could use generic MethodTypeCV of 'Observation')
            # MethodCode = WaterML methodCode
            # MethodName = Doesn't exist in WaterML, but required. Set this to the WaterML methodDescription
            # MethodDescription = WaterML MethodDescription
            # MethodLink = WaterML methodLink - but not all time series have a MethodLink, so need to fix this
            # OrganizationID = NULL (doesn't exist in WaterML)
            method_info = ('Observation',
                           method_code,
                           method_description,
                           method_description,
                           method_link)

            c.execute('INSERT INTO Methods(MethodID, MethodTypeCV, MethodCode, MethodName, MethodDescription, \
                      MethodLink) VALUES (NULL, ?, ?, ?, ?, ?)', method_info)

            # Get the ID of the Method I just inserted
            method_id = c.lastrowid

        else:  # The method already exists in the database
            method_id = row[0]
        # ----------------------------------------------------------------
        # Get the Variable information and load it into the database
        # ----------------------------------------------------------------
        if data_type == 'NASA':
            variable_code_tup = (data_root["timeSeries"]["variable"]["variableCode"]["#text"],)
        else:
            variable_code_tup = (values_result.timeSeries[0].variable.variableCode[0].value,)
        c.execute('SELECT * FROM Variables WHERE VariableCode = ?', variable_code_tup)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # VariableID = Automatically generated by SQLite as autoincrement
            # VariableTypeCV = WaterML generalCategory
            # VariableCode = WaterML variableCode
            # VariableNameCV = WaterML variableName
            # VariableDefinition = Set to NULL because it doesn't exist in WaterML and is not required
            # SpeciationCV = WaterML speciation
            # NoDataValue = WaterML noDataValue
            try:
                if data_type == 'NASA':
                    general_category = data_root["timeSeries"]["variable"]["generalCategory"]
                else:
                    general_category = values_result.timeSeries[0].variable.generalCategory
            except:
                general_category = "Variable"
            try:
                if data_type == 'NASA':
                    speciation = data_root["timeSeries"]["variable"]["speciation"]
                else:
                    speciation = values_result.timeSeries[0].variable.speciation
            except:
                speciation = None

            if data_type == 'NASA':
                variable_code = data_root["timeSeries"]["variable"]["variableCode"]["#text"]
            else:
                variable_code = values_result.timeSeries[0].variable.variableCode[0].value
            variable_code = variable_code[:20]  # HydroShare limits the length of variable code field
            if data_type == 'NASA':
                r_variable_name = data_root["timeSeries"]["variable"]["variableName"]
                r_no_data_value = data_root["timeSeries"]["variable"]["NoDataValue"]
            else:
                r_variable_name = values_result.timeSeries[0].variable.variableName
                r_no_data_value = values_result.timeSeries[0].variable.noDataValue
            variable_info = (general_category,
                             variable_code,
                             r_variable_name,
                             speciation,
                             r_no_data_value)

            c.execute('INSERT INTO Variables\
                      (VariableID, VariableTypeCV, VariableCode, VariableNameCV, VariableDefinition, SpeciationCV, \
                      NoDataValue) '
                      'VALUES (NULL, ?, ?, ?, NULL, ?, ?)', variable_info)

            # Get the ID of the Variable I just inserted
            variable_id = c.lastrowid

        else:  # The variable already exists
            variable_id = row[0]

        # ----------------------------------------------------------------
        # Get the Units information and load it into the database
        # ----------------------------------------------------------------
        if data_type == 'NASA':
            units_name = (data_root["timeSeries"]["variable"]["timeSupport"]["unit"]["UnitName"],)
        else:
            units_name = (values_result.timeSeries[0].variable.unit.unitName,)
        c.execute('SELECT * FROM Units WHERE UnitsName = ?', units_name)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # UnitsID = WaterML unitCode (this keeps it consistent with the ODM 1.1.1/WaterML 1.1 UnitIDs)
            # UnitsTypeCV = WaterML unitType
            # UnitsAbbreviation = WaterML unitAbbreviation
            # unitsName = WaterML unitName
            # unitsLink = NULL (doesn't exist in WaterML)
            try:
                if data_type == 'NASA':
                    unit_code = data_root["timeSeries"]["variable"]["timeSupport"]["unit"]["UnitCode"]
                else:
                    unit_code = values_result.timeSeries[0].variable.unit.unitCode
            except:
                unit_code = '1'
            try:
                if data_type == 'NASA':
                    unit_type = data_root["timeSeries"]["variable"]["timeSupport"]["unit"]['UnitType']
                else:
                    unit_type = values_result.timeSeries[0].variable.unit.unitType
            except:
                unit_type = 'unknown'
            try:
                if data_type == 'NASA':
                    unit_abbreviation = data_root["timeSeries"]["variable"]["timeSupport"]["unit"]["UnitAbbreviation"]
                else:
                    unit_abbreviation = values_result.timeSeries[0].variable.unit.unitAbbreviation
            except:
                unit_abbreviation = 'unknown'
            try:
                if data_type == 'NASA':
                    unit_name = data_root["timeSeries"]["variable"]["timeSupport"]["unit"]["UnitName"]
                else:
                    unit_name = values_result.timeSeries[0].variable.unit.unitName
            except:
                unit_name = 'unknown'
            units_info = (unit_code,
                          unit_type,
                          unit_abbreviation,
                          unit_name)

            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName, UnitsLink) '
                      'VALUES (?, ?, ?, ?, NULL)', units_info)

            # Get the ID of the Units I just inserted
            units_id = c.lastrowid

        else:  # The unit already exists in the database
            units_id = row[0]
        # -----------------------------------------------------------------
        # Get the ProcessingLevel information and load it into the database
        # -----------------------------------------------------------------
        if data_type == 'NASA':
            quality_control_level_id = (1,)
        else:
            quality_control_level_id = \
                (values_result.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID,)
        c.execute('SELECT * FROM ProcessingLevels WHERE ProcessingLevelID = ?', quality_control_level_id)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for ProcessingLevel Information
            # ProcessingLevelID = WaterML _qualityControlLevelID
            # ProcessingLevelCode = WaterML qualityControlLevelCode
            # Definition = WaterML definition
            # Explanation = WaterML explanation
            if data_type == 'NASA':
                qa_id = 1
                qa_code = 1
            else:
                qa_id = values_result.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID
                qa_code = values_result.timeSeries[0].values[0].qualityControlLevel[0].qualityControlLevelCode
            # HydroShare expects qa code to be a integer
            try:
                qa_code = int(qa_code)
            except:
                qa_code = qa_id
            try:
                if data_type == 'NASA':
                    r_qa_definition = data_root["timeSeries"]["qualityControlLevel"]["definition"]
                else:
                    r_qa_definition = values_result.timeSeries[0].values[0].qualityControlLevel[0].definition
            except:
                r_qa_definition = "None"
            try:
                if data_type == 'NASA':
                    r_qa_explanation = data_root["timeSeries"]["qualityControlLevel"]["explanation"]
                else:
                    r_qa_explanation = values_result.timeSeries[0].values[0].qualityControlLevel[0].explanation
            except:
                r_qa_explanation = "None"
            processing_level_info = (qa_id,
                                     qa_code,
                                     r_qa_definition,
                                     r_qa_explanation)

            c.execute('INSERT INTO ProcessingLevels(ProcessingLevelID, ProcessingLevelCode, Definition, Explanation) '
                      'VALUES (?, ?, ?, ?)', processing_level_info)

            # Get the ID of the ProcessingLevel I just inserted
            processing_level_id = c.lastrowid

        else:  # The ProcessingLevel already exists in the database
            processing_level_id = row[0]
        # Get the People information and load it
        # -----------------------------------------------------------------
        try:
            if data_type == 'NASA':
                contact_name = data_root["timeSeries"]["source"]["ContactInformation"]["ContactName"]
            else:
                contact_name = values_result.timeSeries[0].values[0].source[0].contactInformation[0].contactName
        except:
            contact_name = 'unknown unknown'
        split_name = contact_name.split(' ')
        person_info = (split_name[0], split_name[-1])
        c.execute('SELECT * FROM People WHERE PersonFirstName = ? AND PersonLastName=?', person_info)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for People Information
            # PersonID = Automatically generated by SQlite as autoincrement
            # PersonFirstName = First element of WaterML contactName split by space delimiter
            # PersonMiddleName = NULL (this could be problematic if a WaterML person actually has a middle name)
            # PersonLastName = Last element of WaterML contactName split by space delimiter

            c.execute('INSERT INTO People(PersonID, PersonFirstName, PersonLastName) '
                      'VALUES (NULL, ?, ?)', person_info)

            # Get the ID of the person I just inserted
            person_id = c.lastrowid

        else:  # The person already exists
            person_id = row[0]

        # Get the Organization information and load it
        # -----------------------------------------------------------------
        if data_type == 'NASA':
            organization_name = (data_root["timeSeries"]["source"]["Organization"],)
        else:
            organization_name = (values_result.timeSeries[0].values[0].source[0].organization,)
        c.execute('SELECT * FROM Organizations WHERE OrganizationName = ?', organization_name)
        row = c.fetchone()
        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Organization Information
            # OrganizationID = Automatically generated by SQlite as autoincrement
            # OrganizationTypeCV = 'Unknown' (doesn't exist in WaterML, but required by ODM2)
            # OrganizationCode = WaterML sourceCode --> WaterML may not provide a unique code, which ODM2 requires.
            # OrganizationName = WaterML organization
            # OrganizationDescription = WaterML sourceDescription
            # OrganizationLink = waterML sourceLink
            # ParentOrganizationID = NULL (doesn't exist in WaterML)
            try:
                if data_type == 'NASA':
                    r_organization = data_root["timeSeries"]["source"]["Organization"]
                else:
                    r_organization = values_result.timeSeries[0].values[0].source[0].organization
            except:
                r_organization = "None"
            try:
                if data_type == 'NASA':
                    r_source_description = data_root["timeSeries"]["source"]["SourceDescription"]
                else:
                    r_source_description = values_result.timeSeries[0].values[0].source[0].sourceDescription
            except:
                r_source_description = "None"
            try:
                if data_type == 'NASA':
                    r_source_link = data_root["timeSeries"]["source"]["SourceLink"]
                else:
                    r_source_link = values_result.timeSeries[0].values[0].source[0].sourceLink[0]
            except:
                r_source_link = "None"

            organization_info = ('unknown',
                                 # values_result.timeSeries[0].values[0].source[0].sourceCode,
                                 random.randint(1, 99),  # TODO Temporary value, should be unique source code.
                                 r_organization,
                                 r_source_description,
                                 r_source_link)
            c.execute('INSERT INTO Organizations\
                      (OrganizationID, OrganizationTypeCV, OrganizationCode, OrganizationName, OrganizationDescription,\
                       OrganizationLink) '
                      'VALUES (NULL, ?, ?, ?, ?, ?)', organization_info)

            # Get the ID of the Organization I just inserted
            organization_id = c.lastrowid

        else:  # The organization already exists
            organization_id = row[0]
        # Create the Affiliation between the person and the organization
        # -----------------------------------------------------------------
        c.execute('SELECT * FROM Affiliations WHERE PersonID = ? AND OrganizationID = ?', (person_id, organization_id))
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Affiliation Information
            # AffiliationID = Automatically generated by SQlite as autoincrement
            # PersonID = ID of the person created above
            # OrganizationID = ID of the organization created above
            # IsPrimaryOrganizationContact = 1 for 'True' (hard coded for now, doesn't really exist in WaterML)
            # AffilationStartDate = set to the current system date (this is required, but doesn't exit in WaterML)
            # AffiliationEndDate = NULL (this doesn't exist in WaterML but is not required)
            # PrimaryPhone = WaterML phone of source contact
            # PrimaryEmail = WaterML email of source contact
            # PrimaryAddress = NULL (doesn't exist in WaterML)
            # PersonLink = NULL (doesn't exist in WaterML)
            try:
                if data_type == 'NASA':
                    phone = data_root["timeSeries"]["source"]["ContactInformation"]["Phone"]
                else:
                    phone = values_result.timeSeries[0].values[0].source[0].contactInformation[0].phone[0]
            except:
                phone = "unknown"
            try:
                if data_type == 'NASA':
                    email = data_root["timeSeries"]["source"]["ContactInformation"]["Email"]
                else:
                    email = values_result.timeSeries[0].values[0].source[0].contactInformation[0].email[0]
            except:
                email = "unknown"
            affiliation_info = (person_id,
                                organization_id,
                                1,
                                datetime.now(),
                                phone,
                                email,)

            c.execute('INSERT INTO Affiliations(AffiliationID, PersonID, OrganizationID, IsPrimaryOrganizationContact, \
                      AffiliationStartDate, PrimaryPhone, PrimaryEmail) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?)', affiliation_info)

            # Get the ID of the Affiliation I just inserted
            affiliation_id = c.lastrowid

        else:  # The affilation already exists
            affiliation_id = row[0]
        # Get the Action information and load it
        # -----------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for Action Information
        # ActionID = Automatically generated by SQlite as autoincrement
        # ActionTypeCV = 'Observation' (used the generic term because this doesn't exist in WaterML)
        # MethodID = ID of the Method created above
        # BeginDateTime = WaterML _dateTime of the first data value
        # BeginDateTimeUTCOffset = split hour off of WaterML _timeOffset of the first data value
        # EndDateTime = WaterML _dateTime of the last data value
        # EndDateTimeUTCOffset = split hour off of WaterML _timeOffset of the last data value
        # ActionDescription = 'An observation action that generated a time series result.' \
        # (HARD CODED FOR NOW - doesn't exist in WaterML)
        # ActionFileLink = NULL (doesn't exist in WaterML)
        if data_type == 'NASA':
            r_begin_date_time = data_root["timeSeries"]["values"]["value"][0]["@dateTime"]
            r_begin_time_offset = 0
            r_end_date_time = data_root["timeSeries"]["values"]["value"][-1]["@dateTime"]
            r_end_time_offset = 0
        else:
            r_begin_date_time = values_result.timeSeries[0].values[0].value[0]._dateTime
            r_begin_time_offset = int(values_result.timeSeries[0].values[0].value[0]._timeOffset.split(':')[0])
            r_end_date_time = values_result.timeSeries[0].values[0].value[-1]._dateTime
            r_end_time_offset = int(values_result.timeSeries[0].values[0].value[-1]._timeOffset.split(':')[0])
        action_info = ('Observation',
                       method_id,
                       r_begin_date_time,
                       r_begin_time_offset,
                       r_end_date_time,
                       r_end_time_offset,
                       'An observation action that generated a time series result.')

        c.execute('INSERT INTO Actions(ActionID, ActionTypeCV, MethodID, BeginDateTime, BeginDateTimeUTCOffset, \
                  EndDateTime, EndDateTimeUTCOffset, ActionDescription) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)', action_info)

        # Get the ID of the Action I just created.
        action_id = c.lastrowid

        # Create the ActionBy information and load it into the database
        # -----------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for ActionBy Information
        # BridgeID = Automatically generated by SQlite as autoincrement
        # ActionID = ID of the Action created above
        # AffiliationID = ID of the Affiliation created above
        # IsActionLead = 1 for 'True' (doesn't exist in WaterML, so hard coded)
        # RoleDescription = 'Responsible party' (doesn't exist in WaterML, so hard coded)
        action_by_info = (action_id, affiliation_id, 1, 'Responsible party')

        c.execute('INSERT INTO ActionBy(BridgeID, ActionID, AffiliationID, IsActionLead, RoleDescription) '
                  'VALUES (NULL, ?, ?, ?, ?)', action_by_info)

        # Create the FeatureAction information and load it into the database
        # ------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for FeatureAction Information
        # FeatureActionID = Automatically generated by SQlite as autoincrement
        # SamplingFeatureID = ID of the SamplingFeature created above
        # ActionID = ID of the Action created above
        feature_action_info = (sampling_feature_id, action_id)

        c.execute('INSERT INTO FeatureActions(FeatureActionID, SamplingFeatureID, ActionID) '
                  'VALUES (NULL, ?, ?)', feature_action_info)

        # Get the FeatureActionID for the record I just created
        feature_action_id = c.lastrowid
        # Create the Result information an load it into the database
        # ------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for Result Information
        # ResultID = Automatically generated by SQlite as autoincrement
        # ResultUUID = Use python UUID to generate a UUID
        # FeatureActionID = ID of the FeatureAction created above
        # ResultTypeCV = 'Time series coverage' (doesn't exist in WaterML, so hard coded)
        # VariableID = ID of Variable created above
        # UnitsID = ID of Units created above
        # TaxonomicClassifierID = NULL (not needed)
        # ProcessingLevelID = ID of ProcessingLevel created above
        # ResultDateTime = current system time (basically the date the data was added to the database)
        # ResultDateTimeUTCOffset = UTCOffset of current system time
        # ValidDateTime = NULL (doesn't exist in WaterML and unknown)
        # ValidDateTImeUTCOffset = NULL (doesn't exist in WaterML and unknown)
        # StatusCV = 'Unknown' (doesn't exist in WaterML - could also be NULL)
        # SampledMediumCV = WaterML sampleMedium
        # ValueCount = python len function length of the WaterML values list
        if data_type == 'NASA':
            r_sample_medium = data_root["timeSeries"]["variable"]["sampleMedium"]
            r_values_length = len(data_root["timeSeries"]["values"])
        else:
            r_sample_medium = values_result.timeSeries[0].variable.sampleMedium
            r_values_length = len(values_result.timeSeries[0].values[0].value)
        result_info = (str(uuid.uuid1()),
                       feature_action_id,
                       'Time series coverage',
                       variable_id,
                       units_id,
                       processing_level_id,
                       datetime.now(),
                       -time.timezone / 3600,
                       'unknown',
                       r_sample_medium,
                       r_values_length)

        c.execute('INSERT INTO Results(ResultID, ResultUUID, FeatureActionID, ResultTypeCV, VariableID, UnitsID, \
                  ProcessingLevelID, ResultDateTime, ResultDateTimeUTCOffset, StatusCV, SampledMediumCV, ValueCount) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', result_info)

        # Get the ID for the Result I just created
        result_id = c.lastrowid

        # Load the Units information for the IntendedTimeSpacing into the database
        # ------------------------------------------------------------------------
        # NOTE: The intended time spacing information isn't in WaterML
        #       This is hard coded and could be problematic for some datasets.
        try:
            units_info = (102, 'unknown', 'unknown')
            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName) '
                      'VALUES (NULL, ?, ?, ?)', units_info)
            # Get the ID of the Units I just inserted
            time_units_id = c.lastrowid
        except:
            time_units_id = 102
            pass

        # Get the TimeSeriesResult information and load it into the database
        # ------------------------------------------------------------------
        # NOTE:  The intended time spacing information isn't in WaterML
        # NOTE:  My test dataset didn't have an Offset, so may need to handle that better here
        # WaterML 1.1 ----> ODM2 Mapping for TimeSeriesResult Information
        # XLocation = NULL
        # XLocationUnitsID = NULL
        # YLocation = NULL
        # YLocationUnitsID = NULL
        # ZLocation = NULL
        # ZLocationUnitsID = NULL
        # SpatialReferenceID = NULL
        # IntendedTimeSpacing = 30 (Hard Coded.  I know this for the test dataset,\
        #  but would have to be null for generic WaterML files because it doesn't exist in WaterML)
        # IntendedTimeSpadingUnitsID = ID of TimeUnits created above (essentially hard coded -\
        #  I know this for the test dataset, but would have to be null for generic WaterML files\
        #  because it doesn't exist in WaterML)
        # AggregationStatisticCV = WaterML dataType
        if data_type == 'NASA':
            r_data_type = data_root["timeSeries"]["variable"]["dataType"]
        else:
            r_data_type = values_result.timeSeries[0].variable.dataType
        time_series_result_info = (result_id,
                                   30,
                                   time_units_id,
                                   r_data_type)

        c.execute('INSERT INTO TimeSeriesResults(ResultID, IntendedTimeSpacing, IntendedTimeSpacingUnitsID, \
                  AggregationStatisticCV) '
                  'VALUES (?, ?, ?, ?)', time_series_result_info)
        # Get the TimeSeriesResultValues information and load it into the database
        # ------------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for TimeSeriesResultValues Information
        # ValueID = Automatically generated by SQLite as autoincrement
        # ResultID = ID of the Result created above
        # DataValue = WaterML value
        # ValueDateTime = WaterML _dateTime
        # ValueDateTimeUTCOffset = split the hour off of the WaterML _timeOffset
        # CensorCodeCV = WaterML _censorCode
        # QualityCodeCV = 'Unknown' (doesn't exist in WaterML, but required)
        # TimeAggregationInterval = WaterML timeSupport
        # TimeAggregationIntervalUnitsID = WaterML timeScale.unit.unitCode
        ts_result_values = []
        if data_type == 'NASA':
            num_values = len(data_root["timeSeries"]["values"]["value"])
        else:
            num_values = len(values_result.timeSeries[0].values[0].value)
        print num_values
        for z in range(0, num_values - 1):
            try:
                if data_type == 'NASA':
                    censor_code = data_root["timeSeries"]["values"]["value"][z]["@censorCode"]
                else:
                    censor_code = values_result.timeSeries[0].values[0].value[z].censorCode
            except:
                censor_code = 'unknown'
            try:
                if data_type == 'NASA':
                    time_support = data_root["timeSeries"]["variable"]["timeScale"]
                else:
                    time_support = values_result.timeSeries[0].variable.timeScale.timeSupport
            except:
                time_support = 'unknown'
            try:
                if data_type == 'NASA':
                    unit_code = data_root["timeSeries"]["variable"]["timeSupport"]["unit"]["unitCode"]
                else:
                    unit_code = values_result.timeSeries[0].variable.timeScale.unit.unitCode
            except:
                unit_code = 'unknown'

            if data_type == 'NASA':
                r_value = data_root["timeSeries"]["values"]["value"][z]["#text"]
                r_date_time = data_root["timeSeries"]["values"]["value"][z]["@dateTime"]
                r_time_offset = 0
            else:
                r_value = values_result.timeSeries[0].values[0].value[z].value
                r_date_time = values_result.timeSeries[0].values[0].value[z]._dateTime
                r_time_offset = int(values_result.timeSeries[0].values[0].value[z]._timeOffset.split(':')[0])

            ts_result_values.append((result_id,
                                     r_value,
                                     r_date_time,
                                     r_time_offset,
                                     censor_code,
                                     'Unknown',
                                     time_support,
                                     unit_code))
        print len(ts_result_values)
        c.execute("BEGIN TRANSACTION;")
        c.executemany('INSERT INTO TimeSeriesResultValues(ValueID, ResultID, DataValue, ValueDateTime, \
                      ValueDateTimeUTCOffset, CensorCodeCV, QualityCodeCV, TimeAggregationInterval, \
                      TimeAggregationIntervalUnitsID) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)', ts_result_values)

        # Now create the DataSets Results bridge record
        data_sets_results_info = (data_set_id, result_id)
        c.execute('INSERT INTO DataSetsResults(BridgeID, DataSetID, ResultID) Values (NULL, ?, ?)',
                  data_sets_results_info)
        # Save (commit) the changes
        c.execute("COMMIT;")
        sql_connect.commit()
        # seriesCounter += 1
    # Close the connection to the database
    # ------------------------------------
    sql_connect.close()
    return "Data Loaded"

    # DO NOT DELETE
    '''
    """
    Loads data into ODM 2 Table.
    
    Arguments:      [url, site_code, variable_code, begin_date, end_date, odm_copy, series_number]
    Returns:        []
    Referenced By:  [create_ts_resource]
    References:     [connect_wsdl_url]
    Libraries:      [sqlite3, requests, xmltodict, uuid, datetime]
    """

    print("LOADING......")
    starttime = datetime.now()

    """ Sets up sqllite3 connect """
    sql_connect = sqlite3.connect(odm_copy, isolation_level=None)
    c = sql_connect.cursor()

    """ Sets temporary test values for the function """
    data_set_id = 1
    autho_token = ''
    # url = 'http://data.iutahepscor.org/LittleBearRiverWOF/cuahsi_1_1.asmx?WSDL'
    # site_code = 'LBR:USU-LBR-Mendon'
    # variable_code = 'LBR:USU36:methodCode=28:qualityControlLevelCode=1'
    # begin_date = '2005-01-01'
    # end_date = '2016-01-01'

    """ Handles NASA data with requests  """
    if 'nasa' in url:
        # TODO need to parse returned data using time series parser and return dictionary matching format of below
        headers = {'content-type': 'text/xml'}
        body = """<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" """ +\
            """xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <GetValuesObject xmlns="http://www.cuahsi.org/his/1.0/ws/">
                        <location>""" + site_code + """</location>
                        <variable>""" + variable_code + """</variable>
                        <startDate>""" + begin_date + """</startDate>
                        <endDate>""" + end_date + """</endDate>
                        <authToken>""" + autho_token + """"</authToken>
                    </GetValuesObject>
                </soap:Body>
            </soap:Envelope>"""
        response = requests.post(url, data=body, headers=headers)
        values_result = response.content
        values_result = xmltodict.parse(values_result)
    else:
        client = connect_wsdl_url(url)
        # The following line bottlenecks getting the results data.
        values_result = client.service.GetValuesObject(site_code, variable_code, begin_date, end_date, autho_token)

    if len(values_result.timeSeries[0].values[0]) == 0:
        print("No data values found.")
    elif len(values_result.timeSeries[0].values[0].value) < 100:
        print("No sensor data found.")
    else:
        # ----------------------------------------------------------------
        # Get the SamplingFeatureInformation and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the sampling feature already exists in the database
        site_code_tup = (values_result.timeSeries[0].sourceInfo.siteCode[0].value,)
        c.execute('SELECT * FROM SamplingFeatures WHERE SamplingFeatureCode = ?', site_code_tup)
        row = c.fetchone()
        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for SamplingFeature Information
            # SamplingFeatureID = Automatically generated by SQlite as autoincrement
            # SamplingFeatureUUID = Use python UUID to generate a UUID
            # SamplingFeatureTypeCV = 'Site'
            # SamplingFeatureCode = WaterML siteCode
            # SamplingFeatureName = WaterML siteName
            # SamplingFeatureDescription = NULL (doesn't exist in WaterML 1.1)
            # SamplingFeatureGeotypeCV = 'Point'
            # FeatureGeometry = Geometry representation of point using WaterML latitude and longitude
            # FeatureGeometryWKT = String Well Known Text representation of point using WaterML latitude and longitude
            # Elevation_m = WaterML elevation_m
            # ElevationDatumCV = WaterML verticalDatum
            try:
                elevation_m = values_result.timeSeries[0].sourceInfo.elevation_m
            except:
                elevation_m = None
            try:
                vertical_datum = values_result.timeSeries[0].sourceInfo.verticalDatum
            except:
                vertical_datum = None
            sampling_feature_info = (str(uuid.uuid1()),
                                     'Site',
                                     values_result.timeSeries[0].sourceInfo.siteCode[0].value,
                                     values_result.timeSeries[0].sourceInfo.siteName,
                                     'Point',
                                     'POINT (' + str(values_result.timeSeries[0].sourceInfo.geoLocation.geogLocation.
                                                     longitude) + ' ' + str(values_result.timeSeries[0].sourceInfo.
                                                                            geoLocation.geogLocation.latitude) + ')',
                                     elevation_m,
                                     vertical_datum)

            c.execute('INSERT INTO SamplingFeatures (SamplingFeatureID, SamplingFeatureUUID, '
                      'SamplingFeatureTypeCV, SamplingFeatureCode, SamplingFeatureName, SamplingFeatureDescription,'
                      'SamplingFeatureGeotypeCV, FeatureGeometry, FeatureGeometryWKT,'
                      'Elevation_m, ElevationDatumCV) VALUES (NULL,?,?,?,?,NULL,?,NULL,?,?,?)', sampling_feature_info)

            # Get the ID of the SamplingFeature I just created
            sampling_feature_id = c.lastrowid

            # ----------------------------------------------------------------
            # Get the Site information and load it into the database
            # ----------------------------------------------------------------
            # The WaterML 1.1 response doesn't have the spatial reference for the latitude and longitude
            # Insert a record into SpatialReferences to indicate that it is unknown
            spatial_reference_info = ('Unknown', 'The spatial reference is unknown')

            c.execute('INSERT INTO SpatialReferences(SpatialReferenceID, SRSCode, SRSName, SRSDescription, SRSLink) '
                      'VALUES (NULL, NULL, ?, ?, NULL)', spatial_reference_info)

            # Get the ID of the SpatialReference I just created
            spatial_reference_id = c.lastrowid

            # WaterML 1.1 ----> ODM2 Mapping for Site Information
            # SamplingFeatureID = SamplingFeatureID of the record just loaded into the SamplingFeatures table
            # SiteTypeCV = Set to the WaterML SiteType property value for the site
            # Latitude = WaterML latitude
            # Longitude = WaterML longitude
            # SpatialReferenceID = SpatialReferenceID of the record just loaded into the SpatialReferences table
            try:
                sitetypecv = values_result.timeSeries[0].sourceInfo.siteProperty[4].value
            except:
                sitetypecv = 'unknown'
            site_info = (sampling_feature_id,
                         sitetypecv,
                         values_result.timeSeries[0].sourceInfo.geoLocation.geogLocation.latitude,
                         values_result.timeSeries[0].sourceInfo.geoLocation.geogLocation.longitude,
                         spatial_reference_id)

            c.execute('INSERT INTO Sites(SamplingFeatureID, SiteTypeCV, Latitude, Longitude, SpatialReferenceID) '
                      'VALUES (?, ?, ?, ?, ?)', site_info)
        else:  # The sampling feature and the site already exist in the database
            sampling_feature_id = row[0]

        # ----------------------------------------------------------------
        # Get the Method information and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the method already exists
        # methodDescription = (valuesResult.timeSeries[0].values[0].method[0].methodDescription,)
        # print valuesResult.timeSeries[0].values[0]
        # methodDescription = ('hi',)
        try:
            method_description = values_result.timeSeries[0].values[0].method[0].methodDescription
        except:
            method_description = 'unknown'
        try:
            method_code = values_result.timeSeries[0].values[0].method[0].methodCode
        except:
            method_code = series_number
        try:
            method_link = None
        except:
            method_link = 'unknown'
        method_description1 = (method_description,)
        c.execute('SELECT * FROM Methods WHERE MethodName = ?', method_description1)
        row = c.fetchone()

        if row is None:
            # NOTE:  Some hard coded stuff here - MethodCode, MethodTypeCV, and MethodDescription don't exist in
            #        WaterML
            # WaterML 1.1 ----> ODM2 Mapping for Method Information
            # MethodID = Automatically generated by SQLite as autoincrement
            # MethodTypeCV = HARD CODED FOR NOW (Could use generic MethodTypeCV of 'Observation')
            # MethodCode = WaterML methodCode
            # MethodName = Doesn't exist in WaterML, but required. Set this to the WaterML methodDescription
            # MethodDescription = WaterML MethodDescription
            # MethodLink = WaterML methodLink - but not all time series have a MethodLink, so need to fix this
            # OrganizationID = NULL (doesn't exist in WaterML)
            method_info = ('Observation',
                           method_code,
                           method_description,
                           method_description,
                           method_link)

            c.execute('INSERT INTO Methods(MethodID, MethodTypeCV, MethodCode, MethodName, MethodDescription, \
                      MethodLink) VALUES (NULL, ?, ?, ?, ?, ?)', method_info)

            # Get the ID of the Method I just inserted
            method_id = c.lastrowid

        else:  # The method already exists in the database
            method_id = row[0]

        # ----------------------------------------------------------------
        # Get the Variable information and load it into the database
        # ----------------------------------------------------------------
        variable_code_tup = (values_result.timeSeries[0].variable.variableCode[0].value, )
        c.execute('SELECT * FROM Variables WHERE VariableCode = ?', variable_code_tup)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # VariableID = Automatically generated by SQLite as autoincrement
            # VariableTypeCV = WaterML generalCategory
            # VariableCode = WaterML variableCode
            # VariableNameCV = WaterML variableName
            # VariableDefinition = Set to NULL because it doesn't exist in WaterML and is not required
            # SpeciationCV = WaterML speciation
            # NoDataValue = WaterML noDataValue
            try:
                general_category = values_result.timeSeries[0].variable.generalCategory
            except:
                general_category = "Variable"
            try:
                speciation = values_result.timeSeries[0].variable.speciation
            except:
                speciation = None

            variable_code = values_result.timeSeries[0].variable.variableCode[0].value
            variable_code = variable_code[:20]  # HydroShare limits the length of variable code field
            variable_info = (general_category,
                             variable_code,
                             values_result.timeSeries[0].variable.variableName,
                             speciation,
                             values_result.timeSeries[0].variable.noDataValue)

            c.execute('INSERT INTO Variables\
                      (VariableID, VariableTypeCV, VariableCode, VariableNameCV, VariableDefinition, SpeciationCV, \
                      NoDataValue) '
                      'VALUES (NULL, ?, ?, ?, NULL, ?, ?)', variable_info)

            # Get the ID of the Variable I just inserted
            variable_id = c.lastrowid

        else:  # The variable already exists
            variable_id = row[0]

        # ----------------------------------------------------------------
        # Get the Units information and load it into the database
        # ----------------------------------------------------------------
        units_name = (values_result.timeSeries[0].variable.unit.unitName,)
        c.execute('SELECT * FROM Units WHERE UnitsName = ?', units_name)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # UnitsID = WaterML unitCode (this keeps it consistent with the ODM 1.1.1/WaterML 1.1 UnitIDs)
            # UnitsTypeCV = WaterML unitType
            # UnitsAbbreviation = WaterML unitAbbreviation
            # unitsName = WaterML unitName
            # unitsLink = NULL (doesn't exist in WaterML)
            try:
                unit_code = values_result.timeSeries[0].variable.unit.unitCode
            except:
                unit_code = '1'
            try:
                unit_type = values_result.timeSeries[0].variable.unit.unitType
            except:
                unit_type = 'unknown'
            try:
                unit_abbreviation = values_result.timeSeries[0].variable.unit.unitAbbreviation
            except:
                unit_abbreviation = 'unknown'
            try:
                unit_name = values_result.timeSeries[0].variable.unit.unitName
            except:
                unit_name = 'unknown'
            units_info = (unit_code,
                          unit_type,
                          unit_abbreviation,
                          unit_name)

            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName, UnitsLink) '
                      'VALUES (?, ?, ?, ?, NULL)', units_info)

            # Get the ID of the Units I just inserted
            units_id = c.lastrowid

        else:  # The unit already exists in the database
            units_id = row[0]

        # -----------------------------------------------------------------
        # Get the ProcessingLevel information and load it into the database
        # -----------------------------------------------------------------
        quality_control_level_id = \
            (values_result.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID,)
        c.execute('SELECT * FROM ProcessingLevels WHERE ProcessingLevelID = ?', quality_control_level_id)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for ProcessingLevel Information
            # ProcessingLevelID = WaterML _qualityControlLevelID
            # ProcessingLevelCode = WaterML qualityControlLevelCode
            # Definition = WaterML definition
            # Explanation = WaterML explanation
            qa_id = values_result.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID
            qa_code = values_result.timeSeries[0].values[0].qualityControlLevel[0].qualityControlLevelCode
            # HydroShare expects qa code to be a integer
            try:
                qa_code = int(qa_code)
            except:
                qa_code = qa_id
            processing_level_info = (qa_id,
                                     qa_code,
                                     values_result.timeSeries[0].values[0].qualityControlLevel[0].definition,
                                     values_result.timeSeries[0].values[0].qualityControlLevel[0].explanation)

            c.execute('INSERT INTO ProcessingLevels(ProcessingLevelID, ProcessingLevelCode, Definition, Explanation) '
                      'VALUES (?, ?, ?, ?)', processing_level_info)

            # Get the ID of the ProcessingLevel I just inserted
            processing_level_id = c.lastrowid

        else:  # The ProcessingLevel already exists in the database
            processing_level_id = row[0]

        # Get the People information and load it
        # -----------------------------------------------------------------
        try:
            contact_name = values_result.timeSeries[0].values[0].source[0].contactInformation[0].contactName
        except:
            contact_name = 'unknown unknown'
        split_name = contact_name.split(' ')
        person_info = (split_name[0], split_name[-1])
        c.execute('SELECT * FROM People WHERE PersonFirstName = ? AND PersonLastName=?', person_info)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for People Information
            # PersonID = Automatically generated by SQlite as autoincrement
            # PersonFirstName = First element of WaterML contactName split by space delimiter
            # PersonMiddleName = NULL (this could be problematic if a WaterML person actually has a middle name)
            # PersonLastName = Last element of WaterML contactName split by space delimiter

            c.execute('INSERT INTO People(PersonID, PersonFirstName, PersonLastName) '
                      'VALUES (NULL, ?, ?)', person_info)

            # Get the ID of the person I just inserted
            person_id = c.lastrowid

        else:  # The person already exists
            person_id = row[0]

        # Get the Organization information and load it
        # -----------------------------------------------------------------
        organization_name = (values_result.timeSeries[0].values[0].source[0].organization,)
        c.execute('SELECT * FROM Organizations WHERE OrganizationName = ?', organization_name)
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Organization Information
            # OrganizationID = Automatically generated by SQlite as autoincrement
            # OrganizationTypeCV = 'Unknown' (doesn't exist in WaterML, but required by ODM2)
            # OrganizationCode = WaterML sourceCode
            # OrganizationName = WaterML organization
            # OrganizationDescription = WaterML sourceDescription
            # OrganizationLink = waterML sourceLink
            # ParentOrganizationID = NULL (doesn't exist in WaterML)
            organization_info = ('unknown',
                                 values_result.timeSeries[0].values[0].source[0].sourceCode,
                                 values_result.timeSeries[0].values[0].source[0].organization,
                                 values_result.timeSeries[0].values[0].source[0].sourceDescription,
                                 values_result.timeSeries[0].values[0].source[0].sourceLink[0])
            print(organization_info[1])
            c.execute('INSERT INTO Organizations\
                      (OrganizationID, OrganizationTypeCV, OrganizationCode, OrganizationName, OrganizationDescription,\
                       OrganizationLink) '
                      'VALUES (NULL, ?, ?, ?, ?, ?)', organization_info)

            # Get the ID of the Organization I just inserted
            organization_id = c.lastrowid

        else:  # The organization already exists
            organization_id = row[0]

        # Create the Affiliation between the person and the organization
        # -----------------------------------------------------------------
        c.execute('SELECT * FROM Affiliations WHERE PersonID = ? AND OrganizationID = ?', (person_id, organization_id))
        row = c.fetchone()

        if row is None:
            # WaterML 1.1 ----> ODM2 Mapping for Affiliation Information
            # AffiliationID = Automatically generated by SQlite as autoincrement
            # PersonID = ID of the person created above
            # OrganizationID = ID of the organization created above
            # IsPrimaryOrganizationContact = 1 for 'True' (hard coded for now, doesn't really exist in WaterML)
            # AffilationStartDate = set to the current system date (this is required, but doesn't exit in WaterML)
            # AffiliationEndDate = NULL (this doesn't exist in WaterML but is not required)
            # PrimaryPhone = WaterML phone of source contact
            # PrimaryEmail = WaterML email of source contact
            # PrimaryAddress = NULL (doesn't exist in WaterML)
            # PersonLink = NULL (doesn't exist in WaterML)
            try:
                phone = values_result.timeSeries[0].values[0].source[0].contactInformation[0].phone[0]
            except:
                phone = "unknown"
            try:
                email = values_result.timeSeries[0].values[0].source[0].contactInformation[0].email[0]
            except:
                email = "unknown"
            affiliation_info = (person_id,
                                organization_id,
                                1,
                                datetime.now(),
                                phone,
                                email,)

            c.execute('INSERT INTO Affiliations(AffiliationID, PersonID, OrganizationID, IsPrimaryOrganizationContact, \
                      AffiliationStartDate, PrimaryPhone, PrimaryEmail) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?)', affiliation_info)

            # Get the ID of the Affiliation I just inserted
            affiliation_id = c.lastrowid

        else:  # The affilation already exists
            affiliation_id = row[0]

        # Get the Action information and load it
        # -----------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for Action Information
        # ActionID = Automatically generated by SQlite as autoincrement
        # ActionTypeCV = 'Observation' (used the generic term because this doesn't exist in WaterML)
        # MethodID = ID of the Method created above
        # BeginDateTime = WaterML _dateTime of the first data value
        # BeginDateTimeUTCOffset = split hour off of WaterML _timeOffset of the first data value
        # EndDateTime = WaterML _dateTime of the last data value
        # EndDateTimeUTCOffset = split hour off of WaterML _timeOffset of the last data value
        # ActionDescription = 'An observation action that generated a time series result.' \
        # (HARD CODED FOR NOW - doesn't exist in WaterML)
        # ActionFileLink = NULL (doesn't exist in WaterML)
        action_info = ('Observation',
                       method_id,
                       values_result.timeSeries[0].values[0].value[0]._dateTime,
                       int(values_result.timeSeries[0].values[0].value[0]._timeOffset.split(':')[0]),
                       values_result.timeSeries[0].values[0].value[-1]._dateTime,
                       int(values_result.timeSeries[0].values[0].value[-1]._timeOffset.split(':')[0]),
                       'An observation action that generated a time series result.')

        c.execute('INSERT INTO Actions(ActionID, ActionTypeCV, MethodID, BeginDateTime, BeginDateTimeUTCOffset, \
                  EndDateTime, EndDateTimeUTCOffset, ActionDescription) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)', action_info)

        # Get the ID of the Action I just created.
        action_id = c.lastrowid

        # Create the ActionBy information and load it into the database
        # -----------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for ActionBy Information
        # BridgeID = Automatically generated by SQlite as autoincrement
        # ActionID = ID of the Action created above
        # AffiliationID = ID of the Affiliation created above
        # IsActionLead = 1 for 'True' (doesn't exist in WaterML, so hard coded)
        # RoleDescription = 'Responsible party' (doesn't exist in WaterML, so hard coded)
        action_by_info = (action_id, affiliation_id, 1, 'Responsible party')

        c.execute('INSERT INTO ActionBy(BridgeID, ActionID, AffiliationID, IsActionLead, RoleDescription) '
                  'VALUES (NULL, ?, ?, ?, ?)', action_by_info)

        # Create the FeatureAction information and load it into the database
        # ------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for FeatureAction Information
        # FeatureActionID = Automatically generated by SQlite as autoincrement
        # SamplingFeatureID = ID of the SamplingFeature created above
        # ActionID = ID of the Action created above
        feature_action_info = (sampling_feature_id, action_id)

        c.execute('INSERT INTO FeatureActions(FeatureActionID, SamplingFeatureID, ActionID) '
                  'VALUES (NULL, ?, ?)', feature_action_info)

        # Get the FeatureActionID for the record I just created
        feature_action_id = c.lastrowid

        # Create the Result information an load it into the database
        # ------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for Result Information
        # ResultID = Automatically generated by SQlite as autoincrement
        # ResultUUID = Use python UUID to generate a UUID
        # FeatureActionID = ID of the FeatureAction created above
        # ResultTypeCV = 'Time series coverage' (doesn't exist in WaterML, so hard coded)
        # VariableID = ID of Variable created above
        # UnitsID = ID of Units created above
        # TaxonomicClassifierID = NULL (not needed)
        # ProcessingLevelID = ID of ProcessingLevel created above
        # ResultDateTime = current system time (basically the date the data was added to the database)
        # ResultDateTimeUTCOffset = UTCOffset of current system time
        # ValidDateTime = NULL (doesn't exist in WaterML and unknown)
        # ValidDateTImeUTCOffset = NULL (doesn't exist in WaterML and unknown)
        # StatusCV = 'Unknown' (doesn't exist in WaterML - could also be NULL)
        # SampledMediumCV = WaterML sampleMedium
        # ValueCount = python len function length of the WaterML values list
        result_info = (str(uuid.uuid1()),
                       feature_action_id,
                       'Time series coverage',
                       variable_id,
                       units_id,
                       processing_level_id,
                       datetime.now(),
                       -time.timezone / 3600,
                       'unknown',
                       values_result.timeSeries[0].variable.sampleMedium,
                       len(values_result.timeSeries[0].values[0].value))

        c.execute('INSERT INTO Results(ResultID, ResultUUID, FeatureActionID, ResultTypeCV, VariableID, UnitsID, \
                  ProcessingLevelID, ResultDateTime, ResultDateTimeUTCOffset, StatusCV, SampledMediumCV, ValueCount) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', result_info)

        # Get the ID for the Result I just created
        result_id = c.lastrowid

        # Load the Units information for the IntendedTimeSpacing into the database
        # ------------------------------------------------------------------------
        # NOTE: The intended time spacing information isn't in WaterML
        #       This is hard coded and could be problematic for some datasets.
        try:
            units_info = (102, 'unknown', 'unknown')
            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName) '
                      'VALUES ( ?, ?, ?)', units_info)
            # Get the ID of the Units I just inserted
            time_units_id = c.lastrowid
        except:
            time_units_id = 102
            pass

        # Get the TimeSeriesResult information and load it into the database
        # ------------------------------------------------------------------
        # NOTE:  The intended time spacing information isn't in WaterML
        # NOTE:  My test dataset didn't have an Offset, so may need to handle that better here
        # WaterML 1.1 ----> ODM2 Mapping for TimeSeriesResult Information
        # XLocation = NULL
        # XLocationUnitsID = NULL
        # YLocation = NULL
        # YLocationUnitsID = NULL
        # ZLocation = NULL
        # ZLocationUnitsID = NULL
        # SpatialReferenceID = NULL
        # IntendedTimeSpacing = 30 (Hard Coded.  I know this for the test dataset,\
        #  but would have to be null for generic WaterML files because it doesn't exist in WaterML)
        # IntendedTimeSpadingUnitsID = ID of TimeUnits created above (essentially hard coded -\
        #  I know this for the test dataset, but would have to be null for generic WaterML files\
        #  because it doesn't exist in WaterML)
        # AggregationStatisticCV = WaterML dataType
        time_series_result_info = (result_id, 30, time_units_id, values_result.timeSeries[0].variable.dataType)

        c.execute('INSERT INTO TimeSeriesResults(ResultID, IntendedTimeSpacing, IntendedTimeSpacingUnitsID, \
                  AggregationStatisticCV) '
                  'VALUES (?, ?, ?, ?)', time_series_result_info)

        # Get the TimeSeriesResultValues information and load it into the database
        # ------------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for TimeSeriesResultValues Information
        # ValueID = Automatically generated by SQLite as autoincrement
        # ResultID = ID of the Result created above
        # DataValue = WaterML value
        # ValueDateTime = WaterML _dateTime
        # ValueDateTimeUTCOffset = split the hour off of the WaterML _timeOffset
        # CensorCodeCV = WaterML _censorCode
        # QualityCodeCV = 'Unknown' (doesn't exist in WaterML, but required)
        # TimeAggregationInterval = WaterML timeSupport
        # TimeAggregationIntervalUnitsID = WaterML timeScale.unit.unitCode
        ts_result_values = []
        num_values = len(values_result.timeSeries[0].values[0].value)
        for z in range(0, num_values-1):
            try:
                censor_code = values_result.timeSeries[0].values[0].value[z].censorCode
            except:
                censor_code = 'unknown'
            try:
                time_support = values_result.timeSeries[0].variable.timeScale.timeSupport
            except:
                time_support = 'unknown'
            try:
                unit_code = values_result.timeSeries[0].variable.timeScale.unit.unitCode
            except:
                unit_code = 'unknown'

            ts_result_values.append((result_id,
                                     values_result.timeSeries[0].values[0].value[z].value,
                                     values_result.timeSeries[0].values[0].value[z]._dateTime,
                                     int(values_result.timeSeries[0].values[0].value[z]._timeOffset.split(':')[0]),
                                     censor_code,
                                     'Unknown',
                                     time_support,
                                     unit_code))
        c.execute("BEGIN TRANSACTION;")
        c.executemany('INSERT INTO TimeSeriesResultValues(ValueID, ResultID, DataValue, ValueDateTime, \
                      ValueDateTimeUTCOffset, CensorCodeCV, QualityCodeCV, TimeAggregationInterval, \
                      TimeAggregationIntervalUnitsID) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)', ts_result_values)

        # Now create the DataSets Results bridge record
        data_sets_results_info = (data_set_id, result_id)
        c.execute('INSERT INTO DataSetsResults(BridgeID, DataSetID, ResultID) Values (NULL, ?, ?)',
                  data_sets_results_info)
        # Save (commit) the changes
        c.execute("COMMIT;")
        sql_connect.commit()
        # seriesCounter += 1
    # Close the connection to the database
    # ------------------------------------
    sql_connect.close()

    print("Total Time: " + str(datetime.now() - starttime))
'''
    # DO NOT DELETE


def connect_wsdl_url(wsdl_url):
    """
    Handles client url errors. 

    Arguments:      [wsdl_url]
    Returns:        [client]
    Referenced By:  [load_into_odm2, ]
    References:     []
    Libraries:      [suds.client.Client]
    """

    try:
        client = Client(wsdl_url)
    except TransportError:
        raise Exception('Url not found')
    except ValueError:
        raise Exception('Invalid url')  # ought to be a 400, but no page implemented for that
    except SAXParseException:
        raise Exception("The correct url format ends in '.asmx?WSDL'.")
    except:
        raise Exception("Unexpected error")

    return client


def trim(string_dic):
    """
    Removes brackets, quotation marks, and commas from a python list.

    Arguments:      [string_dic]
    Returns:        [string_dic]
    Referenced By:  [controllers_ajax.create_layer]
    References:     []
    Libraries:      []
    """

    string_dic = string_dic.strip('[')
    string_dic = string_dic.strip(']')
    string_dic = string_dic.strip('"')
    string_dic = string_dic.replace('"', '')
    string_dic = string_dic.split(',')

    return string_dic
