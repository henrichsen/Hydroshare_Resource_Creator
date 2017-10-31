/**********************************************
************** QUERY SELECTORS ****************
**********************************************/

var $modalResourceDialog = $('#modal-resource-dialog');
var $modalResourceDialogTitle = $('#modal-resource-dialog-title');
var $modalResourceDialogWelcomeInfo = $('#modal-resource-dialog-welcome-info');
var $modalErrorDialog = $('#modal-error-dialog');
var $modalErrorMessage = $('#modal-error-message');
var $btnCreateReferenceTimeseries = $('#btn-create-reference-timeseries');
var $btnUpdateCurrentResource = $('#btn-update-current-resource');
var $btnCreateTimeseriesResource = $('#btn-create-timeseries-resource');
var $publicResource = $('#public_hydro');
var $loadingAnimation = $('#loading');
var $document = $(document);
var $divCreateHydroshareResource = $('#div-create-hydroshare-resource');
var $divViewResource = $('#div_view_resource');
var $tableResourceData = $('#table-resource-data');
var $resTitle = $('#res-title');
var $resAbstract = $('#res-abstract');
var $resKeywords = $('#res-keywords');


/**********************************************
************ FUNCTION DECLARATIONS ************
**********************************************/

var loadResource;
var loadFormData;
var createTimeseriesResource;
var updateResource;
var createReftsResource;
var findQueryParameter;
var finishLoading;
var viewResource;
var getCookie;
var trimInput;
var errorReport;
var ajaxLoadResource;
var ajaxLoginTest;
var ajaxCreateResource;


/**********************************************
****************** FUNCTIONS ******************
**********************************************/

loadResource = function (){
    /**
     * Creates a data table for the resource, and passes the data's URL to the ajaxLoadResource function.
     *
     * @requires trimInput
     * @requires findQueryParameter
     * @requires ajaxLoadResource
     */

    // Hides the page while loading. Update Current Resource button will stay hidden unless a HydroShare resource is loaded. //
    $divCreateHydroshareResource.hide();
    $btnUpdateCurrentResource.hide();

    // Creates the data table to which the resource data will be displayed. //
    var data = [];
    $tableResourceData.DataTable({
        "scrollX": true,
        "createdRow": function (row, data, index){
            var table = $tableResourceData.DataTable();
            table.$('td').tooltip({
                "selector": '[data-toggle="tooltip"]',
                "container": 'body',
                "delay": 0,
                "track": true,
                "fade": 100
            });
        },
        data: data,
        "columns": [
            {
                "className": "legend",
                "data": "legend"
            },
            {"data": "siteName",
            "color":"red"
            },
            {"data": "refType"},
            {"data": "serviceType"},
            {"data": "url"},
            {"data": "returnType"},
            {"data": "latitude"},
            {"data": "longitude"},
            {"data": "beginDate"},
            {"data": "endDate"},
            {"data": "variableName"},
            {"data": "variableCode"},
            {"data": "siteCode"},
            {"data": "networkName"},
            {"data": "methodDescription"},
            {"data": "methodLink"},
            {"data": "valueCount"},
            {"data": "sampleMedium"}
        ],
        "order": [[1, 'asc']],
    });

    // Gets the URL at which the data is located. //
    var serviceurl = trimInput($('#serviceurl').text());
    document.title = 'Create HydroShare Resource';
    var current_url = location.href;
    var index = current_url.indexOf("hydroshare-resource-creator");
    var base_url = current_url.substring(0, index);
    var src = findQueryParameter("src");
    if (src === 'hydroshare'){
        var res_id = findQueryParameter("res_id");
        $('#')
    }
    else{
        res_id ='None'
    }
    var data_url = base_url + 'hydroshare-resource-creator/chart-data/' + res_id + '/';

    // Passes the data to the AJAX function for loading the resource. //
    ajaxLoadResource(data, src, data_url)
};


createTimeseriesResource = function (){
    /**
     * Runs when Create Timeseries Resource button is clicked. Passes data from loadFormData to ajaxLoginTest.
     *
     * @requires loadFormData
     * @requires ajaxLoginTest
     */

    // Displays a loading animation. //
    $loadingAnimation.show();

    // Gets data from the page's data table and runs the ajaxLoginTest function. //
    var data = loadFormData('ts');
    ajaxLoginTest(data)
};


