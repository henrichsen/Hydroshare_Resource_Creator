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
import xml.etree.ElementTree as eTree
import tempfile
import json
import logging

logger = logging.getLogger(__name__)
use_hs_client_helper = True
try:
    from tethys_services.backends.hs_restclient_helper import get_oauth_hs
except Exception as ex:
    use_hs_client_helper = False
    logger.error("tethys_services.backends.hs_restclient_helper import get_oauth_hs: " + ex.message)


def get_workspace():
    """
    Gets app workspace path.
    
    Arguments:      []
    Returns:        [workspace]
    Referenced By:  [error_report, parse_ts_layer, controllers_ajax.chart_data, controllers_ajax.create_layer]
    References:     [app.HydroshareResourceCreator]
    Libraries:      []
    """

    workspace = HydroshareResourceCreator.get_app_workspace().path

    if not os.path.exists(workspace + "/id"):
        os.mkdir(workspace + "/id")

    print "Workspace: " + workspace

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


def parse_ts_layer(file_path, title, abstract):
    """
    Parses Timeseries Layer.

    Arguments:      [file_path, title, abstract]
    Returns:        [counter]
    Referenced By:  [controllers_ajax.create_layer, parse_ts_layer]
    References:     [get_workspace, load_into_odm2]
    Libraries:      [json, shutil, sqlite3]
    """

    temp_dir = get_workspace()
    # file_path_id = get_workspace() + '/id'
    # root_dir = file_path_id + '/' + res_id
    # data_dir = root_dir + '/' + res_id + '/data/contents/'
    # for subdir, dirs, files in os.walk(root_dir):
    #     for file in files:
    #         path = data_dir + file
    #         if '.json.refts' in file:

    with open(file_path, 'r') as f:
        data = f.read()
        # file_number = parse_ts_layer(file_data,title)
    series_count = 0
    # error = ''
    # response = None
    # print data
    data = data.encode(encoding='UTF-8')
    # noinspection PyTypeChecker
    data = data.replace("'", '"')
    json_data = json.loads(data)
    json_data = json_data["timeSeriesReferenceFile"]
    layer = json_data['referencedTimeSeries']
    odm_master = temp_dir+'/ODM2_master/ODM2_master.sqlite'
    odm_copy = temp_dir+'/ODM2/'+title+'.sqlite'
    shutil.copy(odm_master, odm_copy)
    for sub in layer:
        ref_type = sub['requestInfo']['refType']
        service_type = sub['requestInfo']['serviceType']
        url = sub['requestInfo']['url']
        site_code = sub['site']['siteCode']
        variable_code = sub['variable']['variableCode']
        start_date = sub['beginDate']
        # start_date = ''
        end_date = sub['endDate']
        # end_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        # auth_token = ''
        conn = sqlite3.connect(odm_copy, isolation_level=None)
        c = conn.cursor()
        data_set_info = (str(uuid.uuid1()),
                         'Multi-time series',
                         variable_code,
                         title,
                         abstract
                         )
        conn.commit()

        c.execute('INSERT INTO Datasets(DataSetID, DataSetUUID, DataSetTypeCV, DataSetCode, DataSetTitle, \
                  DataSetAbstract) '
                  'VALUES (NULL, ?, ?, ?, ?, ?)', data_set_info)
        if ref_type == 'WOF':
            if service_type == 'SOAP':
                load_into_odm2(url, site_code, variable_code, start_date, end_date, odm_copy, series_count)
            series_count += 1

    return series_count


