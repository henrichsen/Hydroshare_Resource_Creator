from lxml import etree
from lxml.builder import E
import numpy
import requests
import time
from datetime import timedelta
from dateutil import parser
from django.http import HttpResponse

from .app import HydroshareResourceCreator
import csv
import zipfile
import StringIO
import time
import zipfile
import os
import dateutil.parser
from datetime import datetime
import collections
import controllers
import shutil
import json
import urllib2

from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
import requests
import sqlite3
import datetime
from time import gmtime, strftime
from suds.client import Client
import sqlite3
import uuid
import datetime
import time


def get_app_base_uri(request):
    base_url = request.build_absolute_uri()
    if "?" in base_url:
        base_url = base_url.split("?")[0]
    return base_url


def get_workspace():

    return HydroshareResourceCreator.get_app_workspace().path
    #return app.get_app_workspace().path


def get_version(root):
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

def getResourceIDs(page_request):
    resource_string = page_request.GET['res_id']  # retrieves IDs from url
    resource_IDs = resource_string.split(',')  # splits IDs by commma
    return resource_IDs


def findZippedUrl(page_request, res_id):
    base_url = page_request.build_absolute_uri()
    if "?" in base_url:
        base_url = base_url.split("?")[0]
        zipped_url = base_url + "temp_waterml/" + res_id + ".xml"
        return zipped_url




def read_error_file(xml_file):
    try:
        f = open(xml_file)
        return {'status': f.readline()}
    except:
        return {'status': 'invalid WaterML file'}

# finds the waterML file path in the workspace folder
def waterml_file_path(res_id):
    base_path = get_workspace()
    file_path = base_path + "/id/" + res_id
    if not file_path.endswith('.xml'):
        file_path += '.xml'
    return file_path


def file_unzipper(url_cuashi):
    #this function is for unzipping files
    r = requests.get(url_cuashi)
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    file_list = z.namelist()
    for  file in file_list:
        z.read(file)
    return file_list
def error_report(file):
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/error_report.txt'
    file_temp = open(file_temp_name, 'a')

    time = datetime.now()
    time2 = time.strftime('%Y-%m-%d %H:%M')



    file_temp.write(time2+"\n"+file+"\n")
    file_temp.close()
    file_temp.close()
def create_ts_layer_resource(title):
    root = etree.Element('TimeSeriesLayerResource')
    doc = etree.ElementTree(root)
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/hydroshare/' + title + '.xml'
    outFile = open(file_temp_name, 'w')
    doc.write(outFile)
def append_ts_layer_resource(title,metadata):
    print metadata
    lon = metadata['Lon']
    lat = metadata['Lat']

    # RefType =metadata['RefType']
    servicetype = metadata['ServiceType']
    # URL = metadata['URL']
    returntype = metadata['ReturnType']

    # print "adding to file"
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/hydroshare/' + title + '.xml'
    print file_temp_name
    tree = etree.parse(file_temp_name)

    root = tree.getroot()

    print root
    REFTS = etree.SubElement(root,'REFTS')

    RefType = etree.SubElement(REFTS,"RefTye")
    RefType.text='WOF'

    ServiceType= etree.SubElement(REFTS,"ServiceType")
    ServiceType.text= servicetype

    URL= etree.SubElement(REFTS,"URL")
    URL.text='www.hydroserver.com'

    ReturnType= etree.SubElement(REFTS,"ReturnType")
    ReturnType.text= returntype

    Location= etree.SubElement(REFTS,"Location")
    Location.text= lon+', '+ lat
    doc = etree.ElementTree(root)
    doc.write(file_temp_name)
def get_hydroshare_resource(request,res_id,data_for_chart):
    error = False
    is_owner = False
    file_path = get_workspace() + '/id'
    root_dir = file_path + '/' + res_id
    #
    # elif 'hydroshare_generic' in src:
    #     target_url =  'https://www.hydroshare.org/django_irods/download/'+res_id+'/data/contents/HIS_reference_timeseries.txt'
    #     d

    try:
        shutil.rmtree(root_dir)
    except:
        nothing =None
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
                            print data
                            try:
                                data= data.decode('latin-1')
                            except:
                                data = data
                            data_for_chart.update({str(file): data})

            # data_for_chart = {'bjo':'hello'}
            user =  hs.getUserInfo()
            user1 = user['username']
            # resource = hs.getResourceList(user ='editor')
            resource = hs.getResourceList(owner = user1)
            for  res in resource:
                # print res
                id = res["resource_id"]
                # print id
                if(res_id ==res["resource_id"]):
                    is_owner = True
            data_dic = {"data":data_for_chart,"owner":is_owner,"error":error}

            return data_dic
        except:
            error = "Unable to load resource"+res_id
            return error
    except Exception as inst:
        data_for_chart = 'You are not authorized to access this resource'
        owner = False
        error = True
        print 'start'
        print(type(inst))
        print(inst.args)
        try:
            data_for_chart = str(inst)
        except:
            data_for_chart = "There was an error loading data for resource"+res_id
        print "end"
def parse_JSON():
    temp_dir = get_workspace()
    # file=  temp_dir+'/id/timeSeriesResource.json'
    file=  temp_dir+'/id/timeseriesLayerResource.json.refts'
    with open(file,'r') as outfile:
        x = outfile.read()
        y = json.loads(x)
        return y
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
def parse_ts_layer(file_path,title):
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
    counter = 0
    print ('HIIIIIIIIIIIIIIIIIIIII')
    error=''
    response=None
    data = data.encode(encoding ='UTF-8')
    data = data.replace("'",'"')
    json_data = json.loads(data)
    json_data = json_data["timeSeriesLayerResource"]
    layer = json_data['REFTS']
    for sub in layer:
        ref_type= sub['refType']
        service_type = sub['serviceType']
        url =sub['url']
        site_code = sub['siteCode']
        variable_code = sub['variableCode']
        start_date = sub['beginDate']
        # start_date = ''
        end_date = sub['endDate']
        # end_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        auth_token = ''

        if ref_type =='WOF':
            if service_type =='SOAP':
                # print url
                # print site_code
                # print variable_code
                # print start_date
                # print end_date
                load_into_odm2(url,site_code,variable_code,start_date,end_date,title)
                # print client
                # site_code = 'NWISUV:10164500'
                # variable_code = 'NWISUV:00060'
                # start_date ='2016-06-03T00:00:00+00:00'
                # end_date = '2016-10-26T00:00:00+00:00'

                # client = connect_wsdl_url(url)
                # print client
                # print "client!!!!!!!!!!!!!!!!!!!!!"
                # sites = client.service.GetSiteInfo([site_code])
                # print sites
            #     try:
            #         response = client.service.GetValues(site_code, variable_code,start_date,end_date,auth_token)
            #     except:
            #         error = "unable to connect to HydroSever"
            #     # print response
            #     print "AAAAAAAAAAAAAAA"
            #     temp_dir = get_workspace()
            #     file_path = temp_dir + '/id/' + 'timeserieslayer'+str(counter) + '.xml'
            #     try:
            #         response = response.encode('utf-8')
            #     except:
            #         response = response
            #     # print response1
            #     # print "Response"
            #     # response1 = unicode(response1.strip(codecs.BOM_UTF8), 'utf-8')
            #     with open(file_path, 'w') as outfile:
            #         outfile.write(response)
            #     print "done"
            # if(service_type=='REST'):
            #     waterml_url = url+'/GetValueObject'
            #     response = urllib2.urlopen(waterml_url)
            #     html = response.read()
            counter = counter +1
    return counter
def Original_Checker(xml_file):
    print xml_file
    tree = etree.parse(xml_file)
    root = tree.getroot()
    wml_version = get_version(root)
    print wml_version

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
        #     error_report("xml parse error")
        #     return read_error_file(xml_file)
        # except:
        #     error_report("xml parse error")
        #     return read_error_file(xml_file)
