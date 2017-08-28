from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import shutil
import os
import time
from .utilities import get_workspace, parse_ts_layer, get_o_auth_hs, trim, \
     process_file_data


@csrf_exempt
# @login_required()
def chart_data(request, res_id):
    """
    Ajax controller for chart_data.

    Arguments:      [request, res_id]
    Returns:        [JsonResponse(return_obj)]
    Referenced By:  [main.js]
    References:     [utilities.process_file_data, utilities.get_workspace, utilities.get_o_auth_hs, get_oauth_hs]
    Libraries:      [time, shutil, os, JsonResponse, json]
    """

    return_obj = {
        'success': False,
        'message': None,
        'results': {}
    }

    temp_dir = get_workspace()
    ref_file = temp_dir + '/id/timeseriesLayerResource.json'

    # Temporary File Path
    # ref_file = '/home/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/timeseriesLayerResource.json.refts'

    if request.is_ajax() and request.method == 'POST':
        if res_id == 'None':
            try:
                processed_file_data = process_file_data(ref_file)

                ''''''''''''''''  PROCESSED FILE DATA  '''''''''''''''
                return_obj['success'] = True
                return_obj['message'] = 'File data processed successfully'
                return_obj['results'] = processed_file_data

            except:
                if os.path.isfile(ref_file) and os.path.getsize(ref_file) < 3:

                    ''''''''''''''''  NO DATA IN FILE  '''''''''''''''
                    return_obj['success'] = False
                    return_obj['message'] = 'No data in file'
                    return_obj['results'] = {}

                else:

                    ''''''''''''''''  FILE PROCESSING ERROR  '''''''''''''''
                    return_obj['success'] = False
                    return_obj['message'] = 'File processing error.'
                    return_obj['results'] = {}

        else:
            temp_dir = get_workspace()
            root_dir = temp_dir + '/id/' + res_id
            try:
                # Ensures that resource is downloaded each time
                shutil.rmtree(root_dir)
            except:
                pass
            if not os.path.exists(temp_dir + "/id"):
                os.makedirs(temp_dir + "/id")
            else:
                hs = get_o_auth_hs(request)
                file_path = temp_dir + '/id'
                delay = 0
                # resource = None
                status = 'running'
                while status == 'running' or delay < 10:
                    if delay > 10:
                        # error = 'Request timed out'
                        break
                    elif status == 'done':
                        # error = ''
                        break
                    else:
                        try:
                            # res_info = hs.getSystemMetadata(res_id)
                            # res_info = res_info['public']
                            hs.getResource(res_id, destination=file_path, unzip=True)
                            root_dir = file_path + '/' + res_id
                            data_dir = root_dir + '/' + res_id + '/data/contents/'
                            file_data = ''
                            for subdir, dirs, files in os.walk(data_dir):
                                for ref_file in files:
                                    if '.json.refts' in ref_file:
                                        data_file = data_dir + ref_file
                                        with open(data_file, 'r') as f:
                                            file_data = f.read()
                                            # print file_data
                                            file_data = file_data.encode(encoding='UTF-8')
                                            file_data = json.loads(file_data)
                                            file_data = file_data['timeSeriesReferenceFile']
                            if file_data is None:
                                status = 'running'
                                time.sleep(2)
                            else:
                                status = 'done'
                        except:
                            # error = 'error'
                            status = 'running'
                            time.sleep(2)
                    delay = delay + 1
    else:

        ''''''''''''''''  AJAX ERROR  '''''''''''''''
        return_obj['success'] = False
        return_obj['message'] = "Encountered AJAX Error."
        return_obj['results'] = {}

    return JsonResponse(return_obj)


