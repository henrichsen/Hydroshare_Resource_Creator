/**********************************************
************** QUERY SELECTORS ****************
**********************************************/

var $modalResourceDialog = $('#modal-resource-dialog');
var $modalResourceDialogTitle = $('#modal-resource-dialog-title');
var $modalResourceDialogWelcomeInfo = $('#modal-resource-dialog-welcome-info');
var $modalErrorDialog = $('#modal-error-dialog');
var $modalRedirectDialog = $('#modal-redirect-dialog');
var $modalErrorMessage = $('#modal-error-message');
var $modalLoginDialog = $('#modal-login-dialog');
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
var createTimeseriesResource;
var updateResource;
var createReftsResource;
var finishLoading;
var viewResource;
var getCookie;
var errorReport;
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

    originalData = $('#source').text()
    console.log("Original Data")
    console.log(originalData)
    formData = $('#form_body').text()
    console.log(formData)

    if (formData === '"No data"'){

        $modalRedirectDialog.modal('show');
        $modalErrorDialog.on('hidden.bs.modal', $loadingAnimation.hide())

    } 
    else if ($('#form_body').text() === "File processing error"){
        $modalErrorMessage.text("File processing error.");
        console.log("File processing error.")
        $modalErrorDialog.modal('show');
        $modalErrorDialog.on('hidden.bs.modal', $loadingAnimation.hide())

    }
    else{
        var formBody = JSON.parse($('#form_body').text())
        var dataSeriesList = formBody['timeSeriesReferenceFile']['referencedTimeSeries']
        var dataSet = []
        var varList = []
        var siteList = []
        var keywordsList = []
        var dateList = []
        var dateNow = new Date();
        for (var dataSeriesCount = 0; dataSeriesCount < dataSeriesList.length; dataSeriesCount++) {
            var legend = "<div style='text-align:center' '>" +
                            "<input class = 'checkbox' id =" + dataSeriesCount + 
                            " data1-resid =" + dataSeriesCount + 
                            " type='checkbox' checked = 'checked'>" + 
                         "</div>"
            var siteName = dataSeriesList[dataSeriesCount]['site']['siteName']
            var refType = dataSeriesList[dataSeriesCount]['requestInfo']['refType']
            var serviceType = dataSeriesList[dataSeriesCount]['requestInfo']['serviceType']
            var url = dataSeriesList[dataSeriesCount]['requestInfo']['url']
            var returnType = dataSeriesList[dataSeriesCount]['requestInfo']['returnType']
            var latitude = dataSeriesList[dataSeriesCount]['site']['latitude']
            var longitude = dataSeriesList[dataSeriesCount]['site']['longitude']
            var beginDate = dataSeriesList[dataSeriesCount]['beginDate']
            var endDate = dataSeriesList[dataSeriesCount]['endDate']
            var variableName = dataSeriesList[dataSeriesCount]['variable']['variableName']
            var variableCode = dataSeriesList[dataSeriesCount]['variable']['variableCode']
            var siteCode = dataSeriesList[dataSeriesCount]['site']['siteCode']
            var networkName = dataSeriesList[dataSeriesCount]['requestInfo']['networkName']
            var methodDescription = dataSeriesList[dataSeriesCount]['method']['methodDescription']
            var methodLink = dataSeriesList[dataSeriesCount]['method']['methodLink']
            var valueCount = dataSeriesList[dataSeriesCount]['valueCount']
            var sampleMedium = dataSeriesList[dataSeriesCount]['sampleMedium']
            dataSet.push([legend, siteName, refType, serviceType, url, returnType, latitude, longitude,
                          beginDate, endDate, variableName, variableCode, siteCode, networkName, 
                          methodDescription, methodLink, valueCount, sampleMedium])
            varList.push(variableName.replace(/,/g, ''));
            siteList.push(siteName.replace(/,/g, ''));
            keywordsList.push(variableName.replace(/,/g, ''))
            keywordsList.push(networkName.replace(/,/g, ''))
            dateList.push(beginDate);
            dateList.push(endDate);
        };
        var tableResourceData = $('#table-resource-data').DataTable({
            scrollX: true,
            data: dataSet, 
            columns: [
                {title: ""},
                {title: "Site Name"},
                {title: "Reference Type"},
                {title: "Service Type"},
                {title: "URL"},
                {title: "Return Type"},
                {title: "Latitude"},
                {title: "Longitude"},
                {title: "Begin Date"},
                {title: "End Date"},
                {title: "Variable Name"},
                {title: "Variable Code"},
                {title: "Site Code"},
                {title: "Network Name"},
                {title: "Method Description"},
                {title: "Method Link"},
                {title: "Value Count"},
                {title: "Sample Medium"},
            ],
            order: [[1, 'asc']],
            columnDefs: [
                { orderable: false, targets: 0 }
            ]
        });

        var uSiteList = []
        var siteMultiplicty = 's'
        $.each(siteList, function(i, el){
            if($.inArray(el, uSiteList) === -1) uSiteList.push(el);
        });
        if(uSiteList.length === 2) {
            var sSiteList = uSiteList.join(" and ")
        }
        if(uSiteList.length === 1) {
            var sSiteList = uSiteList.toString()
            var siteMultiplicty = ''
        }
        if(uSiteList.length > 2) {
            var uSiteListLast = uSiteList.pop()
            uSiteList.push("and " + uSiteListLast)
            var sSiteList = (uSiteList.join(", "))
        }
        var uVarList = []
        $.each(varList, function(i, el){
            if($.inArray(el, uVarList) === -1) uVarList.push(el);
        });
        if(uVarList.length === 2) {
            sVarList = ((uVarList.join(" and ")).toLowerCase()).charAt(0).toUpperCase() + ((uVarList.join(" and ")).toLowerCase()).slice(1);
        }
        if(uVarList.length === 1) {
            sVarList = ((uVarList.toString()).toLowerCase()).charAt(0).toUpperCase() + ((uVarList.toString()).toLowerCase()).slice(1);
        }
        if(uVarList.length > 2) {
            uVarListLast = uVarList.pop()
            uVarList.push("and " + uVarListLast)
            sVarList = ((uVarList.join(", ")).toLowerCase()).charAt(0).toUpperCase() + ((uVarList.join(", ")).toLowerCase()).slice(1);
        }
        var uKeywordsList = []
        $.each(keywordsList, function(i, el){
            if($.inArray(el, uKeywordsList) === -1) uKeywordsList.push(el);
        });  
        orderedDates = dateList.sort(function(a,b){
            return Date.parse(a) > Date.parse(b);
        })                                                     
        title = "Time series dataset created on " + dateNow + " by the CUAHSI HydroClient";
        abstract = sVarList + " data collected from " + orderedDates[0] +
            " to " + orderedDates.slice(-1)[0] + " created on " + dateNow +
            " from the following site" + siteMultiplicty + ": " + sSiteList + ". Data created by CUAHSI HydroClient: " +
            "http://data.cuahsi.org/#."
        $resTitle.val(title);
        $resAbstract.text(abstract);
        $resKeywords.val(uKeywordsList);


        tableResourceData.$('tr').tooltip( {
            "delay": 0,
            "track": true,
            "fade": 250
        } );


        $("#table-resource-data").on("mouseenter", "td", function() {
            $(this).attr('title', this.innerText);
        });

        finishLoading();
    }
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
    var currentUrl = location.href;
    var index = currentUrl.indexOf("hydroshare-resource-creator");
    var baseUrl = currentUrl.substring(0, index);
    var dataUrl = baseUrl + 'hydroshare-resource-creator/login-test';
    var resTitle = $resTitle.val();
    var resAbstract = $resAbstract.val();
    var resKeywords = $resKeywords.val();
    var checkedIds = $('input[data1-resid]:checkbox:checked').map(function() {
        return this.getAttribute("data1-resid");
    }).get();
    if($("#chk_public").is(':checked'))
        var resAccess = 'public';
    else
        resAccess = 'private';
    formBody = $('#form_body').text()
    var data = {
        'baseUrl': baseUrl,
        'dataUrl': dataUrl,
        'resTitle': resTitle,
        'resAbstract': resAbstract,
        'resKeywords': resKeywords,
        'checkedIds': checkedIds.toString(),
        'resAccess': resAccess,
        'formBody': formBody,
        'actionRequest': 'ts'
    }
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
    var currentUrl = location.href;
    var index = currentUrl.indexOf("hydroshare-resource-creator");
    var baseUrl = currentUrl.substring(0, index);
    var dataUrl = baseUrl + 'hydroshare-resource-creator/login-test';
    var resTitle = $resTitle.val();
    var resAbstract = $resAbstract.val();
    var resKeywords = $resKeywords.val();
    var checkedIds = $('input[data1-resid]:checkbox:checked').map(function() {
        return this.getAttribute("data1-resid");
    }).get();
    if($("#chk_public").is(':checked')){
        var resAccess = 'public';
    }
    else{
        resAccess = 'private';
    };
    formBody = $('#form_body').text()
    
    var data = {
        'baseUrl': baseUrl,
        'dataUrl': dataUrl,
        'resTitle': resTitle,
        'resAbstract': resAbstract,
        'resKeywords': resKeywords,
        'checkedIds': checkedIds.toString(),
        'resAccess': resAccess,
        'formBody': formBody,
        'actionRequest': 'refts',
    }
    ajaxLoginTest(data)
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

