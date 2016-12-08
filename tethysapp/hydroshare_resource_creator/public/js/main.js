function find_query_parameter(name) {
    url = location.href;
    //name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( url );
    return results == null ? null : results[1];
}
series_counter = 0
//$.ajaxSetup({
//   async: false
//});
var number = 0
function create_resource(){

    current_url = location.href;
    index = current_url.indexOf("hydroshare-resource-creator");
    base_url = current_url.substring(0, index);
    //var src = find_query_parameter("src");
    //console.log( serviceurl)
    var uri = "my test.asp?name=ståle&car=saab";
    var res = encodeURI(uri);
    //data = find_query_parameter('data')
    //if(data !=null){
    //    console.log(decodeURIComponent(data))
    //    decode = decodeURI(decodeURIComponent(data))
    //    json_data = JSON.parse(decode)
    //    console.log(json)
    //}
    serviceurl = 'test'
    data_url = base_url + 'hydroshare-resource-creator/chart_data/'
    $.ajax({
        type:"POST",
        dataType: 'json',
        data:{'serviceurl':serviceurl},
        url: data_url,
        success: function (json) {
            json1 = null

            if (json.error !=''){
                error_report(json.error)
                finishloading()
            }
            else {
                //json1 = json
                //json_data = find_query_parameter('data')
                //if(json_data != null)
                //{
                //
                //    decode = decodeURI(decodeURIComponent(json_data))
                //    console.log('aaa')
                //    json_data = JSON.parse(decode)
                //    console.log('aaa')
                //    json1 = json_data
                //}
                console.log(json)
                console.log(json.data)
                //console.log(json.data.timeSeriesLayerResource["REFTS"])
                decode = decodeURI(decodeURIComponent(json.data))
                console.log(decode)
                console.log(JSON.parse(json.data))
                series_details = JSON.parse(json.data)
                var title=series_details.title
                var abstract= series_details.abstract
                var keywords= series_details.keyWords
                series_details = series_details.REFTS
                total_number = series_details.length

                for (val in series_details) {
                    entry = series_details[val]
                    console.log(series_details[val])

                    console.log(entry.beginDate)
                    console.log(entry.location)
                    console.log(entry['location'])


                    series_counter = series_counter + 1
                    var site_name = entry.site
                    var variable_name = entry.variable
                    var RefType = entry.refType
                    var ServiceType = entry.serviceType
                    var URL = entry.url
                    var ReturnType = entry.returnType
                    var Lat = entry.location.latitude
                    var Lon = entry.location.longitude
                    var begindate = entry.beginDate
                    var enddate = entry.endDate
                    var variable = entry.variable
                    var var_code = entry.variableCode
                    var site_code = entry.siteCode
                    var network = entry.networkName


                    //var boxplot_count = number

                    if (site_name == null) {
                        site_name = "N/A"
                    }
                    if (variable_name == null) {
                        variable_name = "N/A"
                    }
                    if (RefType == null) {
                        RefType = "N/A"
                    }
                    if (ServiceType == null) {
                        ServiceType = "N/A"
                    }
                    if (URL == null) {
                        URL = "N/A"
                    }
                    if (ReturnType == null) {
                        ReturnType = "N/A"
                    }
                    if (Lat == null) {
                        Lat = "N/A"
                    }
                    if (Lon == null) {
                        Lon = "N/A"
                    }


                    var legend = "<div style='text-align:center' '><input class = 'checkbox' id =" + number + " data1-resid =" + number
                        + " type='checkbox' onClick ='myFunc(this.id,this.name);'checked = 'checked'>" + "</div>"
                    console.log(title)
                    console.log(keywords)
                    $('#res-title').val(title)
                    $('#res-abstract').text(abstract)
                    $('#res-keywords').val(keywords)
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
                        endDate: enddate,
                        variable: variable,
                        var_code: var_code,
                        site_code: site_code,
                        network: network

                    }
                    console.log(dataset)
                    var table = $('#data_table').DataTable();
                    table.row.add(dataset).draw();
                    number = number + 1
                }

                //finished_resource()
                if (number == total_number) {
                    finishloading()
                }

            }

        },
        error: function(){
            error_report("Error loading data from data client")
            console.log("error")
        }
    })

    console.log(series_counter)



}
function finished_resource(callback){

    console.log("done")

    current_url = location.href;
    index = current_url.indexOf("hydroshare-resource-creator");
    base_url = current_url.substring(0, index);
    var src = find_query_parameter("src");
    data_url = base_url + 'hydroshare-resource-creator/write_file';
    $.ajax({
        url: data_url,
        success: function (json) {
        },
        error:function(){
            console.log("error 2")
        }
    })
}
var data = [];
$(document).ready(function () {
    $('#stat_div').hide();
    //finishloading()
    console.log("ready")
    //initializes table
    var table = $('#data_table').DataTable({
        "createdRow": function (row, data2, dataIndex) {

            //console.log({"data": "quality"})
            var table = $('#data_table').DataTable()
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
            {"data": "site"},
            {"data": "RefType"},
            {"data": "ServiceType"},
            {"data": "URL"},
            {"data": "ReturnType"},
            {"data": "Lat"},
            {"data": "Lon"},
            {"data": "beginDate"},
            {"data": "endDate"},
            {"data": "variable"},
            {"data": "var_code"},
            {"data": "site_code"},
            {"data": "network"},
            //{"data":"download"}
        ],
        "order": [[1, 'asc']]
    });

    series_total  = 0
    //var res_ids = find_query_parameter("res_id");
    var res_ids=$('#cuahsi_ids').text()
    res_ids =trim_input(res_ids)
    var serviceurl=$('#serviceurl').text()
    serviceurl = trim_input(serviceurl)

    //if (res_ids != null)
    //{
    //    res_ids = res_ids.split(",");
    //}

    //var source = $('#source').text()
    //if (source == "['cuahsi']"){
    //    source='cuahsi'
    //}
    //for ( var r in res_ids)
    //{
    //    series_total  = series_total  +1
    //}
    //for  (var res_id in res_ids)
    //{
    create_resource()
    //}


})
function finishloading(callback) {
    $(window).resize()
    $('#stat_div').show();
    $(window).resize();
    $('#loading').hide();
    $('#multiple_units').show();
}
//$('#btn_show_modal_create').click(function() {
//    var popupDiv = $('#create_resource');
//    popupDiv.modal('show')
//});

