
This script is designed to take TV listings from zap2it and convert them to xmltv for use with applications such as Jellyfin/Emby.

    $ python3 zap2it-GuideScrape.py -h
    usage: Parse Zap2it Guide into XMLTV [-h] [-c CONFIGFILE] [-o OUTPUTFILE]
                                     [-l LANGUAGE]

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIGFILE, --configfile CONFIGFILE, -i CONFIGFILE, --ifile CONFIGFILE
                        Path to config file
      -o OUTPUTFILE, --outputfile OUTPUTFILE, --ofile OUTPUTFILE
                        Path to output file
      -l LANGUAGE, --language LANGUAGE
                        Language
      -f, --findid          Find Headendid / lineupid

07-JUL-2020
Finally upgraded for python 3

18-OCT-2021
Please note that --ofile, --ifile, and -i arguments may be deprecated and removed in a future release. Please use -c, --configfile, and -o, --outputfile accordingly.

31-AUG-2022
Added the -f flag to assist with finding the headendId and lineupId for various providers.
Added an optional [lineup] section to the config to accomodate loading data for non-OTA providers
The script will attempt to derive the lineupId from data available, but the headendId is buried deeper and must be set manually if changing providers.
The 'device' field has also been added to the [lineup] config section and is supported in the script
    type           |name                                    |location       |headendID      |lineupID                 |device         
    OTA            |Local Over the Air Broadcast            |               |lineupId       |USA-lineupId-DEFAULT     |               
    CABLE          |Xfinity - Digital                       |Daly City      |CA55528        |USA-CA55528-DEFAULT      |X              
    SATELLITE      |DISH San Francisco - Satellite          |San Francisco  |DISH807        |USA-DISH807-DEFAULT      |-              
    CABLE          |AT&T U-verse TV - Digital               |San Francisco  |CA66343        |USA-CA66343-DEFAULT      |X              
