
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

07-JUL-2020
Finally upgraded for python 3

18-OCT-2021
Please note that --ofile, --ifile, and -i arguments may be deprecated and removed in a future release. Please use -c, --configfile, and -o, --outputfile accordingly.
