import sys
from collections import defaultdict
from google.cloud import logging
from google.cloud import storage

'''
   NMEA - 0183 is latest std. To get a complete list of messages and format we have to pay to 
   download the spec.
   I used info from https://www.ae.utexas.edu/courses/ase389p7/projects/svatek/nmea0183.html
   https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_MessageOverview.html

   We may want to parse all available NMEA messages in future. 
   So adding TODOs for some
'''


class Samsara(object):

    def __init__(self):
        self.IDs = defaultdict(str, {
            'AP': 'Autopilotmagnetic ',
            'GA': 'Galileo',
            'GB': 'BeiDou',
            'GL': 'GLONASS',
            'GP': 'GPS',
            'GN': 'GNSS',
            'HC': 'Magnetic heading compass',
            'LC': 'Loran-C',
            'RA': 'Radar',
            'TR': 'Transit SATNAV',
            'SD': 'Depth sounder',
            'VW': 'Mechanical speed log'})

        self.sat_lost = True
        self.sat_lost_time = 0
        self.sat_acquired_time = 0
        self.MAX_SATELLITES = 4
        self.start_of_sentence = 5
        # 2024-03-03T12:41:43.473939 ,AXN_5.1.6_3333_18041700,0005,FW786786,SW156523,$GNRMC,184143.000,V,,,,,0.00,118.37,030324,,,N*52
        # time                        serial                   rev  FW        Sw

        # Track # pfo satellites seen from any system; GPS, GNSS, BeiDou etc
        self.current_number_of_satellites_seen = 0

        # For now hardcode this value. We can have a more complex data structure to determine
        # if fix is achieved
        self.number_of_satellites_for_fix = 4
        self.satellites_lost = True

        # Dummy message count
        self.message_count = 0

        # Instantiates a client
        # logging_client = logging.Client()

        # The name of the log to write to
        # log_name = "device_gps_reports.csv"
        # Selects the log to write to
        # self.logger = logging_client.logger(log_name)

        # Instantiates a client
        # self.storage_client = storage.Client()

    def write_to_cloud_raw_log(self, sentence):
        """
        Logs can be accessed from
        https://console.cloud.google.com/logs/query;cursorTimestamp=2024-03-01T03:23:47.383520165Z;startTime=2024-02-29T01:55:00.000Z?project=samsara-415701
        Graph is at https://lookerstudio.google.com/reporting/4af75780-9504-4189-a7e0-5173e2192c38
        LOgs can also be uploaded to storage at
        https://console.cloud.google.com/storage/browser/samsara_test;tab=objects?project=samsara-415701

        """
        # Writes the log entry
        self.logger.log_text(sentence)

    def supported_talker_identifier(self, sentence_word_0):
        # 1st 2 characters are the 2 letter identifier for the satellite system
        return self.IDs[sentence_word_0.strip()[1:3]]

    def decode_gga(self, sentence):
        """
        The standard NMEA message with position data. It contains 3D coordinates,
        solution status, and the number of satellites used.

        Generic method, Currently returns # of satellites used. Can be expanded to
        save/store other values.

        Field	Meaning
        0	Message ID $GPGGA
        1	UTC of position fix
        2	Latitude
        3	Direction of latitude:              N: North                S: South
        4	Longitude
        5	Direction of longitude:             E: East             W: West
        6	GPS Quality indicator:
                0: Fix not valid
                1: GPS fix
                2: Differential GPS fix (DGNSS), SBAS, OmniSTAR VBS, Beacon, RTX in GVBS mode
                3: Not applicable
                4: RTK Fixed, xFill
                5: RTK Float, OmniSTAR XP/HP, Location RTK, RTX
                6: INS Dead reckoning
        7	Number of SVs in use, range from 00 through to 24+
        8	HDOP
        9	Orthometric height (MSL reference)
        10	M: unit of measure for orthometric height is meters
        11	Geoid separation
        12	M: geoid separation measured in meters
        13	Age of differential GPS data record, Type 1 or Type 9. Null field when DGPS is not used.
        14	Reference station ID, range 0000 to 4095. A null field when any reference station ID is selected and no corrections are received. See table below for a description of the field values.
        15
        """
        self.message_count += 1
        # print('----', sentence)
        # print('----', sentence.split(','))
        number_of_satellites_being_used = -1
        gps_status_indicator = sentence.split(',')[self.start_of_sentence + 6]
        if gps_status_indicator:
            number_of_satellites_being_used = sentence.split(',')[self.start_of_sentence + 7]
            if number_of_satellites_being_used:
                number_of_satellites_being_used = int(number_of_satellites_being_used)
            else:
                number_of_satellites_being_used = -1

        return number_of_satellites_being_used

    def decode_gsv(self, sentence):
        """
        :param sentence: the NMEA sentence
        :return: list of satellites

        1 $GPGSV Log header $GPGSV
        2 # msgs Total number of messages (1-9) x 3
        3 msg # Message number (1-9) x 1
        4 # sats Total number of satellites in view. May be different than the number of satellites in use
        5 prn Satellite PRN number GPS = 1 to 32 Galileo = 1 to 36 BeiDou = 1 to 63 NavIC = 1 to 14 QZSS = 1 to 10 SBAS = 33 to 64 (add 87 for PRN#s) GLONASS = 65 to 96 1 xx 03
        6 elev Elevation, degrees, 90 maximum xx 51
        7 azimuth Azimuth, degrees True, 000 to 359 xxx 140
        8 SNR SNR (C/No) 00-99 dB, null when not tracking xx
        """
        # print('---------', sentence)
        num_sats = -1
        # The GSV message may not have sat entries
        if len(sentence.split(',')) > 15:
           if sentence.split(',')[self.start_of_sentence + 3]:
              num_sats = int(sentence.split(',')[self.start_of_sentence + 3])
           # print('---------', num_sats)
        return num_sats

    def decode_rmc(self, sentence):
        """
            Provides minimum GPS sentences information. This sentence is created only by the
            GPS and is based on the data received only by the receiver.
            GPRMC type sentences are available from every GPS receiver, and for most
            applications they provide all the data you need. For example, they contain
            your exact position, speed, and direction of movement.

            But they dont carry # of satellites used information. So skipping for now
        """
        # TODO: qasimm@
        pass

    def decode_gsa(self, sentence):
        """
        Provides the Satellite status data
        contains information about the list of satellites used for navigation.
        0	Message ID $GNGSA
        1	Mode 1:     M = Manual          A = Automatic
        2	Mode 2: Fix type:               1 = not available               2 = 2D          3 = 3D
        3	PRN number:
                01 to 32 for GPS
                33 to 64 for SBAS
                64+ for GLONASS

        4	PDOP: 0.5 to 99.9
        5	HDOP: 0.5 to 99.9
        6	VDOP: 0.5 to 99.9
        7	The checksum data, always begins with *
        """
        self.message_count += 1
        # Extract the list of all satellites used
        satellite_list = sentence.split(',')[self.start_of_sentence + 3:self.start_of_sentence + 14]
        # Remove empty strings from the satellite_list
        satellite_list = [i for i in satellite_list if i]
        # print('---------', sentence)
        # print('---------', satellite_list)
        return len(satellite_list)

    def extract_satellites_used(self, sentence):
        # Return a -ve # for sentences that do not carr satellite info
        satellites_used = -1
        sentence_word_1 = sentence.split(',')[self.start_of_sentence]
        if 'GGA' in sentence_word_1:
            satellites_used = self.decode_gga(sentence)
        elif 'GSA' in sentence_word_1:
            satellites_used = self.decode_gsa(sentence)
        elif 'GSV' in sentence_word_1:
            satellites_used = self.decode_gsv(sentence)
        return satellites_used

    def compute_time_for_first_fix(self, sat_count, sat_time):
        """
          This algo can be made as complex as one would want:
          eg: Declare position determined if 2 GSS + 1 GNSS or 2 GNSS + 1 GPS or 1 GNSS + 1 GPS + 11 LOCA...
          For simplicity lets assume
          position is determined if any 4 satellites are seen by the receiver
        """
        # print('1. compute_time_for_first_fix',self.sat_lost, self.sat_acquired_time, self.sat_lost_time)
        if sat_count >= self.MAX_SATELLITES:
            if self.sat_lost:
                self.sat_lost = False
                self.sat_acquired_time = sat_time
                print('--- TFF = %f=' % (self.sat_acquired_time - self.sat_lost_time))
        else:
            if not self.sat_lost:
                self.sat_lost = True
                self.sat_lost_time = sat_time
        # print('2. compute_time_for_first_fix',self.sat_lost, self.sat_acquired_time, self.sat_lost_time)

    # 2024-03-03T12:41:37.134396 ,AXN_5.1.6_3333_18041700,0005,FW786786,SW156523,$GLGSA,A,1,,,,,,,,,,,,,,,*02
    # 0                            1                       2     3         4       5
    # time                         serial                  HW    FW       SW       sentencee
    def parse(self, sentence):
        # A valid sentence will have a timestamp in it
        # print("\n\n-----------------", line)
        if sentence.count('2024') ==1 and '*' in sentence:
            # Extract the talker ID and check it is a supported ID
            talker_id = self.supported_talker_identifier(sentence.split(',')[self.start_of_sentence])
            # Find the TFF
            # print('2.....  ', talker_id)
            if talker_id:
                timestamp = sentence.split(',')[0]
                satellites_seen = self.extract_satellites_used(sentence)
                # if satellites_seen >= 0:
                # self.compute_time_for_first_fix(satellites_seen, timestamp)

                csv_line = '{},{},{}'.format(timestamp, talker_id, satellites_seen)
                print(csv_line)
                # print("========\n\n")


if __name__ == "__main__":
    x = Samsara()
    for line in sys.stdin:
        # print(line)
        # x.write_to_cloud_raw_log(line)
        # print('       ', end='')
        x.parse(line)
