<?php
// header("Cache-Control: no-cache, must-revalidate");
// header("Pragma: no-cache");
// header("Expires: Mon,26 Jul 1997 05:00:00 GMT");
	include "./common_OilGasMonitor.inc";
	date_default_timezone_set("America/Denver");
?>

<html>
<head>
<!-- OilGasMonitor -->
<!-- LoadMonitor -->


<?php
	global $link_id;
	global $remote;
	global $FileDate;
	$link_id = db_connect();
	MonitorFile();  

    function MonitorFile() {
		global $link_id;
		global $FileDate;		
		// tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq) 
		// this picks any file by file name (YYYY-MO-DD HH:MM_1.txt) from the scan folder
		// It has been FTPed to web /Scan folder from remote locations
		// doesn't matter which one - the location is the last number before .txt
		$LastCol = 10;  // does not include Loc and Date i.e. starts with MP1
		$isQuitNow=0;

		$ScanFilePath = "./Scan/";
		chdir( $ScanFilePath );		
		$ThisFile = "";
		// *************************** outer while 
		While ($isQuitNow==0) { // the outer loop		
			echo "ScanFilePath = $ScanFilePath<br>";
			// get new file:
			$PrevFile = $ThisFile;
			$ThisFile = NextFileName($ScanFilePath);  
			echo "ThisFile = $ThisFile" . "<br>";	
			If ($ThisFile == $PrevFile OR empty($ThisFile)) { // no more files
				$isQuitNow = 1;
				//If ($isQuitNow==1) {
				echo "No more files " . date('Y-m-d H:i:s') . "<br>";
				break;
			}
			
			If (substr($ThisFile, 0, 6) == "Error:") {
				echo "ThisFile=$ThisFile<br>";
				exit(-1);  //error out
			} 
			/*
			Inputs:
			PM2.5 Air Quality Sensor - I2C
			https://learn.adafruit.com/pm25-air-quality-sensor
			0	PM 1.0 um
			1	PM 2.5 um
			2	PM 10  um
			BMI680 Air Quality - I2C
			3	Temp Degrees C x 100
			4	Pressure Pa (hPa x 100)
			5	RH   Percent (x 100)
			6	Ohms 0-300,000 Ohms
			7	Methane
			Samson Microphone - USB
			http://www.samsontech.com/samson/products/microphones/usb-microphones/gomic/
			8	SoundDb  dB
			9	Freq 	Hz
			*/
			$handle = @fopen($ThisFile, "r");
			if ($handle) {
				while (($line = fgets($handle, 128)) !== false) {
					echo "line: $line " . "<br>";
					$MinuteAve = explode(',', $line);
					for ($j = 0; $j<$LastCol; $j++) {
						echo "MinuteAve: $MinuteAve[$j]" . "<br>";
					}
				}	
				if (!feof($handle)) {
					echo "Error: unexpected fgets()" . "<br>";
					exit(-2);
				}
				fclose($handle);
			}

			// save the data in the database
			$Underscore = strpos($ThisFile, "_",15); // 2017-01-05 15_51_1.txt -- get the second underscore
			$Extn = strpos($ThisFile, ".txt");
			echo "Underscore:$Underscore Extn:$Extn " . "<br>";
			$FileDate = substr($ThisFile, 0, $Underscore) . ":00";  // 2017-01-05 15_51:00
			$FileDate = str_replace("_", ":", $FileDate); // 2017-01-05 15:51:00
			$iLoc = substr($ThisFile,$Underscore+1,$Extn-$Underscore-1); // 1			
			echo "FileDate: $FileDate Loc: $iLoc " . "<br>";
			$quality = CalcQual($iLoc,$MinuteAve); // quality
			$voc = CalcVoc($iLoc,$MinuteAve); // voc
			// $qry = "INSERT INTO tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq) 
			//							VALUES (1,'2017-01-05 15:55:00',272,460,281,75,84400,27, 200000,80, 1, 350,20,1000)";
			$qry = "INSERT INTO tblMonitor VALUES ($iLoc,'$FileDate',$MinuteAve[0],$MinuteAve[1],$MinuteAve[2],$MinuteAve[3],
								$MinuteAve[4],$MinuteAve[5],$MinuteAve[6],$quality,$voc,$MinuteAve[7],$MinuteAve[8],$MinuteAve[9])";
			echo $qry . "<br>";
			$rsNew = mysqli_query($link_id, $qry);
			$w = mysqli_affected_rows($link_id);
			
			if ($w == 1) {
				echo "Delete File: $ThisFile" . "<br>";
				unlink($ThisFile); // delete it				
			}
			if ($w < 1) { // 0 or negative
				$isQuitNow=1;
				echo "<h3>Unknown Failure to Insert: $ThisFile</h3></br>";  
				exit(3);
			}
			DoEvents(); 
		}		
	}

	function NextFileName($dir) {
		// Open a directory, and read its contents
		echo "NextFileName $dir" . "<br>";
		foreach (glob("*.*") as $filename) {
			echo "$filename " . "<br>";
			return $filename; // take the first one
		}
		return "";
	}
		
	Function CalcQual($iLoc,$MinuteAve)	{
		global $link_id;
		global $FileDate;
		$StartDate = date("Y-m-d H:i:s", strtotime('-24 hours', strtotime($FileDate)));

		// PM1, PM25, PM10, Temp, Press, RH, Ohms, Methane, SoundDb, Freq		
		// tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq)
		// Set the humidity baseline to 40%, an optimal indoor humidity.
		$hum_baseline = 40.0;
		// This sets the balance between humidity and gas reading in the 
		//calculation of air_quality_score (25:75, humidity:gas)
		$hum_weighting = 0.25;
		// get the best quality air (highest ohms) for this loc
		$qry = "SELECT Ohms FROM tblMonitor WHERE Loc = $iLoc AND Date > $StartDate
				ORDER BY Ohms DESC Limit 10";
		$rs = mysqli_query($link_id, $qry);
		$cnt = mysqli_num_rows($rs);
		$gas_baseline = 0;
		for ($i = 0; $i<$cnt; $i++) {
			mysqli_data_seek($rs, $i);
			$row = mysqli_fetch_row($rs); 
			$gas_baseline += $row[0];
		}
		$gas_baseline /= $cnt; // gas base quality (voc gas highest ohms) 
		echo " baseline: $gas_baseline, cnt: $cnt<br>";		
		$gas = $MinuteAve[6]; // Ohms
		$gas_offset = $gas_baseline - $gas;

		$hum = $MinuteAve[5];
		$hum_offset = $hum - $hum_baseline;

		// Calculate hum_score as the distance from the hum_baseline.
		if ($hum_offset > 0) {
			$hum_score = (100 - $hum_baseline - $hum_offset) / (100 - $hum_baseline) * ($hum_weighting * 100);
		} else {
			$hum_score = ($hum_baseline + $hum_offset) / $hum_baseline * ($hum_weighting * 100);
		}
		// Calculate gas_score as the distance from the gas_baseline.
		if ($gas_offset > 0) {
			$gas_score = ($gas / $gas_baseline) * (100 - ($hum_weighting * 100));
		} else {
			$gas_score = 100 - ($hum_weighting * 100);
		}
		// Calculate air_quality_score. 
		$air_quality_score = $hum_score + $gas_score;
		$quality = round($air_quality_score); // Quality
		echo " Gas:$MinuteAve[6] Ohms, humidity:$MinuteAve[5] %RH, air quality: $quality<br>";
		return $quality;
	}	

	Function CalcVoc($iLoc,$MinuteAve)	{
		global $link_id;
		global $FileDate;
		$StartDate = date("Y-m-d H:i:s", strtotime('-24 hours', strtotime($FileDate)));
		
		// PM1, PM25, PM10, Temp, Press, RH, Ohms, Qual, SoundDb, Freq		
		// tblMonitor (Loc, Date, PM1, PM25, PM10, Temp, Press, RH, Ohms, Quality, VOC, Methane, SoundDb, Freq)
		$qry = "SELECT Ohms FROM tblMonitor WHERE Loc = $iLoc AND Date > $StartDate
				ORDER BY Ohms DESC Limit 10";
		$rs = mysqli_query($link_id, $qry);
		$cnt = mysqli_num_rows($rs);
		$gas_baseline = 0;
		for ($i = 0; $i<$cnt; $i++) {
			mysqli_data_seek($rs, $i);
			$row = mysqli_fetch_row($rs); 
			$gas_baseline += $row[0];
		}
		$gas_baseline /= $cnt; // gas base quality (voc gas highest ohms) 
		echo " baseline: $gas_baseline, cnt: $cnt<br>";		
		$gas = $MinuteAve[6]; // Ohms
		$gas_parts = ($gas_baseline - $gas) / $gas_baseline; // parts
		$ppb = round(($gas_parts * 1000000000) / $gas_baseline);   // parts/baseline = ppb/1000000000 -> 1000000000*parts=ppb*baseline -> (1000000000*parts)/baseline
		echo "ppb baseline: $gas_baseline, gas: $gas, parts: $gas_parts, ppb: $ppb<br>";
		return $ppb;

	}
	
	function DoEvents() {
		ob_flush();
	} // DoEvents
	
?>

	<link rel="stylesheet" type="text/css" href="msStyle.css" />
	<title>Monitor</title>

	</head>
	<body>
	<form method="post" action="Monitor.php" name="frmMonitor" >

	</form>

	</body>
</html>
