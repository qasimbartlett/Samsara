#!/bin/bash

SERIAL_NUM=AXN_5.1.6_3333_18041700

while [ true ]
do
	Dir_Date=`date +%Y_%m_%d`
	Dir_Date_dash=`date +%Y-%m-%d`
        Dir_Hr=`date +%H`
        Dir_Min=`date +%M`

	if   [ $Dir_Min -le 15 ]; then
        	Dir_15Min=${Dir_Hr}_00_15
	elif [ $Dir_Min -le 30 ];then
        	Dir_15Min=${Dir_Hr}_15_30
	elif [ $Dir_Min -le 45 ]; then
        	Dir_15Min=${Dir_Hr}_30_45
	else
        	Dir_15Min=${Dir_Hr}_45_00
	fi


     	GPS_FILE_NAME=${SERIAL_NUM}__${Dir_Date}___${Dir_15Min}


	mkdir ${SERIAL_NUM}  ${SERIAL_NUM}/$Dir_Date    ${SERIAL_NUM}/$Dir_Date/$Dir_15Min
	echo ""
	echo ""
	echo ""
	echo ""
	echo "------------------------------------------------------------------------------------------------------"
	echo "####  GPS_FILE_NAME=$GPS_FILE_NAME=  GPS_TXT=$GPS_TXT=;  Executing mkdir $Dir_Date    $Dir_Date/$Dir_15Min"
	echo "####  Starting log collection "

	# Run adafruit for 15 mins and save the logs
	timeout 900 python adafruit.py > /tmp/$GPS_FILE_NAME
	# move logs into cloud
	# Find all satellite counting messages for whole day
 	grep -h $Dir_Date_dash /tmp/* | egrep "GGA|GSA|GSV" | python main_2.py >  /tmp/AllDay_Satellites_seen_${Dir_Date}.csv
 	grep -h $Dir_Date_dash /tmp/* | egrep "VTG"                            >  /tmp/AllDay_VTG_${Dir_Date}.csv
	# upload the satellite count csv
        cd /tmp/
	# use ping 8.8.8.8  to detect internet service
    	gsutil.cmd -m cp -r *_${Dir_Date}*                          gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/$Dir_Date/

	# Concatenate all results into 1 file
	rm -rf AllDay_Satellite*
	echo "Date,ID,NumSatellites" > TotalDays.csv
	for i in `gsutil.cmd -m ls -r gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/ | grep AllDay_Satellites_se`
	do
		gsutil.cmd -m cp -r $i .
		cat AllDay_Satel* | sed -e "s/\r//g" | sort | uniq >> TotalDays.csv
		gsutil.cmd -m cp -r TotalDays.csv gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/
		rm -rf AllDay_Satellite* TotalDays.csv
	done

	# Concatenate multiple days VTG into a single file
	cd /tmp
        rm -rf AllDay_VTG*
        echo "Date,Serial,Rev,Firmware,Software,VTG,Tracktrue,T,Trackmag,MagneticIndicator,Speed Kn,N, Speed Km,K,Checksum" > TotalVTG.csv
        for i in `gsutil.cmd -m ls -r gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/ | grep AllDay_VTG`
        do
                gsutil.cmd -m cp -r $i .
                cat AllDay_VTG* | sed -e "s/\r//g"  | sort | uniq  >> TotalVTG.csv
                gsutil.cmd -m cp -r TotalVTG.csv  gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/
                rm -rf *VTG*
        done
    	cd
done
