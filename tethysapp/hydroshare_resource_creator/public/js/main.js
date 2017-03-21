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
    console.log("create_resource")

    current_url = location.href;
    index = current_url.indexOf("hydroshare-resource-creator");
    base_url = current_url.substring(0, index);
    //var src = find_query_parameter("src");
    //console.log( serviceurl)
    var uri = "my test.asp?name=ståle&car=saab";
    var res = encodeURI(uri);
    var src = find_query_parameter("src");
    if (src=='hydroshare'){
        res_id = find_query_parameter("res_id");
        $('#')
    }
    else{
        res_id ='None'
    }
    //data = find_query_parameter('data')
    //if(data !=null){
    //    console.log(decodeURIComponent(data))
    //    decode = decodeURI(decodeURIComponent(data))
    //    json_data = JSON.parse(decode)
    //    console.log(json)
    //}
    serviceurl = 'test'
    data_url = base_url + 'hydroshare-resource-creator/chart_data/'+res_id+'/'
    $.ajax({
        type:"POST",
        dataType: 'json',
        data:{'serviceurl':serviceurl},
        url: data_url,
        success: function (json) {
            json1 = null
            console.log(json)
            if (json.error !=''){

                error_report(json.error)

                console.log('error')
            }
            else {
                console.log(json.public)
                //checks checkbox 'public' if resource is already public
                if (json.public ==true){document.getElementById("chk_public").checked = true;}


                console.log('No error')
                decode = decodeURI(decodeURIComponent(json.data))

                //series_details = JSON.parse(json.data)
                series_details = json.data
                //console.log(series_details)
                var title=series_details.title
                var abstract= series_details.abstract
                var keywords= series_details.keyWords

                var date_small=new Date()
                var date_large=new Date('1600-01-01')
                var date_now = new Date()
                var site_list =[]
                var var_list=[]
                series_details = series_details.REFTS
                total_number = series_details.length
                console.log(total_number)

                for (val in series_details) {
                    entry = series_details[val]
                    series_counter = series_counter + 1
                    var site_name = entry.site
                    if(site_list.indexOf(site_name)==-1){
                        site_list.push(site_name)
                    }

                    var variable_name = entry.variable
                    var RefType = entry.refType
                    var ServiceType = entry.serviceType
                    var URL = entry.url
                    var ReturnType = entry.returnType
                    var Lat = entry.location.latitude
                    var Lon = entry.location.longitude


                    var begindate = entry.beginDate
                    var enddate = entry.endDate

                    var date_begindate = new Date(begindate)
                    var date_enddate = new Date(enddate)


                    if(date_small > date_begindate){
                        date_small = date_begindate
                    }
                    if(date_large < date_enddate){
                        date_large = date_enddate
                    }

                    var variable = entry.variable
                    if(var_list.indexOf(variable)==-1){
                        var_list.push(variable)
                    }
                    var var_code = entry.variableCode
                    var site_code = entry.siteCode
                    var network = entry.networkName


                //if (total_number >1)
                //{title = "Data from various sites coll"
                //abstract = "Data created from the CUAHSI HIS"
                //}
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
                        + " type='checkbox' checked = 'checked'>" + "</div>"

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

                    }
                    var table = $('#data_table').DataTable();
                    table.row.add(dataset).draw();
                    number = number + 1
                }
                if (number == total_number) {
                    if(src =='hydroshare')    {}
                    else {
                        console.log("formatting abstract")
                        if (site_list.length > 1) {
                        last = site_list[site_list.length - 1]
                        site_list.pop()
                        site_list.push('and ' + last)
                        site_list = site_list.join(', ')
                        }

                        title ="Time series layer resource created on "+date_now
                        abstract = var_list +" data collected from "+date_small.toISOString().substring(0, 10) +" to "+ date_large.toISOString().substring(0, 10)+
                                " created on "+ date_now+" from the following site(s): " + site_list+". Data created by CUAHSI HydroClient: " +
                                "http://data.cuahsi.org/#."
                    }
                    $('#res-title').val(title)
                    $('#res-abstract').text(abstract)
                    $('#res-keywords').val(keywords)
                    finishloading()
                }
            }
        },
        error: function(){
            error_report("Error loading data from data client")
            console.log("error")
        }
    })
}