def load_into_odm2(url, site_code, variable_code, begin_date, end_date, odm_copy, series_number):
    """
    Loads data into ODM 2 Table.

    Arguments:      [url, site_code, variable_code, begin_date, end_date, odm_copy, series_number]
    Returns:        []
    Referenced By:  [parse_ts_layer]
    References:     [connect_wsdl_url]
    Libraries:      [sqlite3, requests, xmltodict, uuid, datetime]
    """

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
    else:
        client = connect_wsdl_url(url)
        # The following line bottlenecks getting the results data.
        values_result = client.service.GetValuesObject(site_code, variable_code, begin_date, end_date, autho_token)

    if len(values_result.timeSeries[0].values[0]) == 0:
        print "No data values found."
    elif len(values_result.timeSeries[0].values[0].value) < 100:
        print "No sensor data found."
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
            # OrganizationCode = WaterML sourceCode --> WaterML may not provide a unique code, which ODM2 requires.
            # OrganizationName = WaterML organization
            # OrganizationDescription = WaterML sourceDescription
            # OrganizationLink = waterML sourceLink
            # ParentOrganizationID = NULL (doesn't exist in WaterML)
            organization_info = ('unknown',
                                 # values_result.timeSeries[0].values[0].source[0].sourceCode,
                                 random.randint(1, 99),  # TODO Temporary value, should be unique source code.
                                 values_result.timeSeries[0].values[0].source[0].organization,
                                 values_result.timeSeries[0].values[0].source[0].sourceDescription,
                                 values_result.timeSeries[0].values[0].source[0].sourceLink[0])
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
        for z in range(0, num_values - 1):
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

    # DO NOT DELETE
    '''
    """
    Loads data into ODM 2 Table.
    
    Arguments:      [url, site_code, variable_code, begin_date, end_date, odm_copy, series_number]
    Returns:        []
    Referenced By:  [parse_ts_layer]
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


# #########################  WATERML PARSER  ######################### #

def compile_refts_data(file_upload):
    """
    Passes uploaded file to appropriate parsers and returns a referenced timeseries json file.

    Arguments:      [file_upload]
    Returns:        [refts_json_data]
    Referenced By:  []
    References:     [file_type, parse_wml_1, compile_refts_json_files]
    Libraries:      []
    """

    refts_data = {
        'refType': [],
        'serviceType': [],
        'endDate': [],
        'url': [],
        'beginDate': [],
        'site': [],
        'returnType': [],
        'latitude': [],
        'longitude': [],
        'variable': [],
        'variableCode': [],
        'networkName': [],
        'siteCode': [],
        'keyWords': [],
        'creationTime': [],
        'beginTime': [],
        'endTime': []
    }

    if file_type(file_upload) is 'wml_1':
        refts_data = parse_wml_1(file_upload, refts_data)
        refts_json_data = compile_refts_json_files(refts_data)
        return refts_json_data

    elif file_type(file_upload) is 'wml_2':
        print("WaterML 2 not currently supported.")

    elif file_type(file_upload) is 'tsml_1':
        print("TimeseriesML not currently supported.")

    elif file_type(file_upload) is 'unknown_xml':
        print("File type not supported.")

    elif file_type(file_upload) is 'parse_error':
        print("Parse Error")

    elif file_type(file_upload) is 'upload_error':
        print("File does not exist.")

    elif file_type(file_upload) is 'unknown_error':
        print("Encountered an unknown error.")

    else:
        print("Encountered unknown error.")


def file_type(doc):
    """
    Identifies file type for compile_refts_data

    Arguments:      [doc]
    Returns:        [return_obj]
    Referenced By:  []
    References:     []
    Libraries:      [eTree]
    """

    doc.seek(0)
    try:
        tree = eTree.parse(doc)
        root = tree.getroot()
        if '{http://www.cuahsi.org/waterML/1.1/}timeSeriesResponse' in root.tag:
            return_obj = 'wml_1'
        elif '{http://www.opengis.net/waterml/2.0}Collection' in root.tag:
            return_obj = 'wml_2'
        elif '{http://www.opengis.net/timeseriesml/1.0}Collection' in root.tag:
            return_obj = 'tsml_1'
        else:
            return_obj = 'unknown_xml'
    except eTree.ParseError:
        return_obj = "parse_error"
    except IOError:
        return_obj = "upload_error"

    return return_obj


def parse_tsml(tsml_file, refts_data):
    """
    Recieves a TimeseriesML file and an empty data structure, parses the file, passes relevant data into the data
    structure, and returns the data structure to be used in compiling the refts file.

    Arguments:      [tsml_file, refts_data]
    Returns:        [refts_data]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    tsml_file.seek(0)
    return refts_data


def parse_wml_2(wml_2_file, refts_data):
    """
    Recieves a WaterML 2.0 file and an empty data structure, parses the file, passes relevant data into the data
    structure, and returns the data structure to be used in compiling the refts file.

    Arguments:      [wml_2_file, refts_data]
    Returns:        [refts_data]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    wml_2_file.seek(0)
    return refts_data


def parse_wml_1(wml_1_file, refts_data):
    """
    Recieves a WaterML 1.0/1.1 file and an empty data structure, parses the file, passes relevant data into the data
    structure, and returns the data structure to be used in compiling the refts file.

    Arguments:      [wml_1_file, refts_data]
    Returns:        [refts_data]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    wml_1_file.seek(0)

    tree = eTree.parse(wml_1_file)

    previous_node = None
    wml = "{http://www.cuahsi.org/waterML/1.1/}"

    for node in tree.iter():
        if previous_node is None:
            previous_node = node

        if str(node.tag) == wml + "timeSeries":
            refts_data['returnType'].append('WaterML 1.1')
            refts_data['refType'].append('WOF')
            refts_data['serviceType'].append('SOAP')

        if str(node.tag) == wml + "value" and str(previous_node.tag) != wml + "value":
            refts_data['beginDate'].append(node.attrib['dateTime'])

        if str(node.tag) != wml + "value" and str(previous_node.tag) == wml + "value":
            refts_data['endDate'].append(previous_node.attrib['dateTime'])

        if str(node.tag) == wml + "siteName":
            refts_data['site'].append(node.text)

        if str(node.tag) == wml + "latitude":
            refts_data['latitude'].append(node.text)

        if str(node.tag) == wml + "longitude":
            refts_data['longitude'].append(node.text)

        if str(node.tag) == wml + "variableName":
            refts_data['variable'].append(node.text)

        if str(node.tag) == wml + "variableCode":
            refts_data['variableCode'].append(node.text)

        if str(node.tag) == wml + "sourceLink":
            refts_data['url'].append(node.text)

        if str(node.tag) == wml + "siteCode":
            refts_data['siteCode'].append(node.text)
            refts_data['networkName'].append(node.attrib['network'])

        if str(node.tag) == wml + "creationTime":
            refts_data['creationTime'].append(node.text)

        if str(node.tag) == wml + "parameter":
            if str(node.attrib['name']) == "startDate":
                refts_data['beginTime'].append(node.attrib['value'])

        if str(node.tag) == wml + "parameter":
            if str(node.attrib['name']) == "endDate":
                refts_data['endTime'].append(node.attrib['value'])

        previous_node = node

    return refts_data


def compile_refts_json_files(refts_data):
    """
    Receives refts data from the parser, compiles it into the proper refts json structure, and saves it to a 
    temporary file. Currently, the json data is simply printed to the terminal.

    Arguments:      [refts_data]
    Returns:        [refts_file]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    n = 0
    refts_list = []

    for _ in refts_data['returnType']:
        refts = {
            "refType": refts_data['refType'][n],
            "serviceType": refts_data['serviceType'][n],
            "endDate": refts_data['endDate'][n],
            "url": refts_data['url'][n],
            "beginDate": refts_data['beginDate'][n],
            "site": refts_data['site'][n],
            "returnType": refts_data['returnType'][n],
            "location": {
                "latitude": refts_data['latitude'][n],
                "longitude": refts_data['longitude'][n]
            },
            "variable": refts_data['variable'][n],
            "variableCode": refts_data['variableCode'][n],
            "networkName": refts_data['networkName'][n],
            "SiteCode": refts_data['siteCode'][n]
        }
        refts_list.append(refts)
        n += 1

    compiled_json_data = {
        "timeSeriesLayerResource": {
            "fileVersion": 1,
            "title": ", ".join(sorted(set(refts_data['site'])) + sorted(set(refts_data['variable']))),
            "symbol": "http://data.cuahsi.org/content/images/cuahsi_logo_small.png",
            "REFTS": refts_list,
            "keyWords": "Timeseries, CUAHSI",
            "abstract": ", ".join(sorted(set(refts_data['variable']))) +
                        ' data collected from ' +
                        ", ".join(refts_data['beginTime']) +
                        ' to ' +
                        ", ".join(refts_data['endTime']) +
                        ' created on ' +
                        ", ".join(refts_data['creationTime']) +
                        ' from the following site(s): ' +
                        ", ".join(sorted(set(refts_data['site']))) +
                        '. Data created by CUAHSI HydroClient: http://data.cuahsi.org/#.'
        }
    }
    refts_file = tempfile.TemporaryFile()
    refts_file.write(json.dumps(compiled_json_data))
    refts_file.seek(0)
    print(":::REFTS CONTENT:::")
    print(refts_file.read())
    print(":::END CONTENT:::")
    return refts_file

'''
import collections
from time import gmtime, strftime
from lxml import etree
import controllers
import csv
import StringIO
import zipfile
import os
'''

'''

