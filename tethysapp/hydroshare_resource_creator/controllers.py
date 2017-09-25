from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import json
from .utilities import get_user_workspace


# @login_required()
@csrf_exempt
def home(request):
    """
    Controller for app home page.

    Arguments:      [request]
    Returns:        [render_obj]
    Referenced By:  [app.HydroshareResourceCreator]
    References:     [utilities.get_user_workspace]
    Libraries:      [json]
    """

    if request.user.is_authenticated():
        user_login = 'True'
    else:
        user_login = 'False'

    # FORM DATA FOR LOCAL TESTING
    # test_file_name = 'provo_refts.json'  # Comment out before uploading to GitHub

    try:  # LOCAL TESTING USE ONLY
        local_path = '/home/klippold/tethysdev/HS_TimeseriesCreator/tethysapp/hydroshare_resource_creator/static_data/refts_test_files/'
        local_file = local_path + test_file_name
        print local_file
        with open(local_file, 'r') as test_file:
            form_body = json.load(test_file)

    except:  # PRODUCTION USE ONLY
        try:
            form_body = request.POST
        except:
            form_body = "No data"

    base_path = get_user_workspace(request) + "/timeseriesLayerResource.json"

    with open(base_path, 'w') as outfile:
        json.dump(form_body, outfile)

    source_id = []
    service_url = []
    body = request.body

    context = {'source': body,
               'quality': form_body,
               'method': request,
               'source_id': source_id,
               'service_url': service_url,
               'user_login': user_login
               }

    render_obj = render(request, 'hydroshare_resource_creator/home.html', context)

    return render_obj


@csrf_exempt
@never_cache
def login_callback(request):
    """
    Controller for login_callback. Checks if the user is logged in.

    Arguments:      [request]
    Returns:        [render_obj]
    Referenced By:  [app.HydroshareResourceCreator]
    References:     []
    Libraries:      []
    """

    context = {}
    if request.user.is_authenticated():
        context["login"] = "yes"
    else:
        context["login"] = "no"

    render_obj = render(request, 'hydroshare_resource_creator/login_callback.html', context)

    return render_obj