def parse_1_0_and_1_1(root):

    root_tag = root.tag.lower()

    master_values=collections.OrderedDict()
    master_times = collections.OrderedDict()
    master_boxplot = collections.OrderedDict()
    master_stat = collections.OrderedDict()
    meth_qual = [] # List of all the quality, method, and source combinations

    meta_dic ={'method':{},'quality':{},'source':{},'organization':{},'quality_code':{}}
    m_des = None
    m_code = None
    m_org =None

    master_counter =True
    nodata = "-9999"  # default NoData value. The actual NoData value is read from the XML noDataValue tag
    timeunit=None
    sourcedescription = None
    timesupport =None
    units, site_name, variable_name,quality,method,organization = None

    datatype = None
    valuetype = None
    samplemedium = None

    unitId,unitAb =None
    varCode,speciation = None

    q_code,q_des,q_exp,q_id =None
    processCode, processDef, processExpl,processId = []

    m_code,m_name,m_des,m_link,m_id = None
    methCode,methName,methDes,methLink,methId=[]

    o_code,o_name,o_des,o_link = None
    orgCode,OrgName,OrgDes,Olink = []
    try:
        if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag or 'timeSeriesResponse' in root_tag:

            # lists to store the time-series data

            # iterate through xml document and read all values
            for element in root.iter():
                bracket_lock = -1
                if '}' in element.tag:
                    # print element.tag
                    bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                    tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace
                    tag = tag.lower()

                    if 'value'!= tag:
                        # in the xml there is a unit for the value, then for time. just take the first
                        # print tag
                        if 'unitName' == tag or 'units' ==tag:
                            units = element.text
                        if 'unitCode' == tag:
                            unitId = element.text
                        if 'unitabbreviation' ==tag:
                            unitAb = element.text

                        if 'variablecode' in tag:
                            varCode = element.text
                        if 'variableName' == tag:
                            variable_name = element.text
                        if 'noDataValue' == tag:
                            nodata = element.text
                        if 'speciation' in tag:
                            speciation = element.text



                        if "qualitycontrollevel" in tag:
                            try:
                                q_id= element.attrib['qualityControlLevelID']
                            except:
                                q_id ='None'
                            for subele in element:
                                if 'qualitycontrollevelcode' in subele.tag.lower():
                                    q_code = subele.text
                                    q_code = m_code.replace(" ","")
                                if 'definition' in subele.tag.lower():
                                    q_des = subele.text
                                if 'explanation' in subele.tag.lower():
                                    q_exp = subele.text
                            processCode.append(q_code)
                            processDef.append(q_des)
                            processExpl.append(q_exp)
                            processId.append(q_id)

                            m_code,m_name,m_des,m_link,m_id = None
                            methCode,methodName,methodDes,methLink, methId=[]


                        if "method" in tag:
                            try:
                                m_id = element.attrib['methodID']
                            except:
                                m_id ='None'
                            for subele in element:
                                if 'methodcode' in subele.tag.lower():
                                    m_code = subele.text
                                    m_code = m_code.replace(" ","")
                                if 'methodname'in subele.tag.lower():
                                    m_name = subele.text
                                if 'methoddescription' in subele.tag.lower():
                                    m_des = subele.text
                                if 'methodLink' in subele.tag.lower():
                                    m_link =subele.text
                            methCode.append(m_code)
                            methName.append(m_name)
                            methDes.append(m_des)
                            methLink.append(m_link)
                            methId.append(m_id)
                            # meta_dic['method'].update({m_code:m_des})

                        o_code,o_name,o_des,o_link = None
                        orgCode,OrgName,OrgDes,Olink = []

                        if "source" ==tag.lower():
                            for subele in element:
                                if'organization'in subele.tag.lower():
                                    o_name = subele.text
                                if 'sourcecode' in subele.tag.lower():
                                    o_code = subele.text
                                    o_code = o_code.replace(" ","")
                                if 'sourcedescription' in subele.tag.lower():
                                    o_des = subele.text
                                if 'sourceLink' in subele.tag.lower():
                                    o_link = subele.text
                                print subele
                            meta_dic['source'].update({m_code:m_des})
                            meta_dic['organization'].update({m_code:m_org})







                        if 'siteName' == tag:
                            site_name = element.text

                        if 'organization'==tag or 'sitecode'==tag:
                            try:
                                organization = element.attrib['agencyCode']
                            except:
                                organization = element.text
                        if 'dataType' == tag :
                            datatype = element.text
                        if 'valueType' == tag:
                            valuetype = element.text
                        if "sampleMedium" == tag:
                            samplemedium = element.text
                        if "timeSupport"== tag or"timeInterval" ==tag:
                            timesupport =element.text
                        if"unitName"== tag or "UnitName"==tag:
                            timeunit =element.text
                        if"sourceDescription"== tag or "SourceDescription"==tag:
                            sourcedescription =element.text




                            # print meta_dic
                    elif 'value' == tag:
                        n =element.attrib['dateTime']
                        try:
                            quality= element.attrib['qualityControlLevelCode']
                        except:
                            quality =''
                        try:
                            quality1 = element.attrib['qualityControlLevel']
                        except:
                            quality1 =''
                        if quality =='' and quality1 != '':
                            quality = quality1
                        try:
                            method = element.attrib['methodCode']
                        except:
                            method=''
                        try:
                            method1 = element.attrib['methodID']
                        except:
                            method1=''
                        if method =='' and method1 != '':
                            method = method1
                        try:
                            source = element.attrib['sourceCode']
                        except:
                            source=''
                        try:
                            source1 = element.attrib['sourceID']
                        except:
                            source1=''
                        if source =='' and source1 != '':
                            source = source1
                        dic = quality +'aa'+method+'aa'+source
                        dic = dic.replace(" ","")


                        if dic not in meth_qual:

                            meth_qual.append(dic)
                            master_values.update({dic:[]})
                            master_times.update({dic:[]})
                            master_boxplot.update({dic:[]})
                            master_stat.update({dic:[]})
                            # master_data_values.update({dic:[]})

                        v = element.text
                        if v == nodata:
                            value = None
                            # x_value.append(n)
                            # y_value.append(value)
                            v =None

                        else:
                            v = float(element.text)
                            # x_value.append(n)
                            # y_value.append(v)
                            # master_data_values[dic].append(v) #records only none null values for running statistics
                        master_values[dic].append(v)
                        master_times[dic].append(n)





            return {
                'site_name': site_name,
                'variable_name': variable_name,
                'units': units,
                'meta_dic':meta_dic,

                'organization': organization,
                'quality': quality,
                'method': method,
                'status': 'success',
                'datatype' :datatype,
                'valuetype' :valuetype,
                'samplemedium':samplemedium,
                'timeunit':timeunit,
                'sourcedescription' :sourcedescription,
                'timesupport' : timesupport,
                'master_counter':master_counter,

                'master_values':master_values,
                'master_times':master_times,
                'master_boxplot':master_boxplot,
                'master_stat':master_stat,
                # 'master_data_values':master_data_values
            }
        else:
            parse_error = "Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series"
            error_report("Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series")
            print parse_error
            return {
                'status': parse_error
            }
    except Exception, e:
        data_error = "Parsing error: The Data in the Url, or in the request, was not correctly formatted for water ml 1."
        error_report("Parsing error: The Data in the Url, or in the request, was not correctly formatted.")
        print data_error
        print e
        return {
            'status': data_error
        }
def create_odm2(file_path,title):
    print "odm2 stuff"
    temp_dir = get_workspace()
    series_number = parse_ts_layer(file_path,title)
    series_number =1
    print series_number
    for series in range(0,series_number):
        file_path_series = temp_dir + '/id/timeserieslayer'+str(series)+'.xml'


        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-09-13-57929645.xml'
        file_path_series = temp_dir+'/id/timeserieslayer0.xml' #multiple methods
        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-05-05-55046159.xml' #multiple quality


        data = Original_Checker(file_path_series) #parses waterml file
        # odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'


        # insert_odm2(data,title) #inserts waterml data into ODM2 database
        #read and parse time series
        #copy blank odm2
        #take data and insert metadata and then dates and values
        #return file path of filled odm2