@ensure_csrf_cookie
# @login_required()
def ajax_create_timeseries_resource(request, res_id):
    """
    Ajax controller for create_layer.

    Arguments:      []
    Returns:        []
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    return_obj = {
        'success': False,
        'message': None,
        'results': {}
    }

    ''' Sets some initial values '''
    error = ''

    ''' Gets data from JavaScript '''
    title = str(request.POST.get('resTitle'))
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords')).split(',')
    res_access = str(request.POST.get('resAccess'))
    str_resource = trim(request.POST.get('checked_ids'))
    file_name = title.replace(" ", "")[:10]
    # keywords = keywords.split(',')
    # str_resource = trim(str_resource)
    # file_name = file_name[:10]
    int_resource = []
    for res in str_resource:
        int_resource.append(int(res))
    metadata = []

    ''' Gets HydroShare Open Authorization '''
    hs = get_o_auth_hs(request)

    ''' Sets directory name '''
    temp_dir = get_workspace()
    fpath = temp_dir + '/id/' + file_name + '.json.refts'
    # path where file will be stored before upload to hydroshare
    if res_id == 'null':  # if resource is coming for data client
        file_path = temp_dir + '/id/timeseriesLayerResource.json'
    else:  # if resource is already a HydroShare resource
        # file_path = temp_dir + '/id/timeseriesLayerResource.json'
        data_dir = temp_dir + '/id/' + res_id
        for subdir, dirs, files in os.walk(data_dir):
            for ref_file in files:
                if '.json.refts' in ref_file:
                    file_path = subdir + '/' + ref_file

    # Temporary file path.
    # file_path = \
    #     "/home/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/timeseriesLayerResource.json.refts"

    ''' Create data dictionaries '''
    with open(file_path, 'r') as outfile:
        file_data = outfile.read()
        data = file_data.encode(encoding='UTF-8')
        data = json.loads(data)
        data = data['timeSeriesReferenceFile']
        try:
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        except:
            data = json.loads(data)
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        data_stor = []
        counter = 0
        for i in data['referencedTimeSeries']:
            if counter in int_resource:
                data_stor.append(i)
            counter = counter + 1
        data_dic = {"referencedTimeSeries": data_stor, "fileVersion": data_file, "title": title,
                    "symbol": data_symbol, "abstract": abstract, 'keyWords': keywords}
        data.update(data_dic)
        final_dic = {"timeSeriesReferenceFile": data}
        with open(fpath, 'w') as outfile1:
            json.dump(final_dic, outfile1)
    # r_title = title
    r_keywords = keywords
    r_abstract = abstract

    ''' Create Resource '''
    # utilities.create_odm2(fpath,file_name)
    r_type = 'TimeSeriesResource'
    r_title = title
    # fpath = temp_dir + '/ODM2/ODM2_single_variable_multi_site.sqlite'
    parse_ts_layer(fpath, file_name, abstract)
    fpath = temp_dir + '/ODM2/' + file_name + '.sqlite'
    # resource_id = hs.createResource(
    #     r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
    # resource_id1 = hs.addResourceFile(resource_id, fpath)
    resource_id = hs.createResource(r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract,
                                    metadata=metadata)
    """
    if res_access == 'public':
        delay = 0
        public = 'false'
        while public == 'false' or delay :
            if delay > 10:
                error = 'Request timed out'
                break
            else:
                try:
                    hs.setAccessRules(resource_id, public=True)
                    public = 'true'
                except:
                    public = 'false'
                    time.sleep(2)
                    delay += 1
    """

    if res_access == "public":
        public = False
        timeout = time.time() + 20
        while public is False or time.time() < timeout:
            try:
                hs.setAccessRules(resource_id, public=True)
                public = True
            except:
                time.sleep(2)

        if public is False:
            ''''''''''''''''  TIME OUT ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'Request timed out.'
            return_obj['results'] = {}

    '''                
    except:
        error = 'At least one resource needs to be selected'
        # utilities.parse_ts_layer(fpath,file_name,abstract)
        # fpath = temp_dir+'/ODM2/'+file_name+'.sqlite'
        # resource_id = hs.createResource(r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
        # resource_id1 = hs.addResourceFile(resource_id, fpath)
        "uploaded to HydroShare"
    '''

    return JsonResponse({'Request': resource_id, 'error': error})


@ensure_csrf_cookie
# @login_required()
def ajax_update_resource(request, res_id):
    """
    Ajax controller for create_layer.

    Arguments:      []
    Returns:        []
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    ''' Sets some initial values '''
    resource_id = None
    data_stor = []
    int_resource = []
    counter = 0
    error = ''
    public = 'false'

    ''' Gets data from JavaScript '''
    title = str(request.POST.get('resTitle'))
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords'))
    res_access = str(request.POST.get('resAccess'))
    str_resource = request.POST.get('checked_ids')
    keywords = keywords.split(',')
    str_resource = trim(str_resource)
    file_name = title.replace(" ", "")
    file_name = file_name[:10]
    for res in str_resource:
        # Throws an error if no resources are checked.
        # Should be tested in the javascript before this function is called.
        int_resource.append(int(res))
    # metadata = []

    ''' Gets HydroShare Open Authorization '''
    hs = get_o_auth_hs(request)

    ''' Sets directory name '''
    temp_dir = get_workspace()
    # print title.lstrip(10)
    fpath = temp_dir + '/id/' + file_name + '.json.refts'
    # path where file will be stored before upload to hydroshare
    file_path = ""
    fname = ""
    root_dir = ""
    if res_id == 'null':  # if resource is coming for data client
        file_path = temp_dir + '/id/timeseriesLayerResource.json'
    else:  # if resource is already a HydroShare resource
        # file_path = temp_dir + '/id/timeseriesLayerResource.json'
        data_dir = temp_dir + '/id/' + res_id
        for subdir, dirs, files in os.walk(data_dir):
            for file in files:
                if '.json.refts' in file:
                    fname = file
                    file_path = subdir + '/' + file

    ''' Create data dictionaries '''
    with open(file_path, 'r') as outfile:
        file_data = outfile.read()
        data = file_data.encode(encoding='UTF-8')
        data = json.loads(data)
        data = data['timeSeriesReferenceFile']
        try:
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        except:
            data = json.loads(data)
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        for i in data['referencedTimeSeries']:
            if counter in int_resource:
                data_stor.append(i)
            counter = counter + 1
        data_dic = {"referencedTimeSeries": data_stor, "fileVersion": data_file, "title": title,
                    "symbol": data_symbol, "abstract": abstract, 'keyWords': keywords}
        data.update(data_dic)
        final_dic = {"timeSeriesReferenceFile": data}
        with open(fpath, 'w') as outfile1:
            json.dump(final_dic, outfile1)
    # r_title = title
    # r_keywords = keywords
    # r_abstract = abstract

    ''' Create Resource '''
    # r_type = 'GenericResource'
    # r_type = 'CompositeResource'
    try:
        try:
            resource_id = hs.deleteResourceFile(res_id, fname)
        except:
            error = 'File does not exist'
        resource_id = hs.addResourceFile(res_id, fpath)
        temp_dir = get_workspace()
        root_dir = temp_dir + '/id/' + res_id
    except:
        error = "error"
    try:
        shutil.rmtree(root_dir)
    except:
        pass
        # nothing = None

    if res_access == 'public':
        delay = 0
        while public == 'false' or delay < 10:
            if delay > 10:
                error = 'Request timed out'
                break
            else:
                try:
                    hs.setAccessRules(resource_id, public=True)
                    # public = 'true'
                    break
                except:
                    public = 'false'
                    time.sleep(2)
                delay = delay + 1
    else:
        print 'BROKE'
    '''                
    except:
        error = 'At least one resource needs to be selected'
        # utilities.parse_ts_layer(fpath,file_name,abstract)
        # fpath = temp_dir+'/ODM2/'+file_name+'.sqlite'
        # resource_id = hs.createResource(r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
        # resource_id1 = hs.addResourceFile(resource_id, fpath)
        "uploaded to HydroShare"
    '''
    return JsonResponse({'Request': resource_id, 'error': error})


