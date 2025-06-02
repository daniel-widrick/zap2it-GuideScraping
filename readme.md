
This script is designed to take TV listings from zap2it and convert them to xmltv for use with applications such as Jellyfin/Emby.

```
$ python3 zap2it-GuideScrape.py -h
usage: Parse Zap2it Guide into XMLTV [-h] [-c CONFIGFILE] [-o OUTPUTFILE] [-l LANGUAGE] [-f] [-C] [-w]

options:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configfile CONFIGFILE, -i CONFIGFILE, --ifile CONFIGFILE
                        Path to config file
  -o OUTPUTFILE, --outputfile OUTPUTFILE, --ofile OUTPUTFILE
                        Path to output file
  -l LANGUAGE, --language LANGUAGE
                        Language
  -f, --findid          Find Headendid / lineupid
  -C, --channels        List available channels
  -w, --web             Start a webserver at http://localhost:9000 to serve /xmlguide.xmltv
```

## 18-OCT-2021
Please note that --ofile, --ifile, and -i arguments may be deprecated and removed in a future release. Please use -c, --configfile, and -o, --outputfile accordingly.

## 31-AUG-2022
Added the -f flag to assist with finding the headendId and lineupId for various providers.
Added an optional [lineup] section to the config to accomodate loading data for non-OTA providers
The script will attempt to derive the lineupId from data available, but the headendId is buried deeper and must be set manually if changing providers.
The 'device' field has also been added to the [lineup] config section and is supported in the script
<pre>
    type           |name                                    |location       |headendID      |lineupID                 |device         
    OTA            |Local Over the Air Broadcast            |               |lineupId       |USA-lineupId-DEFAULT     |               
    CABLE          |Xfinity - Digital                       |Daly City      |CA55528        |USA-CA55528-DEFAULT      |X              
    SATELLITE      |DISH San Francisco - Satellite          |San Francisco  |DISH807        |USA-DISH807-DEFAULT      |-              
    CABLE          |AT&T U-verse TV - Digital               |San Francisco  |CA66343        |USA-CA66343-DEFAULT      |X              
</pre>

## 07-NOV-2022
Docker isn't my strongest area so I'm not sure of the exact usecase, but I've created a VERY basic Dockerfile 
Basic Docker Support:
Run the following commands from the root of this repo in Windows(PowerShell) or linux:
<pre>
docker build -t zap2it:latest .
docker run -v ${PWD}:/guide zap2it
</pre>
Running the script like this will read zap2itconfig.ini from the host current directory and output the .xmltv files to the host current directory.

## 09-MAR-2025
### Multiple Zipcodes
Added support for multiple zipcodes. zap2itconfig.ini now supports listing multiple zip codes and should deduplicate the resulting guide with consideration to overlapping channels:
```
zipCode: [55555, 44444]
```

Single zip codes are still supporting using the old format:
```
zipCode: 55555
```

or a single entry in the new json format:
```
[55555]
```

### Channel Filtering
Added support for channel filtering via `favoriteChannels:` in config. If this value is populated, only channel IDs listed in the config will be listed. Example:
```
favoriteChannels: [53158,42578]
```

### Web based guide
Added a docker-compose.yml file that will run a webserver at `0.0.0.0:9000` and serve `/xmlguide.xmltv` while updating the guide in the background every 24 hours.

This allows Jellyfin to point at the url and automatically receive guide updates with no further scripting.

## 02-JUN-2025
### Environment variable config
All values in the zap2itconfig.ini can now be passed as environment variables via docker compose (or in the normal env). Variables take the form:
`ZAP2IT_SECITON_KEY`

Variables passed from the environment take precedence. Then variables from the zap2itconfig.ini. Then any hard coded defaults int he script.

EG:
```
services:
  guide-scraper-dtv:
    build: .
    container_name: guide-scraper-dtv
    ports:
      - "9000:9000"
    environment:
      - TZ=America/New_York
      - ZAP2IT_PREFS_LANG=es
      - ZAP2IT_PREFS_COUNTRY=US
      - ZAP2IT_CRED_USERNAME=your_username
      - ZAP2IT_CRED_PASSWORD=your_password
      - ZAP2IT_LINEUP_LINEUPID=USA-DITV528-DEFAULT
      - ZAP2IT_LINEUP_HEADENDID=DITV528
  guide-scraper-ota:
    build: .
    container_name: guide-scraper-ota
    ports:
      - "9001:9000"
    environment:
      - TZ=America/New_York
      - ZAP2IT_PREFS_LANG=es
      - ZAP2IT_PREFS_COUNTRY=US
      - ZAP2IT_CRED_USERNAME=your_username
      - ZAP2IT_CRED_PASSWORD=your_password
      - ZAP2IT_LINEUP_LINEUPID=DFLT
      - ZAP2IT_LINEUP_HEADENDID=lineupId
    restart: always
```