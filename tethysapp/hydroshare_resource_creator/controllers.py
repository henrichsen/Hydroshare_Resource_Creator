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
import time

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
    # try:
    #     decode11 = request.GET['data']
    # except:
    #     decode11 = 'nothing'
    # try:
    #     decode_body = json.loads(request.body.decode("utf-8"))
    # except:
    #     decode_body = "no data"
    try:
        form_body = request.POST
    except:
        form_body = "no data"

    # form_body = '{"fileVersion":1,"title":"HydroClient-2017-01-09T17:46:47.810Z","abstract":"Retrieved timeseries...","symbol":"http://data.cuahsi.org/content/images/cuahsi_logo_small.png","keyWords":["Time Series","CUAHSI"],"REFTS":[{"refType":"WOF","serviceType":"SOAP","url":"http://hydro1.sci.gsfc.nasa.gov/daac-bin/his/1.0/GLDAS_NOAH_001.cgi?WSDL","site":"X282-Y404 of Global Land Data Assimilation System (GLDAS) NASA","siteCode":"GLDAS_NOAH:X282-Y404","variable":"Surface runoff","variableCode":"GLDAS:GLDAS_NOAH025_3H.001:Qs","networkName":"GLDAS_NOAH","beginDate":"2016-01-09T00:00:00","endDate":"2016-09-30T21:00:00+00:00","returnType":"WaterML 1.0","location":{"latitude":41.125,"longitude":-109.375}}]}'
    with open(base_path, 'w') as outfile:
        json.dump(form_body, outfile)

    """
    Controller for the app home page.
    """
    # utilities.append_ts_layer_resource("testtt",'test')
    context = {'source':body,
               # 'cuahsi_ids':decode_body,
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
    error='error'
    res_info=None
    file_data=None
    status = 'running'
    #parse xml data from 'data' from data_for_js and prepare for the table
    if res_id =='None':
        data = utilities.parse_JSON()
        try:
            file_data = data['timeSeriesLayerResource']
            file_data = json.loads(file_data)
        except:
            file_data=''
        print file_data
        if file_data=='':
            try:
                file_data = data['timeSeriesLayerResource']
            except:
                file_data=''
        if file_data =='':
            error = "No data in file"
        else:
            error=''
    else:
        temp_dir = utilities.get_workspace()
        root_dir = temp_dir + '/id/' + res_id
        try: #Insures that resource is downloaded each time
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
            print "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDd"
            delay=0
            print res_id
            resource = None

            while(status =='running' or delay<10):
                print "looping"

                if (delay>10):
                    error ='Request timed out'
                    break
                elif( status =='done'):
                    error =''
                    break
                else:
                    try:
                        print "downloading"
                        res_info = hs.getSystemMetadata(res_id)
                        res_info = res_info['public']

                        hs.getResource(res_id, destination=file_path, unzip=True)

                        print status
                        print resource
                        root_dir = file_path + '/' + res_id
                        data_dir = root_dir + '/' + res_id + '/data/contents/'
                        for subdir, dirs, files in os.walk(data_dir):
                            for file in files:
                                if '.json.refts' in file:
                                    data_file = data_dir +file
                                    with open(data_file, 'r') as f:
                                        file_data = f.read()
                                        # print file_data
                                        file_data= file_data.encode(encoding ='UTF-8')
                                        file_data = json.loads(file_data)
                                        file_data = file_data['timeSeriesLayerResource']


                        if file_data ==None:
                            status = 'running'
                            time.sleep(2)
                        else:
                            status = 'done'
                    except:
                        error='error'
                        status = 'running'
                        time.sleep(2)

                delay=delay+1
                print delay
                print error
                print status
    # data_for_chart = {"data": '{"fileVersion":1,"title":"HydroClient-2017-01-09T17:46:47.810Z","abstract":"Retrieved timeseries...","symbol":"http://data.cuahsi.org/content/images/cuahsi_logo_small.png","keyWords":["Time Series","CUAHSI"],"REFTS":[{"refType":"WOF","serviceType":"SOAP","url":"http://hydro1.sci.gsfc.nasa.gov/daac-bin/his/1.0/GLDAS_NOAH_001.cgi?WSDL","site":"X282-Y404 of Global Land Data Assimilation System (GLDAS) NASA","siteCode":"GLDAS_NOAH:X282-Y404","variable":"Surface runoff","variableCode":"GLDAS:GLDAS_NOAH025_3H.001:Qs","networkName":"GLDAS_NOAH","beginDate":"2016-01-09T00:00:00","endDate":"2016-09-30T21:00:00+00:00","returnType":"WaterML 1.0","location":{"latitude":41.125,"longitude":-109.375}}]}','error':error}
    data_for_chart = {"data": file_data,'error':error,"public":res_info}
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
def create_layer(request,fun_type,res_id,res_type):
    resource_id=None
    data_stor=[]
    int_resource=[]
    counter=0
    error=''
    public ='false'
    title = str(request.POST.get('resTitle'))
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords'))
    res_access = str(request.POST.get('resAccess'))
    str_resource = request.POST.get('checked_ids')

    keywords = keywords.split(',')
    str_resource = trim(str_resource)
    file_name = title.replace(" ", "")
    file_name = file_name[:10]


    try:
        for res in str_resource:
            int_resource.append(int(res))
        metadata = []
        if use_hs_client_helper:
            hs = get_oauth_hs(request)
        else:
            hs = getOAuthHS(request)
        temp_dir = utilities.get_workspace()
        # print title.lstrip(10)
        fpath = temp_dir + '/id/'+file_name+'.json.refts' #path where file will be stored before upload to hydroshare
        if res_id =='null': #if resource is coming for data client
            file_path = temp_dir + '/id/timeseriesLayerResource.json.refts'

        else: #if resource is already a HydroShare resource
            # file_path = temp_dir + '/id/timeseriesLayerResource.json.refts'
            data_dir = temp_dir+'/id/' + res_id
            for subdir, dirs, files in os.walk(data_dir):
                for file in files:
                    print file
                    if '.json.refts' in file:
                        print subdir
                        fname=file
                        file_path = subdir+'/'+file
        with open(file_path, 'r') as outfile:
            file_data = outfile.read()
            data = file_data.encode(encoding ='UTF-8')
            data = json.loads(data)
            # print data
            data = data['timeSeriesLayerResource']
            try:
                data_symbol = data['symbol']
                data_file =data['fileVersion']
            except:
                data = json.loads(data)
                data_symbol = data['symbol']
                data_file =data['fileVersion']

            for i in data['REFTS']:
                print i
                if counter in int_resource:
                    data_stor.append(i)
                counter = counter+1
            data_dic = {"REFTS":data_stor,"fileVersion": data_file, "title": title,
                        "symbol":data_symbol,"abstract": abstract,'keyWords':keywords}
            data.update(data_dic)
            final_dic = {"timeSeriesLayerResource":data}
            with open(fpath, 'w') as outfile:
                json.dump(final_dic, outfile)
        r_title = title
        r_keywords = (keywords)
        r_abstract = abstract
        print res_id
        if res_type == 'refts':
            r_type = 'GenericResource'


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
                        resource_id = hs.deleteResourceFile(res_id, fname)
                    except:
                        error = 'File does not exist'
                    resource_id = hs.addResourceFile(res_id, fpath)
                    temp_dir = utilities.get_workspace()
                    root_dir = temp_dir + '/id/' + res_id
                except:
                    error ="error"
                try:
                    shutil.rmtree(root_dir)
                    print "removing directory"
                except:
                    nothing =None
        elif res_type =='ts':
            print "odm2 stuff"
            # utilities.create_odm2(fpath,file_name)
            # r_type = 'TimeSeries'
            # r_title = "time series upload"
            # fpath = temp_dir + '/ODM2/ODM2_single_variable_multi_site.sqlite'
            print fpath
            # resource_id = hs.createResource(r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
            print resource_id
            print "AAAAAAAAAAA"

        print res_access
        if res_access == 'public':
            delay = 0
            while (public =='false' or delay<10):
                if (delay>10):
                    error ='Request timed out'
                    break
                else:
                    try:
                        print "making public"
                        print resource_id
                        hs.setAccessRules(resource_id, public=True)
                        public ='true'
                        print "break now"
                        break
                    except:
                        public='false'
                        time.sleep(2)
                    delay=delay+1

    except:
        error = 'At least one resource needs to be selected'
    # utilities.create_odm2(fpath,file_name)
    fpath = temp_dir+'/ODM2/'+file_name+'.sqlite'

    # utilities.create_csv(file_name)
    # fpath = temp_dir+'/ODM2/'+file_name+'.csv'

    print "database updated"
    r_type = 'TimeSeriesResource'
    r_title = "ODM test"
    # fpath = temp_dir + '/ODM2/ODM2_single_variable_multi_site.sqlite'



    # resource_id = hs.createResource(r_type, r_title, fpath, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
    # print resource_id
    print fpath


    #Create empty resource and then add file so metadate is parsed (Bug with hydroshare)
    # resource_id = hs.createResource(r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
    # resource_id1 = hs.addResourceFile(resource_id, fpath)



    "uploaded to HydroShare"
    return JsonResponse({'Request':resource_id,'error':error})
def trim(string_dic):
    string_dic=string_dic.strip('[')
    string_dic=string_dic.strip(']')
    string_dic=string_dic.strip('"')
    string_dic = string_dic.replace('"','')
    string_dic = string_dic.split(',' )
    return string_dic
@csrf_exempt
@never_cache
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