@ensure_csrf_cookie
# @login_required()
def ajax_create_refts_resource(request, res_id):

    """
    Ajax controller for create_layer.

    Arguments:      [request, res_id]
    Returns:        [JsonResponse(return_obj)]
    Referenced By:  [ajaxCreateTimeseriesResource]
    References:     [utilities.get_workspace, utilities.get_o_auth_hs, utilities.trim]
    Libraries:      [JsonResponse, json, os, time]
    """

    return_obj = {
        'success': False,
        'message': None,
        'results': {}
    }

    if request.is_ajax() and request.method == 'POST':
        try:
            int_resource = []
            title = str(request.POST.get('resTitle'))
            abstract = str(request.POST.get('resAbstract'))
            keywords = str(request.POST.get('resKeywords'))
            res_access = str(request.POST.get('resAccess'))
            str_resource = request.POST.get('checked_ids')
            keywords = keywords.split(',')
            str_resource = trim(str_resource)
            file_name = title.replace(" ", "")
            file_name = file_name[:10]
            for res in str_resource:
                int_resource.append(int(res))
            metadata = []

        except:

            ''''''''''''''''  DATA REQUEST ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'Data request error.'
            return_obj['results'] = {}

            return JsonResponse(return_obj)

        try:
            ''' Gets HydroShare Open Authorization '''
            hs = get_o_auth_hs(request)

        except:

            ''''''''''''''''  HYDROSHARE OAUTH ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'HydroShare Open Authorization error.'
            return_obj['results'] = {}

            return JsonResponse(return_obj)

        try:
            temp_dir = get_workspace()
            # print title.lstrip(10)
            fpath = temp_dir + '/id/' + file_name + '.json.refts'
            # path where file will be stored before upload to hydroshare
            file_path = ""
            # fname = ""
            # root_dir = ""
            if res_id == 'null':  # if resource is coming for data client
                file_path = temp_dir + '/id/timeseriesLayerResource.json'
            else:  # if resource is already a HydroShare resource
                # file_path = temp_dir + '/id/timeseriesLayerResource.json'
                data_dir = temp_dir + '/id/' + res_id
                for subdir, dirs, files in os.walk(data_dir):
                    for json_file in files:
                        if '.json.refts' in json_file:
                            # fname = json_file
                            file_path = subdir + '/' + json_file

            # Temporary File Path
            # file_path = \
            #    "/home/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/timeseriesLayerResource.json.refts"

        except:

            ''''''''''''''''  FILE PATH ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'File path error.'
            return_obj['results'] = {}

            return JsonResponse(return_obj)
        try:
            counter = 0
            data_stor = []
            with open(file_path, 'r') as outfile:
                file_data = outfile.read()
                data = file_data.encode(encoding='UTF-8')
                data = json.loads(data)
                data = data['timeSeriesReferenceFile']
                try:
                    data_symbol = data['symbol']
                    data_file = data['fileVersion']
                except:
                    data = json.loads(data)
                    data_symbol = data['symbol']
                    data_file = data['fileVersion']
                for i in data['referencedTimeSeries']:
                    if counter in int_resource:
                        data_stor.append(i)
                    counter = counter + 1
                data_dic = {"referencedTimeSeries": data_stor, "fileVersion": data_file, "title": title,
                            "symbol": data_symbol, "abstract": abstract, 'keyWords': keywords}
                data.update(data_dic)
                final_dic = {"timeSeriesReferenceFile": data}
                with open(fpath, 'w') as outfile1:
                    json.dump(final_dic, outfile1)
            r_title = title
            r_keywords = keywords
            r_abstract = abstract
        except SyntaxError:

            ''''''''''''''''  DATA LOADING ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'Data loading error.'
            return_obj['results'] = {}

            return JsonResponse(return_obj)

        ''' Create Resource '''
        # r_type = 'GenericResource'
        r_type = 'CompositeResource'
        try:
            resource_id = hs.createResource(
                r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract,
                metadata=metadata)
        except:
            resource_id = "error"

            ''''''''''''''''  RESOURCE ID ERROR  '''''''''''''''
            return_obj['success'] = False
            return_obj['message'] = 'Resource ID error.'
            return_obj['results'] = {}

        if res_access == 'public':
            public = 'false'
            delay = 0

            while public == 'false' and delay < 10:
                try:
                    hs.setAccessRules(resource_id, public=True)
                    public = 'true'
                except:
                    time.sleep(2)
                    delay = delay + 1

            if public == 'false':

                ''''''''''''''''  REQUEST TIMEOUT ERROR  '''''''''''''''
                return_obj['success'] = False
                return_obj['message'] = 'Request timed out.'
                return_obj['results'] = {}

                return JsonResponse(return_obj)

        '''                
        except:
            error = 'At least one resource needs to be selected'
            # utilities.parse_ts_layer(fpath,file_name,abstract)
            # fpath = temp_dir+'/ODM2/'+file_name+'.sqlite'
            # resource_id = hs.createResource(r_type, r_title, keywords=r_keywords, abstract=r_abstract, 
                                              metadata=metadata)
            # resource_id1 = hs.addResourceFile(resource_id, fpath)
            "uploaded to HydroShare"
        '''

        ''''''''''''''''  RESOURCE CREATED SUCCESSFULLY  '''''''''''''''
        return_obj['success'] = True
        return_obj['message'] = 'Resource created successfully'
        return_obj['results'] = {}

        return JsonResponse(return_obj)

    else:

        ''''''''''''''''  AJAX ERROR  '''''''''''''''
        return_obj['success'] = False
        return_obj['message'] = "Encountered AJAX Error."
        return_obj['results'] = {}

        return JsonResponse(return_obj)