var data = [];
$(document).ready(function () {
    $('#stat_div').hide();
    $('#btn_update_ts_layer').hide();

    //finishloading()
    console.log("ready")
    //initializes table
    var table = $('#data_table').DataTable({
        "scrollX": true,
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
            //{"data": "endDate"},
            {"data": "variable"},
            {"data": "var_code"},
            {"data": "site_code"},
            {"data": "network"},
            //{"data":"download"}
        ],
        "order": [[1, 'asc']]
    });

    series_total  = 0
    var res_ids=$('#cuahsi_ids').text()
    res_ids =trim_input(res_ids)
    var serviceurl=$('#serviceurl').text()
    serviceurl = trim_input(serviceurl)
    document.title = 'Create HydroShare Resource';
    create_resource()
})
function finishloading(callback) {
    $(window).resize()
    $('#stat_div').show();
    $(window).resize();
    console.log('hide')
    $('#loading').hide();
    $('#multiple_units').show();
    var src = find_query_parameter("src");
    if(src == 'hydroshare')
    {
        $('#btn_update_ts_layer').show();
    }
}
//$('#btn_show_modal_create').click(function() {
//    var popupDiv = $('#create_resource');
//    popupDiv.modal('show')
//});
function create_update(fun_type,res_type){
    $('#loading').show();
    console.log(fun_type)
    console.log(res_type)
    res_id = find_query_parameter('res_id')
    console.log(res_id)
    console.log(res_type.value)

    //var popupDiv = $('#create_resource');
    //popupDiv.modal('hide')
    //login = $('#login1').text()
    data_url = base_url + 'hydroshare-resource-creator/login-test';
    $.ajax({
        url: data_url,
        async: false,
        success: function (json) {
            login = json.Login
            if (login == 'False'){

                window.open("/oauth2/login/hydroshare/?next=/apps/hydroshare-resource-creator/login-callback/", 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                //$('#login1').text('True')
            }
            else{
                //gets the id of each series that has been checked
                var checked_ids = $('input[data1-resid]:checkbox:checked').map(function() {
                    return this.getAttribute("data1-resid");
                }).get();

                //gets the type of time series reference the user wants to create
                var series_type = $('input[name]:checkbox:checked').map(function() {
                    return this.getAttribute("name");
                }).get();
                if($("#chk_public").is(':checked'))
                    res_access = 'public'  // checked
                else
                    res_access = 'private'  // unchecked
                console.log(res_access)
                //console.log(checked_ids)
                if($('#res-title').val()==''){
                    alert("Resource Title field cannot be blank")
                }
                else {

                    $('#stat_div').hide();
                    $('#loading').show();
                    var csrf_token = getCookie('csrftoken');
                    data_url = base_url + 'hydroshare-resource-creator/create_layer/'+fun_type+'/'+res_id+'/'+res_type+'/'
                    $.ajax({
                        type: "POST",
                        headers: {'X-CSRFToken': csrf_token},
                        dataType: 'json',
                        data: {
                            'checked_ids': JSON.stringify(checked_ids),
                            'resource_type': JSON.stringify(series_type),
                            'resTitle': $('#res-title').val(),
                            'resAbstract': $('#res-abstract').val(),
                            'resKeywords': $('#res-keywords').val(),
                            'resAccess': res_access
                        },
                        url: data_url,
                        success: function (json) {
                            console.log(json)

                            if(json.error !=''){alert(json.error)}
                            else
                            {
                                //create_resource()
                                if (fun_type=='update')//reloads page so that resource is reloaded
                                {
                                    //wait(50000);
                                    current_url = location.href;
                                    index = current_url.indexOf("hydroshare-resource-creator");
                                    base_url = current_url.substring(0, index);
                                    //window.open(base_url +"hydroshare-resource-creator/?src=hydroshare&res_id="+res_id, 'windowName', 'width=1000, height=700, left=24, top=24, scrollbars, resizable');
                                    window.location = base_url +'hydroshare-resource-creator/?src=hydroshare&res_id='+res_id
                                }
                                else{$('#modal_title').append("Resource Created Successfully") }
                                resource = json.Request
                                $('#welcome-info').append('<a href="https://www.hydroshare.org/resource/'+resource+'"target="_blank">Click here to view.</a>')

                                $('#btn_create_ts_layer').hide()
                                $('#public_hydro').hide()
                                //$('#btn_view_resource').html("")
                                $('#div_view_resource').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="'+json.Request+'"onclick="view_resource(this.name)">View Resource</button>')
                                //$('#div_view_resource2').append('<button id ="btn_view_resource" type="button" class="btn btn-success" name ="'+json.Request+'"onclick="view_resource(this.name)">View Resource</button>')
                                $('#resource_dialog').modal('show');
                            }
                            finishloading()
                        },
                        error:function(json){
                        }
                    })
                }}
        },
        error:function(){
        }})

    //unit1 = document.querySelector('input[name = "units"]:not(:checked)').value;
};

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
    $(window).resize()
    $('#loading').hide()
    $('#error-message').append(error)
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
function wait(ms){
   var start = new Date().getTime();
   var end = start;
   while(end < start + ms) {
     end = new Date().getTime();
  }
}