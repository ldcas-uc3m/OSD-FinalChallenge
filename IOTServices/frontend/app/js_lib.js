/*
 * Javascript file to implement client side usability for 
 * Operating Systems Desing exercises.
 */
var backend_api_address = "34.159.103.125"

var get_current_sensor_data = function() {
    console.log("Requesting data from backend")
    $.getJSON("http://" + backend_api_address + ":5001/device_state", function(data) {
        $.each(data, function(index, item) {
          $("#"+item.room).data(item.type, item.value)
      });
    });
}

var draw_rooms = function(){
    $("#rooms").empty()
    var room_index = 1;
    for (var i = 0; i < 7; i++) {
        $("#rooms").append("<tr id='floor"+i+"'></tr>")
        for (var j = 0; j < 10; j++) {
            $("#floor"+i).append("\
                <td \
                data-bs-toggle='modal' \
                data-bs-target='#room_modal' \
                class='room_cell'\
                id='Room"+room_index+"'\
                > \
                Room "+room_index+"\
                </td>"
                )
            room_index++
        }
    }
}

$("#air_mode").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"air-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})


$("#inner_light_mode").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner-light-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#exterior_light_mode").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner-light-mode",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#exterior_light_level").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"exterior_light_level",
            "value":value,
        }),
        contentType: 'application/json'
    });
})

$("#inner_light_level").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner_light_level",
            "value":value,
        }),
        contentType: 'application/json'
    });
})


$("#my_presence_value").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: "http://" + backend_api_address + ":5001/device_state",
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner_light_level",
            "value":value,
        }),
        contentType: 'application/json'
    });
    if(value ="0"){
        value = "no"
    }else{
        vale ="Yes"
    }


})

$("#rooms").on("click", "td", function() {
    $("#room_id").text($( this ).attr("id") || "");
    $("#temperature_value").text($( this ).data("temperature") || "");
    $("#presence_value").text($( this ).data("presence") || "0");
    $("#air_conditioner_value").text($( this ).data("air-level") || "");
    $("#air_conditioner_mode").val($( this ).data("air-mode"));
});

draw_rooms()
setInterval(get_current_sensor_data,2000)