def login_test(request):
    """
    Ajax controller for login_test. Tests user login.

    Arguments:      [request]
    Returns:        [JsonResponse({'Login': login_status})]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    if request.user.is_authenticated():
        login_status = "True"
    else:
        login_status = "False"
    return JsonResponse({'Login': login_status})


"""
def create_layer(request, fun_type, res_id, res_type):
    '''
    Ajax controller for create_layer.

    Arguments:      [request, fun_type, res_id, res_type]
    Returns:        [JsonResponse(return_obj)]
    Referenced By:  [main.js]
    References:     [utilities.trim, utilities.get_o_auth_hs, utilities.get_workspace, utilities.parse_ts_layer]
    Libraries:      [get_oauth_hs, os, json, shutil]
    '''

    ''' Sets some initial values '''
    resource_id = None
    data_stor = []
    int_resource = []
    counter = 0
    error = ''
    public = 'false'

    ''' Gets data from JavaScript '''
    title = str(request.POST.get('resTitle'))
    abstract = str(request.POST.get('resAbstract'))
    keywords = str(request.POST.get('resKeywords'))
    res_access = str(request.POST.get('resAccess'))
    str_resource = request.POST.get('checked_ids')
    keywords = keywords.split(',')
    str_resource = trim(str_resource)
    file_name = title.replace(" ", "")
    file_name = file_name[:10]
    for res in str_resource:
        # Throws an error if no resources are checked.
        # Should be tested in the javascript before this function is called.
        int_resource.append(int(res))
    metadata = []

    ''' Gets HydroShare Open Authorization '''
    if use_hs_client_helper:
        hs = get_oauth_hs(request)
    else:
        hs = get_o_auth_hs(request)

    ''' Sets directory name '''
    temp_dir = get_workspace()
    # print title.lstrip(10)
    fpath = temp_dir + '/id/' + file_name + '.json.refts'
    # path where file will be stored before upload to hydroshare
    file_path = ""
    fname = ""
    root_dir = ""
    if res_id == 'null':  # if resource is coming for data client
        file_path = temp_dir + '/id/timeseriesLayerResource.json'
    else:  # if resource is already a HydroShare resource
        # file_path = temp_dir + '/id/timeseriesLayerResource.json'
        data_dir = temp_dir + '/id/' + res_id
        for subdir, dirs, files in os.walk(data_dir):
            for file in files:
                if '.json.refts' in file:
                    print(subdir)
                    fname = file
                    file_path = subdir + '/' + file
    print(file_path)
    file_path = \
        "/Users/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/timeseriesLayerResource.json.refts"

    ''' Create data dictionaries '''
    with open(file_path, 'r') as outfile:
        file_data = outfile.read()
        data = file_data.encode(encoding='UTF-8')
        data = json.loads(data)
        data = data['timeSeriesLayerResource']
        try:
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        except:
            data = json.loads(data)
            data_symbol = data['symbol']
            data_file = data['fileVersion']
        for i in data['REFTS']:
            if counter in int_resource:
                data_stor.append(i)
            counter = counter + 1
        data_dic = {"REFTS": data_stor, "fileVersion": data_file, "title": title,
                    "symbol": data_symbol, "abstract": abstract, 'keyWords': keywords}
        data.update(data_dic)
        final_dic = {"timeSeriesLayerResource": data}
        with open(fpath, 'w') as outfile1:
            json.dump(final_dic, outfile1)
    r_title = title
    r_keywords = keywords
    r_abstract = abstract

    ''' Create Resource '''
    if res_type == 'refts':
        # r_type = 'GenericResource'
        r_type = 'CompositeResource'
        if fun_type == 'create':
            try:
                resource_id = hs.createResource(
                    r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract,
                    metadata=metadata)
            except:
                resource_id = "error"
        elif fun_type == 'update':
            try:
                try:
                    resource_id = hs.deleteResourceFile(res_id, fname)
                except:
                    error = 'File does not exist'
                resource_id = hs.addResourceFile(res_id, fpath)
                temp_dir = get_workspace()
                root_dir = temp_dir + '/id/' + res_id
            except:
                error = "error"
            try:
                shutil.rmtree(root_dir)
                print("removing directory")
            except:
                pass
                # nothing = None
    elif res_type == 'ts':
        # utilities.create_odm2(fpath,file_name)
        r_type = 'TimeSeriesResource'
        r_title = title
        # fpath = temp_dir + '/ODM2/ODM2_single_variable_multi_site.sqlite'
        print(fpath)
        parse_ts_layer(fpath, file_name, abstract)
        # fpath = temp_dir + '/ODM2/' + file_name + '.sqlite'
        resource_id = hs.createResource(
            r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
        # resource_id1 = hs.addResourceFile(resource_id, fpath)
        # resource_id = hs.createResource\
        # (r_type, r_title, resource_file=fpath, keywords=r_keywords, abstract=r_abstract, metadata=metadata)

    if res_access == 'public':
        delay = 0
        while public == 'false' or delay < 10:
            if delay > 10:
                error = 'Request timed out'
                break
            else:
                try:
                    hs.setAccessRules(resource_id, public=True)
                    # public = 'true'
                    break
                except:
                    public = 'false'
                    time.sleep(2)
                delay = delay + 1
    else:
        print('BROKE')
    '''                
    except:
        error = 'At least one resource needs to be selected'
        # utilities.parse_ts_layer(fpath,file_name,abstract)
        # fpath = temp_dir+'/ODM2/'+file_name+'.sqlite'
        # resource_id = hs.createResource(r_type, r_title, keywords=r_keywords, abstract=r_abstract, metadata=metadata)
        # resource_id1 = hs.addResourceFile(resource_id, fpath)
        "uploaded to HydroShare"
    '''
    return JsonResponse({'Request': resource_id, 'error': error})
"""

'''
@login_required()
def write_file(request):
    """
    Ajax controller for write_file.

    :param request: 
    :return JsonResponse(success): 
    """

    success = {"File uploaded": "success"}
    metadata = []
    # hs = get_o_auth_hs(request)
    waterml_url = "http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValuesObject?location=CHMI-H:140&variable=\
    CHMI-H:TEPLOTA&startDate=2015-07-01&endDate=2015-07-10&authToken="
    ref_type = "rest"
    metadata.append({"referenceurl": {"value": waterml_url, "type": ref_type}})
    # r_type = 'RefTimeSeriesResource'
    # r_title = "test"
    # r_keywords = ["test"]
    # r_abstract = "This is a test of the resource creator"
    # res_id = hs.createResource(r_type,
    #                            r_title,
    #                            resource_file=None,
    #                            keywords=r_keywords,
    #                            abstract=r_abstract,
    #                            metadata=json.dumps(metadata))

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
    return JsonResponse(success)


@login_required()
def temp_waterml(request, id):
    """
    Ajax controller for temp_waterml.

    :param request: 
    :param id: 
    :return response:
    """
    
    base_path = get_workspace() + "/id"
    file_path = base_path + "/" + id
    response = HttpResponse(FileWrapper(open(file_path)), content_type='application/xml')
    return response


def response(request):
    """
    Ajax controller response.

    :param request: 
    :return service_url: 
    """

    service_url = 'http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL'
    # service_url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx?WSDL'
    # # site_code = '10147100'
    site_code = 'ODM:010210JHI'
    # variable_code = 'ODM:Discharge'
    variable_code = 'NWISDV:00060'
    client = connect_wsdl_url(service_url)
    # print client
    start_date = ''
    end_date = ''
    auth_token = ''
    response1 = client.service.GetValues(site_code, variable_code, start_date, end_date, auth_token)
    print(response1)
    response_ = urllib2.urlopen('http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo')
    html = response_.read()
    temp_dir = get_workspace()
    file_temp_name = temp_dir + '/id/' + 'WaterOneFlowServiceInfo' + '.xml'
    file_temp = open(file_temp_name, 'wb')
    file_temp.write(html)
    file_temp.close()
    service_url = parse_service_info(file_temp_name)
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
'''

'''
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from .app import HydroshareResourceCreator
import urllib2
'''