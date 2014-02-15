var properties = {};
var map;
var infoWindow;
var circles = [];

function getRGBForPrice(price) {
	var r = 0;
	var g = 0;
	var b = 0;
	if (price >= 250000) {
		r = 255;
		if (price < 350000) {
			g = 255 - 255*((price - 250000) / 100000);
		}
	} else if (price >= 150000) {
		g = 255;
		r = 255 * ((price - 150000) / 100000);
	} else {
		b = 255;
		if (price > 50000) {
			g = 255 * ((price - 50000) / 100000);
		} else {
			g = 255;
		}
	}
	return [Math.floor(r), Math.floor(g), Math.floor(b)];
}

$(document).ready(function() {
	var myOptions = {
	  center: new google.maps.LatLng(43.286, -107.633),
	  zoom: 7,
	  mapTypeId: google.maps.MapTypeId.HYBRID
	};
	map = new google.maps.Map(document.getElementById("map_canvas"),
	  myOptions);
	infoWindow = new google.maps.InfoWindow();
	google.maps.event.addListener(map, 'zoom_changed', function() {
		var newRadius = Math.pow((20 - map.getZoom()), 3);
		$(circles).each(function(index, circle) {
			circle.setRadius(newRadius);
		});
	});
	$.ajax({
		url: "http://zebfross.com/php/heatmap_api.php",
		success: function(responseText, textStatus) {
			properties = JSON.parse(responseText);		
			$(properties).each(function(index, property) {
				var latlng = new google.maps.LatLng(property["latitude"], property["longitude"]);
				var title = "$" + property["price"] + " - ";
				title += property["address"];
				var rgb = getRGBForPrice(property["price"]);
				var color = "rgb(" + rgb[0] + ", " + rgb[1] + ", " + rgb[2] + ")";
				var circleOps = {
					strokeColor: color,
					fillColor: color,
					map: map,
					center: latlng,
					radius: 6000,
					title: title
				};
				var circle  = new google.maps.Circle(circleOps);
				circles.push(circle);
				google.maps.event.addListener(circle, 'click', function(event) {
					var msg = "<b>Price: </b>" + property["price"];
					msg += "<br />";
					msg += "<b>Address: </b>" + property["address"];
					msg += "<br />";
					msg += "<b>Link: </b> <a href='" + property["url"];
					msg += "'>" + property["url"] + "</a>";
					infoWindow.setContent(msg);
					infoWindow.setPosition(circle.center);
					infoWindow.open(map);
				});
			});
		},
		error: function(jqXHR, textStatus, errorThrown) {
			console.log(jqXHR);
			console.log(textStatus);
			console.log(errorThrown);
		}
	});
});
