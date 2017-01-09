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
from oauthlib.oauth2 import TokenExpiredError
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import urllib2
import urllib
import json
import logging
import shutil

logger = logging.getLogger(__name__)

use_hs_client_helper = True
try:
    from tethys_services.backends.hs_restclient_helper import get_oauth_hs
except Exception as ex:
    use_hs_client_helper = False
    logger.error("tethys_services.backends.hs_restclient_helper import get_oauth_hs: " + ex.message)




@login_required()
def temp_waterml(request, id):
    base_path = utilities.get_workspace() + "/id"
    file_path = base_path + "/" + id
    response = HttpResponse(FileWrapper(open(file_path)), content_type='application/xml')
    return response
# @login_required()
@csrf_exempt
def home(request):
    ids=[]
    meta =[]
    source=[]
    quality=[]
    method=[]
    sourceid=[]
    serviceurl=[]
    data = request.META['QUERY_STRING']
    data = data.encode(encoding ='UTF-8')
    base_path = utilities.get_workspace() + "/id/timeseriesLayerResource.json.refts"
    if request.user.is_authenticated():
        login1 = 'True'
    else:
        login1 ='False'
    print request.body

    body = request.body
    try:
        decode11 = request.GET['data']
    except:
        decode11 = 'nothing'
    try:
        decode_body = json.loads(request.body.decode("utf-8"))
    except:
        decode_body = "no data"
    try:
        form_body = request.POST
    except:
        form_body = "no data"
    #
    with open(base_path, 'w') as outfile:
        json.dump(form_body, outfile)

    """
    Controller for the app home page.
    """
    # utilities.append_ts_layer_resource("testtt",'test')
    context = {'source':body,
               'cuahsi_ids':decode_body,
               'quality':form_body,
               'method':request,
               'sourceid':sourceid,
                'serviceurl':serviceurl,
               'login1':login1
               }
    return render(request, 'hydroshare_resource_creator/home.html', context)
# @login_required()
@csrf_exempt
def chart_data(request,res_id):
    data_for_chart={}
    error=''
    data1=None
    #parse xml data from 'data' from data_for_js and prepare for the table
    if res_id =='None':
        data = utilities.parse_JSON()
        print "ddddddddddddddddddddddddddddddddd"
        print data
        try:
            data1 = data['timeSeriesLayerResource']
        except:
            data1 = ''
        print data1
        # data_n = urllib.unquote(data1).decode(encoding ="UTF-8")
        # print data_n
        if data1 =='':
            error = "No data in file"
        else:
            error=''
    else:
        temp_dir = utilities.get_workspace()
        root_dir = temp_dir + '/id/' + res_id
        try:
            shutil.rmtree(root_dir)
        except:
            nothing =None
        if not os.path.exists(temp_dir+"/id"):
            os.makedirs(temp_dir+"/id")
        else:
            if use_hs_client_helper:
                hs = get_oauth_hs(request)
            else:
                hs = getOAuthHS(request)
            file_path = temp_dir + '/id'
            hs.getResource(res_id, destination=file_path, unzip=True)
            root_dir = file_path + '/' + res_id
            data_dir = root_dir + '/' + res_id + '/data/contents/'
            for subdir, dirs, files in os.walk(data_dir):
                for file in files:
                    if  'wml_1_' in file:
                        data_file = data_dir + file
                        with open(data_file, 'r') as f:
                            # print f.read()
                            file_data = f.read()
                            f.close()
                            file_temp_name = temp_dir + '/id/' + res_id + '.xml'
                            file_temp = open(file_temp_name, 'wb')
                            file_temp.write(file_data)
                            file_temp.close()
                    if '.json.refts' in file:
                        data_file = data_dir +file
                        with open(data_file, 'r') as f:
                            file_data = f.read()
                            print file_data
                            data = file_data.encode(encoding ='UTF-8')
                            print data
                            data1 = json.loads(data)
                            data1 = data1['timeSeriesLayerResource']

    data_for_chart = {"data": data1,'error':error}
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
@login_required()
def write_file(request):
    sucess = {"File uploaded":"sucess"}
    metadata = []
    # hs = getOAuthHS(request)
    waterml_url = "http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValuesObject?location=CHMI-H:140&variable=CHMI-H:TEPLOTA&startDate=2015-07-01&endDate=2015-07-10&authToken="
    ref_type = "rest"
    metadata.append({"referenceurl":
            {"value": waterml_url,
            "type": ref_type}})
    r_type = 'RefTimeSeriesResource'
    r_title = "test"
    r_keywords = ["test"]
    r_abstract = "This is a test of the resource creator"
    # res_id = hs.createResource(r_type,
    #                     r_title,
    #                     resource_file=None,
    #                     keywords=r_keywords,
    #                     abstract=r_abstract,
    #                     metadata=json.dumps(metadata))


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
    service_url = 'http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL'
    # service_url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx?WSDL'
    # # site_code = '10147100'
    site_code = 'ODM:010210JHI'
    # variable_code = 'ODM:Discharge'
    variable_code = 'NWISDV:00060'
    client = connect_wsdl_url(service_url)
    # print client
    start_date =''
    end_date = ''
    auth_token = ''
    response1 = client.service.GetValues(site_code, variable_code, start_date, end_date, auth_token)
    print response1

    response= urllib2.urlopen('http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo')
    html = response.read()

    temp_dir = utilities.get_workspace()
    file_temp_name = temp_dir + '/id/' + 'WaterOneFlowServiceInfo' + '.xml'
    file_temp = open(file_temp_name, 'wb')
    file_temp.write(html)
    file_temp.close()
    service_url = utilities.parse_service_info(file_temp_name)
    # service_url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx?WSDL'
    # client = connect_wsdl_url(service_url)
    # print client
    # print response1
    # response1 = {"File uploaded":"sucess"}
    # base_path = utilities.get_workspace()+"/hydroshare"
    # file_path = base_path + "/" +title
    # response = HttpResponse(FileWrapper(open(file_path)), content_type='application/xml')
    # return response1
    return service_url