def get_version(root):
    """
    Checks WaterML file and returns the either version 1.0 or 2.0.

    Arguments:      [root]
    Returns:        [wml_version]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    wml_version = None
    for element in root.iter():
        if '{http://www.opengis.net/waterml/2.0}Collection' in element.tag:
            wml_version = '2.0'
            break
        if '{http://www.cuahsi.org/waterML/1.1/}timeSeriesResponse' \
                or '{http://www.cuahsi.org/waterML/1.0/}timeSeriesResponse' in element.tag:
            wml_version = '1'
            break
    return wml_version


def read_error_file(xml_file):
    """
    Attempts to open WaterML file, returns an error if the file is invalid.

    Arguments:      [xml_file]
    Returns:        [error_status]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    try:
        f = open(xml_file)
        error_status = {'status': f.readline()}
        return error_status
    except:
        error_status = {'status': 'invalid WaterML file'}
        return error_status


def error_report(file):
    """
    Error report.

    Arguments:      [file]
    Returns:        []
    Referenced By:  [parse_1_0_and_1_1]
    References:     [get_workspace]
    Libraries:      [datetime]
    """

    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/errorReport.txt'
    file_temp = open(file_temp_name, 'a')
    time1 = datetime.now()
    time2 = time1.strftime('%Y-%m-%d %H:%M')
    file_temp.write(time2+"\n"+file+"\n")
    file_temp.close()
    file_temp.close()


