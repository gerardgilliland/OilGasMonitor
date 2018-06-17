<?php
// contract.php
// header("Cache-Control: no-cache, must-revalidate");
// header("Pragma: no-cache");
// header("Expires: Mon,26 Jul 1997 05:00:00 GMT");
	include "./common_OilGasMonitor.inc";
	date_default_timezone_set("America/Denver");
	
?>

<html>
<head>
	
<!-- MODEL Software: PlotId -->

<!-- PlotId -->

	<link rel="stylesheet" type="text/css" href="msStyle.css" />
	<title>Plot Id</title>
<?php
	global $link_id;
	global $id;
	global $date, $startDate;
	global $MaxD, $MaxF, $MaxH, $MaxM, $MaxT, $MinT, $rangeT, $MaxV, $MaxY;
	$link_id = db_connect();


	$id = $_GET["id"];
	//echo "Id=$id<br>";
	// 24 hr * 60 min = 1440 records
	//tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq)
	$qry = "SELECT Max(Date) FROM tblMonitor WHERE Loc = $id";
	//echo "$qry<br>";
	$rs = mysqli_query($link_id, $qry);
	$i = mysqli_num_rows($rs);
	//echo "i=$i<br>";
	if ($i == 1) {  // should be one only row
		mysqli_data_seek($rs, $i);
		$row = mysqli_fetch_row($rs); 
		$date = $row[0]; 		
	}
	//echo "date:$date<br>";	
	$startDate = date("Y-m-d H:i:s", strtotime('-24 hours', strtotime($date)));
	//echo "startDate:$startDate<br>";
	
	Function PlotProfileMonitor($plt) {  
		global $Profile;
		global $StateCycle;
		global $startDate, $date;
		global $link_id;
		global $id;
		global $MaxD, $MaxF, $MaxH, $MaxM, $MaxT, $MinT, $rangeT, $MaxV, $MaxY;
		echo "Start Date: $startDate -- End Date: $date<br>";
       
		if ($plt == "voc") {
			//tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq)
			$qry = "SELECT Max(VOC), Max(Methane) FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			//echo "$qry<br>";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			//echo "i=$i<br>";
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$MaxQ = 100;
			$MaxV = $row[0];
			$MaxVI = pow(10,intval(strlen(strval($MaxV))-1));
			$MaxV= intval($MaxV/$MaxVI)*$MaxVI+$MaxVI;
			if ($MaxV < 500) {
				$MaxV = 500;
			}
			//$MaxM = $row[1];
			//$MaxMI = pow(10,intval(strlen(strval($MaxM))-1));
			//$MaxM = intval($MaxM/$MaxMI)*$MaxMI+$MaxMI;
			//echo "MaxM: $MaxM <br>";
			Header("Content-type: image/png");  // let the server know its not html
			$imageV = ImageCreate(721,256);
			$white = ImageColorAllocate($imageV,255,255,255);
			$green = ImageColorAllocate($imageV,0,255,0);
			$red = ImageColorAllocate($imageV,255,0,0); 
			$blue = ImageColorAllocate($imageV,0,0,255);
			$black = ImageColorAllocate($imageV,0,0,0);
			ImageLine($imageV,0,127,720,127,$black);     
			ImageLine($imageV,0,0,720,0,$black);  
			ImageLine($imageV,720,0,720,255,$black);  
			ImageLine($imageV,720,255,0,255,$black);  
			ImageLine($imageV,0,255,0,0,$black);  			
			$qry = "SELECT Quality, VOC FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			//echo "$qry<br>";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			//echo "cntr=$cntr<br>";
			
			$lineCntr = 2;
			$prev[$lineCntr];
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$prev[0] = $row[0];
			ImageLine($imageV,0,255-($prev[0]/$MaxQ)*255,0,255-($prev[0]/$MaxQ)*255,$blue);
			$prev[1] = $row[1];
			ImageLine($imageV,0,255-($prev[1]/$MaxV)*255,0,255-($prev[1]/$MaxV)*255,$red);
			//$prev[2] = $row[2];
			//ImageLine($imageV,0,255-($prev[2]/$MaxM)*255,0,255-($prev[2]/$MaxM)*255,$green);
			for ($i = 1; $i< $cntr; $i++) { 
				$j = $i/2;
				$k = $j+1;
				mysqli_data_seek($rs, $i);
				$row = mysqli_fetch_row($rs); 
				ImageLine($imageV,$j,255-($prev[0]/$MaxQ)*255,$k,255-($row[0]/$MaxQ)*255,$blue);
				ImageLine($imageV,$j,255-($prev[1]/$MaxV)*255,$k,255-($row[1]/$MaxV)*255,$red);
				//ImageLine($imageV,$j,255-($prev[2]/$MaxM)*255,$k,255-($row[2]/$MaxM)*255,$green);
				$prev[0] = $row[0];
				$prev[1] = $row[1];
				//$prev[2] = $row[2];
			}
			
			ImagePNG($imageV,"imageV.png");
			ImageDestroy($imageV);     
		}

		if ($plt == "trh") {
			//tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, Methane, SoundDb, Freq)
			$qry = "SELECT Max(Temp) FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$MaxT = $row[0];
			$MaxT += 10;
			$MaxT = intval($MaxT / 10);
			$MaxT = intval($MaxT * 10);
			$rangeT = 60;
			$MinT = $MaxT - $rangeT;
			//$MaxTI = pow(10,intval(strlen(strval($MaxT))-1)); 
			//$MaxT = intval($MaxT/$MaxTI)*$MaxTI+$MaxTI;  			
			$MaxH = 100;

			Header("Content-type: image/png");  // let the server know its not html
			$imageT = ImageCreate(721,256);
			$white = ImageColorAllocate($imageT,255,255,255);
			$red = ImageColorAllocate($imageT,255,0,0); 
			$blue = ImageColorAllocate($imageT,0,0,255);
			$black = ImageColorAllocate($imageT,0,0,0);
			ImageLine($imageT,0,128,720,128,$black);     
			ImageLine($imageT,0,0,720,0,$black);  
			ImageLine($imageT,720,0,720,255,$black);  
			ImageLine($imageT,720,255,0,255,$black);  
			ImageLine($imageT,0,255,0,0,$black);  			
			
			$qry = "SELECT Temp, RH FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			//echo "$qry<br>";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			//echo "cntr=$cntr<br>";
			
			$lineCntr = 2;
			$prev[$lineCntr];
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$prev[0] = $row[0];
			ImageLine($imageT,0,255-(($prev[0]-$MinT)/$rangeT)*255,0,255-(($prev[0]-$MinT)/$rangeT)*255,$red);
			$prev[1] = $row[1];
			ImageLine($imageT,0,255-($prev[1]/$MaxH)*255,0,255-($prev[1]/$MaxH)*255,$blue);
			for ($i = 1; $i< $cntr; $i++) { 
				$j = $i/2;
				$k = $j+1;
				mysqli_data_seek($rs, $i);
				$row = mysqli_fetch_row($rs); 
				ImageLine($imageT,$j,255-(($prev[0]-$MinT)/$rangeT)*255,$k,255-(($row[0]-$MinT)/$rangeT)*255,$red);
				ImageLine($imageT,$j,255-($prev[1]/$MaxH)*255,$k,255-($row[1]/$MaxH)*255,$blue);
				$prev[0] = $row[0];
				$prev[1] = $row[1];
			}
			ImagePNG($imageT,"imageT.png");
			ImageDestroy($imageT);     
		}
		
		if ($plt == "dbf") {
			//tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, Methane, SoundDb, Freq)
			$qry = "SELECT Max(SoundDb), Max(Freq) FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$MaxD = 120; // 0 to 120 db //130;  //  minus 125 to plus 130 = range 255
			$MaxF = 8000; // 0 to 8000 hz //22050;  // 44100 / 2

			Header("Content-type: image/png");  // let the server know its not html
			$imageD = ImageCreate(721,256);
			$white = ImageColorAllocate($imageD,255,255,255);
			$red = ImageColorAllocate($imageD,255,0,0); 
			$blue = ImageColorAllocate($imageD,0,0,255);
			$black = ImageColorAllocate($imageD,0,0,0);
			ImageLine($imageD,0,127,720,127,$black);    // 60 
			ImageLine($imageD,0,0,720,0,$black);  
			ImageLine($imageD,720,0,720,255,$black);  
			ImageLine($imageD,720,255,0,255,$black);  
			ImageLine($imageD,0,255,0,0,$black);  			
			// Draw the text 'PHP Manual' using font size 13
			//$font_file = './arial.ttf';
			//imagefttext($imageD, 13, 0, 105, 55, $black, $font_file, 'PHP Manual');
			//$font = imageloadfont('./04b.gdf');
			//imagestring($im, $font, 0, 0, 'Hello', $black);
						
			$qry = "SELECT SoundDb, Freq FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			//echo "$qry<br>";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			//echo "cntr=$cntr<br>";
			
			$lineCntr = 2;
			$prev[$lineCntr];
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$prev[0] = $row[0];
			ImageLine($imageD,0,255-($prev[0]/$MaxD)*255,0,255-($prev[0]/$MaxD)*255,$red);
			$prev[1] = $row[1];
			ImageLine($imageD,0,255-($prev[1]/$MaxF)*255,0,255-($prev[1]/$MaxF)*255,$blue);
			for ($i = 1; $i< $cntr; $i++) { 
				$j = $i/2;
				$k = $j+1;
				mysqli_data_seek($rs, $i);
				$row = mysqli_fetch_row($rs); 
				$dat[0] = $row[0];
				ImageLine($imageD,$j,255-($prev[0]/$MaxD)*255,$k,255-($row[0]/$MaxD)*255,$red);
				$dat[1] = $row[10];
				ImageLine($imageD,$j,255-($prev[1]/$MaxF)*255,$k,255-($row[1]/$MaxF)*255,$blue);
				$prev[0] = $row[0];
				$prev[1] = $row[1];
			}
			ImagePNG($imageD,"imageD.png");
			ImageDestroy($imageD);     
		}

		if ($plt == "pms") {
			//tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, Methane, SoundDb, Freq)
			//https://cdn-shop.adafruit.com/product-files/3686/plantower-pms5003-manual_v2-3.pdf
			$qry = "SELECT Max(PM1), Max(PM25), Max(PM10) FROM tblMonitor WHERE Loc = $id AND Date > '$startDate'";
			//echo "$qry<br>";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);			
			mysqli_data_seek($rs, $cntr);
			$row = mysqli_fetch_array($rs); 
			$MaxY = $row[0];
			if ($MaxY < $row[1]) 
				$MaxY = $row[1];
			if ($MaxY < $row[2])
				$MaxY = $row[2];
			$MaxYI = pow(10,intval(strlen(strval($MaxY))-1)); 
			$MaxY = intval($MaxY/$MaxYI)*$MaxYI+$MaxYI;  

			Header("Content-type: image/png");  // let the server know its not html
			$imageP = ImageCreate(721,256);
			$white = ImageColorAllocate($imageP,255,255,255);
			$red = ImageColorAllocate($imageP,255,0,0); 
			$green = ImageColorAllocate($imageP,0,255,0);
			$blue = ImageColorAllocate($imageP,0,0,255);
			$black = ImageColorAllocate($imageP,0,0,0);
			ImageLine($imageP,0,128,720,128,$black);     
			ImageLine($imageP,0,0,720,0,$black);  
			ImageLine($imageP,720,0,720,255,$black);  
			ImageLine($imageP,720,255,0,255,$black);  
			ImageLine($imageP,0,255,0,0,$black);  			
			
			$qry = "SELECT PM1, PM25, PM10 FROM tblMonitor WHERE Loc = $id AND Date > '$startDate' ORDER BY Date";
			$rs = mysqli_query($link_id, $qry);
			$cntr = mysqli_num_rows($rs);
			//echo "i=$i<br>";
			
			$lineCntr = 3;
			$prev[$lineCntr];
			mysqli_data_seek($rs, 0);
			$row = mysqli_fetch_row($rs); 
			$prev[0] = $row[0];
			ImageLine($imageP,0,255-($prev[0]/$MaxY)*255,0,255-($prev[0]/$MaxY)*255,$red);
			$prev[1] = $row[1];
			ImageLine($imageP,0,255-($prev[1]/$MaxY)*255,0,255-($prev[1]/$MaxY)*255,$blue);
			$prev[2] = $row[2];
			ImageLine($imageP,0,255-($prev[2]/$MaxY)*255,0,255-($prev[2]/$MaxY)*255,$green);
			for ($i = 1; $i< $cntr; $i++) { 
				$j = $i/2;
				$k = $j+1;
				mysqli_data_seek($rs, $i);
				$row = mysqli_fetch_row($rs); 
				ImageLine($imageP,$j,255-($prev[0]/$MaxY)*255,$k,255-($row[0]/$MaxY)*255,$red);
				ImageLine($imageP,$j,255-($prev[1]/$MaxY)*255,$k,255-($row[1]/$MaxY)*255,$blue);
				ImageLine($imageP,$j,255-($prev[2]/$MaxY)*255,$k,255-($row[2]/$MaxY)*255,$green);
				$prev[0] = $row[0];
				$prev[1] = $row[1];
				$prev[2] = $row[2];
			}
			ImagePNG($imageP,"imageP.png");
			ImageDestroy($imageP);     
		}
      
	}
		

