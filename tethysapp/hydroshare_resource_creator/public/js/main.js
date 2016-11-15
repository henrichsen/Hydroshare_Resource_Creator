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
function create_resource(res_id,series_total,src,serviceurl){
    console.log(res_id)
    current_url = location.href;
    index = current_url.indexOf("hydroshare-resource-creator");
    base_url = current_url.substring(0, index);
    //var src = find_query_parameter("src");
    serviceurl = 'http://hydroportal.cuahsi.org/nwisdv/cuahsi_1_1.asmx?WSDL'
    serviceurl = encodeURI(serviceurl)
    console.log( serviceurl)
    var uri = "my test.asp?name=ståle&car=saab";
    var res = encodeURI(uri);
    console.log(res)


    data_url = base_url + 'hydroshare-resource-creator/chart_data/' + res_id + '/'+src +'/';
    $.ajax({
        type:"POST",
        dataType: 'json',
        data:{'serviceurl':serviceurl},
        url: data_url,
        success: function (json) {

            console.log("ajax")
            console.log(series_counter)
            console.log(json)

            series_counter = series_counter +1
            var site_name = json.site_name
            var variable_name = json.variable_name
            var RefType = json.ReturnType
            var ServiceType = json.ServiceType
            var URL = json.URL
            var ReturnType = json.ReturnType
            var Lat = json.Lat
            var Lon = json.Lon

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



            var legend = "<div style='text-align:center' '><input class = 'checkbox' id =" + number + " data1-resid =" + res_id
                + " type='checkbox' onClick ='myFunc(this.id,this.name);'checked = 'checked'>" + "</div>"

            var dataset = {
                legend: legend,
                RefType:RefType,
                ServiceType:ServiceType,
                URL:URL,
                ReturnType:ReturnType,
                Lat:Lat,
                Lon:Lon
            }
            console.log(dataset)
            var table = $('#data_table').DataTable();
            table.row.add(dataset).draw();


            number = number +1
            if(number == series_total)
            {
                //finished_resource()
                finishloading()
            }

        },
        error: function(){
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

            {"data": "RefType"},
            {"data": "ServiceType"},
            {"data": "URL"},
            {"data": "ReturnType"},
            {"data": "Lat"},
            {"data": "Lon"},
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

    var source = $('#source').text()
    if (source == "['cuahsi']"){
        source='cuahsi'
    }
    for ( var r in res_ids)
    {
        series_total  = series_total  +1
    }
    for  (var res_id in res_ids)
    {
        create_resource(res_ids[res_id],series_total,source,serviceurl[res_id])
    }


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
    $('#stat_div').hide();
    $('#loading').show();
    //gets the id of each series that has been checked
    var checked_ids = $('input[data1-resid]:checkbox:checked').map(function() {
        return this.getAttribute("data1-resid");
    }).get();
    console.log(checked_ids)
    //gets the type of time series reference the user wants to create
    var series_type = $('input[name]:checkbox:checked').map(function() {
        return this.getAttribute("name");
    }).get();


    console.log(series_type)
    var csrf_token = getCookie('csrftoken');
    data_url = base_url + 'hydroshare-resource-creator/create_layer/cuahsi/'
    $.ajax({
        type:"POST",
        headers:{'X-CSRFToken':csrf_token},
        dataType: 'json',
        data:{'checked_ids':JSON.stringify(checked_ids),
            'resource_type':JSON.stringify(series_type),
            'resTitle': $('#res-title').val(),
            'resAbstract': $('#res-abstract').val(),
            'resKeywords': $('#res-keywords').val()
        },
        url: data_url,
        success: function (json) {
            alert(json.Request)
            finishloading()
        }
    })

    //unit1 = document.querySelector('input[name = "units"]:not(:checked)').value;


});

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