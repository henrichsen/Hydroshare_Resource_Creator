from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from tethys_apps.base import TethysWorkspace
import json
import uuid
import requests
from .utilities import get_user_workspace, process_form_data


@csrf_exempt
def home(request):
    """
    Controller for app home page.

    Arguments:      [request]
    Returns:        [render_obj]
    Referenced By:  [app.HydroshareResourceCreator]
    References:     [utilities.get_app_workspace]
    Libraries:      [json]
    """

    # FORM DATA FOR LOCAL TESTING
    #test_file_name = 'stroud_refts.json'  # Comment out before uploading to GitHub

    try:  # LOCAL TESTING USE ONLY
        local_path = "/Users/klippold/Documents/Tethys/tethysdev/HS_TimeseriesCreator/tethysapp/hydroshare_resource_creator/static_data/refts_test_files/"
        local_file = local_path + test_file_name

        with open(local_file, "r") as test_file:
            form_body = json.load(test_file)

    except:  # PRODUCTION USE ONLY
        if request.GET:
            res_id = request.GET["res_id"]
            rest_url = "https://beta.hydroshare.org/hsapi/resource/" + res_id + "/files/"
            response = requests.get(rest_url)
            for refts in json.loads(response.content)["results"]:
                if ".refts.json" in refts["url"]:
                    file_path = str(refts["url"]).replace("www", "beta")
                    break
            rest_url = file_path
            response = requests.get(rest_url)
            form_body = json.loads(response.content)
        else:
            try:
                form_body = request.POST
                if bool(form_body) is False:
                    form_body = "No data"
            except:
                form_body = "No data"

    body = request.body
    if form_body == "No data":
        context = {"source": body,
                   "form_body": "No data",
                   "method": request
                   }

    else:
        original_data = json.dumps(form_body)
        form_body = process_form_data(form_body)

    if form_body == "Data Processing Error":
        context = {"source": original_data,
                   "form_body": "File processing error",
                   "method": request,
                   }
    else:
        context = {"source": body,
                   "form_body": json.dumps(form_body),
                   "method": request
                   }

    render_obj = render(request, "hydroshare_resource_creator/home.html", context)

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

    render_obj = render(request, "hydroshare_resource_creator/login_callback.html", context)

    return render_obj