def parse_1_0_and_1_1(root):
    """
    Parses WaterML 1.0/1.1 and returns reference timeseries data.

    Arguments:      [root]
    Returns:        [return_object]
    Referenced By:  []
    References:     [error_report]
    Libraries:      [collectios]
    """

    root_tag = root.tag.lower()

    master_values = collections.OrderedDict()
    master_times = collections.OrderedDict()
    master_boxplot = collections.OrderedDict()
    master_stat = collections.OrderedDict()
    meth_qual = []  # List of all the quality, method, and source combinations

    meta_dic = {'method': {}, 'quality': {}, 'source': {}, 'organization': {}, 'quality_code': {}}
    # m_des = None
    # m_code = None
    m_org = None

    master_counter = True
    nodata = "-9999"  # default NoData value. The actual NoData value is read from the XML noDataValue tag
    timeunit = None
    sourcedescription = None
    timesupport = None
    units, site_name, variable_name, quality, method, organization = None, None, None, None, None, None

    datatype = None
    valuetype = None
    samplemedium = None

    # unit_id, unit_ab = None, None
    # var_code, speciation = None, None

    q_code, q_des, q_exp, q_id = None, None, None, None
    process_code, process_def, process_expl, process_id = [], [], [], []

    m_code, m_name, m_des, m_link, m_id = None, None, None, None, None
    meth_code, meth_name, meth_des, meth_link, meth_id = [], [], [], [], []

    # o_code, o_name, o_des, o_link = None, None, None, None
    # org_code, org_name, org_des, olink = [], [], [], []
    try:
        if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag\
         or 'timeSeriesResponse' in root_tag:

            # lists to store the time-series data

            # iterate through xml document and read all values
            for element in root.iter():
                # bracket_lock = -1
                if '}' in element.tag:
                    # print element.tag
                    bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                    tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace
                    tag = tag.lower()

                    if 'value' != tag:
                        # in the xml there is a unit for the value, then for time. just take the first
                        # print tag
                        if 'unitName' == tag or 'units' == tag:
                            units = element.text
                        if 'unitCode' == tag:
                            pass
                            # unit_id = element.text
                        if 'unitabbreviation' == tag:
                            pass
                            # unit_ab = element.text

                        if 'variablecode' in tag:
                            pass
                            # var_code = element.text
                        if 'variableName' == tag:
                            variable_name = element.text
                        if 'noDataValue' == tag:
                            nodata = element.text
                        if 'speciation' in tag:
                            pass
                            # speciation = element.text

                        if "qualitycontrollevel" in tag:
                            try:
                                q_id = element.attrib['qualityControlLevelID']
                            except:
                                q_id = 'None'
                            for subele in element:
                                if 'qualitycontrollevelcode' in subele.tag.lower():
                                    # q_code = subele.text
                                    q_code = m_code.replace(" ", "")
                                if 'definition' in subele.tag.lower():
                                    q_des = subele.text
                                if 'explanation' in subele.tag.lower():
                                    q_exp = subele.text
                            process_code.append(q_code)
                            process_def.append(q_des)
                            process_expl.append(q_exp)
                            process_id.append(q_id)

                            m_code, m_name, m_des, m_link, m_id = None, None, None, None, None
                            meth_code, method_name, method_des, meth_link, meth_id = [], [], [], [], []

                        if "method" in tag:
                            try:
                                m_id = element.attrib['methodID']
                            except:
                                m_id = 'None'
                            for subele in element:
                                if 'methodcode' in subele.tag.lower():
                                    m_code = subele.text
                                    m_code = m_code.replace(" ", "")
                                if 'methodname'in subele.tag.lower():
                                    m_name = subele.text
                                if 'methoddescription' in subele.tag.lower():
                                    m_des = subele.text
                                if 'methodLink' in subele.tag.lower():
                                    m_link = subele.text
                            meth_code.append(m_code)
                            meth_name.append(m_name)
                            meth_des.append(m_des)
                            meth_link.append(m_link)
                            meth_id.append(m_id)
                            # meta_dic['method'].update({m_code:m_des})

                        # o_code, o_name, o_des, o_link = None, None, None, None
                        # org_code, org_name, org_des, olink = [], [], [], []

                        if "source" == tag.lower():
                            for subele in element:
                                if'organization'in subele.tag.lower():
                                    pass
                                    # o_name = subele.text
                                if 'sourcecode' in subele.tag.lower():
                                    # o_code = subele.text
                                    pass
                                    # o_code = o_code.replace(" ", "")
                                if 'sourcedescription' in subele.tag.lower():
                                    pass
                                    # o_des = subele.text
                                if 'sourceLink' in subele.tag.lower():
                                    pass
                                    # o_link = subele.text
                                print(subele)
                            meta_dic['source'].update({m_code: m_des})
                            meta_dic['organization'].update({m_code: m_org})

                        if 'siteName' == tag:
                            site_name = element.text

                        if 'organization' == tag or 'sitecode' == tag:
                            try:
                                organization = element.attrib['agencyCode']
                            except:
                                organization = element.text
                        if 'dataType' == tag:
                            datatype = element.text
                        if 'valueType' == tag:
                            valuetype = element.text
                        if "sampleMedium" == tag:
                            samplemedium = element.text
                        if "timeSupport" == tag or"timeInterval" == tag:
                            timesupport = element.text
                        if"unitName" == tag or "UnitName" == tag:
                            timeunit = element.text
                        if"sourceDescription" == tag or "SourceDescription" == tag:
                            sourcedescription = element.text
                            # print meta_dic
                    elif 'value' == tag:
                        n = element.attrib['dateTime']
                        try:
                            quality = element.attrib['qualityControlLevelCode']
                        except:
                            quality = ''
                        try:
                            quality1 = element.attrib['qualityControlLevel']
                        except:
                            quality1 = ''
                        if quality == '' and quality1 != '':
                            quality = quality1
                        try:
                            method = element.attrib['methodCode']
                        except:
                            method = ''
                        try:
                            method1 = element.attrib['methodID']
                        except:
                            method1 = ''
                        if method == '' and method1 != '':
                            method = method1
                        try:
                            source = element.attrib['sourceCode']
                        except:
                            source = ''
                        try:
                            source1 = element.attrib['sourceID']
                        except:
                            source1 = ''
                        if source == '' and source1 != '':
                            source = source1
                        dic = quality + 'aa' + method + 'aa' + source
                        dic = dic.replace(" ", "")

                        if dic not in meth_qual:

                            meth_qual.append(dic)
                            master_values.update({dic: []})
                            master_times.update({dic: []})
                            master_boxplot.update({dic: []})
                            master_stat.update({dic: []})
                            # master_data_values.update({dic:[]})

                        v = element.text
                        if v == nodata:
                            # value = None
                            # x_value.append(n)
                            # y_value.append(value)
                            v = None

                        else:
                            v = float(element.text)
                            # x_value.append(n)
                            # y_value.append(v)
                            # master_data_values[dic].append(v) #records only none null values for running statistics
                        master_values[dic].append(v)
                        master_times[dic].append(n)
            return_object = {
                'site_name': site_name,
                'variable_name': variable_name,
                'units': units,
                'meta_dic': meta_dic,

                'organization': organization,
                'quality': quality,
                'method': method,
                'status': 'success',
                'datatype': datatype,
                'valuetype': valuetype,
                'samplemedium': samplemedium,
                'timeunit': timeunit,
                'sourcedescription': sourcedescription,
                'timesupport': timesupport,
                'master_counter': master_counter,

                'master_values': master_values,
                'master_times': master_times,
                'master_boxplot': master_boxplot,
                'master_stat': master_stat,
                # 'master_data_values':master_data_values
            }
            return return_object
        else:
            parse_error = "Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series"
            error_report("Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series")
            print(parse_error)
            return_object = {
                'status': parse_error
            }
            return return_object
    except Exception as e:
        data_error = "Parsing error: The Data in the Url, or the request, was not correctly formatted for water ml 1."
        error_report("Parsing error: The Data in the Url, or in the request, was not correctly formatted.")
        print(data_error)
        print(e)
        return_object = {
            'status': data_error
        }
        return return_object