def parsing_test(root):
    root_tag = root.tag.lower()

    master_values=collections.OrderedDict()


    result_total = [] # List of all the quality, method, and source combinations
    value_counter=0
    quality_key=None
    method_key = None
    source_key = None

    nodata = "-9999"  # default NoData value. The actual NoData value is read from the XML noDataValue tag

    # units, site_name, variable_name,quality,method,organization = None,None,None,None,None,None
    datatype = None
    valuetype = None
    samplemedium = None

    unitId,unitAb =None,None
    varCode,speciation = None,None

    q_code,q_def,q_exp,q_id =None,None,None,None
    qualityCode, qualityDef, qualityExpl,qualityId = [],[],[],[]
    quality_levels =[]

    m_code,m_name,m_des,m_link,m_id = None,None,None,None,None
    methCode,methName,methDes,methLink,methId=[],[],[],[],[]
    methods=[]

    o_code,o_name,o_des,o_link,o_per_name,o_per_email,o_per_phone,o_per_add,o_per_link = None,None,None,None,None,None,None,None,None
    orgCode,orgName,orgDes,orglink,orgPerName,orgPerEmail,orgPerPhone,orgPerAdd,orgPerLink = [],[],[],[],[],[],[],[],[]
    organizations =[]
    people =[]
    affliations=[]
    sam_code,sam_name,sam_des,sam_fea,sam_geo_wkt,sam_ele,sam_dat =None,None,None,None,None,None,None
    lat, long =None,None

    time_interval,time_code,time_ab,time_unit = None,None,None,None
    UTCOfset=None
    if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag or 'timeSeriesResponse' in root_tag:

        # lists to store the time-series data
        # iterate through xml document and read all values
        for element in root.iter():
            bracket_lock = -1
            if '}' in element.tag:
                # print element.tag
                bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace
                tag = tag.lower()
                if 'value'!= tag:
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
                        speciation = element.text

                    if "qualitycontrollevel" == tag.lower():
                        try:
                            q_id= element.attrib['qualityControlLevelID']
                        except:
                            q_id ='None'
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if 'qualitycontrollevelcode' in subele_text:
                                q_code = subele.text
                                q_code = q_code.replace(" ","")
                            if 'definition' in subele_text:
                                q_def = subele.text
                            if 'explanation' in subele_text:
                                q_exp = subele.text
                        quality_levels.append((None,q_code,q_def,q_exp))
                        # qualityCode.append(q_code)
                        # qualityDef.append(q_des)
                        # qualityExpl.append(q_exp)
                        qualityId.append(q_id)

                    if "method" == tag.lower():
                        try:
                            m_id = element.attrib['methodID']
                        except:
                            m_id ='None'
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if 'methodcode' in subele_text:
                                m_code = subele.text
                                m_code = m_code.replace(" ","")
                            if 'methodname'in subele_text:
                                m_name = subele.text
                            if 'methoddescription' in subele_text:
                                m_des = subele.text
                            if 'methodLink' in subele_text:
                                m_link =subele.text
                        # print "adding methods to sub dic"

                        methods.append((None,'Instrument deployment',m_code,"hi",m_des,m_link,None))
                        # methCode.append(m_code)
                        # methName.append(m_name)
                        # methDes.append(m_des)
                        # methLink.append(m_link)
                        # methId.append(m_id)

                    if "source" ==tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()
                            if'organization'in subele_text:
                                o_name = subele.text
                            if 'sourcecode' in subele_text:
                                o_code = subele.text
                                o_code = o_code.replace(" ","")
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
                                    o_per_fname =  o_per_name
                                    o_per_lname =  o_per_name
                            if 'email'in subele_text:
                                o_per_email = subele.text
                            if 'phone'in subele_text:
                                o_per_phone = subele.text
                            if 'adress'in subele_text:
                                o_per_add = subele.text
                            if 'link'in subele_text:
                                o_per_link = subele.text
                            start_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        organizations.append((None,'unknown',o_code,o_name,o_des,o_link,None))
                        people.append((None,o_per_fname,None,o_per_lname))
                        affliations.append([None,None,None,'1',start_date,None,o_per_phone,o_per_email,o_per_add,o_per_link])
                        orgPerName.append(o_per_name)
                        orgPerEmail.append(o_per_email)
                        orgPerPhone.append(o_per_phone)
                        orgPerAdd.append(o_per_add)
                        orgPerLink.append(o_per_link)
                        orgCode.append(o_code)
                        orgDes.append(o_des)
                        orglink.append(o_link)
                        orgName.append(o_name)

                    if 'sourceinfo' ==tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()

                            if 'sitecode'in subele_text:
                                sam_code =subele.text
                            if 'sitename'in subele_text:
                                sam_name = subele.text
                            if 'sitedescription' in subele_text:
                                sam_description = subele.text
                            if 'featuregeometry' in subele_text:
                                sam_fea = subele.text
                            if 'latitude'in subele_text:
                                lat = subele.text
                            if 'longitude'in subele_text:
                                long = subele.text
                            if 'elevation_m' in subele_text:
                                sam_ele = subele.text
                            if 'verticaldatum' in subele_text:
                                sam_dat = subele.text

                            if 'latitude' in  subele_text:
                                lat = subele.text
                            if 'longitude' in  subele_text:
                                long = subele.text

                        sam_geo_wkt = 'POINT('+long+','+lat+')'

                    if 'dataType' == tag :
                        datatype = element.text
                    if 'valueType' == tag:
                        valuetype = element.text
                    if "sampleMedium" == tag:
                        samplemedium = element.text
                    if "timescale" in tag.lower():
                        for subele in element.iter():
                            subele_text = subele.tag.lower()

                            if 'timesupport' in subele_text:
                                time_interval = subele.text
                            if 'unitname' in subele_text:
                                time_unit = subele.text
                            if 'unitabbreviation'in subele_text:
                                time_ab = subele.text
                            if 'unitcode' in subele_text:
                                time_code = subele.text
                elif 'value' == tag:
                    quality_str = 'quality'
                    method_str = 'method'
                    source_str = 'source'
                    if value_counter ==0:
                        l = element.keys()
                        for s in l:
                            if quality_str in s.lower():
                                quality_key = s
                            if method_str in s.lower():
                                method_key =s
                            if source_str in s.lower():
                                source_key=s
                    n =element.attrib['dateTime']
                    UTCOfset = element.attrib['timeOffset']
                    try:
                        quality= element.attrib[quality_key]
                    except:
                        quality=''
                    try:
                        method = element.attrib[method_key]
                    except:
                        method = ''
                    try:
                        source = element.attrib[source_key]
                    except:
                        source=''
                    v = element.text
                    if v == nodata:
                        v =None
                    else:
                        v = float(element.text)
                    result_entry = quality+'aa'+method+'aa'+source
                    result_entry = result_entry.replace(" ","")

                    if result_entry not in result_total:
                        result_total.append(result_entry)
                        master_values.update({result_entry:[]})
                    master_values[result_entry].append([n,v,quality,method,source,time_interval,time_code])
                    value_counter += 1
        print methods
        # quality_levels.extend((qualityCode, qualityDef, qualityExpl,qualityId))
        # methods.append((methCode,methName,methDes,methLink,methId))
        # organizations.append((orgCode,orgName,orgDes,orglink,orgPerName,orgPerEmail,orgPerPhone,orgPerAdd,orgPerLink))

        print "end of waterml data!!!!!!!!!!!!!!"
        # quality_sqlite = 'Insert Into ProcessingLevels(ProcessingLevelCode,Definition,Explanation) Values(?,?,?)'
        quality_sqlite = 'Insert Into ProcessingLevels Values(?,?,?,?)'
        method_sqlite = 'Insert Into Methods Values(?,?,?,?,?,?,?)'
        organizations_sqlite = 'Insert Into Organizations Values(?,?,?,?,?,?,?)'
        people_sqlite ='Insert Into People Values(?,?,?,?)'

        print organizations
    return {
        # 'data_values':master_values,
        'quality_levels':quality_levels,
        'methods':methods,
        'people':people,
        'organizations':organizations,
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
def insert_odm2(data,title):
    temp_dir = get_workspace()

    print "loading into database"
    odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'
    # odm_master = temp_dir+'/ODM2/ODM2_7series_test_addingValues.sqlite'
    odm_copy = temp_dir+'/ODM2/'+title+'.sqlite'
    shutil.copy(odm_master,odm_copy)
    #insert into TimeSeriesResultValues

    people_sqlite ='Insert Into People Values(?,?,?,?)'
    value = [(None,'Joe',None,"Black")]



    for entry in data:
        conn = sqlite3.connect(odm_copy, isolation_level=None)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION;")
        c.executemany(data[entry][0],data[entry][1]) #list of tuples
        c.execute("COMMIT;")
        conn.close()
def create_csv(file_name):

    temp_dir = get_workspace()
    file_path_series = temp_dir + '/ODM2/'+file_name+'.csv'
    print file_path_series
    with open(file_path_series, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(0,1000000):
            spamwriter.writerow(['2007-01-01 12:30:00',str(i)])
def load_into_odm2(url,siteCode,variableCode,beginDate,endDate,title):
    print "load into odm2111"
    # -------------------------------------------------------------------------------
    # Summary: Load data from multiple WaterML 1.1 files into an ODM2 SQLite database
    # Created by: Jeff Horsburgh
    # Created on: 5-20-2016
    #
    # Requirements:
    # 1.  Expects a blank ODM2 SQLite database called ODM2.sqlite in the same
    #     directory as this script. CVs should already be loaded.
    # 2.  Expects a WSDL URL for a WaterOneFlow web service that can deliver
    #     WaterML 1.1 responses.
    # 3.  Requires NetworkCode, SiteCode, BeginDate and
    #     EndDate for each of the web service calls.
    #
    # Outputs:
    # 1.  Loads data into the input ODM2.sqlite database
    #
    # NOTE: WaterML 1.1 does not have all of the information needed to
    #       populate the ODM2 database. I have made notes below where that
    #       is the case.
    # TODO: DataValue qualifiers need to be handled - this script doesn't load them
    # TODO: Handle MethodLinks correctly.
    # TODO: Handle SpatialReferences for sites correctly
    # -------------------------------------------------------------------------------

    # Create the connection to the SQLite database and get a cursor
    # -------------------------------------------------------------
    temp_dir = get_workspace()
    print "loading into database1111111111111111111111111111"
    odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'
    # odm_master = temp_dir+'/ODM2/ODM2_7series_test_addingValues.sqlite'
    odm_copy = temp_dir+'/ODM2/'+title+'.sqlite'
    shutil.copy(odm_master,odm_copy)
    #insert into TimeSeriesResultValues

    conn = sqlite3.connect(odm_copy, isolation_level=None)
    # c = conn.cursor()
    # c.execute("BEGIN TRANSACTION;")
    # # c.executemany(data[entry][0],data[entry][1]) #list of tuples
    # c.execute("COMMIT;")


    # Get the Dataset information and load it into the database
    # ------------------------------------------------------------------------
    # NOTE: The WaterML files doesn't have information in it to satisfy many of the Dublin Core elements of the
    # HydroShare Science Metadata. However ODM2 is capable of storing some of this information and so I am going
    # to load it into the database. I have this information because I know this particular data, but it obviously
    # wouldn't be available from other WaterML files
    # conn = sqlite3.connect('ODM2.sqlite')
    print "dateset"
    c = conn.cursor()
    dataSetInfo = (str(uuid.uuid1()),
                   'Multi-time series',
                    variableCode,
                   'Water temperature data from the Little Bear River, UT',
                   'This dataset contains time series of observations of water temperature in '
                   'the Little Bear River, UT. Data were recorded every '
                   '30 minutes. The values were recorded using a HydroLab MS5 multi-parameter water quality '
                   'sonde connected to a Campbell Scientific datalogger. ')

    c.execute('INSERT INTO Datasets(DataSetID, DataSetUUID, DataSetTypeCV, DataSetCode, DataSetTitle, DataSetAbstract) '
              'VALUES (NULL, ?, ?, ?, ?, ?)', dataSetInfo)

    # Get the ID of the DataSet record I just inserted
    dataSetID = c.lastrowid

    # Save (commit) the changes
    conn.commit()

    # Loop through the sites, get the time series for each site, and load into the ODM2 database
    # ------------------------------------------------------------------------------------------

    # Construct the variableCode string to pass to the web service
    variableCodeString = variableCode + ':qualityControlLevelCode=1'
    # Call the web service to return the data values for the current time series
    client = connect_wsdl_url(url)
    autho_token =''
    print url
    print "connect to database"
    print url
    print siteCode
    print variableCode
    print beginDate
    print endDate
    print autho_token
    valuesResult = client.service.GetValuesObject(siteCode, variableCode,
                                                  beginDate, endDate,autho_token)
    # print valuesResult
    # Check to make sure there are data values. Otherwise, skip this series
    if len(valuesResult.timeSeries[0].values[0]) == 0:
    # There's no data values to load for the give site/variable/date range so skip
        print "No data"

    elif len(valuesResult.timeSeries[0].values[0].value) < 100:

    # There's a small number of water quality samples (not sensor data) so skip
        print "no sensor data"

    else:
        print "sample feature"
        # Get the SamplingFeatureInformation and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the sampling feature already exists
        siteCodeTup = (valuesResult.timeSeries[0].sourceInfo.siteCode[0].value,)
        c.execute('SELECT * FROM SamplingFeatures WHERE SamplingFeatureCode = ?', siteCodeTup)
        row = c.fetchone()

        if row == None:
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
                elevation_m = valuesResult.timeSeries[0].sourceInfo.elevation_m
            except:
                elevation_m = None
            try:
                verticalDatum = valuesResult.timeSeries[0].sourceInfo.verticalDatum
            except:
                verticalDatum = None
            samplingFeatureInfo = (str(uuid.uuid1()),
                                   'Site',
                                   valuesResult.timeSeries[0].sourceInfo.siteCode[0].value,
                                   valuesResult.timeSeries[0].sourceInfo.siteName,
                                   'Point',
                                   'POINT (' + str(valuesResult.timeSeries[0].sourceInfo.geoLocation.geogLocation.longitude) + ' ' + str(valuesResult.timeSeries[0].sourceInfo.geoLocation.geogLocation.latitude) + ')',
                                   elevation_m,
                                   verticalDatum)

            c.execute('INSERT INTO SamplingFeatures (SamplingFeatureID, SamplingFeatureUUID, '
                      'SamplingFeatureTypeCV, SamplingFeatureCode, SamplingFeatureName, SamplingFeatureDescription,'
                      'SamplingFeatureGeotypeCV, FeatureGeometry, FeatureGeometryWKT,'
                      'Elevation_m, ElevationDatumCV) VALUES (NULL,?,?,?,?,NULL,?,NULL,?,?,?)', samplingFeatureInfo)

            # Get the ID of the SamplingFeature I just created
            samplingFeatureID = c.lastrowid

            # Get the Site information and load it into the database
            # ----------------------------------------------------------------
            # The WaterML 1.1 response doesn't have the spatial reference for the latitude and longitude
            # Insert a record into SpatialReferences to indicate that it is unknown
            spatialReferenceInfo = ('Unknown', 'The spatial reference is unknown')

            c.execute('INSERT INTO SpatialReferences(SpatialReferenceID, SRSCode, SRSName, SRSDescription, SRSLink) '
                      'VALUES (NULL, NULL, ?, ?, NULL)', spatialReferenceInfo)

            # Get the ID of the SpatialReference I just created
            spatialReferenceID = c.lastrowid

            # WaterML 1.1 ----> ODM2 Mapping for Site Information
            # SamplingFeatureID = SamplingFeatureID of the record just loaded into the SamplingFeatures table
            # SiteTypeCV = Set to the WaterML SiteType property value for the site
            # Latitude = WaterML latitude
            # Longitude = WaterML longitude
            # SpatialReferenceID = SpatialReferenceID of the record just loaded into the SpatialReferences table
            try:
                sitetypecv =  valuesResult.timeSeries[0].sourceInfo.siteProperty[4].value
            except:
                sitetypecv =  'testing'
            siteInfo = (samplingFeatureID,
                        sitetypecv,
                        valuesResult.timeSeries[0].sourceInfo.geoLocation.geogLocation.latitude,
                        valuesResult.timeSeries[0].sourceInfo.geoLocation.geogLocation.longitude,
                        spatialReferenceID)

            c.execute('INSERT INTO Sites(SamplingFeatureID, SiteTypeCV, Latitude, Longitude, SpatialReferenceID) '
                      'VALUES (?, ?, ?, ?, ?)', siteInfo)

        else:  # The sampling feature and the site already exist in the database
            samplingFeatureID = row[0]

        # Get the Method information and load it into the database
        # ----------------------------------------------------------------
        # Check first to see if the method already exists
        # methodDescription = (valuesResult.timeSeries[0].values[0].method[0].methodDescription,)
        # print valuesResult.timeSeries[0].values[0]
        # methodDescription = ('hi',)
        try:
            methodDescription = valuesResult.timeSeries[0].values[0].method[0].methodDescription
            methodCode = valuesResult.timeSeries[0].values[0].method[0].methodCode
            methodLink = None
            c.execute('SELECT * FROM Methods WHERE MethodName = ?', methodDescription)
            row = c.fetchone()
        except:
            methodCode = 1
            methodDescription = 'unknown'
            methodLink = 'unknown'
            row =None


        if row == None:
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
            methodInfo = ('Instrument deployment',
                          methodCode,
                          methodDescription,
                          methodDescription,
                          methodLink)

            c.execute('INSERT INTO Methods(MethodID, MethodTypeCV, MethodCode, MethodName, MethodDescription, MethodLink) '
                      'VALUES (NULL, ?, ?, ?, ?, ?)', methodInfo)

            # Get the ID of the Method I just inserted
            methodID = c.lastrowid

        else:  # The method already exists in the database
            methodID = row[0]

        # Get the variable information and load it into the database
        # ----------------------------------------------------------------
        variableCodeTup = (variableCode,)
        c.execute('SELECT * FROM Variables WHERE VariableCode = ?', variableCodeTup)
        row = c.fetchone()

        if row == None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # VariableID = Automatically generated by SQLite as autoincrement
            # VariableTypeCV = WaterML generalCategory
            # VariableCode = WaterML variableCode
            # VariableNameCV = WaterML variableName
            # VariableDefinition = Set to NULL because it doesn't exist in WaterML and is not required
            # SpeciationCV = WaterML speciation
            # NoDataValue = WaterML noDataValue
            try:
                generalCategory=valuesResult.timeSeries[0].variable.generalCategory
            except:
                generalCategory = "Variable"
            try:
                speciation=valuesResult.timeSeries[0].variable.speciation
            except:
                speciation = None

            variableInfo = (generalCategory,
                            valuesResult.timeSeries[0].variable.variableCode[0].value,
                            valuesResult.timeSeries[0].variable.variableName,
                            speciation,
                            valuesResult.timeSeries[0].variable.noDataValue)

            c.execute('INSERT INTO Variables(VariableID, VariableTypeCV, VariableCode, VariableNameCV, VariableDefinition, SpeciationCV, NoDataValue) '
                      'VALUES (NULL, ?, ?, ?, NULL, ?, ?)', variableInfo)

            # Get the ID of the Variable I just inserted
            variableID = c.lastrowid

        else:  # The variable already exists
            variableID = row[0]

        # Get the Units information and load it into the database
        # ----------------------------------------------------------------
        unitsName = (valuesResult.timeSeries[0].variable.unit.unitName,)
        c.execute('SELECT * FROM Units WHERE UnitsName = ?', unitsName)
        row = c.fetchone()

        if row == None:
            # WaterML 1.1 ----> ODM2 Mapping for Variable Information
            # UnitsID = WaterML unitCode (this keeps it consistent with the ODM 1.1.1/WaterML 1.1 UnitIDs)
            # UnitsTypeCV = WaterML unitType
            # UnitsAbbreviation = WaterML unitAbbreviation
            # unitsName = WaterML unitName
            # unitsLink = NULL (doesn't exist in WaterML)
            try:
                unitCode = valuesResult.timeSeries[0].variable.unit.unitCode
            except:
                unitCode='1'
            try:
                unitType = valuesResult.timeSeries[0].variable.unit.unitType
            except:
                unitType='unknown'
            try:
                unitAbbreviation = valuesResult.timeSeries[0].variable.unit.unitAbbreviation
            except:
                unitAbbreviation='unknown'
            try:
                unitName = valuesResult.timeSeries[0].variable.unit.unitName
            except:
                unitName='unknown'
            unitsInfo = (unitCode,
                         unitType,
                         unitAbbreviation,
                         unitName)

            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName, UnitsLink) '
                      'VALUES (?, ?, ?, ?, NULL)', unitsInfo)

            # Get the ID of the Units I just inserted
            unitsID = c.lastrowid

        else:  # The unit already exists in the database
            unitsID = row[0]

        # Get the ProcessingLevel information and load it into the database
        # -----------------------------------------------------------------
        qualityControlLevelID = (valuesResult.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID,)
        c.execute('SELECT * FROM ProcessingLevels WHERE ProcessingLevelID = ?', qualityControlLevelID)
        row = c.fetchone()

        if row == None:
            # WaterML 1.1 ----> ODM2 Mapping for ProcessingLevel Information
            # ProcessingLevelID = WaterML _qualityControlLevelID
            # ProcessingLevelCode = WaterML qualityControlLevelCode
            # Definition = WaterML definition
            # Explanation = WaterML explanation
            processingLevelInfo = (valuesResult.timeSeries[0].values[0].qualityControlLevel[0]._qualityControlLevelID,
                                   valuesResult.timeSeries[0].values[0].qualityControlLevel[0].qualityControlLevelCode,
                                   valuesResult.timeSeries[0].values[0].qualityControlLevel[0].definition,
                                   valuesResult.timeSeries[0].values[0].qualityControlLevel[0].explanation)

            c.execute('INSERT INTO ProcessingLevels(ProcessingLevelID, ProcessingLevelCode, Definition, Explanation) '
                      'VALUES (?, ?, ?, ?)', processingLevelInfo)

            # Get the ID of the ProcessingLevel I just inserted
            processingLevelID = c.lastrowid

        else:  # The ProcessingLevel already exists in the database
            processingLevelID = row[0]

        # Get the People information and load it
        # -----------------------------------------------------------------
        try:
            contactName = valuesResult.timeSeries[0].values[0].source[0].contactInformation[0].contactName
        except:
            contactName = 'unknown unknown'
        splitName = contactName
        personInfo = (splitName[0], splitName[-1])
        c.execute('SELECT * FROM People WHERE PersonFirstName = ? AND PersonLastName=?', personInfo)
        row = c.fetchone()

        if row == None:
            # WaterML 1.1 ----> ODM2 Mapping for People Information
            # PersonID = Automatically generated by SQlite as autoincrement
            # PersonFirstName = First element of WaterML contactName split by space delimiter
            # PersonMiddleName = NULL (this could be problematic if a WaterML person actually has a middle name)
            # PersonLastName = Last element of WaterML contactName split by space delimiter

            c.execute('INSERT INTO People(PersonID, PersonFirstName, PersonLastName) '
                      'VALUES (NULL, ?, ?)', personInfo)

            # Get the ID of the person I just inserted
            personID = c.lastrowid

        else:  # The person already exists
            personID = row[0]

        # Get the Organization information and load it
        # -----------------------------------------------------------------
        organizationName = (valuesResult.timeSeries[0].values[0].source[0].organization,)
        c.execute('SELECT * FROM Organizations WHERE OrganizationName = ?', organizationName)
        row = c.fetchone()

        if row == None:
            # WaterML 1.1 ----> ODM2 Mapping for Organization Information
            # OrganizationID = Automatically generated by SQlite as autoincrement
            # OrganizationTypeCV = 'Unknown' (doesn't exist in WaterML, but required by ODM2)
            # OrganizationCode = WaterML sourceCode
            # OrganizationName = WaterML organization
            # OrganizationDescription = WaterML sourceDescription
            # OrganizationLink = waterML sourceLink
            # ParentOrganizationID = NULL (doesn't exist in WaterML)
            organizationInfo = ('unknown',
                                valuesResult.timeSeries[0].values[0].source[0].sourceCode,
                                valuesResult.timeSeries[0].values[0].source[0].organization,
                                valuesResult.timeSeries[0].values[0].source[0].sourceDescription,
                                valuesResult.timeSeries[0].values[0].source[0].sourceLink[0])

            c.execute('INSERT INTO Organizations(OrganizationID, OrganizationTypeCV, OrganizationCode, OrganizationName, OrganizationDescription, OrganizationLink) '
                      'VALUES (NULL, ?, ?, ?, ?, ?)', organizationInfo)

            # Get the ID of the Organization I just inserted
            organizationID = c.lastrowid

        else:  # The organization already exists
            organizationID = row[0]

        # Create the Affiliation between the person and the organization
        # -----------------------------------------------------------------
        c.execute('SELECT * FROM Affiliations WHERE PersonID = ? AND OrganizationID = ?', (personID, organizationID))
        row = c.fetchone()

        if row == None:
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
                phone=valuesResult.timeSeries[0].values[0].source[0].contactInformation[0].phone[0]
            except:
                phone="unknown"
            try:
                email=valuesResult.timeSeries[0].values[0].source[0].contactInformation[0].email[0]
            except:
                email= "unknown"
            affiliationInfo = (personID,
                               organizationID,
                               1,
                               datetime.datetime.now(),
                               phone,
                               email, )

            c.execute('INSERT INTO Affiliations(AffiliationID, PersonID, OrganizationID, IsPrimaryOrganizationContact, AffiliationStartDate, PrimaryPhone, PrimaryEmail) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?)', affiliationInfo)

            # Get the ID of the Affiliation I just inserted
            affiliationID = c.lastrowid

        else:  # The affilation already exists
            affilationID = row[0]

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
        # ActionDescription = 'An observation action that generated a time series result.' (HARD CODED FOR NOW - doesn't exist in WaterML)
        # ActionFileLink = NULL (doesn't exist in WaterML)
        actionInfo = ('Observation',
                      methodID,
                      valuesResult.timeSeries[0].values[0].value[0]._dateTime,
                      int(valuesResult.timeSeries[0].values[0].value[0]._timeOffset.split(':')[0]),
                      valuesResult.timeSeries[0].values[0].value[-1]._dateTime,
                      int(valuesResult.timeSeries[0].values[0].value[-1]._timeOffset.split(':')[0]),
                      'An observation action that generated a time series result.')

        c.execute('INSERT INTO Actions(ActionID, ActionTypeCV, MethodID, BeginDateTime, BeginDateTimeUTCOffset, EndDateTime, EndDateTimeUTCOffset, ActionDescription) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)', actionInfo)

        # Get the ID of the Action I just created.
        actionID = c.lastrowid

        # Create the ActionBy information and load it into the database
        # -----------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for ActionBy Information
        # BridgeID = Automatically generated by SQlite as autoincrement
        # ActionID = ID of the Action created above
        # AffiliationID = ID of the Affiliation created above
        # IsActionLead = 1 for 'True' (doesn't exist in WaterML, so hard coded)
        # RoleDescription = 'Responsible party' (doesn't exist in WaterML, so hard coded)
        actionByInfo = (actionID, affiliationID, 1, 'Responsible party')

        c.execute('INSERT INTO ActionBy(BridgeID, ActionID, AffiliationID, IsActionLead, RoleDescription) '
                  'VALUES (NULL, ?, ?, ?, ?)', actionByInfo)

        # Create the FeatureAction information and load it into the database
        # ------------------------------------------------------------------
        # WaterML 1.1 ----> ODM2 Mapping for FeatureAction Information
        # FeatureActionID = Automatically generated by SQlite as autoincrement
        # SamplingFeatureID = ID of the SamplingFeature created above
        # ActionID = ID of the Action created above
        featureActionInfo = (samplingFeatureID, actionID)

        c.execute('INSERT INTO FeatureActions(FeatureActionID, SamplingFeatureID, ActionID) '
                  'VALUES (NULL, ?, ?)', featureActionInfo)

        # Get the FeatureActionID for the record I just created
        featureActionID = c.lastrowid

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
        resultInfo = (str(uuid.uuid1()),
                      featureActionID,
                      'Time series coverage',
                      variableID,
                      unitsID,
                      processingLevelID,
                      datetime.datetime.now(),
                      -time.timezone/3600,
                      'unknown',
                      valuesResult.timeSeries[0].variable.sampleMedium,
                      len(valuesResult.timeSeries[0].values[0].value))

        c.execute('INSERT INTO Results(ResultID, ResultUUID, FeatureActionID, ResultTypeCV, VariableID, UnitsID, ProcessingLevelID, ResultDateTime, ResultDateTimeUTCOffset, StatusCV, SampledMediumCV, ValueCount) '
                  'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', resultInfo)

        # Get the ID for the Result I just created
        resultID = c.lastrowid

        # Load the Units information for the IntendedTimeSpacing into the database
        # ------------------------------------------------------------------------
        # NOTE: The intended time spacing information isn't in WaterML
        #       This is hard coded and could be problematic for some datasets.
        try:
            unitsInfo = ('unknown', 'unknown', 'unknown')

            c.execute('INSERT INTO Units(UnitsID, UnitsTypeCV, UnitsAbbreviation, UnitsName) '
                      'VALUES ( ?, ?, ?)', unitsInfo)

            # Get the ID of the Units I just inserted
            timeUnitsID = c.lastrowid
        except:
            timeUnitsID = 102
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
        # IntendedTimeSpacing = 30 (Hard Coded.  I know this for the test dataset, but would have to be null for generic WaterML files because it doesn't exist in WaterML)
        # IntendedTimeSpadingUnitsID = ID of TimeUnits created above (essentially hard coded - I know this for the test dataset, but would have to be null for generic WaterML files because it doesn't exist in WaterML)
        # AggregationStatisticCV = WaterML dataType
        timeSeriesResultInfo = (resultID, 30, timeUnitsID, valuesResult.timeSeries[0].variable.dataType)

        c.execute('INSERT INTO TimeSeriesResults(ResultID, IntendedTimeSpacing, IntendedTimeSpacingUnitsID, AggregationStatisticCV) '
                  'VALUES (?, ?, ?, ?)', timeSeriesResultInfo)

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
        tsResultValues = []
        numValues = len(valuesResult.timeSeries[0].values[0].value)
        for z in range(0, numValues-1):
            try:
                censorCode=valuesResult.timeSeries[0].values[0].value[z]._censorCode
            except:
                censorCode='unknown'
            try:
                timeSupport=valuesResult.timeSeries[0].variable.timeScale.timeSupport
            except:
                timeSupport='unknown'
            try:
                unitCode=valuesResult.timeSeries[0].variable.timeScale.unit.unitCode
            except:
                unitCode='unknown'

            tsResultValues.append((resultID,
                                   valuesResult.timeSeries[0].values[0].value[z].value,
                                   valuesResult.timeSeries[0].values[0].value[z]._dateTime,
                                   int(valuesResult.timeSeries[0].values[0].value[z]._timeOffset.split(':')[0]),
                                   censorCode,
                                   'Unknown',
                                   timeSupport,
                                   unitCode))
        c.execute("BEGIN TRANSACTION;")
        print "loading values and time into database"
        c.executemany('INSERT INTO TimeSeriesResultValues(ValueID, ResultID, DataValue, ValueDateTime, ValueDateTimeUTCOffset, CensorCodeCV, QualityCodeCV, TimeAggregationInterval, TimeAggregationIntervalUnitsID) '
                      'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)', tsResultValues)

        # Now create the DataSets Results bridge record
        dataSetsResultsInfo = (dataSetID, resultID)
        c.execute('INSERT INTO DataSetsResults(BridgeID, DataSetID, ResultID) Values (NULL, ?, ?)', dataSetsResultsInfo)

        # Save (commit) the changes
        c.execute("COMMIT;")
        conn.commit()

        # seriesCounter += 1
        print 'Loaded series Number '
    # Close the connection to the database
    # ------------------------------------
    conn.close()

    print 'Done loading data!'


