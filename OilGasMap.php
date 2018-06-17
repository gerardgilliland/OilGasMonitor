<?php
// contract.php
// header("Cache-Control: no-cache, must-revalidate");
// header("Pragma: no-cache");
// header("Expires: Mon,26 Jul 1997 05:00:00 GMT");
	include "./common_OilGasMonitor.inc";
	date_default_timezone_set("America/Denver");
	
?>

<!DOCTYPE html >
	<head>
		<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
		<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
		<title>Gas and Oil Map</title>
		<style>
		/* Always set the map height explicitly to define the size of the div
		* element that contains the map. */
		#map {
			height: 100%;
		}
		/* Optional: Makes the sample page fill the window. */
		html, body {
			height: 100%;
			margin: 0;
			padding: 0;
		}
		</style>
<?php	
	global $link_id;
	$link_id = db_connect();
	UpdateMap();
	
	Function updateMap() {		
		global $link_id;
		$qry = "SELECT Max(Loc) as maxLoc FROM tblLocation";
		$rs = mysqli_query($link_id, $qry);
		$k = mysqli_num_rows($rs); // it will be one row
		mysqli_data_seek($rs, $k);
		$row = mysqli_fetch_row($rs); 
		$maxLoc = $row[0];
		//echo "maxLoc=$maxLoc<br>";
		$XmlName = "OilGasMarkers.xml";
		$fpx = fopen($XmlName, "w"); // For Output 
		$nl = chr(13) . chr(10);		
		fwrite($fpx, "<?xml version=\"1.0\" ?>" . $nl);
		fwrite($fpx, "<markers>" . $nl);		
		for ($id = 1; $id <= $maxLoc; $id++) {			
			$qry = "SELECT * FROM tblLocation WHERE Loc = $id";
			$rs = mysqli_query($link_id, $qry);
			$k = mysqli_num_rows($rs);
			//echo "id=$id k=$k <br>";
			if ($k == 1) {
				mysqli_data_seek($rs, $k);
				$row = mysqli_fetch_row($rs); 
				$lat = $row[1];
				$lng = $row[2];
				//echo "id=$id lat=$lat lng=$lng <br>"; 
				$qry = "SELECT MAX(Date) FROM tblMonitor WHERE Loc = $id";
				$rs = mysqli_query($link_id, $qry);
				$i = mysqli_num_rows($rs);
				if ($i == 1) {  // should be one only row
					mysqli_data_seek($rs, $i);
					$row = mysqli_fetch_row($rs); 
					$date = $row[0];
					$qry = "SELECT * FROM tblMonitor WHERE Loc = $id and Date = '$date'";
					$rs = mysqli_query($link_id, $qry);
					$j = mysqli_num_rows($rs);
					if ($j == 1) {
						mysqli_data_seek($rs, $j);
						$row = mysqli_fetch_row($rs); 
						// tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq)
						$loc = $row[0];
						$date = $row[1];
						fwrite($fpx, "<marker id=\"$row[0]\"" );
						fwrite($fpx, " lat=\"$lat\"");
						fwrite($fpx, " lng=\"$lng\"");
						fwrite($fpx, " date=\"$row[1]\"");
						fwrite($fpx, " pm1=\"$row[2]\"");
						fwrite($fpx, " pm25=\"$row[3]\"");
						fwrite($fpx, " pm10=\"$row[4]\"");
						fwrite($fpx, " temp=\"$row[5]\""); 						
						fwrite($fpx, " press=\"$row[6]\""); 						
						fwrite($fpx, " rh=\"$row[7]\""); 
						fwrite($fpx, " qual=\"$row[9]\"");
						fwrite($fpx, " voc=\"$row[10]\"");						
						//fwrite($fpx, " ch4=\"$row[11]\""); 
						fwrite($fpx, " db=\"$row[12]\"");
						fwrite($fpx, " hz=\"$row[13]\"");
						$type = "I";
						if ($row[10] > 10 || $row[11] > 200 || $row[9] < 80) {
							$type = "W";
						} elseif ($row[10] > 100 || $row[11] > 500 || $row[9] < 70) {
							$type = "A";
						}
						fwrite($fpx, " type=\"$type\" />" . $nl);
					}
				}	
			}		
		}		
		fwrite($fpx, "</markers>" . $nl);
		//echo "write markers<br>";
	}

