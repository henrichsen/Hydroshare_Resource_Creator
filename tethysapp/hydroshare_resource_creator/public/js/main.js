function find_query_parameter(name) {
   url = location.href;
   //name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
   var regexS = "[\\?&]"+name+"=([^&#]*)";
   var regex = new RegExp( regexS );
   var results = regex.exec( url );
   return results == null ? null : results[1];
 }
 console.log("hello")
 current_url = location.href;
 index = current_url.indexOf("hydroshare-resource-creator");
 base_url = current_url.substring(0, index);
 var src = find_query_parameter("src");
 var res_id = find_query_parameter("res_id");
 data_url = base_url + 'hydroshare-resource-creator/chart_data/' + res_id + '/'+src+'/';
console.log("hello1")