def _extract_metadata(resource, sqlite_file_name):
    err_message = "Not a valid ODM2 SQLite file"
    # log = logging.getLogger()

    con = sqlite3.connect(sqlite_file_name)
    with con:
        # get the records in python dictionary format
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # populate the lookup CV tables that are needed later for metadata editing
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableType', CVVariableType)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableName', CVVariableName)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_Speciation', CVSpeciation)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_SiteType', CVSiteType)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_ElevationDatum', CVElevationDatum)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_MethodType', CVMethodType)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_UnitsType', CVUnitsType)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_Status', CVStatus)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_Medium', CVMedium)
        # _create_cv_lookup_models(cur, resource.metadata, 'CV_AggregationStatistic',
        #                          CVAggregationStatistic)

        # read data from necessary tables and create metadata elements
        # extract core metadata

        # extract abstract and title
        cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
        dataset = cur.fetchone()
        # update title element
        if dataset["DataSetTitle"]:
            resource.metadata.update_element('title', element_id=resource.metadata.title.id,
                                             value=dataset["DataSetTitle"])

        # create abstract/description element
        if dataset["DataSetAbstract"]:
            resource.metadata.create_element('description', abstract=dataset["DataSetAbstract"])

        # extract keywords/subjects
        # these are the comma separated values in the VariableNameCV column of the Variables
        # table
        cur.execute("SELECT VariableID, VariableNameCV FROM Variables")
        variables = cur.fetchall()
        keyword_list = []
        for variable in variables:
            keywords = variable["VariableNameCV"].split(",")
            keyword_list = keyword_list + keywords

        # use set() to remove any duplicate keywords
        for kw in set(keyword_list):
            resource.metadata.create_element("subject", value=kw)

        # find the contributors for metadata
        _extract_creators_contributors(resource, cur)

        # extract coverage data
        _extract_coverage_metadata(resource, cur)

        # extract extended metadata
        cur.execute("SELECT * FROM Sites")
        sites = cur.fetchall()
        is_create_multiple_site_elements = len(sites) > 1

        cur.execute("SELECT * FROM Variables")
        variables = cur.fetchall()
        is_create_multiple_variable_elements = len(variables) > 1

        cur.execute("SELECT * FROM Methods")
        methods = cur.fetchall()
        is_create_multiple_method_elements = len(methods) > 1

        cur.execute("SELECT * FROM ProcessingLevels")
        processing_levels = cur.fetchall()
        is_create_multiple_processinglevel_elements = len(processing_levels) > 1

        cur.execute("SELECT * FROM TimeSeriesResults")
        timeseries_results = cur.fetchall()
        is_create_multiple_timeseriesresult_elements = len(timeseries_results) > 1

        cur.execute("SELECT * FROM Results")
        results = cur.fetchall()
        for result in results:
            # extract site element data
            # Start with Results table to -> FeatureActions table -> SamplingFeatures table
            # check if we need to create multiple site elements
            cur.execute("SELECT * FROM FeatureActions WHERE FeatureActionID=?",
                        (result["FeatureActionID"],))
            feature_action = cur.fetchone()
            if is_create_multiple_site_elements or len(resource.metadata.sites) == 0:
                cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                            (feature_action["SamplingFeatureID"],))
                sampling_feature = cur.fetchone()

                cur.execute("SELECT * FROM Sites WHERE SamplingFeatureID=?",
                            (feature_action["SamplingFeatureID"],))
                site = cur.fetchone()
                if not any(sampling_feature["SamplingFeatureCode"] == s.site_code for s
                           in resource.metadata.sites):

                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    data_dict['site_code'] = sampling_feature["SamplingFeatureCode"]
                    data_dict['site_name'] = sampling_feature["SamplingFeatureName"]
                    if sampling_feature["Elevation_m"]:
                        data_dict["elevation_m"] = sampling_feature["Elevation_m"]

                    if sampling_feature["ElevationDatumCV"]:
                        data_dict["elevation_datum"] = sampling_feature["ElevationDatumCV"]

                    if site["SiteTypeCV"]:
                        data_dict["site_type"] = site["SiteTypeCV"]

                    data_dict["latitude"] = site["Latitude"]
                    data_dict["longitude"] = site["Longitude"]

                    # create site element
                    resource.metadata.create_element('site', **data_dict)
                else:
                    _update_element_series_ids(resource.metadata.sites[0], result["ResultUUID"])
            else:
                _update_element_series_ids(resource.metadata.sites[0], result["ResultUUID"])

            # extract variable element data
            # Start with Results table to -> Variables table
            if is_create_multiple_variable_elements or len(resource.metadata.variables) == 0:
                cur.execute("SELECT * FROM Variables WHERE VariableID=?",
                            (result["VariableID"],))
                variable = cur.fetchone()
                if not any(variable["VariableCode"] == v.variable_code for v
                           in resource.metadata.variables):

                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    data_dict['variable_code'] = variable["VariableCode"]
                    data_dict["variable_name"] = variable["VariableNameCV"]
                    data_dict['variable_type'] = variable["VariableTypeCV"]
                    data_dict["no_data_value"] = variable["NoDataValue"]
                    if variable["VariableDefinition"]:
                        data_dict["variable_definition"] = variable["VariableDefinition"]

                    if variable["SpeciationCV"]:
                        data_dict["speciation"] = variable["SpeciationCV"]

                    # create variable element
                    resource.metadata.create_element('variable', **data_dict)
                else:
                    _update_element_series_ids(resource.metadata.variables[0],
                                               result["ResultUUID"])
            else:
                _update_element_series_ids(resource.metadata.variables[0], result["ResultUUID"])

            # extract method element data
            # Start with Results table -> FeatureActions table to -> Actions table to ->
            # Method table
            if is_create_multiple_method_elements or len(resource.metadata.methods) == 0:
                cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                            (feature_action["ActionID"],))
                action = cur.fetchone()
                cur.execute("SELECT * FROM Methods WHERE MethodID=?", (action["MethodID"],))
                method = cur.fetchone()
                if not any(method["MethodCode"] == m.method_code for m
                           in resource.metadata.methods):

                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    data_dict['method_code'] = method["MethodCode"]
                    data_dict["method_name"] = method["MethodName"]
                    data_dict['method_type'] = method["MethodTypeCV"]

                    if method["MethodDescription"]:
                        data_dict["method_description"] = method["MethodDescription"]

                    if method["MethodLink"]:
                        data_dict["method_link"] = method["MethodLink"]

                    # create method element
                    resource.metadata.create_element('method', **data_dict)
                else:
                    _update_element_series_ids(resource.metadata.methods[0],
                                               result["ResultUUID"])
            else:
                _update_element_series_ids(resource.metadata.methods[0], result["ResultUUID"])

            # extract processinglevel element data
            # Start with Results table to -> ProcessingLevels table
            if is_create_multiple_processinglevel_elements \
                    or len(resource.metadata.processing_levels) == 0:
                cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?",
                            (result["ProcessingLevelID"],))
                pro_level = cur.fetchone()
                if not any(pro_level["ProcessingLevelCode"] == p.processing_level_code for p
                           in resource.metadata.processing_levels):

                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
                    if pro_level["Definition"]:
                        data_dict["definition"] = pro_level["Definition"]

                    if pro_level["Explanation"]:
                        data_dict["explanation"] = pro_level["Explanation"]

                    # create processinglevel element
                    resource.metadata.create_element('processinglevel', **data_dict)
                else:
                    _update_element_series_ids(resource.metadata.processing_levels[0],
                                               result["ResultUUID"])
            else:
                _update_element_series_ids(resource.metadata.processing_levels[0],
                                           result["ResultUUID"])

            # extract data for TimeSeriesResult element
            # Start with Results table
            if is_create_multiple_timeseriesresult_elements \
                    or len(resource.metadata.time_series_results) == 0:
                data_dict = {}
                data_dict['series_ids'] = [result["ResultUUID"]]
                data_dict["status"] = result["StatusCV"]
                data_dict["sample_medium"] = result["SampledMediumCV"]
                data_dict["value_count"] = result["ValueCount"]

                cur.execute("SELECT * FROM Units WHERE UnitsID=?", (result["UnitsID"],))
                unit = cur.fetchone()
                data_dict['units_type'] = unit["UnitsTypeCV"]
                data_dict['units_name'] = unit["UnitsName"]
                data_dict['units_abbreviation'] = unit["UnitsAbbreviation"]

                cur.execute("SELECT AggregationStatisticCV FROM TimeSeriesResults WHERE "
                            "ResultID=?", (result["ResultID"],))
                ts_result = cur.fetchone()
                data_dict["aggregation_statistics"] = ts_result["AggregationStatisticCV"]

                # create the TimeSeriesResult element
                resource.metadata.create_element('timeseriesresult', **data_dict)
            else:
                _update_element_series_ids(resource.metadata.time_series_results[0],
                                           result["ResultUUID"])

        return None