?>
	<script>
		<!-- setInterval(function(){ alert("Hello"); }, 3000); -->
		<!-- UpdateMap(); -->
	</script>
	
	</head>

	<body>
		<link rel="stylesheet" type="text/css" href="msStyle.css" />
		<div id="map"></div>

		<script>
		

		var customLabel = {
			W: {
				label: 'W'
			},
			A: {
				label: 'A'
			},
			I: {
				label: 'I'
			}  
		};
		
	
		function initMap() {
			var map = new google.maps.Map(
				document.getElementById('map'), {
					center: new google.maps.LatLng(39.985860,-105.020848),
					zoom: 12
				}
			);
			var infoWindow = new google.maps.InfoWindow;

			// Change this depending on the name of your PHP or XML file
			downloadUrl('https://www.modelsw.com/OilGasMonitor/OilGasMarkers.xml', function(data) {
				var xml = data.responseXML;
				var markers = xml.documentElement.getElementsByTagName('marker');
				Array.prototype.forEach.call(markers, function(markerElem) {
					var id = markerElem.getAttribute('id');
					var dat = markerElem.getAttribute('date');
					var qual = markerElem.getAttribute('qual');
					var voc = markerElem.getAttribute('voc');
					//var ch4 = markerElem.getAttribute('ch4');
					var temp = markerElem.getAttribute('temp');
					var press = markerElem.getAttribute('press');
					var rh = markerElem.getAttribute('rh');
					var db = markerElem.getAttribute('db');
					var hz = markerElem.getAttribute('hz');
					var pm1 = markerElem.getAttribute('pm1');
					var pm25 = markerElem.getAttribute('pm25');
					var pm10 = markerElem.getAttribute('pm10');
					var type = markerElem.getAttribute('type');
					var point = new google.maps.LatLng(
						parseFloat(markerElem.getAttribute('lat')),
						parseFloat(markerElem.getAttribute('lng')));

					var infowincontent = document.createElement('div');
		
				    var btn = document.createElement('button');
					var btntxt = document.createTextNode('Plot');
					btn.appendChild(btntxt);
					btn.onclick = function() {
						plotid(id);
					};
					infowincontent.appendChild(btn);
					infowincontent.appendChild(document.createElement('br'));
					
					var text = document.createElement('text');
					text.textContent = " id = " + id + ", date = " + dat;			
					infowincontent.appendChild(text);
					infowincontent.appendChild(document.createElement('br'));
					
					text = document.createElement('text');
					text.textContent = " qual = " + qual + ", voc = " + voc;
					infowincontent.appendChild(text);
					infowincontent.appendChild(document.createElement('br'));
					
					text = document.createElement('text');
					text.textContent = " temp = " + temp + ", Pa = " + press + ", rh = " + rh;
					infowincontent.appendChild(text);
					infowincontent.appendChild(document.createElement('br'));	
					
					text = document.createElement('text');
					text.textContent = " sound db = " + db + " @hz = " + hz;
					infowincontent.appendChild(text);
					infowincontent.appendChild(document.createElement('br'));	
					
					text = document.createElement('text');
					text.textContent = " pm<1.0=" + pm1 + ", pm<2.5=" + pm25 + ", pm<10.0=" + pm10;
					infowincontent.appendChild(text);
					infowincontent.appendChild(document.createElement('br'));		
					
					var icon = customLabel[type] || {};
					var marker = new google.maps.Marker({
						map: map,
						position: point,
						label: icon.label
					});
					marker.addListener('click', function() {
						infoWindow.setContent(infowincontent);
						infoWindow.open(map, marker);
					});
				});
			});
        }

		function plotid(id) {
			<!-- alert('plot id:' + id); -->
			<!-- window.open("<a href='Plotid.html#'<?php id ?> target='_blank'></a>") -->
			<!-- window.open("https://www.modelsw.com/OilGasMonitor/PlotId.html#1" target="_blank") -->
			window.location.href = "https://www.modelsw.com/OilGasMonitor/PlotId.php?id="+id;
			
		}

		function downloadUrl(url, callback) {
			var request = window.ActiveXObject ?
				new ActiveXObject('Microsoft.XMLHTTP') :
				new XMLHttpRequest;

			request.onreadystatechange = function() {
				if (request.readyState == 4) {
					request.onreadystatechange = doNothing;
					callback(request, request.status);
				}
			};

			request.open('GET', url, true);
			request.send(null);
		}

		function doNothing() {}
		</script>
		<script async defer
			src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD_MCmPQPSTE0eNY8zXEGzkmziLFQx_IMM&callback=initMap">
		</script>

<?php
    include "./footer.inc";
?>
	</body>
</html>