def parsing_test(root):
    """
    Tests parser.

    Arguments:      [root]
    Returns:        [return_obj]
    Referenced By:  []
    References:     []
    Libraries:      [collections, time.strftime, time.gmtime]
    """

    root_tag = root.tag.lower()

    master_values = collections.OrderedDict()

    result_total = []  # List of all the quality, method, and source combinations
    value_counter = 0
    quality_key = None
    method_key = None
    source_key = None

    nodata = "-9999"  # default NoData value. The actual NoData value is read from the XML noDataValue tag

    # units, site_name, variable_name,quality,method,organization = None,None,None,None,None,None
    # datatype = None
    # valuetype = None
    # samplemedium = None

    # unit_id, unit_ab = None, None
    # var_code, speciation = None, None

    q_code, q_def, q_exp, q_id = None, None, None, None
    quality_code, quality_def, quality_expl, quality_id = [], [], [], []
    quality_levels = []

    m_code, m_name, m_des, m_link, m_id = None, None, None, None, None
    # meth_code, meth_name, meth_des, meth_link, meth_id = [], [], [], [], []
    methods = []

    o_code, o_name, o_des, o_link, o_per_name, o_per_email, o_per_phone, o_per_add, o_per_link = \
        None, None, None, None, None, None, None, None, None
    org_code, org_name, org_des, orglink, org_per_name, org_per_email, org_per_phone, org_per_add, org_per_link = \
        [], [], [], [], [], [], [], [], []
    organizations = []
    people = []
    affliations = []
    # sam_code, sam_name, sam_des, sam_fea, sam_geo_wkt, sam_ele, sam_dat = None, None, None, None, None, None, None
    # lat, long = None, None

    time_interval, time_code, time_ab, time_unit = None, None, None, None
    # utc_offset = None
    if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag\
       or 'timeSeriesResponse' in root_tag:

        # lists to store the time-series data
        # iterate through xml document and read all values
        for element in root.iter():
            # bracket_lock = -1
            if '}' in element.tag:
                # print element.tag
                bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace
                tag = tag.lower()
                if 'value' != tag:
                    # in the xml there is a unit for the value, then for time. just take the first
                    # print tag
                    # if 'unitName' == tag or 'units' ==tag:
                    #     units = element.text
                    # if 'unitCode' == tag:
                    #     unitId = element.text
                    # if 'unitabbreviation' ==tag:
                    #     unitAb = element.text
                    # if 'variablecode' in tag:
                    #     varCode = element.text
                    # if 'variableName' == tag:
                    #     variable_name = element.text
                    if 'noDataValue' == tag:
                        nodata = element.text
                    if 'speciation' in tag:
                        pass
                        # speciation = element.text

                    if "qualitycontrollevel" == tag.lower():
                        try:
                            q_id = element.attrib['qualityControlLevelID']
                        except:
                            q_id = 'None'
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if 'qualitycontrollevelcode' in subele_text:
                                q_code = subele.text
                                q_code = q_code.replace(" ", "")
                            if 'definition' in subele_text:
                                q_def = subele.text
                            if 'explanation' in subele_text:
                                q_exp = subele.text
                        quality_levels.append((None, q_code, q_def, q_exp))
                        # qualityCode.append(q_code)
                        # qualityDef.append(q_des)
                        # qualityExpl.append(q_exp)
                        quality_id.append(q_id)

                    if "method" == tag.lower():
                        try:
                            pass
                            # m_id = element.attrib['methodID']
                        except:
                            pass
                            # m_id = 'None'
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if 'methodcode' in subele_text:
                                m_code = subele.text
                                m_code = m_code.replace(" ", "")
                            if 'methodname'in subele_text:
                                pass
                                # m_name = subele.text
                            if 'methoddescription' in subele_text:
                                m_des = subele.text
                            if 'methodLink' in subele_text:
                                m_link = subele.text
                        # print "adding methods to sub dic"

                        methods.append((None, 'Instrument deployment', m_code, "hi", m_des, m_link, None))
                        # methCode.append(m_code)
                        # methName.append(m_name)
                        # methDes.append(m_des)
                        # methLink.append(m_link)
                        # methId.append(m_id)

                    if "source" == tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if'organization'in subele_text:
                                o_name = subele.text
                            if 'sourcecode' in subele_text:
                                o_code = subele.text
                                o_code = o_code.replace(" ", "")
                            if 'sourcedescription' in subele_text:
                                o_des = subele.text
                            if 'sourceLink' in subele_text:
                                o_link = subele.text
                            if 'contactname' in subele_text:
                                o_per_name = subele.text
                                try:
                                    o_per_fname = o_per_name.split(' ')[0]
                                    o_per_lname = o_per_name.split(' ')[1]
                                except:
                                    o_per_fname = o_per_name
                                    o_per_lname = o_per_name
                            if 'email'in subele_text:
                                o_per_email = subele.text
                            if 'phone'in subele_text:
                                o_per_phone = subele.text
                            if 'adress'in subele_text:
                                o_per_add = subele.text
                            if 'link'in subele_text:
                                o_per_link = subele.text
                            start_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        organizations.append((None, 'unknown', o_code, o_name, o_des, o_link, None))
                        people.append((None, o_per_fname, None, o_per_lname))
                        affliations.append([None, None, None, '1', start_date, None, o_per_phone, o_per_email,
                                            o_per_add, o_per_link])
                        org_per_name.append(o_per_name)
                        org_per_email.append(o_per_email)
                        org_per_phone.append(o_per_phone)
                        org_per_add.append(o_per_add)
                        org_per_link.append(o_per_link)
                        org_code.append(o_code)
                        org_des.append(o_des)
                        orglink.append(o_link)
                        org_name.append(o_name)

                    if 'sourceinfo' == tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()

                            if 'sitecode'in subele_text:
                                pass
                                # sam_code = subele.text
                            if 'sitename'in subele_text:
                                pass
                                # sam_name = subele.text
                            if 'sitedescription' in subele_text:
                                pass
                                # sam_description = subele.text
                            if 'featuregeometry' in subele_text:
                                pass
                                # sam_fea = subele.text
                            if 'latitude'in subele_text:
                                pass
                                # lat = subele.text
                            if 'longitude'in subele_text:
                                pass
                                # long = subele.text
                            if 'elevation_m' in subele_text:
                                pass
                                # sam_ele = subele.text
                            if 'verticaldatum' in subele_text:
                                pass
                                # sam_dat = subele.text
                            if 'latitude' in subele_text:
                                pass
                                # lat = subele.text
                            if 'longitude' in subele_text:
                                pass
                                # long = subele.text

                        # sam_geo_wkt = 'POINT('+long+','+lat+')'

                    if 'dataType' == tag:
                        pass
                        # datatype = element.text
                    if 'valueType' == tag:
                        pass
                        # valuetype = element.text
                    if "sampleMedium" == tag:
                        pass
                        # samplemedium = element.text
                    if "timescale" in tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if 'timesupport' in subele_text:
                                time_interval = subele.text
                            if 'unitname' in subele_text:
                                pass
                                # time_unit = subele.text
                            if 'unitabbreviation'in subele_text:
                                pass
                                # time_ab = subele.text
                            if 'unitcode' in subele_text:
                                time_code = subele.text
                elif 'value' == tag:
                    quality_str = 'quality'
                    method_str = 'method'
                    source_str = 'source'
                    if value_counter == 0:
                        l = element.keys()
                        for s in l:
                            if quality_str in s.lower():
                                quality_key = s
                            if method_str in s.lower():
                                method_key = s
                            if source_str in s.lower():
                                source_key = s
                    n = element.attrib['dateTime']
                    # utc_offset = element.attrib['timeOffset']
                    try:
                        quality = element.attrib[quality_key]
                    except:
                        quality = ''
                    try:
                        method = element.attrib[method_key]
                    except:
                        method = ''
                    try:
                        source = element.attrib[source_key]
                    except:
                        source = ''
                    v = element.text
                    if v == nodata:
                        v = None
                    else:
                        v = float(element.text)
                    result_entry = quality+'aa'+method+'aa'+source
                    result_entry = result_entry.replace(" ", "")
                    if result_entry not in result_total:
                        result_total.append(result_entry)
                        master_values.update({result_entry: []})
                    master_values[result_entry].append([n, v, quality, method, source, time_interval, time_code])
                    value_counter += 1
        print(methods)
        # quality_levels.extend((qualityCode, qualityDef, qualityExpl,qualityId))
        # methods.append((methCode,methName,methDes,methLink,methId))
        # organizations.append((orgCode,orgName,orgDes,orglink,orgPerName,orgPerEmail,orgPerPhone,orgPerAdd,orgPerLink))

        print("end of waterml data!!!!!!!!!!!!!!")
        # quality_sqlite = 'Insert Into ProcessingLevels(ProcessingLevelCode,Definition,Explanation) Values(?,?,?)'
        quality_sqlite = 'Insert Into ProcessingLevels Values(?,?,?,?)'
        method_sqlite = 'Insert Into Methods Values(?,?,?,?,?,?,?)'
        organizations_sqlite = 'Insert Into Organizations Values(?,?,?,?,?,?,?)'
        people_sqlite ='Insert Into People Values(?,?,?,?)'

        print(organizations)
    return_obj = {
        # 'data_values':master_values,
        'quality_levels': quality_levels,
        'methods': methods,
        'people': people,
        'organizations': organizations,
        # 'datatype' : datatype,
        # 'valuetype' : valuetype,
        # 'samplemedium' :samplemedium,
        # 'unitId':unitId,
        # 'unitAb' :unitAb,
        # 'varCode' :varCode,
        # 'speciation' :speciation,
        # 'sam_code':sam_code,
        # 'sam_name':sam_name,
        # 'sam_des':sam_des,
        # 'sam_fea':sam_fea,
        # 'sam_geo_wkt':sam_geo_wkt,
        # 'sam_ele':sam_ele,
        # 'sam_dat' :sam_dat,
        # 'lat': lat,
        # 'long':long,
        # 'time_interval':time_interval,
        # 'time_code':time_code,
        # 'time_ab':time_ab,
        # 'time_unit' :time_unit,
        # 'UTCOfset':UTCOfset
    }
    return return_obj