def _update_element_series_ids(element, series_id):
    element.series_ids = element.series_ids + [series_id]
    element.save()

def _extract_creators_contributors(resource, cur):
    # check if the AuthorList table exists
    authorlists_table_exists = False
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                ("table", "AuthorLists"))
    qry_result = cur.fetchone()
    if qry_result[0] > 0:
        authorlists_table_exists = True

    # contributors are People associated with the Actions that created the Result
    cur.execute("SELECT * FROM People")
    people = cur.fetchall()
    is_create_multiple_author_elements = len(people) > 1

    cur.execute("SELECT FeatureActionID FROM Results")
    results = cur.fetchall()
    authors_data_dict = {}
    author_ids_already_used = []
    for result in results:
        if is_create_multiple_author_elements or (len(resource.metadata.creators.all()) == 1 and
                                                  len(resource.metadata.contributors.all()) == 0):
            cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                        (result["FeatureActionID"],))
            feature_actions = cur.fetchall()
            for feature_action in feature_actions:
                cur.execute("SELECT ActionID FROM Actions WHERE ActionID=?",
                            (feature_action["ActionID"],))

                actions = cur.fetchall()
                for action in actions:
                    # get the AffiliationID from the ActionsBy table for the matching ActionID
                    cur.execute("SELECT AffiliationID FROM ActionBy WHERE ActionID=?",
                                (action["ActionID"],))
                    actionby_rows = cur.fetchall()

                    for actionby in actionby_rows:
                        # get the matching Affiliations records
                        cur.execute("SELECT * FROM Affiliations WHERE AffiliationID=?",
                                    (actionby["AffiliationID"],))
                        affiliation_rows = cur.fetchall()
                        for affiliation in affiliation_rows:
                            # get records from the People table
                            if affiliation['PersonID'] not in author_ids_already_used:
                                author_ids_already_used.append(affiliation['PersonID'])
                                cur.execute("SELECT * FROM People WHERE PersonID=?",
                                            (affiliation['PersonID'],))
                                person = cur.fetchone()

                                # get person organization name - get only one organization name
                                organization = None
                                if affiliation['OrganizationID']:
                                    cur.execute("SELECT OrganizationName FROM Organizations WHERE "
                                                "OrganizationID=?",
                                                (affiliation["OrganizationID"],))
                                    organization = cur.fetchone()

                                # create contributor metadata elements
                                person_name = person["PersonFirstName"]
                                if person['PersonMiddleName']:
                                    person_name = person_name + " " + person['PersonMiddleName']

                                person_name = person_name + " " + person['PersonLastName']
                                data_dict = {}
                                data_dict['name'] = person_name
                                if affiliation['PrimaryPhone']:
                                    data_dict["phone"] = affiliation["PrimaryPhone"]
                                if affiliation["PrimaryEmail"]:
                                    data_dict["email"] = affiliation["PrimaryEmail"]
                                if affiliation["PrimaryAddress"]:
                                    data_dict["address"] = affiliation["PrimaryAddress"]
                                if organization:
                                    data_dict["organization"] = organization[0]

                                # check if this person is an author (creator)
                                author = None
                                if authorlists_table_exists:
                                    cur.execute("SELECT * FROM AuthorLists WHERE PersonID=?",
                                                (person['PersonID'],))
                                    author = cur.fetchone()

                                if author:
                                    # save the extracted creator data in the dictionary
                                    # so that we can later sort it based on author order
                                    # and then create the creator metadata elements
                                    authors_data_dict[author["AuthorOrder"]] = data_dict
                                else:
                                    # create contributor metadata element
                                    resource.metadata.create_element('contributor', **data_dict)

    # TODO: extraction of creator data has not been tested as the sample database does not have
    # any records in the AuthorLists table
    authors_data_dict_sorted_list = sorted(authors_data_dict,
                                           key=lambda key: authors_data_dict[key])
    for data_dict in authors_data_dict_sorted_list:
        # create creator metadata element
        resource.metadata.create_element('creator', **data_dict)
