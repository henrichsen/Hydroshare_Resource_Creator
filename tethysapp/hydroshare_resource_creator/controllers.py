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
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}
    return render(request, 'hydroshare_resource_creator/home.html', context)

def chart_data(request, res_id, src):
    # checks if we already have an unzipped xml file
    file_path = utilities.waterml_file_path(res_id)
    # if we don't have the xml file, downloads and unzips it
    if not os.path.exists(file_path):
        utilities.unzip_waterml(request, res_id,src)
    utilities.unzip_waterml(request, res_id,src)
    # returns an error message if the unzip_waterml failed
    if not os.path.exists(file_path):
        data_for_chart = {'status': 'Resource file not found'}
    else:
        # parses the WaterML to a chart data object
        data_for_chart = utilities.Original_Checker(file_path)
        temp_dir = utilities.get_workspace()
        if not os.path.exists(temp_dir+"/hydroshare"):
            os.makedirs(temp_dir+"/hydroshare")
        file_temp_name = temp_dir + '/hydroshare/HIS_reference_timeseries.txt'
        file_temp = open(file_temp_name, 'a')
        file_temp.writelines(str(data_for_chart))
        file_temp.close()

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
def write_file(request):
    sucess = {"File uploaded":"sucess"}
    temp_dir = utilities.get_workspace()
    file_temp_name = temp_dir + '/hydroshare/HIS_reference_timeseries.txt'
    hs = getOAuthHS(request)
    abstract = 'My abstract'
    title = 'My resource'
    keywords = ('my keyword 1', 'my keyword 2')
    rtype = 'GenericResource'
    fpath = file_temp_name
    resource_id = hs.createResource(rtype, title, resource_file=fpath, keywords=keywords, abstract=abstract)
    os.remove(file_temp_name)
    return JsonResponse(sucess)