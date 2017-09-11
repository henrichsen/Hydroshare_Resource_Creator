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
    base_path = utilities.get_workspace() + "/id/timeseriesLayerResource.json"
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
    # with open(base_path, 'w') as outfile:
    #     json.dump(form_body, outfile)

    print decode11
    print urllib.unquote(decode11).decode(encoding ="UTF-8")

    # print data
    # data  =data.split('&')
    # for e in data:
    #     s= e.split('=')
    #     meta.append(s)
    # print data
    # print meta
    # for e in meta:
    #     print e[0]
    #     if e[0] == 'Source':
    #         source.append(e[1])
    #     if e[0] == 'WofUri':
    #         ids.append(e[1])
    #     if e[0] == 'QCLID':
    #         quality.append(e[1])
    #     if e[0] == 'MethodId':
    #         method.append(e[1])
    #     if e[0] == 'SourceId':
    #         sourceid.append(e[1])
    #     if e[0] == 'ServiceURL':
    #         serviceurl.append(e[1])
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
def chart_data(request):
    data_for_chart={}
    # serviceurl = request.POST.get('serviceurl')
    # # checks if we already have an unzipped xml file
    # file_path = utilities.waterml_file_path(res_id)
    # print file_path
    # print serviceurl
    # # if we don't have the xml file, downloads and unzips it
    # if not os.path.exists(file_path):
    #     print "does not exist"
    #     utilities.unzip_waterml(request, res_id,src)
    # if src =='cuahsi':
    #     source = "WOF"
    #     data_for_chart = utilities.Original_Checker(file_path)
    #     try:
    #
    #         services = response(request)
    #         network = data_for_chart['network']
    #         service = services[network]
    #
    #     except:
    #         service = 'N/A'
    #     data_for_chart.update({'URL':service})
    #     data_for_chart.update({'network':services})
    #     print service
    #     return JsonResponse(data_for_chart)
    #
    # elif src=='hydroshare':
    #     # returns an error message if the unzip_waterml failed
    #     # parses the WaterML to a chart data object
    #     # data_for_chart = utilities.Original_Checker(file_path)
    #         temp_dir = utilities.get_user_workspace()
    #         if not os.path.exists(temp_dir+"/hydroshare"):
    #             os.makedirs(temp_dir+"/hydroshare")
    #         file_temp_name = temp_dir + '/hydroshare/HIS_reference_timeseries.txt'
    #         file_temp = open(file_temp_name, 'w')
    #         data_for_js = utilities.get_hydroshare_resource(request,res_id,data_for_chart)
    #     # file_temp.writelines(str(data_for_chart))
    #     # file_temp.close()
    #     # data_for_chart['RefType']=source




    #parse xml data from 'data' from data_for_js and prepare for the table
    data = utilities.parse_JSON()
    print "ddddddddddddddddddddddddddddddddd"
    print data
    try:
        data1 = data['timeSeriesLayerResource']
    except:
        data1 = ''
    print data1
    data_n = urllib.unquote(data1).decode(encoding ="UTF-8")
    print data_n
    if data1 =='':
        error = "No data in file"
    else:
        error=''
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


    # temp_dir = utilities.get_user_workspace()
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
    # base_path = utilities.get_user_workspace()+"/hydroshare"
    # file_path = base_path + "/" +title
    # response = HttpResponse(FileWrapper(open(file_path)), content_type='application/xml')
    # return response1
    return service_url
@ensure_csrf_cookie
# @login_required()
def create_layer(request,src):
    # res_id = request.POST.get('checked_ids')
    # # res_id = res_id.encode(encoding ='UTF-8')
    # print res_id
    # resource_type = request.POST.get('resource_type')
    # # resource_type = resource_type.encode(encoding ='UTF-8')
    # client_id = 'MYCLIENTID'
    # client_secret = 'MYCLIENTSECRET'
    #
    # auth = HydroShareAuthOAuth2(client_id, client_secret,
    #                             username='myusername', password='mypassword')
    # hs = HydroShare(auth=auth)

    # try:
    #   for resource in hs.getResourceList():
    #     print(resource)
    # except TokenExpiredError as e:
    #    hs = HydroShare(auth=auth)
    #    for resource in hs.getResourceList():
    #          print(resource)

    title = str(request.POST.get('resTitle'))# causing errors because not strints?
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords'))
    keywords = keywords.split(',')
    # # title = "test"
    # res_id = trim(res_id)
    # resource_type = trim(resource_type)
    service_type = 'test'
    url = 'test'

    # print resource_type
    # utilities.create_ts_layer_resource(title)
    #
    #
    # for id in res_id:
    #
    #     file_path = utilities.waterml_file_path(id)
    #
    #     meta_data = utilities.Original_Checker(file_path)
    #     utilities.append_ts_layer_resource(title,meta_data)
    resource_type = ['ts']
    metadata = []
    res_id = 'cuahsi-wdc-2016-10-21-64527889'
    hs = getOAuthHS(request)
    print keywords
    #create a time series resource
    #file needs to be a csv
    r_type = 'GenericResource'
    r_title = title
    r_keywords = (keywords)
    r_abstract = abstract
    print r_title, r_keywords,r_abstract
    temp_dir = utilities.get_workspace()
    fpath = temp_dir + '/id/timeseriesLayerResource.json'
    try:
        resource_id = hs.createResource(r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
    except:
        resource_id ="error"

    # if(resource_type[0]=='ref_ts'or resource_type[1]=='ref_ts'):
    #
    #     #rest call
    #     # waterml_url = "http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValuesObject?location=CHMI-H:140&variable=CHMI-H:TEPLOTA&startDate=2015-07-01&endDate=2015-07-10&authToken="
    #     if(service_type=='REST'):
    #         waterml_url = url+'/GetValueObject'
    #         ref_type = "rest"
    #         metadata.append({"referenceurl":
    #                 {"value": waterml_url,
    #                 "type": ref_type}})
    #         r_type = 'RefTimeSeriesResource'
    #         r_title = "test of rest reftime series"
    #         r_keywords = ["test"]
    #         r_abstract = "This is a test of the resource creator"
    #         res_id = hs.createResource(r_type,
    #                             r_title,
    #                             resource_file=None,
    #                             keywords=r_keywords,
    #                             abstract=r_abstract,
    #                             metadata=json.dumps(metadata))
    #
    #     elif (service_type =='SOAP'):
    #         #Soap Call
    #         soap_url = 'http://hydrodata.info/chmi-d/cuahsi_1_1.asmx?wsdl'
    #         site_code = ':248'
    #         var_code = ':SRAZKY'
    #         ref_type = 'soap'
    #         metadata.append({"referenceurl":
    #                  {"value": soap_url,
    #                 "type": ref_type,}})
    #         metadata.append({"variable":{'code':var_code}})
    #         metadata.append({"site":{'code':site_code}})
    #         r_type = 'RefTimeSeriesResource'
    #         r_title = "test of rest reftime series soap request"
    #         r_keywords = ["test"]
    #         r_abstract = "This is a test of the resource creator"
    #         res_id = hs.createResource(r_type,
    #                             r_title,
    #                             resource_file=None,
    #                             keywords=r_keywords,
    #                             abstract=r_abstract,
    #                             metadata=json.dumps(metadata))


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