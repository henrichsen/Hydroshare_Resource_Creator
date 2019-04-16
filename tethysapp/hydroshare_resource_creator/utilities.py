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
import itertools
import os
import collections
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from xml.sax._exceptions import SAXParseException
from django.conf import settings
from .app import HydroshareResourceCreator
import json
from logging import getLogger
import zipfile, io
import traceback
import sys
import pandas
from lxml import etree

logger = getLogger('django')
use_hs_client_helper = True
try:
    from tethys_services.backends.hs_restclient_helper import get_oauth_hs
except:
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
        client = ""
    except ValueError:
        raise Exception('Invalid url')  # ought to be a 400, but no page implemented for that
    except SAXParseException:
        raise Exception("The correct url format ends in '.asmx?WSDL'.")
    except:
        raise Exception("Unexpected error")

    return client


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


def search_wml(unique_code, ns, tag_names, default_value=None, attr=None, get_tree=False, mult=False):
    if unique_code is None:
        return default_value
    if get_tree:
        for tag_name in tag_names:
            if list(unique_code.iter(ns + tag_name)) and mult:
                tree = list(unique_code.iter(ns + tag_name))
            elif list(unique_code.iter(ns + tag_name)) and not mult:
                tree = list(unique_code.iter(ns + tag_name))[0]
            elif not list(unique_code.iter(ns + tag_name)) and mult:
                tree = []
            elif not list(unique_code.iter(ns + tag_name)) and not mult:
                tree = None
            else:
                tree = None
            if tree != None and tree != []:
                return tree
        return tree
    else:
        for tag_name in tag_names:
            if list(unique_code.iter(ns + tag_name)) and not mult and attr == None:
                tag_value = list(unique_code.iter(ns + tag_name))[0].text
            elif list(unique_code.iter(ns + tag_name)) and not mult and attr != None:
                tag_value = list(unique_code.iter(ns + tag_name))[0].get(attr)
            elif list(unique_code.iter(ns + tag_name)) and mult and attr == None:
                tag_value = [i.text for i in list(unique_code.iter(ns + tag_name))]
            elif list(unique_code.iter(ns + tag_name)) and mult and attr != None:
                tag_value = [i.get(attr) for i in list(unique_code.iter(ns + tag_name))]
            elif not list(unique_code.iter(ns + tag_name)) and not mult:
                tag_value = None
            elif not list(unique_code.iter(ns + tag_name)) and mult:
                tag_value = []
            else:
                tag_value = None
            if tag_value != None and tag_value != []:
                return tag_value
        return default_value


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
    curs = sql_connect.cursor()
    series_count = 0
    parse_status = []

    with open(refts_path, "rb") as refts_file:
        refts_data = json.load(refts_file)
        ts_list = refts_data["timeSeriesReferenceFile"]["referencedTimeSeries"]
        res_title = refts_data["timeSeriesReferenceFile"]["title"]
        res_abstract = refts_data["timeSeriesReferenceFile"]["abstract"]
    
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
                wml_version = "1.1"
                ns = "{http://www.cuahsi.org/waterML/1.1/}"
            elif return_type == "WaterML 1.0":
                wml_version = "1.0"
                ns = "{http://www.cuahsi.org/waterML/1.0/}"

            response = requests.post(
                url=url,
                headers={
                    "SOAPAction": "http://www.cuahsi.org/his/" + wml_version + "/ws/GetValuesObject",
                    "Content-Type": "text/xml; charset=utf-8"
                },
                data = '<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">' + \
                      '<soap-env:Body>' + \
                        '<ns0:GetValuesObject xmlns:ns0="http://www.cuahsi.org/his/' + wml_version + '/ws/">' + \
                          '<ns0:location>' + site_code + '</ns0:location>' + \
                          '<ns0:variable>' + variable_code + '</ns0:variable>' + \
                          '<ns0:startDate>' + start_date + '</ns0:startDate>' + \
                          '<ns0:endDate>' + end_date + '</ns0:endDate>' + \
                          '<ns0:authToken>' + autho_token + '</ns0:authToken>' + \
                        '</ns0:GetValuesObject>' + \
                      '</soap-env:Body>' + \
                    '</soap-env:Envelope>'
            )

            values_result = response.content

        except:
            print("FAILED TO DOWNLOAD WML")
            sql_connect.rollback()
            continue
            
        
        # --------------------------- #
        #   Validates WaterML files   #
        # --------------------------- #
        
        try:
            wml_tree = etree.fromstring(values_result)
            if not list(wml_tree.iter(ns + "values")):
                print("No timeseries data found")
                continue
            if len(list(list(wml_tree.iter(ns + "values"))[0].iter(ns + "value"))) == 0:
                print("No timeseries data found")
                continue
        except:
            print("Unable to validate WML")
            continue
        
        # ------------------------------------ #
        #   Extracts Data for Datasets Table   #
        # ------------------------------------ #

        dataset_code = 1
        curs.execute("SELECT * FROM Datasets WHERE DataSetCode = ?", (dataset_code,))
        row = curs.fetchone()
        if not row:
            dataset = (
                str(uuid.uuid4()),
                ("singleTimeSeries" if len(ts_list) == 1 else "multiTimeSeries"),
                1,
                res_title,
                res_abstract,
            )

            curs.execute("""INSERT INTO Datasets (
                                DataSetID, 
                                DataSetUUID, 
                                DataSetTypeCV, 
                                DataSetCode,
                                DataSetTitle, 
                                DataSetAbstract
                            ) VALUES (NULL, ?, ?, ?, ?, ?)""", dataset)
            dataset_id = curs.lastrowid
        else:
            dataset_id = row[0]

        # -------------------------------------------- #
        #   Extracts Data for SamplingFeatures Table   #
        # -------------------------------------------- #

        sf_tree = search_wml(wml_tree, ns, ["sourceInfo"], get_tree=True)
        sampling_feature_code = search_wml(sf_tree, ns, ["siteCode"], default_value=None)
        if sampling_feature_code:
            curs.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureCode = ?", (sampling_feature_code,))
            row = curs.fetchone()
            if not row:
                sampling_feature = (
                    str(uuid.uuid4()),
                    "site",
                    sampling_feature_code,
                    search_wml(sf_tree, ns, ["siteName"], default_value=None),
                    None,
                    "point",
                    None,
                    f'POINT ("{search_wml(sf_tree, ns, ["latitude"], default_value=None)}" "{search_wml(sf_tree, ns, ["longitude"], default_value=None)}")',
                    search_wml(sf_tree, ns, ["elevation_m"], default_value=None),
                    search_wml(sf_tree, ns, ["verticalDatum"], default_value=None),
                )
                curs.execute("""INSERT INTO SamplingFeatures (
                                    SamplingFeatureID, 
                                    SamplingFeatureUUID,
                                    SamplingFeatureTypeCV, 
                                    SamplingFeatureCode, 
                                    SamplingFeatureName,
                                    SamplingFeatureDescription, 
                                    SamplingFeatureGeotypeCV, 
                                    FeatureGeometry,
                                    FeatureGeometryWKT, 
                                    Elevation_m, 
                                    ElevationDatumCV
                                ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sampling_feature)
                sampling_feature_id = curs.lastrowid
            else:
                sampling_feature_id = row[0]
        else:
            print("SF Failed")
            sql_connect.rollback()
            continue

        # --------------------------------------------- #
        #   Extracts Data for SpatialReferences Table   #
        # --------------------------------------------- #

        srs_code = search_wml(sf_tree, ns, ["geogLocation"], default_value="EPSG:4269", attr="srs")
        curs.execute("SELECT * FROM SpatialReferences WHERE SRSCode = ?", (srs_code,))
        row = curs.fetchone()
        if not row:
            spatial_reference = (
                srs_code, 
                srs_code, 
                None,
                None,
            )
            curs.execute("""INSERT INTO SpatialReferences(
                            SpatialReferenceID, 
                            SRSCode, 
                            SRSName,
                            SRSDescription, 
                            SRSLink
                        ) VALUES (NULL, ?, ?, ?, ?)""", spatial_reference)
            spatial_reference_id = curs.lastrowid
        else:
            spatial_reference_id = row[0]

        # --------------------------------- #
        #   Extracts Data for Sites Table   #
        # --------------------------------- #

        curs.execute("SELECT * FROM Sites WHERE SamplingFeatureID = ?", (sampling_feature_id,))
        row = curs.fetchone()
        if not row:
            site = (
                sampling_feature_id,
                "unknown",
                search_wml(sf_tree, ns, ["latitude"], default_value=None),
                search_wml(sf_tree, ns, ["longitude"], default_value=None),
                spatial_reference_id,
            )
            curs.execute("""INSERT INTO Sites(
                            SamplingFeatureID, 
                            SiteTypeCV, 
                            Latitude, 
                            Longitude,
                            SpatialReferenceID
                        ) VALUES (?, ?, ?, ?, ?)""", site)
            site_id = curs.lastrowid
        else:
            site_id = row[0]

        # ------------------------------------- #
        #   Extracts Data for Variables Table   #
        # ------------------------------------- #

        vr_tree = search_wml(wml_tree, ns, ["variable"], get_tree=True)
        variable_code = search_wml(vr_tree, ns, ["variableCode", "VariableCode"], default_value=None)
        if variable_code:
            curs.execute("SELECT * FROM Variables WHERE VariableCode = ?", (variable_code,))
            row = curs.fetchone()
            if not row:
                variable = (
                    "Unknown", 
                    variable_code, 
                    search_wml(vr_tree, ns, ["variableName", "VariableName"], default_value="Unknown"),
                    search_wml(vr_tree, ns, ["variableDescription", "VariableDescription"], default_value=None),
                    search_wml(vr_tree, ns, ["speciation", "Speciation"], default_value=None),
                    search_wml(vr_tree, ns, ["noDataValue", "NoDataValue"], default_value=-9999),
                )
                curs.execute("""INSERT INTO Variables (
                                VariableID, 
                                VariableTypeCV, 
                                VariableCode, 
                                VariableNameCV, 
                                VariableDefinition, 
                                SpeciationCV, 
                                NoDataValue 
                            ) VALUES (NULL, ?, ?, ?, ?, ?, ?)""", variable)
                variable_id = curs.lastrowid
            else:
                variable_id = row[0]
        else:
            print("VR Failed")
            sql_connect.rollback()
            continue

        # --------------------------------- #
        #   Extracts Data for Units Table   #
        # --------------------------------- #

        ut_tree = search_wml(vr_tree, ns, ["unit"], get_tree=True)
        unit_code = search_wml(ut_tree, ns, ["unitCode", "UnitCode", "unitsCode", "UnitsCode"], default_value=9999)
        curs.execute("SELECT * FROM Units WHERE UnitsID = ?", (unit_code,))
        row = curs.fetchone()
        if not row:
            unit = (
                unit_code,
                search_wml(ut_tree, ns, ["unitType", "unitsType", "UnitType", "UnitsType"], default_value="other") if unit_code != 9999 else "other",
                search_wml(ut_tree, ns, ["unitAbbreviation", "unitsAbbreviation", "UnitAbbreviation", "UnitsAbbreviation"], default_value="unknown") if unit_code != 9999 else "unknown",
                search_wml(ut_tree, ns, ["unitName", "unitsName", "UnitName", "UnitsName"], default_value="unknown") if unit_code != 9999 else "unknown",
                search_wml(ut_tree, ns, ["unitLink", "unitsLink", "UnitLink", "UnitsLink"], default_value=None) if unit_code != 9999 else None,
            )
            curs.execute("""INSERT INTO Units (
                            UnitsID, 
                            UnitsTypeCV, 
                            UnitsAbbreviation, 
                            UnitsName,
                            UnitsLink
                        ) VALUES (?, ?, ?, ?, ?)""", unit)
            unit_id = curs.lastrowid
        else:
            unit_id = row[0]

        # ------------------------------------------ #
        #    Extracts Data for Time Spacing Units    #
        # ------------------------------------------ #

        tu_tree = search_wml(vr_tree, ns, ["timeScale"], get_tree=True)
        time_unit_code = search_wml(tu_tree, ns, ["unitCode", "UnitCode", "unitsCode", "UnitsCode"], default_value=9999)
        curs.execute("SELECT * FROM Units WHERE UnitsID = ?", (time_unit_code,))
        row = curs.fetchone()
        if not row:
            time_unit = (
                time_unit_code,
                search_wml(tu_tree, ns, ["unitType", "unitsType", "UnitType", "UnitsType"], default_value="other") if time_unit_code != 9999 else "other",
                search_wml(tu_tree, ns, ["unitAbbreviation", "unitsAbbreviation", "UnitAbbreviation", "UnitsAbbreviation"], default_value="unknown") if time_unit_code != 9999 else "unknown",
                search_wml(tu_tree, ns, ["unitName", "unitsName", "UnitName", "UnitsName"], default_value="unknown") if time_unit_code != 9999 else "unknown",
                search_wml(tu_tree, ns, ["unitLink", "unitsLink", "UnitLink", "UnitsLink"], default_value=None) if time_unit_code != 9999 else None,
            )
            curs.execute("""INSERT INTO Units (
                            UnitsID, 
                            UnitsTypeCV, 
                            UnitsAbbreviation, 
                            UnitsName,
                            UnitsLink
                        ) VALUES (?, ?, ?, ?, ?)""", time_unit)
            time_unit_id = curs.lastrowid
        else:
            time_unit_id = row[0]

        # ------------------------------------------------------------------- #
        #   Extracts Data for People, Organizations, and Affiliations Table   #
        # ------------------------------------------------------------------- #

        sr_tree = search_wml(wml_tree, ns, ["source"], get_tree=True)
        person_name = search_wml(sr_tree, ns, ["contactName"], default_value="unknown")
        curs.execute("SELECT * FROM People WHERE PersonFirstName = ?", (person_name,))
        row = curs.fetchone()
        if not row:
            person = (
                person_name,
                " ",
            )
            curs.execute("""INSERT INTO People (
                            PersonID, 
                            PersonFirstName, 
                            PersonLastName
                        ) VALUES (NULL, ?, ?)""", person)
            person_id = curs.lastrowid
        else:
            person_id = row[0]
        organization_code = search_wml(sr_tree, ns, ["sourceCode"], default_value="unknown")
        curs.execute("SELECT * FROM Organizations WHERE OrganizationCode = ?", (organization_code,))
        row = curs.fetchone()
        if not row:
            organization = (
                "unknown",
                organization_code,
                search_wml(sr_tree, ns, ["organization"], default_value="unknown") if organization_code != "unknown" else "unknown",
                search_wml(sr_tree, ns, ["sourceDescription"], default_value=None) if organization_code != "unknown" else None,
                search_wml(sr_tree, ns, ["sourceLink"], default_value=None) if organization_code != "unknown" else None,
            )
            curs.execute("""INSERT INTO Organizations (
                            OrganizationID, 
                            OrganizationTypeCV,
                            OrganizationCode, 
                            OrganizationName, 
                            OrganizationDescription, 
                            OrganizationLink
                        ) VALUES (NULL, ?, ?, ?, ?, ?)""", organization)
            organization_id = curs.lastrowid
        else:
            organization_id = row[0]
        curs.execute("SELECT * FROM Affiliations WHERE PersonID = ? AND OrganizationID = ?", (person_id, organization_id,))
        row = curs.fetchone()
        if not row:
            affiliation = (
                person_id,
                organization_id,
                "unknown",
                search_wml(sr_tree, ns, ["phone"], default_value=None),
                search_wml(sr_tree, ns, ["email"], default_value="unknown"),
                search_wml(sr_tree, ns, ["address"], default_value=None),
            )
            curs.execute("""INSERT INTO Affiliations (
                            AffiliationID, 
                            PersonID, 
                            OrganizationID,
                            AffiliationStartDate, 
                            PrimaryPhone, 
                            PrimaryEmail,
                            PrimaryAddress
                        ) VALUES (NULL, ?, ?, ?, ?, ?, ?)""", affiliation)
            affiliation_id = curs.lastrowid
        else:
            affiliation_id = row[0]

        # -------------------------------------------- #
        #   Extracts Data for ProcessingLevels Table   #
        # -------------------------------------------- #

        pl_trees = search_wml(wml_tree, ns, ["qualityControlLevel"], get_tree=True, mult=True)
        processing_level_data_list = [{"processing_level_code": search_wml(pl_tree, ns, ["qualityControlLevelCode"], default_value=9999), "processing_level_tree": pl_tree, "processing_level_id": None} for pl_tree in pl_trees] if pl_trees else [{"processing_level_code": 9999, "processing_level_tree": None, "processing_level_id": None}]
        for processing_level_data in processing_level_data_list:
            curs.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelCode = ?", (processing_level_data["processing_level_code"],))
            row = curs.fetchone()
            if not row:
                processing_level = (
                    processing_level_data["processing_level_code"],
                    search_wml(processing_level_data["processing_level_tree"], ns, ["definition"], None) if processing_level_data["processing_level_code"] != 9999 else None,
                    search_wml(processing_level_data["processing_level_tree"], ns, ["explanation"], None) if processing_level_data["processing_level_code"] != 9999 else None,
                )
                curs.execute("""INSERT INTO ProcessingLevels (
                                ProcessingLevelID, 
                                ProcessingLevelCode,
                                Definition, 
                                Explanation
                            ) VALUES (NULL, ?, ?, ?)""", processing_level)
                processing_level_data["processing_level_id"] = curs.lastrowid
            else:
                processing_level_data["processing_level_id"] = row[0]

        # -------------------------------------------------------------------------- #
        #   Extracts Data for Methods, Actions, ActionBy, and FeatureActions Table   #
        # -------------------------------------------------------------------------- #

        md_trees = search_wml(wml_tree, ns, ["method"], get_tree=True, mult=True)
        method_data_list = [{"method_code": search_wml(md_tree, ns, ["methodCode", "MethodCode"], default_value=9999), "method_tree": md_tree, "method_id": None, "feature_action_id": None, "start_date": None, "start_date_offset": None, "value_count": None} for md_tree in md_trees] if md_trees else [{"method_code": 9999, "method_tree": None, "method_id": None}]
        for method_data in method_data_list:
            curs.execute("SELECT * FROM Methods WHERE MethodCode = ?", (method_data["method_code"],))
            row = curs.fetchone()
            if not row:
                method = (
                    "observation" if method_data["method_code"] != 9999 else "unknown",
                    method_data["method_code"],
                    method_data["method_code"] if method_data["method_code"] != 9999 else "unknown",
                    search_wml(method_data["method_tree"], ns, ["methodDescription", "MethodDescription"], None) if method_data["method_code"] != 9999 else None,
                    search_wml(method_data["method_tree"], ns, ["methodLink", "MethodLink"], None) if method_data["method_code"] != 9999 else None,
                )
                curs.execute("""INSERT INTO Methods (
                                MethodID, 
                                MethodTypeCV, 
                                MethodCode, 
                                MethodName,
                                MethodDescription, 
                                MethodLink
                            ) VALUES (NULL, ?, ?, ?, ?, ?)""", method)
                method_data["method_id"] = curs.lastrowid
            else:
                method_data["method_id"] = row[0]
            method_code_list = search_wml(wml_tree, ns, ["value"], attr="methodCode", mult=True)
            datetime_list = [i for j, i in enumerate(search_wml(wml_tree, ns, ["value"], attr="dateTime", mult=True)) if method_code_list[j] == method_data["method_code"] or not method_code_list[j]]
            time_offset_list = search_wml(wml_tree, ns, ["value"], attr="timeOffset", mult=True)
            start_date = datetime_list[0]
            value_count = len(datetime_list)
            end_date = datetime_list[-1]
            method_data["start_date"] = start_date[0]
            method_data["start_date_offset"] = time_offset_list[0] if time_offset_list[0] else "+00:00"
            method_data["value_count"] = value_count
            action = (
                "observation",
                method_data["method_id"],
                start_date,
                time_offset_list[0] if time_offset_list[0] else "+00:00",
                end_date,
                time_offset_list[-1] if time_offset_list[-1] else "+00:00",
                "An observation action that generated a time series result.",
            )
            curs.execute("""INSERT INTO Actions (
                            ActionID, 
                            ActionTypeCV, 
                            MethodID, 
                            BeginDateTime,
                            BeginDateTimeUTCOffset, 
                            EndDateTime, 
                            EndDateTimeUTCOffset, 
                            ActionDescription
                        ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)""", action)
            action_id = curs.lastrowid
            action_by = (
                action_id,
                affiliation_id,
                1,
            )
            curs.execute("""INSERT INTO ActionBy (
                            BridgeID, 
                            ActionID, 
                            AffiliationID, 
                            IsActionLead
                        ) VALUES (NULL, ?, ?, ?)""", action_by)
            action_by_id = curs.lastrowid
            feature_action = (
                sampling_feature_id,
                action_id,
            )
            curs.execute("""INSERT INTO FeatureActions (
                            FeatureActionID, 
                            SamplingFeatureID, 
                            ActionID
                        ) VALUES (NULL, ?, ?)""", feature_action)
            method_data["feature_action_id"] = curs.lastrowid

        # ----------------------------------------------------------------------------------------------------- #
        #    Extracts Data for Results, TimeSeriesResults, TimeSeriesResultValues, and DataSetResults Tables    #
        # ----------------------------------------------------------------------------------------------------- #

        result_data_list = list(itertools.product(method_data_list, processing_level_data_list))
        for result_data in result_data_list:
            result = (
                str(uuid.uuid4()),
                result_data[0]["feature_action_id"],
                "timeSeriesCoverage",
                variable_id,
                unit_id,
                result_data[1]["processing_level_id"],
                result_data[0]["start_date"],
                result_data[0]["start_date_offset"],
                None,
                search_wml(vr_tree, ns, ["sampleMedium"], default_value="unknown"),
                result_data[0]["value_count"],
            )
            curs.execute("""INSERT INTO Results (
                            ResultID, 
                            ResultUUID, 
                            FeatureActionID, 
                            ResultTypeCV,
                            VariableID, 
                            UnitsID, 
                            ProcessingLevelID, 
                            ResultDateTime, 
                            ResultDateTimeUTCOffset, 
                            StatusCV, 
                            SampledMediumCV, 
                            ValueCount
                        ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", result)
            result_id = curs.lastrowid
            timeseries_result = (
                result_id,
                "Unknown",
            )
            curs.execute("""INSERT INTO TimeSeriesResults (
                            ResultID, 
                            AggregationStatisticCV
                        ) VALUES (?, ?)""", timeseries_result)
            timeseries_result_values = tuple([(
                result_id,
                i[0],
                i[1],
                i[2] if i[2] else "+00:00",
                i[3] if i[3] else "nc",
                "unknown",
                "unknown",
                "unknown",
            ) for i in list(map(list, zip(*[
                search_wml(wml_tree, ns, ["value"], mult=True),
                search_wml(wml_tree, ns, ["value"], attr="dateTime", mult=True),
                search_wml(wml_tree, ns, ["value"], default_value="+00:00", attr="timeOffset", mult=True),
                search_wml(wml_tree, ns, ["value"], default_value="nc", attr="censorCode", mult=True)
            ])))])
            curs.execute("BEGIN TRANSACTION;")
            curs.executemany("""INSERT INTO TimeSeriesResultValues ( 
                                ValueID, 
                                ResultID, 
                                DataValue, 
                                ValueDateTime,
                                ValueDateTimeUTCOffset, 
                                CensorCodeCV, 
                                QualityCodeCV, 
                                TimeAggregationInterval,
                                TimeAggregationIntervalUnitsID
                            ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""", timeseries_result_values)
            dataset_result = (
                1,
                result_id,
            )
            curs.execute("""INSERT INTO DataSetsResults ( 
                            BridgeID, 
                            DataSetID, 
                            ResultID
                        ) Values (NULL, ?, ?)""", dataset_result)

        # -------------------- #
        #    Commits Changes   #
        # -------------------- #

        try:
            sql_connect.commit()
        except:
            sql_connect.rollback()
            continue
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