def parse_service_info():
    """
    Function appears in response ajax controller, but the function was not originally defined.
    
    Arguments:      []
    Returns:        [controllers_ajax.response]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    return None


def original_checker(xml_file):
    """


    Arguments:      [xml_file]
    Returns:        []
    Referenced By:  [create_odm2]
    References:     [get_version, parsing_test]
    Libraries:      [etree]
    """
    
    print(xml_file)
    tree = etree.parse(xml_file)
    root = tree.getroot()
    wml_version = get_version(root)
    print(wml_version)

    if wml_version == '1':

        # return parse_1_0_and_1_1(root)
        return parsing_test(root)

        # try:
        #     tree = etree.parse(xml_file)
        #     root = tree.getroot()
        #     wml_version = get_version(root)
        #     print wml_version
        #
        #     if wml_version == '1':
        #
        #         # return parse_1_0_and_1_1(root)
        #         return parsing_test(root)
        #
        #     # elif wml_version == '2.0':
        #     #     return parse_2_0(root)
        # except ValueError, e:
        #     errorReport("xml parse error")
        #     return read_error_file(xml_file)
        # except:
        #     errorReport("xml parse error")
        #     return read_error_file(xml_file)


def create_csv(file_name):
    """
    *** Function does not appear to be used. ***
    
    :param file_name: 
    :return: 
    """

    temp_dir = get_workspace()
    file_path_series = temp_dir + '/ODM2/'+file_name+'.csv'
    print(file_path_series)
    with open(file_path_series, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(0,1000000):
            spamwriter.writerow(['2007-01-01 12:30:00',str(i)])
            

def insert_odm2(data, title):
    """
    *** Function appears in create_odm2 utility, but is not used. ***
    
    :param data: 
    :param title: 
    :return: 
    """
    temp_dir = get_workspace()

    print("loading into database")
    odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'
    # odm_master = temp_dir+'/ODM2/ODM2_7series_test_addingValues.sqlite'
    odm_copy = temp_dir+'/ODM2/'+title+'.sqlite'
    shutil.copy(odm_master,odm_copy)
    # insert into TimeSeriesResultValues

    people_sqlite = 'Insert Into People Values(?,?,?,?)'
    value = [(None, 'Joe', None, "Black")]

    for entry in data:
        conn = sqlite3.connect(odm_copy, isolation_level=None)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION;")
        c.executemany(data[entry][0],data[entry][1]) #list of tuples
        c.execute("COMMIT;")
        conn.close()
        
        
def connect_wsdl_url(wsdl_url):
    """


    :param wsdl_url: 
    :return client: 
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
    
    
def create_odm2(file_path, title):
    """
    *** Function appears in create_layer ajax controller, but is not used. ***
    
    :param file_path: 
    :param title: 
    :return file path of filled odm2: 
    """
    print("odm2 stuff")
    temp_dir = get_workspace()
    series_number = parse_ts_layer(file_path, title, None)
    series_number = 1
    print(series_number)
    for series in range(0, series_number):
        file_path_series = temp_dir + '/id/timeserieslayer'+str(series)+'.xml'

        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-09-13-57929645.xml'
        file_path_series = temp_dir+'/id/timeserieslayer0.xml'  # multiple methods
        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-05-05-55046159.xml' #multiple quality

        data = original_checker(file_path_series)  # parses waterml file
        # odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'

        # insert_odm2(data,title) #inserts waterml data into ODM2 database
        # read and parse time series
        # copy blank odm2
        # take data and insert metadata and then dates and values
        # return file path of filled odm2
        

