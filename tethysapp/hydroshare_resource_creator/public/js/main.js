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
            if(series_counter == series_total)
            {
                finished_resource()

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

$(document).ready(function () {
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