ajaxCreateResource = function (data) {
    $divCreateHydroshareResource.hide();
    $modalErrorMessage.empty()
    var dataUrl = data.baseUrl + 'hydroshare-resource-creator/create-resource/';
    console.log(dataUrl)
    $.ajax({
        type: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        dataType: 'json',
        data: data,
        url: dataUrl,
        timeout: 3600000,
        success: function (response) {
            if (response.success === true) {
                $modalResourceDialogTitle.append('Resource Created Successfully');
                var resource = response.results;
                var hs_href = 'https://' + resource['hs_version'] + '/resource/' + resource['resource_id'];
                $modalResourceDialogWelcomeInfo.append('<a href=' + hs_href + ' target="_blank">Click here to view.</a>');
                $btnCreateTimeseriesResource.hide();
                $btnCreateReferenceTimeseries.hide();
                $publicResource.hide()
                $resTitle.prop("disabled", true);
                $resAbstract.prop("disabled", true);
                $resKeywords.prop("disabled", true);
                $divViewResource.append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="' + hs_href + '" onclick="viewResource(this.name)">View Resource</button>');
                $modalResourceDialog.modal('show');
                $modalResourceDialog.on('hidden.bs.modal', finishLoading)
            }
            else {

                $loadingAnimation.hide();
                if (response.message === "PARSE_ERROR") {
                    $modalErrorMessage.append("<div>We encountered a problem while processing the following timeseries:</div><ul style='list-style-type:circle; margin-left: 2em; padding:0'>")
                    for (var i = 0; i < (response.results).length; i++) {
                        $modalErrorMessage.append("<li>" + response.results[i] + "</li>")

                    };
                    $modalErrorMessage.append("</ul><br><div>Please deselect these timeseries and try again.</div>")
                    $modalErrorDialog.modal('show');
                    $modalErrorDialog.on('hidden.bs.modal', finishLoading);
                } else {
                    $modalErrorMessage.text(response.message);
                    console.log(response.results);
                    $modalErrorDialog.modal('show');
                    $modalErrorDialog.on('hidden.bs.modal', finishLoading);
                };
            };

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
        url: data.dataUrl + '/',
        async: true,
        success: function (response) {
            if (response['success'] === "True"){
                var errorList = [];
                if (response['message'] === "TooManyValues"){
                    errorList.push('Your selected resources contain more than one hundred thousand total values. Please select fewer resources to continue.')
                }
                if (data['checkedIds'].length === 0){
                    errorList.push('Please select at least one resource to create.')
                }
                if (data['resTitle'] === '') {
                    errorList.push('Please enter a title for your resource.');
                }
                if (data['resAbstract'] === '') {
                    errorList.push('Please enter an abstract for your resource.');
                }
                if (data['resKeywords'] === '') {
                    errorList.push('Please enter at least one keyword for your resource.');
                }
                if (errorList.length === 0) {
                    console.log(data)
                    ajaxCreateResource(data);
                }
                else {
                    $loadingAnimation.hide(); 
                    errorList = (errorList.toString()).split(",").join("\n");
                    setTimeout(function() { alert(errorList); }, 10);
                }

            }
            else {
                $loadingAnimation.hide();

                if (data.dataUrl.includes("appsdev.hydroshare.org")) {
                    $modalLoginDialog.modal('show')
                    $('#login-link').attr("onClick", "window.open('/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')")
                    //"window.open('/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')";
                }
                if (data.dataUrl.includes("apps.hydroshare.org")) {
                    $modalLoginDialog.modal('show')
                    $('#login-link').attr("onClick", "window.open('/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')")
                    //window.open("/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                }
                if (data.dataUrl.includes("hs-apps-dev.hydroshare.org")) {
                    $modalLoginDialog.modal('show')
                    $('#login-link').attr("onClick", "window.open('/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')")
                    //"window.open('/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')";
                }
                if (data.dataUrl.includes("hs-apps.hydroshare.org")) {
                    $modalLoginDialog.modal('show')
                    $('#login-link').attr("onClick", "window.open('/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')")
                    //window.open("/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                }
                if (data.dataUrl.includes("8000")) {
                    $modalLoginDialog.modal('show')
                    $('#login-link').attr("onClick", "window.open('/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/', 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable')")
                    //window.open("/oauth2/login/hydroshare_beta/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
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
