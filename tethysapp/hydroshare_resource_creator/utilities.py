from __future__ import print_function
from datetime import datetime
import shutil
import requests
import sqlite3
import uuid
import traceback
import random
import time
import xmltodict
import os
import collections
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
from django.conf import settings
from .app import HydroshareResourceCreator
import json
import logging
import zipfile, io
import traceback
import sys
import pandas
from lxml import etree

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


def keys_exists(element, *keys):
    if type(element) is not dict:
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


def process_form_data(form_data):
    try:
        try:
            series_count = len(form_data['timeSeriesReferenceFile']['referencedTimeSeries'])
        except:
            form_data = {'timeSeriesReferenceFile': json.loads(form_data['timeSeriesReferenceFile'])}
            series_count = len(form_data['timeSeriesReferenceFile']['referencedTimeSeries'])
        for i in range(series_count):
            if not 'site' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site'] = {}
            if not 'variable' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable'] = {}
            if not 'requestInfo' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo'] = {}
            if not 'method' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method'] = {}
            if not 'siteName' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteName'] = ''
            if not 'siteCode' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteCode'] = ''
            if not 'variableName' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableName'] = ''
            if not 'variableCode' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableCode'] = ''
            if not 'networkName' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['networkName'] = ''
            if not 'refType' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['refType'] = ''
            if not 'serviceType' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['serviceType'] = ''
            if not 'url' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] = ''
            if not 'returnType' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['returnType'] = ''
            if not 'latitude' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['latitude'] = ''
            if not 'longitude' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['longitude'] = ''
            if not 'methodDescription' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodDescription'] = ''
            if not 'methodLink' in form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']:
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] = ''
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteName'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteName'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteCode'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['siteCode'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableName'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableName'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableCode'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['variable']['variableCode'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['networkName'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['networkName'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['refType'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['refType'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['serviceType'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['serviceType'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] = 'UNKNOWN'
            if str(form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'][-5:]) != '?WSDL':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['url'] += '?WSDL'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['returnType'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['requestInfo']['returnType'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['latitude'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['latitude'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['longitude'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['site']['longitude'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodDescription'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodDescription'] = 'UNKNOWN'
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] == '':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] = None
            if form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] == 'Unknown':
                form_data['timeSeriesReferenceFile']['referencedTimeSeries'][i]['method']['methodLink'] = None

        return form_data
    except:
        return "Data Processing Error"


def search_wml(unique_code, ns, tag_names, default_value):
    for tag_name in tag_names:
        if unique_code != "UNKNOWN" and list(unique_code.iter(ns + tag_name)):
            tag_value = list(unique_code.iter(ns + tag_name))[0].text
        else:
            tag_value = default_value
        if tag_value != default_value and tag_value is not None:
            return tag_value   
    if tag_value is None:
        tag_value = "UNKNOWN"
        if default_value is None:
            tag_value = None
    return tag_value


def create_ts_resource(res_data):

    refts_data = create_refts_resource(res_data)
    refts_path = refts_data["res_filepath"]

    print("Starting Transaction")

    user_workspace = get_user_workspace(res_data["request"])
    current_path = os.path.dirname(os.path.realpath(__file__))
    odm_master = os.path.join(current_path, "static_data/ODM2_master.sqlite")
    res_filepath = user_workspace + '/' + res_data['res_filename'] + '.odm2.sqlite'
    shutil.copy(odm_master, res_filepath)
    sql_connect = sqlite3.connect(res_filepath, isolation_level=None)
    conn = sql_connect.cursor()
    series_count = 0
    parse_status = []

    with open(refts_path, "rb") as refts_file:
        refts_data = json.load(refts_file)
        ts_list = refts_data["timeSeriesReferenceFile"]["referencedTimeSeries"]
        res_title = refts_data["timeSeriesReferenceFile"]["title"]
        res_abstract = refts_data["timeSeriesReferenceFile"]["abstract"]
    """
    odm_master = "ODM2_master.sqlite"
    shutil.copy(odm_master, out_path)
    sql_connect = sqlite3.connect(out_path, isolation_level=None)
    conn = sql_connect.cursor()
    """
    odm_tables = {
        "Datasets":                     """INSERT INTO Datasets (DataSetID, DataSetUUID, DataSetTypeCV, DataSetCode,
                                        DataSetTitle, DataSetAbstract)
                                        VALUES (NULL, ?, ?, ?, ?, ?)""",
        "SamplingFeatures":             """INSERT INTO SamplingFeatures (SamplingFeatureID, SamplingFeatureUUID,
                                        SamplingFeatureTypeCV, SamplingFeatureCode, SamplingFeatureName,
                                        SamplingFeatureDescription, SamplingFeatureGeotypeCV, FeatureGeometry,
                                        FeatureGeometryWKT, Elevation_m, ElevationDatumCV)
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "SpatialReferences":            """INSERT INTO SpatialReferences(SpatialReferenceID, SRSCode, SRSName,
                                        SRSDescription, SRSLink)
                                        VALUES (NULL, ?, ?, ?, ?)""",
        "Sites":                        """INSERT INTO Sites(SamplingFeatureID, SiteTypeCV, Latitude, Longitude,
                                        SpatialReferenceID)
                                        VALUES (?, ?, ?, ?, ?)""",
        "Methods":                      """INSERT INTO Methods(MethodID, MethodTypeCV, MethodCode, MethodName,
                                        MethodDescription, MethodLink) 
                                        VALUES (NULL, ?, ?, ?, ?, ?)""",
        "Variables":                    """INSERT INTO Variables (VariableID, VariableTypeCV, VariableCode,
                                        VariableNameCV, VariableDefinition, SpeciationCV, NoDataValue)
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?)""",
        "Units":                        """INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName,
                                        UnitsLink)
                                        VALUES (?, ?, ?, ?, ?)""",
        "ProcessingLevels":             """INSERT INTO ProcessingLevels(ProcessingLevelID, ProcessingLevelCode,
                                        Definition, Explanation)
                                        VALUES (NULL, ?, ?, ?)""",
        "People":                       """INSERT INTO People(PersonID, PersonFirstName, PersonLastName)
                                        VALUES (NULL, ?, ?)""",
        "Organizations":                """INSERT INTO Organizations (OrganizationID, OrganizationTypeCV,
                                        OrganizationCode, OrganizationName, OrganizationDescription, 
                                        OrganizationLink) 
                                        VALUES (NULL, ?, ?, ?, ?, ?)""",
        "Affiliations":                 """INSERT INTO Affiliations(AffiliationID, PersonID, OrganizationID,
                                        IsPrimaryOrganizationContact, AffiliationStartDate, PrimaryPhone, 
                                        PrimaryEmail) 
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?)""",
        "Actions":                      """INSERT INTO Actions(ActionID, ActionTypeCV, MethodID, BeginDateTime,
                                        BeginDateTimeUTCOffset, EndDateTime, EndDateTimeUTCOffset, ActionDescription) 
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)""",
        "ActionBy":                     """INSERT INTO ActionBy(BridgeID, ActionID, AffiliationID, IsActionLead,
                                        RoleDescription) 
                                        VALUES (NULL, ?, ?, ?, ?)""",
        "FeatureActions":               """INSERT INTO FeatureActions(FeatureActionID, SamplingFeatureID, ActionID)
                                        VALUES (NULL, ?, ?)""",
        "Results":                      """INSERT INTO Results(ResultID, ResultUUID, FeatureActionID, ResultTypeCV,
                                        VariableID, UnitsID, ProcessingLevelID, ResultDateTime, ResultDateTimeUTCOffset, 
                                        StatusCV, SampledMediumCV, ValueCount) 
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "TimeSeriesResults":            """INSERT INTO TimeSeriesResults(ResultID, IntendedTimeSpacing,
                                        IntendedTimeSpacingUnitsID, AggregationStatisticCV) 
                                        VALUES (?, ?, ?, ?)""",
        "TimeSeriesResultValues":       """INSERT INTO TimeSeriesResultValues(ValueID, ResultID, DataValue, ValueDateTime,
                                        ValueDateTimeUTCOffset, CensorCodeCV, QualityCodeCV, TimeAggregationInterval,
                                        TimeAggregationIntervalUnitsID) 
                                        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "DataSetsResults":              """INSERT INTO DataSetsResults(BridgeID, DataSetID, ResultID)
                                        Values (NULL, ?, ?)"""
    }
    
    for n, ts in enumerate(ts_list):
        error_code = False
        print("Preparing Series " + str(n + 1), end=" ")
        return_type = (ts["requestInfo"]["returnType"])
        site_code = ts["site"]["siteCode"]
        variable_code = ts["variable"]["variableCode"]
        start_date = ts["beginDate"]
        end_date = ts["endDate"]
        url = ts["requestInfo"]["url"]
        autho_token = ""
        
        # -------------------------- #
        #   Downloads WaterML Data   #
        # -------------------------- #

        try:
            if return_type == "WaterML 1.1":
                client = Client(url)
                values_result = client.service.GetValues(site_code, variable_code, start_date, end_date, autho_token)
                ns = "{http://www.cuahsi.org/waterML/1.1/}"
            elif return_type == "WaterML 1.0":
                headers = {'content-type': 'text/xml'}
                body = """<?xml version="1.0" encoding="utf-8"?>
                    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                      <soap:Body>
                        <GetValuesObject xmlns="http://www.cuahsi.org/his/""" + "1.0" + """/ws/">
                          <location>""" + site_code + """</location>
                          <variable>""" + variable_code + """</variable>
                          <startDate>""" + start_date + """</startDate>
                          <endDate>""" + end_date + """</endDate>
                          <authToken>""" + autho_token +"""</authToken>
                        </GetValuesObject>
                      </soap:Body>
                    </soap:Envelope>"""
                body = body.encode('utf-8')
                response = requests.post(url, data=body, headers=headers)
                values_result = response.content
                ns = "{http://www.cuahsi.org/waterML/1.0/}"
        except:
            print("[FAILED TO DOWNLOAD WML]")
            sql_connect.rollback()
            continue
            
        
        # --------------------------- #
        #   Validates WaterML files   #
        # --------------------------- #
        
        try:
            """
            schema_file = "wml_1_1_schema.xsd"
            with open(schema_file, "rb") as schema:
                xmlschema_doc = etree.parse(schema)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            
            if str(xmlschema.validate(etree.fromstring(values_result))) is True:
                #print("[ VALID ][", end="")
                print("[", end="")
            else:
                #print("[INVALID][", end="")
                print("[", end="")
            """
            #print("Valid WML: " + str(xmlschema.validate(etree.fromstring(values_result))))
            #error_log = str((xmlschema.error_log)).split("<string>")
            #for x in list(filter(lambda k: 'timeOffset' not in k, error_log))[1:]:
            #    print(x)
            wml_ts = etree.fromstring(values_result)
            #if n + 1 == 11:
            #    print(values_result)
            if not list(wml_ts.iter(ns + "values")):
                print("No timeseries data found]")
                continue
            if len(list(list(wml_ts.iter(ns + "values"))[0].iter(ns + "value"))) == 0:
                print("No timeseries data found]")
                continue
            '''
            with open('validation_results.txt', 'a') as the_file:
                for x in list(filter(lambda k: 'timeOffset' not in k, error_log))[1:]:
                    the_file.write(str(x) + '\n')
            '''
        except:
            print("Unable to validate WML]")
            continue
        
        # ------------------------------------ #
        #   Extracts Data for Datasets Table   #
        # ------------------------------------ #
        for c in range(2):
            try:
                if c == 0:
                    ds_dataset_code = 1
                else:
                    ds_dataset_code = "UNKNOWN"
                conn.execute('SELECT * FROM Datasets WHERE DataSetCode = ?', (ds_dataset_code, ))
                row = conn.fetchone()
                if row is None:
                    ds_dataset_uuid = str(uuid.uuid4())
                    ds_dataset_type_cv = ("singleTimeSeries" if len(ts_list) == 1 else "multiTimeSeries") if ds_dataset_code != "UNKNOWN" else "other"
                    ds_dataset_code = ds_dataset_code if ds_dataset_code != "UNKNOWN" else "UNKNOWN"
                    ds_dataset_title = res_title if ds_dataset_code != "UNKNOWN" else "UNKNOWN"
                    ds_dataset_abstract = res_abstract if ds_dataset_code != "UNKNOWN" else "UNKNOWN"
                    dataset = [ds_dataset_uuid, ds_dataset_type_cv, ds_dataset_code, ds_dataset_title, ds_dataset_abstract]  
                    conn.execute(odm_tables["Datasets"], dataset)
                    ds_id = conn.lastrowid
                else:
                    ds_id = row[0]
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][DATASETS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # -------------------------------------------- #
        #   Extracts Data for SamplingFeatures Table   #
        # -------------------------------------------- #
        for c in range(2):
            try:
                if c == 0:
                    sf_source_info = list(wml_ts.iter(ns + "sourceInfo"))
                    sf_site_code = search_wml(sf_source_info[0], ns, ["siteCode"], "UNKNOWN")
                else:
                    sf_site_code = "UNKNOWN"
                conn.execute('SELECT * FROM SamplingFeatures WHERE SamplingFeatureCode = ?', (sf_site_code, ))
                row = conn.fetchone()
                if row is None:
                    sf_exists = False
                    sf_samplingfeature_uuid = str(uuid.uuid4()) if sf_site_code != "UNKNOWN" else "UNKNOWN"
                    sf_samplingfeature_type_cv = "site" if sf_site_code != "UNKNOWN" else "unknown"
                    sf_samplingfeature_code = sf_site_code if sf_site_code != "UNKNOWN" else "UNKNOWN"
                    sf_samplingfeature_name = search_wml(sf_source_info[0], ns, ["siteName"], "UNKNOWN") if sf_site_code != "UNKNOWN" else "UNKNOWN"
                    sf_samplingfeature_description = "UNKNOWN"
                    sf_samplingfeature_geotype_cv = "point" if sf_site_code != "UNKNOWN" else "notApplicable"
                    sf_feature_geometry = "UNKNOWN"
                    sf_latitude = search_wml(sf_source_info[0], ns, ["latitude"], "UNKNOWN")
                    sf_longitude = search_wml(sf_source_info[0], ns, ["longitude"], "UNKNOWN")
                    sf_feature_geometry_wkt = "POINT (" + str(sf_longitude) + " " + str(sf_latitude) + ")" if sf_site_code != "UNKNOWN" else "UNKNOWN"
                    sf_elevation_m = search_wml(sf_source_info[0], ns, ["elevation_m"], None) if sf_site_code != "UNKNOWN" else None
                    sf_elevation_datum_cv = search_wml(sf_source_info[0], ns, ["verticalDatum"], "Unknown") if sf_site_code != "UNKNOWN" else "Unknown"
                    sampling_feature = [sf_samplingfeature_uuid, sf_samplingfeature_type_cv, sf_samplingfeature_code, sf_samplingfeature_name,
                                        sf_samplingfeature_description, sf_samplingfeature_geotype_cv, sf_feature_geometry,
                                        sf_feature_geometry_wkt, sf_elevation_m, sf_elevation_datum_cv]
                    conn.execute(odm_tables["SamplingFeatures"], sampling_feature)
                    sf_sampling_feature_id = conn.lastrowid
                else:
                    sf_exists = True
                    sf_sampling_feature_id = row[0]
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:        
            print("][SAMPLINGFEATURES FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # --------------------------------------------- #
        #   Extracts Data for SpatialReferences Table   #
        # --------------------------------------------- #
        for c in range(2):
            try:
                if sf_exists is False:
                    sr_srs_code = "UNKNOWN" if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    sr_srs_name = "UNKNOWN" if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    sr_srs_description = "The spatial reference is unknown" if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    sr_srs_link = "UNKNOWN" if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    spatialreference = [sr_srs_code, sr_srs_name, sr_srs_description, sr_srs_link]
                    conn.execute(odm_tables["SpatialReferences"], spatialreference)
                    sr_spatial_reference_id = conn.lastrowid
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:       
            print("][SPATIALREFERENCES FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # --------------------------------- #
        #   Extracts Data for Sites Table   #
        # --------------------------------- #
        for c in range(2):
            if True is True:
                if sf_exists is False:
                    st_sampling_feature_id = sf_sampling_feature_id
                    st_site_type_cv = search_wml(sf_source_info[0], ns, ["siteProperty"], "unknown") if (sf_site_code != "UNKNOWN" or c != 1) else "unknown"
                    st_latitude = search_wml(sf_source_info[0], ns, ["latitude"], "UNKNOWN") if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    st_longitude = search_wml(sf_source_info[0], ns, ["longitude"], "UNKNOWN") if (sf_site_code != "UNKNOWN" or c != 1) else "UNKNOWN"
                    st_spatial_reference_id = sr_spatial_reference_id
                    site = [st_sampling_feature_id, st_site_type_cv, st_latitude, st_longitude, st_spatial_reference_id]
                    conn.execute(odm_tables["Sites"], site)
                break
            else:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][SITES FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ------------------------------------- #
        #   Extracts Data for Variables Table   #
        # ------------------------------------- #
        for c in range(2):
            try:
                if c == 0:
                    vr_variable = list(wml_ts.iter(ns + "variable"))
                    vr_variable_code = search_wml(vr_variable[0], ns, ["variableCode", "VariableCode"], "UNKNOWN") if len(vr_variable) != 0 else "UNKNOWN"
                else:
                    vr_variable_code = "UNKNOWN"
                conn.execute('SELECT * FROM Variables WHERE VariableCode = ?', (vr_variable_code, ))
                row = conn.fetchone()
                if row is None:
                    vr_variable_type_cv = search_wml(vr_variable[0], ns, ["generalCategory", "GeneralCategory"], "Unknown") if vr_variable_code != "UNKNOWN" else "Unknown"
                    vr_variable_code = vr_variable_code if vr_variable_code != "UNKNOWN" else "UNKNOWN"
                    vr_variable_name_cv = search_wml(vr_variable[0], ns, ["variableName", "VariableName"], "Unknown") if vr_variable_code != "UNKNOWN" else "Unknown"
                    vr_variable_definition = search_wml(vr_variable[0], ns, ["variableDescription", "VariableDescription"], "UNKNOWN") if vr_variable_code != "UNKNOWN" else "UNKNOWN"
                    vr_speciation_cv = search_wml(vr_variable[0], ns, ["speciation", "Speciation"], "unknown") if vr_variable_code != "UNKNOWN" else "unknown"
                    vr_no_data_value = search_wml(vr_variable[0], ns, ["noDataValue", "NoDataValue"], None) if vr_variable_code != "UNKNOWN" else None
                    variable = [vr_variable_type_cv, vr_variable_code, vr_variable_name_cv, vr_variable_definition, vr_speciation_cv, vr_no_data_value]
                    conn.execute(odm_tables["Variables"], variable)
                    vr_variable_id = conn.lastrowid
                else:
                    vr_variable_id = row[0]
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][VARIABLES FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # --------------------------------- #
        #   Extracts Data for Units Table   #
        # --------------------------------- #
        for c in range(2):
            try:
                if c == 0:
                    ut_variable = list(wml_ts.iter(ns + "variable"))
                    ut_unit = ut_variable[0].find(ns + "unit") if len(ut_variable) != 0 else None
                    ut_unit_code = search_wml(ut_unit, ns, ["unitCode", "UnitCode", "unitsCode", "UnitsCode"], 9999) if ut_unit is not None else 9999
                else:
                    ut_unit_code = 9999
                conn.execute('SELECT * FROM Units WHERE UnitsID = ?', (ut_unit_code,))
                row = conn.fetchone()
                if row is None:
                    ut_units_id = ut_unit_code
                    ut_units_type_cv = search_wml(ut_unit[0], ns, ["unitType", "unitsType", "UnitType", "UnitsType"], "other") if ut_unit_code != 9999 else "other"
                    ut_units_abbreviation = search_wml(ut_unit, ns, ["unitAbbreviation", "unitsAbbreviation", "UnitAbbreviation", "UnitsAbbreviation"], "UNKNOWN") if ut_unit_code != 9999 else "UNKNOWN"
                    ut_units_name = search_wml(ut_unit[0], ns, ["unitName", "unitsName", "UnitName", "UnitsName"], "UNKNOWN") if ut_unit_code != 9999 else "UNKNOWN"
                    ut_units_link = search_wml(ut_unit[0], ns, ["unitLink", "unitsLink", "UnitLink", "UnitsLink"], "UNKNOWN") if ut_unit_code != 9999 else "UNKNOWN"
                    units = [ut_units_id, ut_units_type_cv, ut_units_abbreviation, ut_units_name, ut_units_link]
                    conn.execute(odm_tables["Units"], units)
                    ut_units_id = conn.lastrowid
                else:
                    ut_units_id = row[0]
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][UNITS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")

        # ------------------------------------ #
        #    Extracts Data for Time Spacing    #
        # ------------------------------------ #
        for c in range(2):
            try:
                if c == 0:
                    tu_timeScale = list(wml_ts.iter(ns + "timeScale"))
                    tu_unit_code = search_wml(tu_timeScale[0], ns, ["unitCode", "UnitCode", "unitsCode", "UnitsCode"], 9999) if len(tu_timeScale) != 0 else 9999
                else:
                    tu_unit_code = 9999
                conn.execute('SELECT * FROM Units WHERE UnitsID = ?', (tu_unit_code,))
                row = conn.fetchone()
                if row is None:
                    tu_units_id = tu_unit_code
                    tu_units_type_cv = search_wml(tu_timeScale[0], ns, ["unitType", "unitsType", "UnitType", "UnitsType"], "other") if tu_unit_code != 9999 else "other"
                    tu_units_abbreviation = search_wml(tu_timeScale[0], ns, ["unitAbbreviation", "unitsAbbreviation", "UnitAbbreviation", "UnitsAbbreviation"], "UNKNOWN") if tu_unit_code != 9999 else "UNKNOWN"
                    tu_units_name = search_wml(tu_timeScale[0], ns, ["unitName", "unitsName", "UnitName", "UnitsName"], "UNKNOWN") if tu_unit_code != 9999 else "UNKNOWN"
                    tu_units_link = search_wml(tu_timeScale[0], ns, ["unitLink", "unitsLink", "UnitLink", "UnitsLink"], "UNKNOWN") if tu_unit_code != 9999 else "UNKNOWN"
                    time_units = [tu_units_id, tu_units_type_cv, tu_units_abbreviation, tu_units_name, tu_units_link]
                    conn.execute(odm_tables["Units"], time_units)
                    tu_units_id = conn.lastrowid
                else:
                    tu_units_id = row[0]  
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][TIME SPACING FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ----------------------------------- #
        #   Extracts Data for Methods Table   #
        # ----------------------------------- #
        for c in range(2):
            try:
                if c == 0 and list(wml_ts.iter(ns + "method")):
                    md_methods = list(wml_ts.iter(ns + "method"))
                else:
                    md_methods = ["UNKNOWN"]
                md_code_list = []
                md_id_list = []
                for md_method in md_methods:
                    md_method_code = search_wml(md_method, ns, ["methodCode", "MethodCode"], "UNKNOWN") if md_method != "UNKNOWN" else "UNKNOWN"
                    conn.execute('SELECT * FROM Methods WHERE MethodCode = ?', (md_method_code, ))
                    row = conn.fetchone()
                    if row is None:
                        md_method_type_cv = "Observation" if md_method_code != "unknown" else "unknown"
                        md_method_code = md_method_code if md_method_code != "UNKNOWN" else "UNKNOWN"
                        md_method_name = md_method_code if md_method_code != "UNKNOWN" else "UNKNOWN"
                        md_method_description = search_wml(md_method, ns, ["methodDescription", "MethodDescription"], "UNKNOWN") if md_method_code != "UNKNOWN" else "UNKNOWN"
                        md_method_link = search_wml(md_method, ns, ["methodLink", "MethodLink"], "UNKNOWN") if md_method_code != "UNKNOWN" else "UNKNOWN"
                        method = [md_method_type_cv, md_method_code, md_method_name, md_method_description, md_method_link]
                        conn.execute(odm_tables["Methods"], method)
                        md_method_id = conn.lastrowid
                        md_id_list.append(md_method_id)
                        md_code_list.append(md_method_code)
                    else:
                        md_code_list.append(row[2])
                        md_id_list.append(row[0])
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][METHODS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # -------------------------------------------- #
        #   Extracts Data for ProcessingLevels Table   #
        # -------------------------------------------- #
        for c in range(2):
            try:
                if c == 0 and list(wml_ts.iter(ns + "qualityControlLevel")):
                    pl_processing_levels = list(wml_ts.iter(ns + "qualityControlLevel"))
                else:
                    pl_processing_levels = ["UNKNOWN"]
                pl_code_list = []
                pl_id_list = []
                for pl_processing_level in pl_processing_levels:
                    pl_processing_level_code = search_wml(pl_processing_level, ns, ["qualityControlLevelCode"], "UNKNOWN") if pl_processing_level != "UNKNOWN" else "UNKNOWN"
                    conn.execute('SELECT * FROM ProcessingLevels WHERE ProcessingLevelCode = ?', (pl_processing_level_code, ))
                    row = conn.fetchone()
                    if row is None:
                        pl_processing_level_code = pl_processing_level_code
                        pl_definition = search_wml(pl_processing_level, ns, ["definition"], "UNKNOWN") if pl_processing_level_code != "UNKNOWN" else "UNKNOWN"
                        pl_explanation = search_wml(pl_processing_level, ns, ["explanation"], "UNKNOWN") if pl_processing_level_code != "UNKNOWN" else "UNKNOWN"
                        processing_levels = [pl_processing_level_code, pl_definition, pl_explanation]
                        conn.execute(odm_tables["ProcessingLevels"], processing_levels)
                        pl_processing_level_id = conn.lastrowid
                        pl_id_list.append(pl_processing_level_id)
                        pl_code_list.append(pl_processing_level_code)
                    else:
                        pl_code_list.append(row[2])
                        pl_id_list.append(row[0])
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][PROCESSING LEVELS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ---------------------------------- #
        #   Extracts Data for People Table   #
        # ---------------------------------- #
        for c in range(2):
            try:
                if c == 0 and list(wml_ts.iter(ns + "source")):
                    pp_sources = list(wml_ts.iter(ns + "source"))
                else:
                    pp_sources = ["UNKNOWN"]
                pp_id_list = []
                for pp_source in pp_sources:
                    pp_person_name = search_wml(pp_source, ns, ["contactName"], "UNKNOWN") if pp_source != "UNKNOWN" else "UNKNOWN"
                    conn.execute('SELECT * FROM People WHERE PersonFirstName = ?', (pp_person_name, ))
                    row = conn.fetchone()
                    if row is None:
                        pp_person_first_name = pp_person_name
                        pp_person_last_name = pp_person_name
                        person = [pp_person_first_name, pp_person_last_name]
                        conn.execute(odm_tables["People"], person)
                        pp_id_list.append(conn.lastrowid)
                    else:
                        pp_id_list.append(row[0])
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][PEOPLE FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")

        # ----------------------------------------- #
        #   Extracts Data for Organizations Table   #
        # ----------------------------------------- #
        for c in range(2):
            try:
                if c == 0 and list(wml_ts.iter(ns + "source")):
                    og_sources = list(wml_ts.iter(ns + "source"))
                else:
                    og_sources = ["UNKNOWN"]
                og_code_list = []
                og_id_list = []
                for og_source in og_sources:
                    og_organization_code = search_wml(og_source, ns, ["sourceCode"], "UNKNOWN") if og_source != "UNKNOWN" else "UNKNOWN"
                    conn.execute('SELECT * FROM Organizations WHERE OrganizationCode = ?', (og_organization_code, ))
                    row = conn.fetchone()
                    if row is None:
                        og_organization_type_cv = "unknown"
                        og_organization_code = og_organization_code
                        og_organization_name = search_wml(og_source, ns, ["organization"], "UNKNOWN") if og_source != "UNKNOWN" else "UNKNOWN"
                        og_organization_description = search_wml(og_source, ns, ["sourceDescription"], "UNKNOWN") if og_source != "UNKNOWN" else "UNKNOWN"
                        og_organization_link = search_wml(og_source, ns, ["sourceLink"], "UNKNOWN") if og_source != "UNKNOWN" else "UNKNOWN"
                        organization = [og_organization_type_cv, og_organization_code, og_organization_name, og_organization_description, og_organization_link]
                        conn.execute(odm_tables["Organizations"], organization)
                        og_organization_id = conn.lastrowid
                        og_id_list.append(og_organization_id)
                        og_code_list.append(og_organization_code)
                    else:
                        og_id_list.append(row[0])
                        og_code_list.append(row[2])
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][ORGANIZATIONS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ---------------------------------------- #
        #   Extracts Data for Affiliations Table   #
        # ---------------------------------------- #
        for c in range(2):
            try:
                if c == 0 and list(wml_ts.iter(ns + "source")):
                    af_sources = list(wml_ts.iter(ns + "source"))
                else:
                    af_sources = ["UNKNOWN"]
                af_id_list = []
                for n, af_source in enumerate(af_sources):
                    og_organization_code = search_wml(af_source, ns, ["sourceCode"], "UNKNOWN") if og_source != "UNKNOWN" else "UNKNOWN"
                    conn.execute('SELECT * FROM Affiliations WHERE PersonID = ? AND OrganizationID = ?', (pp_id_list[n], og_id_list[n]))
                    row = conn.fetchone()
                    if row is None:
                        af_person_id = pp_id_list[n]
                        af_organization_id = og_id_list[n]
                        af_is_primary_organization_contact = "UNKNOWN"
                        af_affiliation_start_date = "UNKNOWN"
                        af_primary_phone = search_wml(af_source, ns, ["phone"], "UNKNOWN") if af_source != "UNKNOWN" else "UNKNOWN"
                        af_primary_email = search_wml(af_source, ns, ["email"], "UNKNOWN") if af_source != "UNKNOWN" else "UNKNOWN"
                        affiliation = [af_person_id, af_organization_id, af_is_primary_organization_contact, af_affiliation_start_date, af_primary_phone, af_primary_email]
                        conn.execute(odm_tables["Affiliations"], affiliation)
                        af_affiliation_id = conn.lastrowid
                        af_id_list.append(af_affiliation_id)
                    else:
                        af_id_list.append(row[0])
                break
            except:
                if c == 1:
                    error_code = True
        if error_code is True:
            print("][AFFILIATIONS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ----------------------------------- #
        #   Extracts Data for Actions Table   #
        # ----------------------------------- #
        try:
            ac_list = []
            for md_id in md_id_list:
                result_values = []
                rv_values = list(wml_ts.iter(ns + "values"))[0]
                rv_values_list = list(rv_values.iter(ns + "value"))
                for rv_value in rv_values_list:
                    if rv_value.get("methodCode") == md_code_list[md_id_list.index(md_id)] or rv_value.get("methodCode") is None:
                        result_values.append(rv_value)
                ac_action_type_cv = "observation"
                ac_method_id = md_id
                ac_begin_datetime = result_values[0].get("dateTime") if result_values[0].get("dateTime") and result_values else "UNKNOWN"
                ac_begin_datetime_offset = result_values[0].get("timeOffset") if result_values[0].get("timeOffset") and result_values else "UNKNOWN"
                ac_end_datetime = result_values[-1].get("dateTime") if result_values[-1].get("dateTime") and result_values else "UNKNOWN"
                ac_end_datetime_offset = result_values[-1].get("dateTime") if result_values[-1].get("timeOffset") and result_values else "UNKNOWN"
                ac_action_description = "An observation action that generated a time series result."
                action = [ac_action_type_cv, ac_method_id, ac_begin_datetime, ac_begin_datetime_offset, ac_end_datetime, ac_end_datetime_offset, ac_action_description]
                conn.execute(odm_tables["Actions"], action)
                ac_action_id = conn.lastrowid
                ac_list.append(ac_action_id)
        except:
            print("][ACTIONS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ------------------------------------ #
        #   Extracts Data for ActionBy Table   #
        # ------------------------------------ #
        
        try:
            for ac_id in ac_list:
                ab_action_id = ac_id
                ab_affiliation_id = af_id_list[0]
                ab_is_action_lead = 1
                ab_role_description = "Responsible party"
                actionby = [ab_action_id, ab_affiliation_id, ab_is_action_lead, ab_role_description]
                conn.execute(odm_tables["ActionBy"], actionby)
        except:
            print("][ACTIONBY FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ------------------------------------------ #
        #   Extracts Data for FeatureActions Table   #
        # ------------------------------------------ #
        try:
            fa_list = []
            for ac_id in ac_list:
                fa_sampling_feature_id = sf_sampling_feature_id
                fa_action_id = ac_id       
                featureaction = [fa_sampling_feature_id, fa_action_id]
                conn.execute(odm_tables["FeatureActions"], featureaction)
                fa_feature_action_id = conn.lastrowid
                fa_list.append(fa_feature_action_id)
        except:
            print("][FEATUREACTIONS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ------------------------------------- #
        #    Extracts Data for Results Table    #
        # ------------------------------------- #
        try:
            rt_id_list = []
            for i, fa_id in enumerate(fa_list):
                result_values = []
                rv_values = list(wml_ts.iter(ns + "values"))[0]
                rv_values_list = list(rv_values.iter(ns + "value"))
                for rv_value in rv_values_list:
                    if rv_value.get("methodCode") == md_code_list[md_id_list.index(md_id)] or rv_value.get("methodCode") is None:
                        result_values.append(rv_value)
                rt_result_uuid = str(uuid.uuid4())
                rt_feature_action_id = fa_id
                rt_result_type_cv = "timeSeriesCoverage"
                rt_variable_id = vr_variable_id
                rt_units_id = ut_units_id
                rt_processing_level_id = pl_id_list[0] if pl_id_list else "UNKNOWN"
                rt_result_datetime = result_values[0].get("dateTime") if result_values[0].get("dateTime") else "UNKNOWN"
                rt_result_datetime_utc_offset = result_values[0].get("timeOffset") if result_values[0].get("dateTime") else "UNKNOWN"
                rt_status_cv = "unknown"
                rt_sampled_medium_cv = search_wml(vr_variable[0], ns, ["sampleMedium"], "UNKNOWN") if vr_variable_code != "UNKNOWN" else "UNKNOWN"
                rt_value_count = len(rv_values_list)
                result = [rt_result_uuid, rt_feature_action_id, rt_result_type_cv, rt_variable_id, rt_units_id, rt_processing_level_id, rt_result_datetime,
                          rt_result_datetime_utc_offset, rt_status_cv, rt_sampled_medium_cv, rt_value_count]
                conn.execute(odm_tables["Results"], result)
                rt_result_id = conn.lastrowid
                rt_id_list.append(rt_result_id)
        except:
            print("][RESULTS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ----------------------------------------------- #
        #    Extracts Data for TimeSeriesResults Table    #
        # ----------------------------------------------- #
        try:
            for rt_id in rt_id_list:
                tr_result_id = rt_id
                tr_intended_time_spacing = 30
                tr_time_units_id = tu_units_id
                tr_aggregation_statistic_cv = "Unknown"
                timeseries_result = [tr_result_id, tr_intended_time_spacing, tr_time_units_id, tr_aggregation_statistic_cv]
                conn.execute(odm_tables["TimeSeriesResults"], timeseries_result)
        except:
            print("][TIMESERIESRESULTS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # ---------------------------------------------------- #
        #    Extracts Data for TimeSeriesResultValues Table    #
        # ---------------------------------------------------- #
        try:
            conn.execute("BEGIN TRANSACTION;")
            result_values = []
            rv_values = list(wml_ts.iter(ns + "values"))[0]
            rv_values_list = list(rv_values.iter(ns + "value"))
            for rv_value in rv_values_list:
                rv_result_id = rt_id_list[md_code_list.index(rv_value.get("methodCode")) if rv_value.get("methodCode") in md_code_list else 0]
                rv_data_value = rv_value.text
                rv_value_date_time = rv_value.get("dateTime")
                rv_value_date_time_utc_offset = rv_value.get("timeOffset", "UNKNOWN")
                rv_censor_code_cv = rv_value.get("censorCode", "unknown")
                rv_quality_code_cv = rv_value.get("qualityControlLevelCode", "unknown")
                rv_time_aggregation_interval = "UNKNOWN"
                rv_time_aggregation_interval_units_id = "UNKNOWN"
                result_values.append((rv_result_id, rv_data_value, rv_value_date_time, rv_value_date_time_utc_offset, rv_censor_code_cv, 
                                      rv_quality_code_cv, rv_time_aggregation_interval, rv_time_aggregation_interval_units_id))     
            conn.executemany(odm_tables["TimeSeriesResultValues"], result_values)   
                             
        except:
            print("][TIMESERIESRESULTVALUES FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # -------------------------------------------- #
        #    Extracts Data for DataSetResults Table    #
        # -------------------------------------------- #
        try:
            for rt_id in rt_id_list:
                dr_dataset_id = ds_id
                dr_result_id = rt_id     
                dataset_result = [dr_dataset_id, dr_result_id]
                conn.execute(odm_tables["DataSetsResults"], dataset_result)
        except:
            print("][DATASETRESULTS FAILED]")
            sql_connect.rollback()
            continue
        print("*", end="")
        
        # -------------------- #
        #    Commits Changes   #
        # -------------------- #
        try:
            #conn.execute("COMMIT;")
            sql_connect.commit()
        except:
            print("][COMMIT FAILED]")
            sql_connect.rollback()
            continue
        print("*][SUCCESS]")
        series_count += 1

    print("Database Created Successfully")
    print(series_count)

    return_obj = {
        "res_type": "CompositeResource",
        "res_filepath": res_filepath,
        "file_extension": ".odm2.sqlite",
        "series_count": series_count,
        "parse_status": parse_status
    }

    return return_obj


def create_refts_resource(res_data):

    user_workspace = get_user_workspace(res_data["request"])
    json_data = json.loads(res_data['form_body'])["timeSeriesReferenceFile"]
    series_count = 0
    layer = []
    parse_status = []
    res_filepath = user_workspace + '/' + res_data['res_filename'] + '.refts.json'

    try:
        for selected_id in res_data["selected_resources"]:
            layer.append(json_data['referencedTimeSeries'][selected_id])
    except:
        json_data = json.loads(json_data)
        for selected_id in res_data["selected_resources"]:
            layer.append(json_data['referencedTimeSeries'][selected_id])


    json_dict = {
        "timeSeriesReferenceFile": {
            "fileVersion": json_data["fileVersion"],
            "title": res_data["res_title"],
            "symbol": json_data["symbol"],
            "abstract": res_data["res_abstract"],
            "keyWords": res_data["res_keywords"],
            "referencedTimeSeries" : []
        }
    }

    for refts in layer:
        series_count += 1
        sub = {
            "requestInfo": {
                "serviceType": refts["requestInfo"]["serviceType"],
                "refType": refts["requestInfo"]["refType"],
                "returnType": refts["requestInfo"]["returnType"],
                "networkName": refts["requestInfo"]["networkName"],
                "url": refts["requestInfo"]["url"]
            },
            "sampleMedium": refts["sampleMedium"],
            "valueCount": refts["valueCount"],
            "beginDate": refts["beginDate"],
            "endDate": refts["endDate"],
            "site": {
                "siteCode": refts["site"]["siteCode"],
                "siteName": refts["site"]["siteName"],
                "latitude": refts["site"]["latitude"],
                "longitude": refts["site"]["longitude"]
            },
            "variable": {
                "variableCode": refts["variable"]["variableCode"],
                "variableName": refts["variable"]["variableName"]
            },
            "method": {
                "methodDescription": refts["method"]["methodDescription"],
                "methodLink": refts["method"]["methodLink"]
            }
        }
        json_dict["timeSeriesReferenceFile"]["referencedTimeSeries"].append(sub)
        parse_status.append("SUCCESS")

    with open(res_filepath, 'w') as res_file:
        json.dump(json_dict, res_file, sort_keys=True, indent=4, separators=(',', ': '))

    return_obj = {"res_type": "CompositeResource",
                  "res_filepath": res_filepath,
                  "file_extension": ".refts.json",
                  "series_count": series_count,
                  "parse_status": parse_status
                  }

    return return_obj