def get_hydroshare_resource(request, res_id, data_for_chart):
    """
    *** Function does not appear to be used. ***
    
    :param request: 
    :param res_id: 
    :param data_for_chart: 
    :return data_dic: 
    """
    error = False
    is_owner = False
    file_path = get_workspace() + '/resource_id'
    root_dir = file_path + '/' + res_id
    #
    # elif 'hydroshare_generic' in src:
    # target_url =  'https://www.hydroshare.org/django_irods/download/'+res_id+'/data/contents/
    # HIS_reference_timeseries.txt'
    # d

    try:
        shutil.rmtree(root_dir)
    except:
        nothing = None
    try:
        if controllers.use_hs_client_helper:
            hs = controllers.get_oauth_hs(request)
        else:
            hs = controllers.getOAuthHS(request)
        try:
            hs.getResource(res_id, destination=file_path, unzip=True)
            data_dir = root_dir + '/' + res_id + '/data/contents/'
            for subdir, dirs, files in os.walk(data_dir):
                for file in files:
                    if 'xml' in file:
                        data_file = data_dir + file
                        with open(data_file, 'r') as f:
                            # print f.read()
                            data = f.read()
                            # print data
                            f.close()
                            print(data)
                            try:
                                data = data.decode('latin-1')
                            except:
                                data = data
                            data_for_chart.update({str(file): data})

            # data_for_chart = {'bjo':'hello'}
            user = hs.getUserInfo()
            user1 = user['username']
            # resource = hs.getResourceList(user ='editor')
            resource = hs.getResourceList(owner = user1)
            for res in resource:
                # print res
                resource_id = res["resource_id"]
                # print resource_id
                if res_id == res["resource_id"]:
                    is_owner = True
            data_dic = {"data": data_for_chart, "owner": is_owner, "error": error}

            return data_dic
        except:
            error = "Unable to load resource"+res_id
            return error
    except Exception as inst:
        data_for_chart = 'You are not authorized to access this resource'
        owner = False
        error = True
        print('start')
        print(type(inst))
        print(inst.args)
        try:
            data_for_chart = str(inst)
        except:
            data_for_chart = "There was an error loading data for resource"+res_id
        print("end")
        
        
