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
function create_resource(res_id,series_total){
    console.log(res_id)
    current_url = location.href;
    index = current_url.indexOf("hydroshare-resource-creator");
    base_url = current_url.substring(0, index);
    var src = find_query_parameter("src");

    data_url = base_url + 'hydroshare-resource-creator/chart_data/' + res_id + '/'+src+'/';
    $.ajax({
        url: data_url,
        success: function (json) {
            console.log("ajax")
            console.log(series_counter)
            series_counter = series_counter +1
            var site_name = json.site_name
            var variable_name = json.variable_name
            var RefType = json.RefType
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
    var res_ids = find_query_parameter("res_id");

    if (res_ids != null)
    {
        res_ids = res_ids.split(",");
    }


    for ( var r in res_ids)
    {
        series_total  = series_total  +1
    }
    for  (var res_id in res_ids)
    {
        create_resource(res_ids[res_id],series_total)
    }


})
function finishloading(callback) {
    $(window).resize()
    $('#stat_div').show();
    $(window).resize();
    $('#loading').hide();
    $('#multiple_units').show();
}
 $('#btn_show_modal_create').click(function() {
   var popupDiv = $('#create_resource');
   popupDiv.modal('show')
});
$('#btn_create_ts_layer').click(function() {
    var popupDiv = $('#create_resource');
    popupDiv.modal('hide')
    $('#stat_div').hide();
    $('#loading').show();
    $('input[type=checkbox]').each(function () {
    //var sThisVal = (this.checked ? $(this).val() : "");
    });
    //console.log(sThisVal)
     var checked_ids = $('input[data1-resid]:checkbox:checked').map(function() {
            return this.getAttribute("data1-resid");
        }).get();
    console.log(checked_ids)
    var csrf_token = getCookie('csrftoken');
    data_url = base_url + 'hydroshare-resource-creator/create_layer/testtt'+ '/'
    $.ajax({
        type:"POST",
        headers:{'X-CSRFToken':csrf_token},
        dataType: 'json',
        data:{'checked_ids':JSON.stringify(checked_ids)},
        url: data_url,
        success: function (json) {}})

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