$('#btn_create_ts_layer').click(function() {
    //var popupDiv = $('#create_resource');
    //popupDiv.modal('hide')
    //login = $('#login1').text()
    //console.log(login)
    data_url = base_url + 'hydroshare-resource-creator/login-test';
    $.ajax({
        url: data_url,
        async: false,
        success: function (json) {
            login = json.Login

            console.log(login)
            if (login == 'False'){
                console.log("not logged in")
                window.open("/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                //$('#login1').text('True')
            }
            else{
                //gets the id of each series that has been checked
                var checked_ids = $('input[data1-resid]:checkbox:checked').map(function() {
                    return this.getAttribute("data1-resid");
                }).get();
                console.log(checked_ids)
                //gets the type of time series reference the user wants to create
                var series_type = $('input[name]:checkbox:checked').map(function() {
                    return this.getAttribute("name");
                }).get();
                console.log($('#res-title').val())
                if($('#res-title').val()==''){
                    alert("Resource Title field cannot be blank")

                }
                else {
                    $('#stat_div').hide();
                    $('#loading').show();
                    console.log(series_type)
                    var csrf_token = getCookie('csrftoken');
                    data_url = base_url + 'hydroshare-resource-creator/create_layer/cuahsi/'
                    $.ajax({
                        type: "POST",
                        headers: {'X-CSRFToken': csrf_token},
                        dataType: 'json',
                        data: {
                            'checked_ids': JSON.stringify(checked_ids),
                            'resource_type': JSON.stringify(series_type),
                            'resTitle': $('#res-title').val(),
                            'resAbstract': $('#res-abstract').val(),
                            'resKeywords': $('#res-keywords').val()
                        },
                        url: data_url,
                        success: function (json) {
                            console.log(json.Request)
                            finishloading()
                            if(json.Request =='error'){alert("There was an issue creating your resource")}


                            else
                            {
                                alert("Resource created sucessfully")
                                //$('#btn_view_resource').attr('name') =json.Request
                                $('#div_view_resource').show()
                            }
                        },
                        error:function(json){

                        }
                    })
                }}
        },
        error:function(){
            console.log("error 2")
        }})

    //unit1 = document.querySelector('input[name = "units"]:not(:checked)').value;
});
function view_resource(hydroshare_id){
    window.open('https://www.hydroshare.org/resource/'+hydroshare_id+'/')
}
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function trim_input(string){
    string = string.replace(']','')
    string = string.replace('[','')
    string = string.replace(/'/g,'')
    string = string.replace(/"/g,'')
    string = string.replace(/ /g,'')
    //string = string.replace('[','')
    string =string.split(',')
    return string
}
function error_report(error){
    console.log(error)
}

function dataToUrl() {

    verb = 'post'
    var url= 'http://127.0.0.1:8000/apps/hydroshare-resource-creator/';
    var data = { "timeSeriesLayerResource": {} };
    target = '_blank'

    data.timeSeriesLayerResource = {"fileVersion": 1.0,
        "title": "HydroClient-" ,
        "abstract": "Retrieved timeseries...",
        "symbol": "http://data.cuahsi.org/content/images/cuahsi_logo_small.png",
        "keyWords": ["Time Series", "CUAHSI"],
        "REFTS": ["site:test","url:www"]};
    //Create form for data submission...
    var form = document.createElement("form");
    form.action = url;
    form.method = verb;
    form.target = target || "_self";
    if ('undefined' !== data && null !== data) {
        for (var key in data) {
            var input = document.createElement("textarea");
            input.name = key;
            input.value = typeof data[key] === "object" ? JSON.stringify(data[key]) : data[key];
            form.appendChild(input);
        }
    }

    form.style.display = 'none';
    document.body.appendChild(form);

    //Submit form via jQuery to capture submit event...
    //form.submit();
    var jqForm = $(form);
    jqForm.submit(function(event) {
        jqForm.remove();
    });

    jqForm.submit();

    //Remove form once submitted...
    //Source: http://stackoverflow.com/questions/12853123/remove-form-element-from-document-in-javascript
    //form.parentNode.removeChild(form);
}
