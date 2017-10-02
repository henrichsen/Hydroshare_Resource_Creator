from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from tethys_apps.base import TethysWorkspace
import traceback
import json
import shutil
import os
import time
from .utilities import get_user_workspace, create_ts_resource, create_refts_resource, get_o_auth_hs, trim, \
     process_file_data


@csrf_exempt
# @login_required()
def chart_data(request, res_id):
    """
    Ajax controller for chart_data.

    Arguments:      [request, res_id]
    Returns:        [JsonResponse(return_obj)]
    Referenced By:  [main.js]
    References:     [utilities.process_file_data, utilities.get_user_workspace, utilities.get_o_auth_hs, get_oauth_hs]
    Libraries:      [time, shutil, os, JsonResponse, json]
    """

    return_obj = {
        'success': False,
        'message': None,
        'results': {}
    }

    temp_dir = get_user_workspace(request)

    ref_file = temp_dir + (request.POST)["refts_filename"]
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
            temp_dir = get_user_workspace(request)
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


@csrf_exempt
# @login_required()
def login_test(request):
    """
    Ajax controller for login_test. Tests user login.

    Arguments:      [request]
    Returns:        [JsonResponse({'Login': login_status})]
    Referenced By:  []
    References:     []
    Libraries:      []
    """

    return_obj = {
        'success': "False",
        'message': None,
        'results': {}
    }

    if request.user.is_authenticated():
        data_url = request.POST.get('data_url')
        hs = get_o_auth_hs(request)
        hs_version = hs.hostname

        if "appsdev.hydroshare.org" in str(data_url) and "beta" in str(hs_version):
            return_obj['success'] = "True"
        elif "apps.hydroshare.org" in str(data_url) and "www" in str(hs_version):
            return_obj['success'] = "True"
        elif "127.0.0.1:8000" in str(data_url) and "beta" in str(hs_version):
            return_obj['success'] = "True"
        else:
            return_obj['success'] = "False"
    else:
        return_obj['success'] = "False"

    return JsonResponse(return_obj)


@ensure_csrf_cookie
# @login_required()
def ajax_create_resource(request, res_id):
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

    # -------------------- #
    #   VERIFIES REQUEST   #
    # -------------------- #

    if not (request.is_ajax() and request.method == 'POST'):
        return_obj['success'] = False
        return_obj['message'] = "Unable to communicate with server."
        return_obj['results'] = {}

        return JsonResponse(return_obj)

    # ----------------------------- #
    #   GETS DATA FROM JAVASCRIPT   #
    # ----------------------------- #

    try:
        user_dir = get_user_workspace(request)
        action_request = str(request.POST.get('action_request'))
        res_title = str(request.POST.get('resTitle'))
        res_abstract = str(request.POST.get('resAbstract'))
        res_keywords = str(request.POST.get('resKeywords')).split(',')
        res_access = str(request.POST.get('resAccess'))
        res_filename = res_title.replace(' ', '')[:10]
        res_data_pathname = request.POST.get('refts_filename')
        selected_resources = []
        for res in trim(request.POST.get('checked_ids')):
            selected_resources.append(int(res))
        res_data = {'res_title': res_title,
                    'res_abstract': res_abstract,
                    'res_keywords': res_keywords,
                    'res_access': res_access,
                    'res_filename': res_filename,
                    'selected_resources': selected_resources,
                    'user_dir': user_dir,
                    'res_id': res_id,
                    'res_data_pathname': res_data_pathname
                    }

    except Exception, e:
        return_obj['success'] = False
        return_obj['message'] = 'We encountered a problem while loading your resource data.'
        return_obj['results'] = {'error': str(e)}

        return JsonResponse(return_obj)

    ''''''''''''''''  GETS HYDROSHARE OAUTH  '''''''''''''''
    try:
        hs = get_o_auth_hs(request)
        hs_version = hs.hostname

    except:
        return_obj['success'] = False
        return_obj['message'] = 'We were unable to authenticate your HydroShare sign-in.'
        return_obj['results'] = {}

        return JsonResponse(return_obj)

    ''''''''''''''''  CREATES HYDROSHARE RESOURCE  '''''''''''''''
    try:
        actions = {'ts': create_ts_resource,
                   'update': None,
                   'refts': create_refts_resource}

        processed_data = actions[action_request](res_data)

        res_type = processed_data['res_type']
        res_filepath = processed_data['res_filepath']
        res_filename = res_filename + processed_data['file_extension']

        if processed_data['res_type'] == 'TimeSeriesResource' and 'Data Loaded' not in processed_data['parse_result']:
            return_obj['success'] = False
            return_obj['message'] = processed_data["parse_result"]
            return_obj['results'] = {}

            return JsonResponse(return_obj)

        resource_id = hs.createResource(res_type, res_title, abstract=res_abstract, keywords=res_keywords)

        try:
            with open(res_filepath, 'rb') as res_file:
                hs.addResourceFile(resource_id, resource_file=res_file, resource_filename=res_filename)
            res_file.close()
            hs.getResourceFile(resource_id, res_filename)
            if hs.getSystemMetadata(resource_id)['resource_title'] == 'Untitled resource':
                hs.deleteResource(resource_id)
                raise Exception
        except:
            hs.deleteResource(resource_id)
            raise Exception

    except Exception, e:
        return_obj['success'] = False
        return_obj['message'] = traceback.format_exc()
        return_obj['results'] = {}

        return JsonResponse(return_obj)

    ''''''''''''''''  SETS RESOURCE AS PUBLIC  '''''''''''''''
    if res_access == 'public':
        public = False
        timeout = time.time() + 20
        while public is False or time.time() < timeout:
            try:
                hs.setAccessRules(resource_id, public=True)
                public = True
            except:
                time.sleep(2)

        if public is False:
            return_obj['success'] = False
            return_obj['message'] = 'Request timed out.'
            return_obj['results'] = {}

            return JsonResponse(return_obj)

    ''''''''''''''''  RESOURCE CREATED SUCCESSFULLY  '''''''''''''''
    return_obj['success'] = True
    return_obj['message'] = 'Resource created successfully'
    return_obj['results'] = {'resource_id': resource_id, 'hs_version': hs_version}

    TethysWorkspace(user_dir).clear()

    return JsonResponse(return_obj)