?>
</head>

	<body bgcolor="#FAF0E6">
    <h3>Oil and Gas Monitor Plots</h3>
		<ul>		
			<li>Quality and VOC</li>
				<?php PlotProfileMonitor("voc") ?> 
				<IMG SRC="imageV.png"></br>
				Quality (Blue)<?php echo " 0 to 100 % " ?> VOC (Red)<?php echo " 0 to $MaxV ppb " ?> </br>
				</br>
			<li>Temperature and Relative Humidity</li>
				<?php PlotProfileMonitor("trh") ?> 
				<IMG SRC="imageT.png"></br>
				Temperature (Red)<?php echo " $MinT to $MaxT deg F" ?> -- Relative Humidity (Blue)<?php echo " 0 to $MaxH %" ?> </br>
				</br>
			<li>Sound: Decibels and Frequency</li>			
				<?php PlotProfileMonitor("dbf") ?> 
				<IMG SRC="imageD.png"></br>
				Decibels (Red)<?php echo " 0 to $MaxD db " ?> -- Frequency (Blue)<?php echo " 0 to $MaxF hz" ?> </br>
				</br>
			<li>Particles</li>
				<?php PlotProfileMonitor("pms") ?> 
				<IMG SRC="imageP.png"></br>
				PM 0.3 to 1.0 um (Red)  -- PM 1.0 to 2.5 um (Blue) -- PM 2.5 to 10.0 um (Green) <?php echo " 0 to $MaxY " ?>ug/m3 </br>
				</br>
		</ul>

	  
   <table width = "100%">
      <tr><td colspan = "2"><hr /></td>
          <td rowspan = "2" width = "33px" height = "38px">
            <a href = "index.html" target="_top">
              <img src="Images/x.jpg" 
              width = "33px" height = "38px"
              alt="Image: Corporate image" /></a></td></tr>
	     <tr><td><h5>23June2017 <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.<br></h5></td>
         <td><h5 style="text-align:right">Return to Homepage</h5></td></tr>
     </table>       
  </body>
</html>