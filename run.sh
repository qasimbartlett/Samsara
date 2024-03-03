#!/bin/bash

SERIAL_NUM=AXN_5.1.6_3333_18041700

while [ true ]
do
	Dir_Date=`date +%Y_%m_%d`
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
        GPS_FILE=${SERIAL_NUM}/$Dir_Date/$Dir_15Min/${GPS_FILE_NAME}.csv
	
	
	mkdir ${SERIAL_NUM}  ${SERIAL_NUM}/$Dir_Date    ${SERIAL_NUM}/$Dir_Date/$Dir_15Min 
	echo ""
	echo ""
	echo ""
	echo ""
	echo "------------------------------------------------------------------------------------------------------"
	echo "####  GPS_FILE=$GPS_FILE=  GPS_TXT=$GPS_TXT=;  Executing mkdir $Dir_Date    $Dir_Date/$Dir_15Min"
	echo "####  Starting log collection "

	# Run adafruit for 15 mins and save the logs
	timeout 900 python3 adafruit.py > /tmp/$GPS_FILE_NAME
	# move logs into cloud
	gsutil -m cp -r /tmp/$GPS_FILE_NAME   gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/$Dir_Date/
	# Find all satellite counting messages for whole day
 	grep $Dir_Date /tmp/* | egrep "GGA|GSA|GSV" | python3 main_2.py >  /tmp/AllDay_Satellites_seen_${Dir_Date}.csv 
	# upload the satellite count csv
    	gsutil -m cp -r /tmp/AllDay_Satellites_seen_${Dir_Date}.csv  gs://samsara_test/AdaFruit/Logs/${SERIAL_NUM}/$Dir_Date/
done