updateResource = function (){
    /**
     * Runs when Update Resource button is clicked. Passes data from loadFormData to ajaxLoginTest.
     *
     * @requires loadFormData
     * @requires ajaxLoginTest
     */

    // Displays a loading animation. //
    $loadingAnimation.show();

    // Gets data from the page's data table and runs the ajaxLoginTest function. //
    var data = loadFormData('update');
    ajaxLoginTest(data)
};


createReftsResource = function (){
    /**
     * Runs when Create Reference Timeseries Resource button is clicked. Passes data from loadFormData to ajaxLoginTest.
     *
     * @requires loadFormData
     * @requires ajaxLoginTest
     */

    // Displays a loading animation. //
    $loadingAnimation.show();

    // Gets data from the page's data table and runs the ajaxLoginTest function. //
    var data = loadFormData('refts');
    ajaxLoginTest(data)
};


loadFormData = function (action_request){
    /**
     * Gets resource data from the data table and prepares it for AJAX function.
     *
     * @requires findQueryParameter
     * @returns data
     */

    // Declares data variables. //
    var current_url = location.href;
    var index = current_url.indexOf("hydroshare-resource-creator");
    var base_url = current_url.substring(0, index);
    var data_url = base_url + 'hydroshare-resource-creator/login-test';
    var fun_type = $btnCreateReferenceTimeseries.attr('name');
    var res_type = $btnCreateReferenceTimeseries.attr('value');
    var res_id = findQueryParameter('res_id');
    var resTitle = $resTitle.val();
    var resAbstract = $resAbstract.val();
    var resKeywords = $resKeywords.val();
    var refts_filename = $('#reftsfilename').text()
    var checked_ids = $('input[data1-resid]:checkbox:checked').map(function() {
        return this.getAttribute("data1-resid");
    }).get();
    var series_type = $('input[name]:checkbox:checked').map(function() {
        return this.getAttribute("name");
    }).get();
    if($("#chk_public").is(':checked'))
        var res_access = 'public';
    else
        res_access = 'private';
    var data;

    // Prepares data for AJAX. //
    data = {
        'checked_ids': JSON.stringify(checked_ids),
        'resource_type': JSON.stringify(series_type),
        'resTitle': resTitle,
        'resAbstract': resAbstract,
        'resKeywords': resKeywords,
        'resAccess': res_access,
        'base_url': base_url,
        'fun_type': fun_type,
        'res_type': res_type,
        'res_id': res_id,
        'data_url': data_url,
        'refts_filename': refts_filename,
        'action_request': action_request
    };

    return data
};


findQueryParameter = function (name) {
    /**
     * Gets URL of resource data.
     *
     * @parameter name
     * @returns results
     */

    // Gets URL of data, or returns null if unsuccessful. //
    var url = location.href;
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( url );
    return results === null ? null : results[1];
};


finishLoading = function() {
    /**
     * Reveals page after loading is complete.
     *
     * @requires findQueryParameter
     */

    // Shows page content and hides the loading animation. //
    $(window).resize();
    $divCreateHydroshareResource.show();
    $(window).resize();
    console.log('hide');
    $loadingAnimation.hide();

    // Reveals Update Current Resource button only if a HydroShare resource is loaded. //
    $('#multiple_units').show();
    var src = findQueryParameter("src");
    if(src === 'hydroshare')
    {
        $btnUpdateCurrentResource.show();
    }
};


viewResource = function(hs_href){
    /**
     * Allows the user to view a HydroShare resource.
     *
     * @parameter hydroshare_id
     */

    // Opens the HydroShare resource in a window. //
    window.open(hs_href)
};


getCookie = function(name) {
    /**
     * Gets CSRF Token.
     *
     * @parameter name
     * @returns cookieValue
     */

    // Gets cookie value.
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
};


