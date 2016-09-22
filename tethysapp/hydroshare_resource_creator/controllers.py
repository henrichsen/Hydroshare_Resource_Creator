from django.shortcuts import render
import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from wsgiref.util import FileWrapper
import os
from datetime import datetime
import utilities
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
import json
from django.views.decorators.csrf import ensure_csrf_cookie
@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    # utilities.append_ts_layer_resource("testtt",'test')
    context = {}
    return render(request, 'hydroshare_resource_creator/home.html', context)

def chart_data(request, res_id, src):
    # checks if we already have an unzipped xml file
    file_path = utilities.waterml_file_path(res_id)
    print file_path
    # if we don't have the xml file, downloads and unzips it
    if not os.path.exists(file_path):
        print "does not exist"
        utilities.unzip_waterml(request, res_id,src)

    # returns an error message if the unzip_waterml failed
    # parses the WaterML to a chart data object
    data_for_chart = utilities.Original_Checker(file_path)
    temp_dir = utilities.get_workspace()
    if not os.path.exists(temp_dir+"/hydroshare"):
        os.makedirs(temp_dir+"/hydroshare")
    file_temp_name = temp_dir + '/hydroshare/HIS_reference_timeseries.txt'
    file_temp = open(file_temp_name, 'w')
    file_temp.writelines(str(data_for_chart))
    file_temp.close()

    return JsonResponse(data_for_chart)

def getOAuthHS(request):
    hs_instance_name = "www"
    client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", None)
    client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", None)
    # this line will throw out from django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
    hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)
    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
    hs = HydroShare(auth=auth, hostname=hs_hostname)
    return hs

def connect_wsdl_url(wsdl_url):
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
def write_file(request):
    sucess = {"File uploaded":"sucess"}
    metadata = []
    hs = getOAuthHS(request)
    waterml_url = "http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValuesObject?location=CHMI-H:140&variable=CHMI-H:TEPLOTA&startDate=2015-07-01&endDate=2015-07-10&authToken="
    ref_type = "rest"
    metadata.append({"referenceurl":
            {"value": waterml_url,
            "type": ref_type}})
    r_type = 'RefTimeSeriesResource'
    r_title = "test"
    r_keywords = ["test"]
    r_abstract = "This is a test of the resource creator"
    res_id = hs.createResource(r_type,
                        r_title,
                        resource_file=None,
                        keywords=r_keywords,
                        abstract=r_abstract,
                        metadata=json.dumps(metadata))


    # temp_dir = utilities.get_workspace()
    # file_temp_name = temp_dir + '/hydroshare/cuahsi-wdc-2016-07-26-66422054.xml'
    #
    # abstract = 'My abstract'
    # title = 'My resource script'
    # keywords = ('my keyword 1', 'my keyword 2')
    # rtype = 'RefTimeSeriesResource'
    # fpath = file_temp_name
    # resource_id = hs.createResource(rtype, title, resource_file=fpath, keywords=keywords, abstract=abstract)
    # os.remove(file_temp_name)
    return JsonResponse(sucess)
def response(request):
    # service_url = 'http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL'
    service_url = 'http://143.234.88.22/TarlandHydrologyDataWS/cuahsi_1_1.asmx?WSDL'
    # site_code = '10147100'
    site_code = 'ODM:010210JHI'
    variable_code = 'ODM:Discharge'
    # variable_code = 'NWISDV:00060'
    client = connect_wsdl_url(service_url)
    print client
    start_date =''
    end_date = ''
    auth_token = ''
    # response1 = client.service.GetValues(site_code, variable_code, start_date, end_date, auth_token)
    response1 = client.service.GetSiteInfo(site_code, auth_token)
    # response1 = {"File uploaded":"sucess"}
    return JsonResponse({"File":response1})
@ensure_csrf_cookie
def create_layer(request,title):
    res_id = request.POST.get('checked_ids')
    res_id=res_id.strip('[')
    res_id=res_id.strip(']')
    res_id=res_id.strip('"')
    res_id = res_id.replace('"','')

    res_id = res_id.split(',' )
    print res_id
    utilities.create_ts_layer_resource(title)

    print type(res_id)
    for id in res_id:
        print id
        print "runnnnnnnnnnnnnnnning"
        file_path = utilities.waterml_file_path(id)
        print file_path
        meta_data = utilities.Original_Checker(file_path)
        utilities.append_ts_layer_resource(title,meta_data)

    #upload to hydroshare stuff
    return JsonResponse({'Request':"sucess"})