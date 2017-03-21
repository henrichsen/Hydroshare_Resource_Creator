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
def parse_ts_layer(file_path):
    # file_path_id = get_workspace() + '/id'
    # root_dir = file_path_id + '/' + res_id
    # data_dir = root_dir + '/' + res_id + '/data/contents/'
    # for subdir, dirs, files in os.walk(root_dir):
    #     for file in files:
    #         path = data_dir + file
    #         if '.json.refts' in file:

    with open(file_path, 'r') as f:
        data = f.read()
        # file_number = parse_ts_layer(file_data)
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
                print url
                print site_code
                print variable_code
                print start_date
                print end_date
                # print client
                # site_code = 'NWISUV:10164500'
                # variable_code = 'NWISUV:00060'
                # start_date ='2016-06-03T00:00:00+00:00'
                # end_date = '2016-10-26T00:00:00+00:00'

                client = connect_wsdl_url(url)
                # print client
                # print "client!!!!!!!!!!!!!!!!!!!!!"
                # sites = client.service.GetSiteInfo([site_code])
                # print sites
                try:
                    response = client.service.GetValues(site_code, variable_code,start_date,end_date,auth_token)
                except:
                    error = "unable to connect to HydroSever"
                # print response
                print "AAAAAAAAAAAAAAA"
                temp_dir = get_workspace()
                file_path = temp_dir + '/id/' + 'timeserieslayer'+str(counter) + '.xml'
                try:
                    response = response.encode('utf-8')
                except:
                    response = response
                # print response1
                # print "Response"
                # response1 = unicode(response1.strip(codecs.BOM_UTF8), 'utf-8')
                with open(file_path, 'w') as outfile:
                    outfile.write(response)
                print "done"
            if(service_type=='REST'):
                waterml_url = url+'/GetValueObject'
                response = urllib2.urlopen(waterml_url)
                html = response.read()
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
    # series_number = parse_ts_layer(file_path)
    series_number =1
    print series_number
    for series in range(0,series_number):
        file_path_series = temp_dir + '/id/timeserieslayer'+str(series)+'.xml'


        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-09-13-57929645.xml'
        file_path_series = temp_dir+'/id/timeserieslayer0.xml' #multiple methods
        # file_path_series = temp_dir+'/id/cuahsi-wdc-2016-05-05-55046159.xml' #multiple quality


        data = Original_Checker(file_path_series) #parses waterml file
        # odm_master = temp_dir+'/ODM2/ODM2_master.sqlite'


        insert_odm2(data,title) #inserts waterml data into ODM2 database
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
        'quality_levels':[quality_sqlite,quality_levels],
        'methods':[method_sqlite,methods],
        'people':[people_sqlite,people],
        'organizations':[organizations_sqlite,organizations],
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



        conn = sqlite3.connect(odm_copy, isolation_level=None)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION;")
        c.executemany(people_sqlite,value) #list of tuples
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
# def controlled_vocab(cv_name):
    # methods =(
    # Instrument retrieval
    # Instrument calibration
    # Expedition
    # Specimen preparation
    # Equipment programming
    # Derivation
    # Field activity
    # Unknown
    # Specimen collection
    # Equipment deployment
    # Observation
    # Cruise
    # Submersible launch
    # Data retrieval
    # Simulation
    # Estimation
    # Equipment maintenance
    # Generic non-observation
    # Equipment retrieval
    # Specimen preservation
    # Site visit
    # Instrument Continuing Calibration Verification
    # Specimen fractionation
    # Instrument deployment
    # Specimen analysis)