def get_app_base_uri(request):
    """
    *** Function does not appear to be used. ***
    
    :param request: 
    :return base_url: 
    """
    base_url = request.build_absolute_uri()
    if "?" in base_url:
        base_url = base_url.split("?")[0]
    return base_url
    
    
def get_resource_ids(page_request):
    """
    *** Function does not appear to be used. ***
    
    :param page_request: 
    :return resource_ids: 
    """
    resource_string = page_request.GET['res_id']  # retrieves IDs from url
    resource_ids = resource_string.split(',')  # splits IDs by commma
    return resource_ids


def find_zipped_url(page_request, res_id):
    """
    *** Function does not appear to be used. ***
    
    :param page_request: 
    :param res_id: 
    :return zipped_url: 
    """
    base_url = page_request.build_absolute_uri()
    if "?" in base_url:
        base_url = base_url.split("?")[0]
        zipped_url = base_url + "temp_waterml/" + res_id + ".xml"
        return zipped_url
        
        
def waterml_file_path(res_id):
    """
    *** Function does not appear to be used. ***
    
    :param res_id: 
    :return file_path: 
    """
    base_path = get_workspace()
    file_path = base_path + "/id/" + res_id
    if not file_path.endswith('.xml'):
        file_path += '.xml'
    return file_path


def file_unzipper(url_cuashi):
    """
    *** Function does not appear to be used. ***
    
    :param url_cuashi: 
    :return file_list: 
    """
    r = requests.get(url_cuashi)
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    file_list = z.namelist()
    for file in file_list:
        z.read(file)
    return file_list
    
    
def create_ts_layer_resource(title):
    """
    *** Function does not appear to be used. ***
    
    :param title: 
    :return: 
    """
    root = etree.Element('TimeSeriesLayerResource')
    doc = etree.ElementTree(root)
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/hydroshare/' + title + '.xml'
    out_file = open(file_temp_name, 'w')
    doc.write(out_file)


def append_ts_layer_resource(title, metadata):
    """
    *** Function appears in home controller, but it is not currently used. ***
    
    :param title: 
    :param metadata: 
    :return: 
    """
    print(metadata)
    lon = metadata['Lon']
    lat = metadata['Lat']
    # ref_type =metadata['ref_type']
    servicetype = metadata['service_type']
    # url = metadata['url']
    returntype = metadata['return_type']
    # print "adding to file"
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/hydroshare/' + title + '.xml'
    print(file_temp_name)
    tree = etree.parse(file_temp_name)

    root = tree.getroot()

    print(root)
    refts = etree.SubElement(root, 'refts')

    ref_type = etree.SubElement(refts, "RefTye")
    ref_type.text = 'WOF'

    service_type = etree.SubElement(refts, "service_type")
    service_type.text = servicetype

    url = etree.SubElement(refts, "url")
    url.text = 'www.hydroserver.com'

    return_type = etree.SubElement(refts, "return_type")
    return_type.text = returntype

    location = etree.SubElement(refts, "location")
    location.text = lon + ', ' + lat
    doc = etree.ElementTree(root)
    doc.write(file_temp_name)

'''