def _create_cv_lookup_models(sql_cur, metadata_obj, table_name, model_class):
    sql_cur.execute("SELECT Term, Name FROM {}".format(table_name))
    table_rows = sql_cur.fetchall()
    for row in table_rows:
        model_class.objects.create(metadata=metadata_obj, term=row['Term'], name=row['Name'])
def _extract_coverage_metadata(resource, cur):
    # get point or box coverage
    cur.execute("SELECT * FROM Sites")
    sites = cur.fetchall()
    if len(sites) == 1:
        site = sites[0]
        if site["Latitude"] and site["Longitude"]:
            value_dict = {'east': site["Longitude"], 'north': site["Latitude"],
                          'units': "Decimal degrees"}
            # get spatial reference
            if site["SpatialReferenceID"]:
                cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                            (site["SpatialReferenceID"],))
                spatialref = cur.fetchone()
                if spatialref:
                    if spatialref["SRSName"]:
                        value_dict["projection"] = spatialref["SRSName"]

            resource.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        # in case of multiple sites we will create one coverage element of type 'box'
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for site in sites:
            if site["Latitude"]:
                if bbox['northlimit'] < site["Latitude"]:
                    bbox['northlimit'] = site["Latitude"]
                if bbox['southlimit'] > site["Latitude"]:
                    bbox['southlimit'] = site["Latitude"]

            if site["Longitude"]:
                if bbox['eastlimit'] < site['Longitude']:
                    bbox['eastlimit'] = site['Longitude']

                if bbox['westlimit'] > site['Longitude']:
                    bbox['westlimit'] = site['Longitude']

            if bbox['projection'] == 'Unknown':
                if site["SpatialReferenceID"]:
                    cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                                (site["SpatialReferenceID"],))
                    spatialref = cur.fetchone()
                    if spatialref:
                        if spatialref["SRSName"]:
                            bbox['projection'] = spatialref["SRSName"]

        resource.metadata.create_element('coverage', type='box', value=bbox)

    cur.execute("SELECT * FROM Results")
    results = cur.fetchall()
    min_begin_date = None
    max_end_date = None
    for result in results:
        cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                    (result["FeatureActionID"],))
        feature_action = cur.fetchone()
        cur.execute("SELECT BeginDateTime, EndDateTime FROM Actions WHERE ActionID=?",
                    (feature_action["ActionID"],))
        action = cur.fetchone()
        if min_begin_date is None:
            min_begin_date = action["BeginDateTime"]
        elif min_begin_date > action["BeginDateTime"]:
            min_begin_date = action["BeginDateTime"]

        if max_end_date is None:
            max_end_date = action["EndDateTime"]
        elif max_end_date < action["EndDateTime"]:
            max_end_date = action["EndDateTime"]

    # create coverage element
    value_dict = {"start": min_begin_date, "end": max_end_date}
    resource.metadata.create_element('coverage', type='period', value=value_dict)
