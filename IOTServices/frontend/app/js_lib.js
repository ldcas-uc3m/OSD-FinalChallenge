/*
 * Javascript file to implement client side usability for 
 * Operating Systems Desing exercises.
 */
var backend_api_address = "34.159.252.9"
var backend_api_port = "5001"

var backend_url = "http://" + backend_api_address + ":" + backend_api_port + "/device_state"

var get_current_sensor_data = function() {
    // get room data from backend
    console.log("Requesting data from backend")
    $.getJSON(backend_url, function(data) {
        $.each(data, function(index, item) {
          $("#"+item.room).data(item.type, item.value)
        });
        console.log(data)
    });
}

var draw_rooms = function(){
    // use TDs to draw the room objects on the website
    $("#rooms").empty()
    var room_index = 1;
    for (var i = 0; i < 8; i++) {
        $("#rooms").append("<tr id='floor"+i+"'></tr>")
        for (var j = 0; j < 5; j++) {
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
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"air-mode",
            "value":value
        }),
        contentType: 'application/json'
    });
    console.log("Posting command")
    console.log(JSON.stringify({ "room":$("#room_id").text(), "type":"air-mode", "value":value}))
})


$("#inner_light_mode").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner-light-mode",
            "value":value
        }),
        contentType: 'application/json'
    });
})

$("#inner_light_level").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"inner-light-mode",
            "value":value
        }),
        contentType: 'application/json'
    });
})

$("#exterior_light_mode").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"exterior_light_mode",
            "value":value
        }),
        contentType: 'application/json'
    });
})

$("#exterior_light_level").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"exterior_light_level",
            "value":value
        }),
        contentType: 'application/json'
    });
})

$("#blinds").change(function(){
    var value = $(this).val()
    $.ajax({
        type: "POST",
        url: backend_url,
        data: JSON.stringify({
            "room":$("#room_id").text(),
            "type":"blinds",
            "value":value
        }),
        contentType: 'application/json'
    });
})

$("#rooms").on("click", "td", function() {
    // unpackage data from backend
    $("#room_id").text($( this ).attr("id") || "");
    $("#temperature_value").text($( this ).data("temperature") || "0");
    $("#humidity_value").text($( this ).data("humidity") || "0");
    $("#presence_value").text($( this ).data("presence") || "0");
    $("#air_value").text($( this ).data("air-level") || "0");
    $("#air_mode").val($( this ).data("air-mode"));
    $("#inner_light_mode").val($( this ).data("inner_light_mode"));
    $("#inner_light_level").val($( this ).data("inner_light_level"));
    $("#exterior_light_mode").val($( this ).data("exterior_light_mode"));
    $("#exterior_light_level").val($( this ).data("exterior_light_level"));
    $("#blinds").val($( this ).data("blinds"));
});

draw_rooms()
setInterval(get_current_sensor_data, 3000)