@ensure_csrf_cookie
# @login_required()
def create_layer(request,fun_type,res_id):
    resource_id=None
    data_stor=[]
    int_resource=[]
    counter=0
    title = str(request.POST.get('resTitle'))# causing errors because not strints?
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords'))
    res_access = str(request.POST.get('resAccess'))
    keywords = keywords.split(',')
    str_resource = request.POST.get('checked_ids')
    print "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa"
    print str_resource
    str_resource = trim(str_resource)

    for res in str_resource:
        int_resource.append(int(res))
    print int_resource
    metadata = []
    if use_hs_client_helper:
	    hs = get_oauth_hs(request)
    else:
        hs = getOAuthHS(request)
    temp_dir = utilities.get_workspace()
    file_name = title.replace(" ", "")
    file_path = temp_dir + '/id/timeseriesLayerResource.json.refts'
    fpath = temp_dir + '/id/'+file_name+'.json.refts'
    print fpath
    with open(file_path, 'r') as outfile:
        file_data = outfile.read()
        data = file_data.encode(encoding ='UTF-8')
        data = json.loads(data)
        print data
        data = data['timeSeriesLayerResource']
        data_symbol = data['symbol']
        data_file =data['fileVersion']
        for i in data['REFTS']:
            if counter in int_resource:
                data_stor.append(i)
            counter = counter+1
        data_dic = {"REFTS":data_stor,"fileVersion": data_file, "title": title,
                    "symbol":data_symbol,"abstract": abstract,'keyWords':keywords}
        data.update(data_dic)
        final_dic = {"timeSeriesLayerResource":data}
        with open(fpath, 'w') as outfile:
            json.dump(final_dic, outfile)
    r_type = 'GenericResource'
    r_title = title
    r_keywords = (keywords)
    r_abstract = abstract

    print res_id
    if fun_type =='create':
        try:
            print "creating resource"
            resource_id = hs.createResource(r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
        except:
            resource_id ="error"
    elif fun_type =='update':
        try:
            print "Updating resource"
            try:
                resource_id = hs.deleteResourceFile(res_id, fpath+'.json.refts')
            except:
                print 'file doesnt exist'
            resource_id = hs.addResourceFile(res_id, fpath)
        except:
            resource_id ="error"
    # if res_access == 'public':
    #     hs.setAccessRules(resource_id, public=True)
    # else:
    #     hs.setAccessRules(resource_id, public=False)


    #upload to hydroshare stuff
    return JsonResponse({'Request':resource_id})
def trim(string_dic):
    string_dic=string_dic.strip('[')
    string_dic=string_dic.strip(']')
    string_dic=string_dic.strip('"')
    string_dic = string_dic.replace('"','')
    string_dic = string_dic.split(',' )
    return string_dic
@csrf_exempt
@never_cache
def test(request):
    import json
    request_url = request.META['QUERY_STRING']


    # not ajax
    # curl -X POST -d 'name1=value1&name2=value2&name1=value11' "http://127.0.0.1:8000/apps/timeseries-viewer/test/"

    # curl -X POST -H "Content-Type: application/json" -d '{"mylist": ["item1", "item2", "item3"], "list_type": "array"}' "http://127.0.0.1:8000/apps/timeseries-viewer/test/"

    # curl -X POST -F 'name1=value1' -F 'name2=value2' -F 'name1=value11' "http://127.0.0.1:8000/apps/timeseries-viewer/test/"

    # ajax
    # curl -X POST -H "X-Requested-With: XMLHttpRequest" -d 'name1=value1&name2=value2&name1=value11' "http://127.0.0.1:8000/apps/timeseries-viewer/test/"

    # curl -X POST -H "X-Requested-With: XMLHttpRequest" -H "Content-Type: application/json" -d '{"mylist": ["item1", "item2", "item3"], "list_type": "array"}' "http://127.0.0.1:8000/apps/timeseries-viewer/test/"


    result = {}
    result['query_string'] =request_url
    result["is_ajax"] = request.is_ajax()

    result["request.GET"] = request.GET
    result["request.POST"] = request.POST
    with open('data.JSON', 'w') as outfile:
        json.dump(request.body, outfile)

    try:
        result["request.body"] = request.body
    except:
        pass

    try:
        result["request.body -> json"] = json.loads(request.body)
    except:
        pass

    print result

    context ={"result": json.dumps(result)
               }
    return render(request, 'hydroshare_resource_creator/test.html', context)
def login_callback(request):

    context = {}
    if request.user.is_authenticated():
        context["login"] = "yes"
    else:
        context["login"] = "no"

    return render(request, 'hydroshare_resource_creator/login_callback.html', context)
def login_test(request):
    if request.user.is_authenticated():
        login_status ="True"
    else:
        login_status ="False"
    return JsonResponse({'Login':login_status})