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
var $loadingAnimation = $('#loading');
var $document = $(document);
var $divCreateHydroshareResource = $('#div-create-hydroshare-resource');
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
var ajaxCreateTimeseriesResource;
var ajaxUpdateResource;
var ajaxCreateReftsResource;


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
        "createdRow": function (){
            var table = $tableResourceData.DataTable();
            table.$('td').tooltip({
                selector: '[data-toggle="tooltip"]',
                container: 'body',
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
            "width":"50%"
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
        "order": [[1, 'asc']]
    });

    // Gets the URL at which the data is located. //
    var serviceurl = trimInput($('#serviceurl').text());
    console.log('SERVICE URL:');
    console.log(serviceurl);
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
    var data_url = base_url + 'hydroshare-resource-creator/chart_data/' + res_id + '/';
    console.log('DATA URL:');
    console.log(data_url);

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
    var data = loadFormData();
    ajaxLoginTest(data, 'CreateTimeseriesResource')
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
    var data = loadFormData();
    ajaxLoginTest(data, 'UpdateResource')
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
    var data = loadFormData();
    ajaxLoginTest(data, 'CreateReftsResource')
};


loadFormData = function (){
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
        'data_url': data_url
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
    console.log("REGEX RESULTS");
    console.log(results);
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
        /**
         * Sends data to chart_data AJAX Controller
         *
         * @parameter data
         * @parameter src
         * @parameter data_url
         * @requires finishLoading
         * @param response.results
         * @param results.title
         * @param results.abstract
         * @param results.keyWords
         * @param results.referencedTimeSeries
         * @param entry.site
         * @param entry.requestInfo
         * @param entry.method.methodDescription
         * @param entry.method.methodLink
         * @param entry.variable
         * @param table.row
         */
        type:"POST",
        dataType: 'json',
        public: false,
        data: data,
        url: data_url,
        error: function (ignore, textStatus) {
            showLoadingCompleteStatus('error', textStatus);
        },
        success: function (response) {
            if (response.success === true) {
                var number = 0;
                var results = response.results;
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
                        number = number + 1
                    }
                    if (number === total_number) {
                        if(src === 'hydroshare')    {}
                        else {
                            console.log("formatting abstract");
                            if (site_list.length > 1) {
                                var last = site_list[site_list.length - 1];
                                site_list.pop();
                                site_list.push('and ' + last);
                                site_list = site_list.join(', ')
                            }
                            title = "Time series layer resource created on " + date_now;
                            abstract = var_list + " data collected from " + date_small.toISOString().substring(0, 10) +
                                " to " + date_large.toISOString().substring(0, 10) + " created on " + date_now +
                                " from the following site(s): " + site_list + ". Data created by CUAHSI HydroClient: " +
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


ajaxLoginTest = function (data, type){
    /**
     * Sends data to login_test AJAX Controller
     *
     * @parameter data
     * @parameter src
     * @parameter data_url
     * @requires ajaxCreateTimeseriesResource
     * @requires ajaxUpdateResource
     * @requires ajaxCreateReftsResource
     *
     * @param data.resTitle
     * @param data.checked_ids
     * @param json.Login
     */
    $.ajax({
        type: "POST",
        dataType: "json",
        public: false,
        data: data,
        url: data.data_url + "/",
        async: true,
        success: function (response) {
            var login = response;
            if (login['success'] === "True"){
                var errorList = [];
                if (data.resTitle === '') {
                    errorList.push('Resource title cannot be left blank.');
                }
                if (data.checked_ids.length === 2){
                    errorList.push('At least one resource needs to be selected.')
                }
                if (errorList.length === 0) {
                    if (type === 'CreateTimeseriesResource'){
                        ajaxCreateTimeseriesResource(data)
                    }
                    if (type === 'UpdateResource'){
                        ajaxUpdateResource(data)
                    }
                    if (type === 'CreateReftsResource'){
                        ajaxCreateReftsResource(data)
                    }
                }
                else {
                    errorList = (errorList.toString()).split(",").join("\n");
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
        error: function (ignore, textStatus) {
            //Edit later
            showLoadingCompleteStatus('error', textStatus);
        }
    });
};


ajaxCreateTimeseriesResource = function (data, id){
    /**
     * Sends data to ajax_create_timeseries_resource AJAX Controller.
     *
     * @parameter data
     * @paramter id
     * @requires getCookie
     * @requires finishLoading
     *
     * @param data.base_url
     * @param json.success
     * @param json.error
     * @param json.Request
     */
    $divCreateHydroshareResource.hide();
    var csrf_token = getCookie('csrftoken');
    var data_url = data.base_url + 'hydroshare-resource-creator/create_timeseries_resource/create/' + data.res_id + '/refts/';

    $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': csrf_token},
        dataType: 'json',
        data: data,
        url: data_url,
        timeout: 300000,
        success: function (response) {
            if (response.success === true) {
                $modalResourceDialogTitle.append("Resource Created Successfully");
                var resource = response.results;
                var hs_href = "https://" + resource['hs_version'] + "/resource/" + resource['resource_id'];
                $modalResourceDialogWelcomeInfo.append('<a href=' + hs_href + ' target="_blank">Click here to view.</a>');
                $btnCreateReferenceTimeseries.hide();
                $btnCreateTimeseriesResource.hide();
                $('#public_hydro').hide();
                $('#div_view_resource').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + hs_href + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
            }
            else {
                $modalErrorMessage.text(response.message);
                $modalErrorDialog.modal('show');
            }
            finishLoading()
        },
        error:function(textStatus){
            if (textStatus === 'timeout') {
                $modalErrorMessage.text('Call has timed out.');
                $modalErrorDialog.modal('show');
            }
        }
    })
};


ajaxUpdateResource = function (data, id){
    /**
     * Sends data to ajax_update_resource AJAX Controller.
     *
     * @parameter data
     * @parameter id
     * @requires getCookie
     * @requires finishLoading
     *
     * @param data.base_url
     * @param data.res_id
     * @param json.error
     */
    $divCreateHydroshareResource.hide();
    var csrf_token = getCookie('csrftoken');
    var data_url = data.base_url + 'hydroshare-resource-creator/update_resource/update/' + data.res_id + '/refts/';

    $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': csrf_token},
        dataType: 'json',
        data: data,
        url: data_url,
        timeout: 3000,
        success: function (json) {
            alert('Done');
            console.log(json);
            if(json.error !== ''){alert(json.error)}
            else
            {
                //create_resource()
                //wait(50000);
                var current_url = location.href;
                var index = current_url.indexOf("hydroshare-resource-creator");
                var base_url = current_url.substring(0, index);
                window.location = base_url + 'hydroshare-resource-creator/?src=hydroshare&res_id=' + data.res_id;
                var resource = json.Request;
                $modalResourceDialogWelcomeInfo.append('<a href="https://www.hydroshare.org/resource/' + resource + '" target="_blank">Click here to view.</a>');
                $btnCreateReferenceTimeseries.hide();
                $btnCreateTimeseriesResource.hide();
                $('#public_hydro').hide();
                $('#div_view_resource').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + json.Request + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
            }
            finishLoading()
        },
        error:function(textStatus){
            if (textStatus === 'timeout'){
                alert('Call has timed out.')
            }
        }
    })
};


ajaxCreateReftsResource = function (data, id){
    /**
     * Sends data to ajax_create_refts_resource AJAX Controller.
     *
     * @parameter data
     * @paramter id
     * @requires getCookie
     * @requires finishLoading
     *
     * @param data.base_url
     * @param data.res_id
     * @param json.error
     * @param json.Request
     */
    $divCreateHydroshareResource.hide();
    var csrf_token = getCookie('csrftoken');
    var data_url = data.base_url + 'hydroshare-resource-creator/create_refts_resource/ts/' + data.res_id + '/ts/';

    $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': csrf_token},
        dataType: 'json',
        data: data,
        url: data_url,
        timeout: 300000,
        success: function (response) {
            if (response.success === true) {
                $modalResourceDialogTitle.append("Resource Created Successfully");
                var resource = response.results;
                var hs_href = "https://" + resource['hs_version'] + "/resource/" + resource['resource_id'];
                $modalResourceDialogWelcomeInfo.append('<a href=' + hs_href + ' target="_blank">Click here to view.</a>');
                $btnCreateReferenceTimeseries.hide();
                $btnCreateTimeseriesResource.hide();
                $('#public_hydro').hide();
                $('#div_view_resource').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + hs_href + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
            }
            else {
                $modalErrorMessage.text(response.message);
                $modalErrorDialog.modal('show');
            }
            finishLoading()
        },
        error:function(textStatus){
            if (textStatus === 'timeout'){
                $modalErrorMessage.text('Call has timed out.');
                $modalErrorDialog.modal('show');
            }
        }
    })
};


/**********************************************
*************** EVENT LISTENERS ***************
**********************************************/

$document.ready(loadResource);
$btnCreateReferenceTimeseries.on('click', createReftsResource);
$btnUpdateCurrentResource.on('click', updateResource);
$btnCreateTimeseriesResource.on('click', createTimeseriesResource);


/*
        $.ajax({
        type:"POST",
        dataType: 'json',
        public: false,
        data:{'serviceurl':serviceurl},
        url: data_url,
        success: function (json) {
            console.log(json);
            if (json.error !== ''){
                errorReport(json.error);
                console.log('error')
            }
            else {
                console.log(json.public);
                if (json.public === true){
                    document.getElementById("#chk_public").checked = true;
                }
                console.log('No error');
                var series_details = json.data;
                var title = series_details.title;
                var abstract = series_details.abstract;
                var keywords = series_details.keyWords;
                var date_small = new Date();
                var date_large = new Date('1600-01-01');
                var date_now = new Date();
                var site_list = [];
                var var_list = [];
                series_details = series_details.REFTS;
                var total_number = series_details.length;
                console.log(total_number);
                for (var val in series_details) {
                    var entry = series_details[val];
                    var series_counter = series_counter + 1;
                    var site_name = entry.site;
                    if(site_list.indexOf(site_name) === -1){
                        site_list.push(site_name)
                    }
                    var variable_name = entry.variable;
                    var RefType = entry.refType;
                    var ServiceType = entry.serviceType;
                    var URL = entry.url;
                    var ReturnType = entry.returnType;
                    var Lat = entry.location.latitude;
                    var Lon = entry.location.longitude;
                    var begindate = entry.beginDate;
                    var enddate = entry.endDate;
                    var date_begindate = new Date(begindate);
                    var date_enddate = new Date(enddate);
                    if(date_small > date_begindate){
                        date_small = date_begindate
                    }
                    if(date_large < date_enddate){
                        date_large = date_enddate
                    }
                    var variable = entry.variable;
                    if(var_list.indexOf(variable) === -1){
                        var_list.push(variable)
                    }
                    var var_code = entry.variableCode;
                    var site_code = entry.siteCode;
                    var network = entry.networkName;
                    if (site_name === null) {
                        site_name = "N/A"
                    }
                    if (variable_name === null) {
                        variable_name = "N/A"
                    }
                    if (RefType === null) {
                        RefType = "N/A"
                    }
                    if (ServiceType === null) {
                        ServiceType = "N/A"
                    }
                    if (URL === null) {
                        URL = "N/A"
                    }
                    if (ReturnType === null) {
                        ReturnType = "N/A"
                    }
                    if (Lat === null) {
                        Lat = "N/A"
                    }
                    if (Lon === null) {
                        Lon = "N/A"
                    }
                    var legend = "<div style='text-align:center' '><input class = 'checkbox' id =" + number + " data1-resid =" + number
                        + " type='checkbox' checked = 'checked'>" + "</div>";
                    var dataset = {
                        legend: legend,
                        RefType: RefType,
                        ServiceType: ServiceType,
                        URL: URL,
                        ReturnType: ReturnType,
                        Lat: Lat,
                        Lon: Lon,
                        site: site_name,
                        beginDate: begindate,
                        //endDate: enddate,
                        variable: variable,
                        var_code: var_code,
                        site_code: site_code,
                        network: network
                    };
                    var table = $tableResourceData.DataTable();
                    table.row.add(dataset).draw();
                    number = number + 1
                }
                if (number === total_number) {
                    if(src === 'hydroshare')    {}
                    else {
                        console.log("formatting abstract");
                        if (site_list.length > 1) {
                        var last = site_list[site_list.length - 1];
                        site_list.pop();
                        site_list.push('and ' + last);
                        site_list = site_list.join(', ')
                        }
                        title ="Time series layer resource created on "+date_now;
                        abstract = var_list +" data collected from "+date_small.toISOString().substring(0, 10) +" to "+ date_large.toISOString().substring(0, 10)+
                                " created on "+ date_now+" from the following site(s): " + site_list+". Data created by CUAHSI HydroClient: " +
                                "http://data.cuahsi.org/#."
                    }
                    $resTitle.val(title);
                    $resAbstract.text(abstract);
                    $resKeywords.val(keywords);
                    finishLoading()
                }
            }
        },
        error: function(){
            errorReport("Error loading data from data client");
            console.log("error")
        }
    })
};
*/

/*
onReadyLoadResource = function (){

    * Loads resource data with ajax call, then populates table with resource data.
    *
    *

    $divCreateHydroshareResource.hide();
    $btnUpdateCurrentResource.hide();
    var data = [];
    $tableResourceData.DataTable({
        "scrollX": true,
        "createdRow": function () {
            var table = $tableResourceData.DataTable();
            table.$('td').tooltip({
                selector: '[data-toggle="tooltip"]',
                container: 'body',
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
            {"data": "site",
            "width":"50%"
            },
            {"data": "RefType"},
            {"data": "ServiceType"},
            {"data": "URL"},
            {"data": "ReturnType"},
            {"data": "Lat"},
            {"data": "Lon"},
            {"data": "beginDate"},
            {"data": "variable"},
            {"data": "var_code"},
            {"data": "site_code"},
            {"data": "network"}
        ],
        "order": [[1, 'asc']]
    });
    var serviceurl = $('#serviceurl').text();
    serviceurl = trimInput(serviceurl);
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
    var data_url = base_url + 'hydroshare-resource-creator/chart_data/'+res_id+'/';

    $.ajax({

        * AJAX Controller: chart_data
        *
        * @param response              Response from server.
        * @param response.success      Either true or false.
        * @param response.message      Contains server side error message.
        * @param response.results      Contains results from server.
        * @param results               List of data for each reference timeseries.
        * @param results.abstract      Resource abstract, if available.
        * @param results.keyWords      Resource keywords, if available.
        * @param results.REFTS         Individual reference timeseries data.
        * @param REFTS.site
        * @param REFTS.refType
        * @param REFTS.serviceType
        * @param REFTS.url
        * @param REFTS.returnType
        * @param REFTS.beginDate
        * @param REFTS.endDate
        * @param REFTS.variable
        * @param REFTS.variableCode
        * @param REFTS.siteCode
        * @param REFTS.networkName
        * @param table.row


        type:"POST",
        dataType: 'json',
        public: false,
        data: data,
        url: data_url,
        error: function (ignore, textStatus) {
            showLoadingCompleteStatus('error', textStatus);
        },
        success: function (response) {
            if (response.success === true) {
                var results = response.results;
                var title = results.title;
                var abstract = results.abstract;
                var keywords = results.keyWords;
                var date_small = new Date();
                var date_large = new Date('1600-01-01');
                var date_now = new Date();
                var site_list = [];
                var var_list = [];
                var REFTS = results.REFTS;
                var total_number = REFTS.length;
                for (var val in REFTS) {
                    if (REFTS.hasOwnProperty(val)) {
                        var entry = REFTS[val];
                        var site_name = entry.site;
                        var RefType = entry.refType;
                        var ServiceType = entry.serviceType;
                        var URL = entry.url;
                        var ReturnType = entry.returnType;
                        var Lat = entry.location.latitude;
                        var Lon = entry.location.longitude;
                        var begindate = entry.beginDate;
                        // var enddate = entry.endDate;
                        var variable = entry.variable;
                        var var_code = entry.variableCode;
                        var site_code = entry.siteCode;
                        var network = entry.networkName;
                        var legend = "<div style='text-align:center' '><input class = 'checkbox' id =" + number + " data1-resid =" + number
                            + " type='checkbox' checked = 'checked'>" + "</div>";
                        var dataset = {
                            legend: legend,
                            RefType: RefType,
                            ServiceType: ServiceType,
                            URL: URL,
                            ReturnType: ReturnType,
                            Lat: Lat,
                            Lon: Lon,
                            site: site_name,
                            beginDate: begindate,
                            //endDate: enddate,
                            variable: variable,
                            var_code: var_code,
                            site_code: site_code,
                            network: network
                        };
                        var table = $tableResourceData.DataTable();
                        table.row.add(dataset).draw();
                        number = number + 1
                    }
                    if (number === total_number) {
                        if(src === 'hydroshare')    {}
                        else {
                            console.log("formatting abstract");
                            if (site_list.length > 1) {
                                var last = site_list[site_list.length - 1];
                                site_list.pop();
                                site_list.push('and ' + last);
                                site_list = site_list.join(', ')
                            }
                            title = "Time series layer resource created on " + date_now;
                            abstract = var_list + " data collected from " + date_small.toISOString().substring(0, 10) +
                                " to " + date_large.toISOString().substring(0, 10) + " created on " + date_now +
                                " from the following site(s): " + site_list + ". Data created by CUAHSI HydroClient: " +
                                "http://data.cuahsi.org/#."
                        }
                        $resTitle.val(title);
                        $resAbstract.text(abstract);
                        $resKeywords.val(keywords);
                        finishLoading();
                    }
                }
            } else {
                var message = response.message;
                alert(message)
            }
        }
    })
};
*/

/*
ajaxCreateUpdate = function (data){
    $divCreateHydroshareResource.hide();
    var csrf_token = getCookie('csrftoken');
    var data_url = data.base_url + 'hydroshare-resource-creator/create_layer/' + data.fun_type+'/' + data.res_id + '/' + data.res_type + '/';

    $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': csrf_token},
        dataType: 'json',
        data: data,
        url: data_url,
        timeout: 3000,
        success: function (json) {
            alert('Done');
            console.log(json);
            if(json.error !== ''){alert(json.error)}
            else
            {
                //create_resource()
                if (data.fun_type === 'update')//reloads page so that resource is reloaded
                {
                    //wait(50000);
                    var current_url = location.href;
                    var index = current_url.indexOf("hydroshare-resource-creator");
                    var base_url = current_url.substring(0, index);
                    window.location = base_url + 'hydroshare-resource-creator/?src=hydroshare&res_id=' + data.res_id
                }
                else{$modalResourceDialogTitle.append("Resource Created Successfully") }
                var resource = json.Request;
                $modalResourceDialogWelcomeInfo.append('<a href="https://www.hydroshare.org/resource/' + resource + '" target="_blank">Click here to view.</a>');
                $btnCreateReferenceTimeseries.hide();
                $btnCreateTimeseriesResource.hide();
                $('#public_hydro').hide();
                $('#div_view_resource').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + json.Request + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
            }
            finishLoading()
        },
        error:function(textStatus){
            if (textStatus === 'timeout'){
                alert('Call has timed out.')
            }
        }
    })
};
 */