trimInput = function (string){
    /**
     * Trims a string (list) of extra extra characters.
     *
     * @parameter string
     * @returns string
     */

    // Removes brackets, quotation marks, and spaces from a string, and then splits it
    string = string.replace(']','');
    string = string.replace('[','');
    string = string.replace(/'/g,'');
    string = string.replace(/"/g,'');
    string = string.replace(/ /g,'');
    string = string.split(',');

    return string
};


errorReport = function(error){
    /**
     * Reports errors encountered during loading.
     *
     * @parameter error
     */

    // Appends errors to the error message.
    console.log(error);
    $(window).resize();
    $loadingAnimation.hide();
    $('#error-message').append(error)
};


/**********************************************
**************** AJAX FUNCTIONS ***************
**********************************************/

ajaxLoadResource = function (data, src, data_url){
    $.ajax({
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        type:"POST",
        dataType: 'json',
        public: false,
        data: {"refts_filename": $('#reftsfilename').text()},
        url: data_url,
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log(errorThrown)
            showLoadingCompleteStatus('error', textStatus);
        },
        success: function (response) {
            if (response.success === true) {
                var number = 0;
                var results = response.results;
                console.log(results)
                var title = results.title;
                var abstract = results.abstract;
                var keywords = results.keyWords;
                var date_small = new Date();
                var date_large = new Date('1600-01-01');
                var date_now = new Date();
                var site_list = [];
                var var_list = [];
                var referencedTimeSeries = results.referencedTimeSeries;
                var total_number = referencedTimeSeries.length;
                for (var val in referencedTimeSeries) {
                    if (referencedTimeSeries.hasOwnProperty(val)) {
                        var entry = referencedTimeSeries[val];
                        var siteName = entry.site.siteName;
                        var refType = entry.requestInfo.refType;
                        var serviceType = entry.requestInfo.serviceType;
                        var url = entry.requestInfo.url;
                        var returnType = entry.requestInfo.returnType;
                        var latitude = entry.site.latitude;
                        var longitude = entry.site.longitude;
                        var beginDate = entry.beginDate;
                        var endDate = entry.endDate;
                        var variableName = entry.variable.variableName;
                        var variableCode = entry.variable.variableCode;
                        var siteCode = entry.site.siteCode;
                        var networkName = entry.requestInfo.networkName;
                        var methodDescription = entry.method.methodDescription;
                        var methodLink = entry.method.methodLink;
                        var valueCount = entry.valueCount;
                        var sampleMedium = entry.sampleMedium;
                        var legend = "<div style='text-align:center' '><input class = 'checkbox' id =" + number + " data1-resid =" + number
                            + " type='checkbox' checked = 'checked'>" + "</div>";
                        var dataset = {
                            legend: legend,
                            refType: refType,
                            serviceType: serviceType,
                            url: url,
                            returnType: returnType,
                            latitude: latitude,
                            longitude: longitude,
                            siteName: siteName,
                            beginDate: beginDate,
                            endDate: endDate,
                            variableName: variableName,
                            variableCode: variableCode,
                            siteCode: siteCode,
                            networkName: networkName,
                            methodDescription: methodDescription,
                            methodLink: methodLink,
                            valueCount: valueCount,
                            sampleMedium: sampleMedium
                        };
                        var table = $tableResourceData.DataTable();
                        table.row.add(dataset).draw();
                        var_list.push(variableName);
                        site_list.push(siteName);
                        number = number + 1
                    }
                    if (number === total_number) {
                        if(src === 'hydroshare')    {}
                        else {
                            console.log("Formatting abstract");
                            var u_site_list = []
                            $.each(site_list, function(i, el) {
                                if($.inArray(el, u_site_list) === -1) u_site_list.push(el);
                            });
                            if (u_site_list.length > 1) {
                                var last = u_site_list[u_site_list.length - 1];
                                u_site_list.pop();
                                u_site_list.push('and ' + last);
                                u_site_list = u_site_list.join(', ')
                            } else {
                                u_site_list = site_list.toString()
                            }
                            var u_var_list = []
                            $.each(var_list, function(i, el) {
                                if($.inArray(el, u_var_list) === -1) u_var_list.push(el);
                            });
                            if (u_var_list.length > 1) {
                                var last = u_var_list[u_var_list.length - 1];
                                u_var_list.pop();
                                u_var_list.push('and ' + last);
                                u_var_list = u_var_list.join(', ')
                            } else {
                                u_var_list = var_list.toString()
                            }
                            title = "Time series layer resource created on " + date_now;
                            abstract = u_var_list + " data collected from " + date_small.toISOString().substring(0, 10) +
                                " to " + date_large.toISOString().substring(0, 10) + " created on " + date_now +
                                " from the following site(s): " + u_site_list + ". Data created by CUAHSI HydroClient: " +
                                "http://data.cuahsi.org/#."
                        }
                        $resTitle.val(title);
                        $resAbstract.text(abstract);
                        $resKeywords.val(keywords);
                        finishLoading();
                    }
                }
            } else {
                $loadingAnimation.hide();
                var message = response.message;
                $modalErrorMessage.text(message);
                $modalErrorDialog.modal('show');
            }
        }
    })
};


ajaxCreateResource = function (data) {
    $divCreateHydroshareResource.hide();
    $modalErrorMessage.empty()
    var data_url = data.base_url + 'hydroshare-resource-creator/create-resource/';
    console.log(data_url)
    $.ajax({
        type: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        dataType: 'json',
        data: data,
        url: data_url,
        timeout: 300000,
        success: function (response) {
            if (response.success === true) {
                $modalResourceDialogTitle.append('Resource Created Successfully');
                var resource = response.results;
                var hs_href = 'https://' + resource['hs_version'] + '/resource/' + resource['resource_id'];
                $modalResourceDialogWelcomeInfo.append('<a href=' + hs_href + ' target="_blank">Click here to view.</a>');
                $btnCreateTimeseriesResource.hide();
                $btnCreateReferenceTimeseries.hide();
                $publicResource.hide();
                $divViewResource.append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + hs_href + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
                $modalResourceDialog.on('hidden.bs.modal', finishLoading)
            }
            else {
                $loadingAnimation.hide();
                if (response.message === "PARSE_ERROR") {
                    for (var i = 0; i < (response.results).length; i++) {
                        $modalErrorMessage.append("<div>" + response.results[i] + "</div><br/>")

                    }
                    $modalErrorDialog.modal('show');
                    $modalErrorDialog.on('hidden.bs.modal', finishLoading)
                } else {
                    $modalErrorMessage.text(response.message);
                    console.log(response.results);
                    $modalErrorDialog.modal('show');
                    $modalErrorDialog.on('hidden.bs.modal', finishLoading)
                }
            }

            finishLoading()
        },
        error:function(XMLHttpRequest, textStatus, errorThrown){
            $loadingAnimation.hide();
            console.log('Error: ', errorThrown)
            if (errorThrown === 'timeout') {
                $modalErrorMessage.text('Call has timed out.');
            } else {
                $modalErrorMessage.text('Encountered unknown error.');
            }
            $modalErrorDialog.modal('show');
            $modalErrorDialog.on('hidden.bs.modal', finishLoading)
        }
    })
};


ajaxLoginTest = function (data){
    $.ajax({
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        type: "POST",
        dataType: "json",
        public: false,
        data: data,
        url: data.data_url + '/',
        async: true,
        success: function (response) {
            if (response['success'] === "True"){
                var errorList = [];
                if (data.checked_ids.length === 2){
                    errorList.push('Please select at least one resource to create.')
                }
                if (data.resTitle === '') {
                    errorList.push('Please enter a title for your resource.');
                }
                if (data.resAbstract === '') {
                    errorList.push('Please enter an abstract for your resource.');
                }
                if (data.resKeywords === '') {
                    errorList.push('Please enter at least one keyword for your resource.');
                }
                if (errorList.length === 0) {
                    ajaxCreateResource(data);
                }
                else {
                    errorList = (errorList.toString()).split(",").join("\n");
                    $loadingAnimation.hide();
                    alert(errorList)
                }
            }
            else {
                $loadingAnimation.hide();

                if (data.data_url.includes("appsdev.hydroshare.org")) {
                    window.open("/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                }
                if (data.data_url.includes("apps.hydroshare.org")) {
                    window.open("/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                }
                if (data.data_url.includes("8000")) {
                    window.open("/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            //Edit later
            console.log(errorThrown)
        }
    });
};


/**********************************************
*************** EVENT LISTENERS ***************
**********************************************/

$document.ready(loadResource);
$btnCreateReferenceTimeseries.on('click', createReftsResource);
$btnUpdateCurrentResource.on('click', updateResource);
$btnCreateTimeseriesResource.on('click', createTimeseriesResource);

$("#table-resource-data").on("mouseenter", "td", function() {
  $(this).attr('title', this.innerText);
});
