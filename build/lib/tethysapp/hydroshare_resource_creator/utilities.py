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
            wml_title = "WaterML 2.0"
            break
        if '{http://www.cuahsi.org/waterML/1.1/}timeSeriesResponse' in element.tag:
            wml_version = '1'
            wml_title = "WaterML 1.1"
        if '{http://www.cuahsi.org/waterML/1.0/}timeSeriesResponse' in element.tag:
            wml_version = '1'
            wml_title = "WaterML 1.0"
            break
    return {'version':wml_version,'title':wml_title}

#drew 20150401 convert date string into datetime obj
def time_str_to_datetime(t):
    try:
        t_datetime=parser.parse(t)
        return t_datetime
    except ValueError:
        print "time_str_to_datetime error: "+ t
        raise Exception("time_str_to_datetime error: "+ t)
        return datetime.now()


#drew 20150401 convert datetime obj into decimal second (epoch second)
def time_to_int(t):
    try:
        d=parser.parse(t)
        t_sec_str=d.strftime('%s')
        return int(t_sec_str)
    except ValueError:
        print ("time_to_int error: "+ t)
        raise Exception('time_to_int error: ' + t)

def parse_service_info(xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()
    network = []
    url = []
    dic ={}
    for element in root.iter():
                bracket_lock = -1
                if '}' in element.tag:
                    # if 'waterML/1.1' in element.tag:
                    #     ReturnType = 'WaterML1.1'
                    # elif 'waterML/1.0' in element.tag
                    bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                    tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace

                    if tag == "servURL":
                        url.append(element.text)
                    if tag =='NetworkName':
                        network.append(element.text)
    i = 0
    for id in network:
        dic1 = {id:url[i]}
        dic.update(dic1)
        i = i+1
    return dic
def parse_1_0_and_1_1(root):

    root_tag = root.tag.lower()
    ReturnType= get_version(root)['title']
    ServiceType = None


    if "soap" in str(root):
        ServiceType="SOAP"
    else:
        ServiceType ="REST"
    # we only display the first 50000 values
    threshold = 50000000
    try:
        if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag or 'timeSeriesResponse' in root_tag:

            # lists to store the time-series data
            for_graph = []
            boxplot = []
            master_values=collections.OrderedDict()
            master_values1=collections.OrderedDict()
            master_times = collections.OrderedDict()
            master_boxplot = collections.OrderedDict()
            master_stat = collections.OrderedDict()
            master_data_values = collections.OrderedDict()
            # master_values = collections.namedtuple('id','time','value')
            meth_qual = [] # List of all the quality, method, and source combinations
            for_highchart = []
            for_canvas = []
            my_times = []
            my_values = []
            meta_dic ={'method':{},'quality':{},'source':{},'organization':{},'quality_code':{}}
            m_des = []
            u=0
            m_code = []
            m_org =[]
            quality={}
            source={}
            counter = 0
            x_value = []
            y_value = []
            master_counter =True
            nodata = "-9999"  # default NoData value. The actual NoData value is read from the XML noDataValue tag
            timeunit=None
            sourcedescription = None
            timesupport =None
            # metadata items
            units, site_name, variable_name,quality,method, organization = None, None, None, None, None, None
            unit_is_set = False
            datatype = None
            valuetype = None
            samplemedium = None
            smallest_value = 0
            n = None
            v = None
            t= 0
            times =[]
            x = 'x'
            y = 'y'
            RefType= None

            URL= None

            Lat = None
            Lon =None
            # iterate through xml document and read all values

            # print "parsing values from water ml"
            # print datetime.now()

            for element in root.iter():
                bracket_lock = -1
                if '}' in element.tag:
                    # if 'waterML/1.1' in element.tag:
                    #     ReturnType = 'WaterML1.1'
                    # elif 'waterML/1.0' in element.tag


                    bracket_lock = element.tag.index('}')  # The namespace in the tag is enclosed in {}.
                    tag = element.tag[bracket_lock+1:]     # Takes only actual tag, no namespace


                    if 'value'!= tag:
                        # in the xml there is a unit for the value, then for time. just take the first




                        if 'unitName' == tag or 'units' ==tag or 'UnitName'==tag or 'unitCode'==tag:
                            if not unit_is_set:
                                units = element.text
                                unit_is_set = True
                        if 'noDataValue' == tag:
                            nodata = element.text
                        if 'siteName' == tag:
                            site_name = element.text
                        if 'variableName' == tag:
                            variable_name = element.text
                        if 'organization'==tag or 'Organization'==tag or'siteCode'==tag:
                            try:
                                organization = element.attrib['agencyCode']
                            except:
                                organization = element.text
                        if 'definition' == tag or 'qualifierDescription'==tag:
                            quality = element.text
                        if 'methodDescription' == tag or 'MethodDescription'==tag:
                            # print element.attrib['methodID']
                            method = element.text
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
                        if "latitude" ==tag:
                            Lat = element.text
                        if "longitude"==tag:
                            Lon = element.text
                        if 'siteCode'==tag:
                            network = element.attrib['network']

                        if "method" ==tag.lower():
                            try:
                                mid = element.attrib['methodID']
                            except:
                                mid =None
                                m_code =''
                            for subele in element:
                                bracket_lock = subele.tag.index('}')  # The namespace in the tag is enclosed in {}.
                                tag1 = element.tag[bracket_lock+1:]
                                # Takes only actual tag, no namespace
                                if 'methodcode' in subele.tag.lower() and m_code=='':
                                    m_code = subele.text
                                    m_code = m_code.replace(" ","")

                                if mid != None:
                                    m_code = element.attrib['methodID']
                                    m_code = m_code.replace(" ","")
                                if 'methoddescription' in subele.tag.lower():
                                    m_des = subele.text

                            meta_dic['method'].update({m_code:m_des})
                        if "source" ==tag.lower():

                            try:
                                sid = element.attrib['sourceID']
                            except:
                                sid = None
                                m_code =''

                            for subele in element:
                                bracket_lock = subele.tag.index('}')  # The namespace in the tag is enclosed in {}.
                                tag1 = element.tag[bracket_lock+1:]

                                # Takes only actual tag, no namespace
                                if 'sourcecode' in subele.tag.lower() and m_code =='':
                                    m_code = subele.text
                                    m_code = m_code.replace(" ","")


                                if sid!= None:
                                    m_code = element.attrib['sourceID']
                                    m_code = m_code.replace(" ","")
                                if 'sourcedescription' in subele.tag.lower():
                                    m_des = subele.text
                                if 'organization' in subele.tag.lower():
                                    m_org = subele.text

                            meta_dic['source'].update({m_code:m_des})
                            meta_dic['organization'].update({m_code:m_org})


                        if "qualitycontrollevel" ==tag.lower():
                            try:
                                qlc= element.attrib['qualityControlLevelID']
                            except:
                                qlc =None
                                m_code =''

                            for subele in element:
                                bracket_lock = subele.tag.index('}')  # The namespace in the tag is enclosed in {}.
                                tag1 = element.tag[bracket_lock+1:]
                                # Takes only actual tag, no namespace

                                if  qlc !=None:
                                    m_code =element.attrib['qualityControlLevelID']
                                    m_code = m_code.replace(" ","")
                                if 'qualitycontrollevelcode' in subele.tag.lower():
                                    m_code1 = subele.text
                                    m_code1 = m_code1.replace(" ","")
                                if 'qualitycontrollevelcode' in subele.tag.lower() and m_code =='':
                                    m_code = subele.text
                                    m_code = m_code1.replace(" ","")
                                if 'definition' in subele.tag.lower():
                                    m_des = subele.text
                            meta_dic['quality'].update({m_code:m_des})
                            meta_dic['quality_code'].update({m_code1:m_code})

                    elif 'value' == tag:
                        # print element.attrib
                        try:
                            n = element.attrib['dateTimeUTC']
                        except:
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


                        dic = quality +'aa'+method+'aa'+source

                        if dic not in meth_qual:
                            meth_qual.append(dic)
                            # meth_qual.append(dic1)
                            master_values.update({dic:[]})
                            master_times.update({dic:[]})
                            master_boxplot.update({dic:[]})
                            master_stat.update({dic:[]})
                            master_data_values.update({dic:[]})

                        v = element.text
                        # tii = pd.Timestamp(n).value/1000000#pandas convert string to time object
                        # tii = ti.value/1000000 #gets timestamp and convert time to milliseconds
                        # t =t*1000# This adds three extra zeros for correct formatting

                        if v == nodata:
                            value = None
                            # for_canvas.append({x:n,y:value})
                            # for_graph.append(value)
                            x_value.append(n)
                            y_value.append(value)
                            v =None

                        else:
                            # for_canvas.append({x:n,y:v})

                            v = float(element.text)
                            for_graph.append(v)
                            x_value.append(n)
                            y_value.append(v)
                            master_data_values[dic].append(v) #records only none null values for running statistics
                            # print "hello"
                            #master_values[dic].update({n:v})
                        master_values[dic].append(v)
                        master_times[dic].append(n)
                        # master_values(dic,n,v)

            for item in master_data_values:
                if len(master_data_values[item]) ==0:
                    mean = None
                    median =None
                    quar1 = None
                    quar3 = None
                    min1 = None
                    max1=None
                else:
                    mean = numpy.mean(master_data_values[item])
                    mean = float(format(mean, '.2f'))
                    median = float(format(numpy.median(master_data_values[item]), '.2f'))
                    quar1 = float(format(numpy.percentile(master_data_values[item],25), '.2f'))
                    quar3 = float(format(numpy.percentile(master_data_values[item],75), '.2f'))
                    min1 = float(format(min(master_data_values[item]), '.2f'))
                    max1 = float(format(max(master_data_values[item]), '.2f'))
                master_stat[item].append(mean)
                master_stat[item].append(median)
                master_stat[item].append(max1)
                master_stat[item].append(min1)
                master_boxplot[item].append(1)
                master_boxplot[item].append(min1)#adding data for the boxplot
                master_boxplot[item].append(quar1)
                master_boxplot[item].append(median)
                master_boxplot[item].append(quar3)
                master_boxplot[item].append(max1)
            value_count = len(x_value)
            sd = numpy.std(for_graph)

            return {
                'site_name': site_name,
                # 'start_date': str(smallest_time),
                # 'end_date': str(largest_time),
                'variable_name': variable_name,
                'units': units,
                'wml_version': '1',
                'meta_dic':meta_dic,
                # 'for_highchart': for_highchart,
                'for_canvas':for_canvas,
                'mean': mean,
                'median': median,
                'max':max1,
                'min':min1,
                'stdev': sd,
                'count': value_count,
                'organization': organization,
                'quality': quality,
                'method': method,
                'status': 'success',
                'datatype' :datatype,
                'valuetype' :valuetype,
                'samplemedium':samplemedium,
                'smallest_value':smallest_value,
                'timeunit':timeunit,
                'sourcedescription' :sourcedescription,
                'timesupport' : timesupport,
                'master_counter':master_counter,
                'boxplot':boxplot,
                # 'xvalue':x_value,
                # 'yvalue':y_value,
                # 'master_values':master_values,
                # 'master_times':master_times,
                # 'master_boxplot':master_boxplot,
                # 'master_stat':master_stat,
                'Lat':Lat,
                'Lon':Lon,
                'RefType':RefType,
                'ServiceType':ServiceType,

                'ReturnType':ReturnType,
                'network':network


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


def parse_2_0(root,wml_version):
    print "running parse_2"
    try:
        if 'Collection' in root.tag:
            ts = etree.tostring(root)
            keys = []
            vals = []
            for_graph = []
            for_highchart=[]
            units, site_name, variable_name, latitude, longitude, method = None, None, None, None, None, None
            name_is_set = False
            variable_name = root[1].text
            organization = None
            quality = None
            method =None
            datatype = None
            valuetype = None
            samplemedium = None
            timeunit=None
            sourcedescription = None
            timesupport =None
            smallest_value = 0
            for element in root.iter():
                if 'MeasurementTVP' in element.tag:
                    for e in element:
                        if 'time' in e.tag:
                            keys.append(e.text)
                        if 'value' in e.tag:
                            vals.append(e.text)
                if 'uom' in element.tag:
                    units = element.text
                if 'MonitoringPoint' in element.tag:
                    for e in element.iter():
                        if 'name' in e.tag and not name_is_set:
                            site_name = e.text
                            name_is_set = True
                        if 'pos' in e.tag:
                            lat_long = e.text
                            lat_long = lat_long.split(' ')
                            latitude = lat_long[0]
                            longitude = lat_long[1]
                if 'observedProperty' in element.tag:
                    for a in element.attrib:
                        if 'title' in a:
                            variable_name = element.attrib[a]
                if 'ObservationProcess' in element.tag:
                    for e in element.iter():
                        if 'processType' in e.tag:
                            for a in e.attrib:
                                if 'title' in a:
                                    method=e.attrib[a]

                if 'organization' in element.tag:
                    organization = element.text

                if 'definition' in element.tag:
                    quality = element.text

                if 'methodDescription' in element.tag:
                    method = element.text
                if 'dataType' in element.tag:
                    datatype = element.text
                if 'valueType' in element.tag:
                    valuetype = element.text
                if "sampleMedium" in element.tag:
                    samplemedium = element.text
                if"timeSupport"in element.text:
                    timesupport =element.text
                if"unitName"in element.text:
                    timeunit =element.text
                if"sourceDescription"in element.text:
                    sourcedescription =element.text

            for i in range(0,len(keys)):
                time_str=keys[i]
                time_obj=time_str_to_datetime(time_str)

                if vals[i] == "-9999.0"or vals[i]=="-9999":
                    val_obj = None
                else:
                    val_obj=float(vals[i])

                item=[time_obj,val_obj]
                for_highchart.append(item)
            values = dict(zip(keys, vals))

            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            smallest_time = list(values.keys())[0]
            largest_time = list(values.keys())[0]
            for t in list(values.keys()):
                if t < smallest_time:
                    smallest_time = t
                if t> largest_time:
                    largest_time = t
            for v in list(values.vals()):
                if v < smallest_value:
                    smallest_value = t




            return {'time_series': ts,
                    'site_name': site_name,
                    'start_date': smallest_time,
                    'end_date':largest_time,
                    'variable_name': variable_name,
                    'units': units,
                    'values': values,
                    'wml_version': '2.0',
                    'latitude': latitude,
                    'longitude': longitude,
                    'for_highchart': for_highchart,
                    'organization':organization,
                    'quality':quality,
                    'method':method,
                    'status': 'success',
                    'datatype' :datatype,
                    'valuetype' :valuetype,
                    'samplemedium':samplemedium,
                    'smallest_value':smallest_value,
                    'timeunit':timeunit,
                    'sourcedescription' :sourcedescription,
                    'timesupport' : timesupport,
                    'values':vals
                    }
        else:
            print "Parsing error: The waterml document doesn't appear to be a WaterML 2.0 time series"
            return "Parsing error: The waterml document doesn't appear to be a WaterML 2.0 time series"
    except:
        print "Parsing error: The Data in the Url, or in the request, was not correctly formatted."
        return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."



def Original_Checker(xml_file):

    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
        wml_version = get_version(root)['version']
        if wml_version == '1':
            return parse_1_0_and_1_1(root)
        elif wml_version == '2.0':
            return parse_2_0(root)
    except ValueError, e:
        return read_error_file(xml_file)
    except:
        return read_error_file(xml_file)


def read_error_file(xml_file):
    try:
        f = open(xml_file)
        return {'status': f.readline()}
    except:
        return {'status': 'invalid WaterML file'}


def unzip_waterml(request, res_id,src):
    # print "unzip!!!!!!!"

    # this is where we'll unzip the waterML file to
    temp_dir = get_workspace()
    # waterml_url = ''

    # get the URL of the remote zipped WaterML resource


    if not os.path.exists(temp_dir+"/id"):
        os.makedirs(temp_dir+"/id")
    if 'cuahsi'in src :
        # url_zip = 'http://bcc-hiswebclient.azurewebsites.net/CUAHSI/HydroClient/WaterOneFlowArchive/'+res_id+'/zip'
        url_zip = 'http://qa-webclient-solr.azurewebsites.net/CUAHSI/HydroClient/WaterOneFlowArchive/'+res_id+'/zip'
    elif 'hydroshare' in src:
        url_zip = 'https://www.hydroshare.org/hsapi/_internal/'+res_id+'/download-refts-bag/'
    else:
        url_zip = 'http://' + request.META['HTTP_HOST'] + '/apps/data-cart/showfile/'+res_id
    r = requests.get(url_zip, verify=False)
    try:
        z = zipfile.ZipFile(StringIO.StringIO(r.content))
        file_list = z.namelist()
        print file_list
        try:
            for file in file_list:
                if 'hydroshare' in src:
                    if 'wml_1_' in file:
                        file_data = z.read(file)
                        file_temp_name = temp_dir + '/id/' + res_id + '.xml'
                        file_temp = open(file_temp_name, 'wb')
                        file_temp.write(file_data)
                        file_temp.close()
                        base_url = request.build_absolute_uri()
                        if "?" in base_url:
                            base_url = base_url.split("?")[0]
                        waterml_url = base_url + "temp_waterml/cuahsi/id/" + res_id + '.xml'
                else:
                    file_data = z.read(file)
                    file_temp_name = temp_dir + '/id/' + res_id + '.xml'
                    file_temp = open(file_temp_name, 'wb')
                    file_temp.write(file_data)
                    file_temp.close()
                    # getting the URL of the zip file
                    base_url = request.build_absolute_uri()
                    if "?" in base_url:
                        base_url = base_url.split("?")[0]
                    waterml_url = base_url + "temp_waterml/cuahsi/id/" + res_id + '.xml'

        # error handling

        # checks to see if data is an xml
        except etree.XMLSyntaxError as e:
            print "Error:Not XML"
            return False

        # checks to see if Url is valid
        except ValueError, e:
            print "Error:invalid Url"
            return False

        # checks to see if xml is formatted correctly
        except TypeError, e:
            print "Error:string indices must be integers not str"
            return False

    # check if the zip file is valid
    except zipfile.BadZipfile as e:
        error_message = "Bad Zip File"
        print "Bad Zip file"
        return False

    # finally we return the waterml_url

    return waterml_url


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
        hs = controllers.getOAuthHS(request)
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
    data_dic = {"data":data_for_chart,"owner":is_owner,"error":error}
    return data_dic
def parse_JSON():
    temp_dir = get_workspace()
    # file=  temp_dir+'/id/timeSeriesResource.json'
    file=  temp_dir+'/id/timeseriesLayerResource.json'
    with open(file,'r') as outfile:
      x = outfile.read()
      y = json.loads(x)
      return y