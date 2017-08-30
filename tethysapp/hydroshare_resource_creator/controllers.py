from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import json
import os
from .utilities import get_workspace


# @login_required()
@csrf_exempt
def home(request):
    """
    Controller for app home page.

    Arguments:      [request]
    Returns:        [render_obj]
    Referenced By:  [app.HydroshareResourceCreator]
    References:     [utilities.get_workspace]
    Libraries:      [json]
    """

    # ids = []
    # meta = []
    # source = []
    # quality = []
    # method = []
    sourceid = []
    serviceurl = []
    # data = request.META['QUERY_STRING']
    # data = data.encode(encoding='UTF-8')
    base_path = get_workspace() + "/id/timeseriesLayerResource.json"
    print "BASE PATH: " + base_path
    # Temporary Base Path
    # base_path = "/home/kennethlippold/tethysdev/tethysapp-hydroshare_resource_creator/temp_workspace.json"

    if request.user.is_authenticated():
        login1 = 'True'
    else:
        login1 = 'False'
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
    # form_body = '{"fileVersion":1,"title":"HydroClient-2017-01-09T17:46:47.810Z",\
    # "abstract":"Retrieved timeseries...","symbol":"http://data.cuahsi.org/content/images/cuahsi_logo_small.png",\
    # "keyWords":["Time Series","CUAHSI"],"REFTS":[{"refType":"WOF","serviceType":"SOAP",\
    # "url":"http://hydro1.sci.gsfc.nasa.gov/daac-bin/his/1.0/GLDAS_NOAH_001.cgi?WSDL",\
    # "site":"X282-Y404 of Global Land Data Assimilation System (GLDAS) NASA","siteCode":"GLDAS_NOAH:X282-Y404",\
    # "variable":"Surface runoff","variableCode":"GLDAS:GLDAS_NOAH025_3H.001:Qs","networkName":"GLDAS_NOAH",\
    # "beginDate":"2016-01-09T00:00:00","endDate":"2016-09-30T21:00:00+00:00","returnType":"WaterML 1.0",\
    # "location":{"latitude":41.125,"longitude":-109.375}}]}'
    with open(base_path, 'w') as outfile:
        json.dump(form_body, outfile)
    """
    Controller for the app home page.
    """
    # utilities.append_ts_layer_resource("testtt",'test')
    context = {'source': body,
               # 'cuahsi_ids':decode_body,
               'quality': form_body,
               'method': request,
               'sourceid': sourceid,
               'serviceurl': serviceurl,
               'login1': login1
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
