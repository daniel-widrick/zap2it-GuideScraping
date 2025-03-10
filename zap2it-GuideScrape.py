import configparser
import json
import urllib.parse, urllib.request, urllib.error
import time, datetime
import xml.dom.minidom
import sys, os, argparse

#Use Globals to track state of the guide
ADDED_CHANNELS = []
ADDED_EVENTS = []

class Zap2ItGuideScrape():

    def __init__(self,configLocation="./zap2itconfig.ini",outputFile="xmlguide.xmltv"):
        self.confLocation = configLocation
        self.outputFile=outputFile
        if not os.path.exists(self.confLocation):
            print("Error: " + self.confLocation + " does not exist.")
            print("Copy config.ini.dist to config.ini and update the settings to match your zap2it account")
            exit(1)
        print("Loading config: ", self.confLocation, " and outputting: ", outputFile)

        self.config = configparser.ConfigParser()
        config = self.config.read(self.confLocation)
        if config == []:
            print("Failed to read config: " + self.confLocation)
            print("Check file permissions")
            exit(1)
        self.lang = self.config.get("prefs","lang", fallback="en")

        self.zapToken = ""
    def BuildAuthRequest(self):
        url = "https://tvlistings.zap2it.com/api/user/login"
        parameters = {
            "emailid": self.config.get("creds","username"),
            "password": self.config.get("creds","password"),
            "isfacebookuser": "false",
            "usertype": 0,
            "objectid": ""
        }
        data = urllib.parse.urlencode((parameters))
        data = data.encode('ascii')
        req = urllib.request.Request(url, data)
        return req
    def Authenticate(self):
        #Get token from login form
        authRequest = self.BuildAuthRequest()
        try:
            authResponse = urllib.request.urlopen(authRequest).read()
        except urllib.error.URLError as e:
            print("Error connecting to tvlistings.zap2it.com")
            print(e.reason)
            exit(1)
        authFormVars = json.loads(authResponse)
        self.zapTocken = authFormVars["token"]
        self.headendid= authFormVars["properties"]["2004"]
    def BuildIDRequest(self,zipCode):
        url = "https://tvlistings.zap2it.com/gapzap_webapi/api/Providers/getPostalCodeProviders/"
        url += self.config.get("prefs","country") + "/"
        url += zipCode + "/gapzap/"
        if self.config.has_option("prefs","lang"):
            url += self.config.get("prefs","lang")
        else:
            url += "en-us"
        req = urllib.request.Request(url)
        return req
    def FindID(self,zipCode):
        idRequest = self.BuildIDRequest(zipCode)
        try:
            print("Loading provider ID data from: ",idRequest.full_url)
            idResponse = urllib.request.urlopen(idRequest).read()
        except urllib.error.URLError as e:
            print("Error loading provider IDs:")
            print(e.reason)
            exit(1)
        idVars = json.loads(idResponse)
        print(f'{"type":<15}|{"name":<40}|{"location":<15}|',end='')
        print(f'{"headendID":<15}|{"lineupId":<25}|{"device":<15}')
        for provider in idVars["Providers"]:
            print(f'{provider["type"]:<15}|',end='')
            print(f'{provider["name"]:<40}|',end='')
            print(f'{provider["location"]:<15}|',end='')
            print(f'{provider["headendId"]:<15}|',end='')
            print(f'{provider["lineupId"]:<25}|',end='')
            print(f'{provider["device"]:<15}')

    def BuildDataRequest(self,currentTime,zipCode):
        #Defaults
        lineupId = self.config.get("lineup","lineupId",fallback=self.headendid)
        headendId = self.config.get("lineup","headendId",fallback='lineupId')
        device = self.config.get("lineup","device",fallback='-')

        parameters = {
            'Activity_ID': 1,
            'FromPage': "TV%20Guide",
            'AffiliateId': "gapzap",
            'token': self.zapToken,
            'aid': 'gapzap',
            'lineupId': lineupId,
            'timespan': 3,
            'headendId': headendId,
            'country': self.config.get("prefs", "country"),
            'device': device,
            'postalCode': zipCode,
            'isOverride': "true",
            'time': currentTime,
            'pref': 'm,p',
            'userId': '-'
        }
        data = urllib.parse.urlencode(parameters)
        url = "https://tvlistings.zap2it.com/api/grid?" + data
        req = urllib.request.Request(url)
        return req
    def GetData(self,time,zipCode):
        request = self.BuildDataRequest(time,zipCode)
        print("Load Guide for time: ",str(time)," :: ",zipCode)
        #print(request.full_url)
        response = urllib.request.urlopen(request).read()
        return json.loads(response)
    def AddChannelsToGuide(self, json):
        global ADDED_CHANNELS
        favoriteChannels = ""
        try:
            favoriteChannels = self.config.get("prefs","favoriteChannels")
        except:
            pass
        for channel in json["channels"]:
            if favoriteChannels != "":
                if channel["channelId"] not in favoriteChannels:
                    continue
            if channel["channelId"] in ADDED_CHANNELS:
                print("Duplicate Channel: ",channel["channelId"])
                continue
            else:
                self.rootEl.appendChild(self.BuildChannelXML(channel))
                ADDED_CHANNELS.append(channel["channelId"])
    def AddEventsToGuide(self,json):
        dedup_count = 0
        global ADDED_EVENTS
        favoriteChannels = ""
        try:
            favoriteChannels = self.config.get("prefs","favoriteChannels")
        except:
            pass
        for channel in json["channels"]:
            if favoriteChannels != "":
                if channel["channelId"] not in favoriteChannels:
                    continue
            for event in channel["events"]:
                #Deduplicate json
                eventHash = hash(channel.get("channelId") + event.get("startTime") + event.get("endTime"))
                if eventHash not in ADDED_EVENTS:
                    newChild = self.BuildEventXmL(event,channel["channelId"])
                    self.rootEl.appendChild(newChild)
                    ADDED_EVENTS.append(eventHash)
                else:
                    #print("Duplicate Event: ",event["program"]["title"]," on ",channel["channelId"]) #Debug dedeuplication
                    #This channel has been added for another zip?
                    dedup_count += len(channel["events"])
                    break #This break may cause missing programs? Investigate if someone reports missing programs
                    #The channel listing should be identical across zip codes but two zip codes returning the same channel
                    ## with different event listings could cause this.
        print("Deduped ",dedup_count," events")
                    
    def BuildEventXmL(self,event,channelId):
        #preConfig
        season = "0"
        episode = "0"

        programEl = self.guideXML.createElement("programme")
        programEl.setAttribute("start",self.BuildXMLDate(event["startTime"]))
        programEl.setAttribute("stop",self.BuildXMLDate(event["endTime"]))
        programEl.setAttribute("channel",channelId)

        titleEl = self.guideXML.createElement("title")
        titleEl.setAttribute("lang",self.lang) #TODO: define
        titleTextEl = self.guideXML.createTextNode(event["program"]["title"])
        titleEl.appendChild(titleTextEl)
        programEl.appendChild(titleEl)

        if event["program"]["episodeTitle"] is not None:
            subTitleEl = self.CreateElementWithData("sub-title",event["program"]["episodeTitle"])
            subTitleEl.setAttribute("lang",self.lang)
            programEl.appendChild(subTitleEl)

        if event["program"]["shortDesc"] is None:
            event["program"]["shortDesc"] = "Unavailable"
        descriptionEl = self.CreateElementWithData("desc",event["program"]["shortDesc"])
        descriptionEl.setAttribute("lang",self.lang)
        programEl.appendChild(descriptionEl)

        lengthEl = self.CreateElementWithData("length",event["duration"])
        lengthEl.setAttribute("units","minutes")
        programEl.appendChild(lengthEl)

        if event["thumbnail"] is not None:
            thumbnailEl = self.CreateElementWithData("thumbnail","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
            programEl.appendChild(thumbnailEl)
            iconEl = self.guideXML.createElement("icon")
            iconEl.setAttribute("src","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
            programEl.appendChild(iconEl)


        urlEl = self.CreateElementWithData("url","https://tvlistings.zap2it.com//overview.html?programSeriesId=" + event["seriesId"] + "&amp;tmsId=" + event["program"]["id"])
        programEl.appendChild(urlEl)
        #Build Season Data
        try:
            if event["program"]["season"] is not None:
                season = str(event["program"]["season"])
            if event["program"]["episode"] is not None:
                episode = str(event["program"]["episode"])
        except KeyError:
            print("No Season for:" + event["program"]["title"])

        for category in event["filter"]:
            categoryEl = self.CreateElementWithData("category",category.replace('filter-',''))
            categoryEl.setAttribute("lang",self.lang)
            programEl.appendChild(categoryEl)

        if((int(season) != 0) and (int(episode) != 0)):
            categoryEl = self.CreateElementWithData("category","Series")
            programEl.appendChild(categoryEl)
            episodeNum =  "S" + str(event["seriesId"]).zfill(2) + "E" + str(episode.zfill(2))
            episodeNumEl = self.CreateElementWithData("episode-num",episodeNum)
            episodeNumEl.setAttribute("system","common")
            programEl.appendChild(episodeNumEl)
            episodeNum = str(int(season)-1) + "." +str(int(episode)-1)
            episodeNumEl = self.CreateElementWithData("episode-num",episodeNum)
            programEl.appendChild(episodeNumEl)

        if event["program"]["id"[-4:]] == "0000":
            episodeNumEl = self.CreateElementWithData("episode-num",event["seriesId"] + '.' + event["program"]["id"][-4:])
            episodeNumEl.setAttribute("system","dd_progid")
        else:
            episodeNumEl = self.CreateElementWithData("episode-num",event["seriesId"].replace('SH','EP') + '.' + event["program"]["id"][-4:])
            episodeNumEl.setAttribute("system","dd_progid")
        programEl.appendChild(episodeNumEl)

        #Handle Flags
        for flag in event["flag"]:
            if flag == "New":
                programEl.appendChild(self.guideXML.createElement("New"))
            if flag == "Finale":
                programEl.appendChild(self.guideXML.createElement("Finale"))
            if flag == "Premiere":
                programEl.appendChild(self.guideXML.createElement("Premiere"))
        if "New" not in event["flag"]:
            programEl.appendChild(self.guideXML.createElement("previously-shown"))
        for tag in event["tags"]:
            if tag == "CC":
                subtitlesEl = self.guideXML.createElement("subtitle")
                subtitlesEl.setAttribute("type","teletext")
                programEl.appendChild(subtitlesEl)
        if event["rating"] is not None:
            ratingEl = self.guideXML.createElement("rating")
            valueEl = self.CreateElementWithData("value",event["rating"])
            ratingEl.appendChild(valueEl)
        return programEl
    def BuildXMLDate(self,inTime):
        output = inTime.replace('-','').replace('T','').replace(':','')
        output = output.replace('Z',' +0000')
        return output
    def BuildChannelXML(self,channel):
        channelEl = self.guideXML.createElement('channel')
        channelEl.setAttribute('id',channel["channelId"])
        dispName1 = self.CreateElementWithData("display-name",channel["channelNo"] + " " + channel["callSign"])
        dispName2 = self.CreateElementWithData("display-name",channel["channelNo"])
        dispName3 = self.CreateElementWithData("display-name",channel["callSign"])
        dispName4 = self.CreateElementWithData("display-name",channel["affiliateName"].title())
        iconEl = self.guideXML.createElement("icon")
        iconEl.setAttribute("src","http://"+(channel["thumbnail"].partition('?')[0] or "").lstrip('/'))
        channelEl.appendChild(dispName1)
        channelEl.appendChild(dispName2)
        channelEl.appendChild(dispName3)
        channelEl.appendChild(dispName4)
        channelEl.appendChild(iconEl)
        return channelEl

    def CreateElementWithData(self,name,data):
        el = self.guideXML.createElement(name)
        elText = self.guideXML.createTextNode(data)
        el.appendChild(elText)
        return el
    def GetGuideTimes(self):
        currentTimestamp = time.time()
        currentTimestamp -= 60 * 60 * 24
        halfHourOffset = currentTimestamp % (60 * 30)
        currentTimestamp = currentTimestamp - halfHourOffset
        days = 14
        try:
            days = int(self.config.get("prefs","guideDays"))
        except:
            print("guideDays not in config. using default: 14")
        print("Loading guide data for ",days," days")
        endTimeStamp = currentTimestamp + (60 * 60 * 24 * days)
        return (currentTimestamp,endTimeStamp)
    def BuildRootEl(self):
        self.rootEl = self.guideXML.createElement('tv')
        self.rootEl.setAttribute("source-info-url","http://tvlistings.zap2it.com/")
        self.rootEl.setAttribute("source-info-name","zap2it")
        self.rootEl.setAttribute("generator-info-name","zap2it-GuideScraping)")
        self.rootEl.setAttribute("generator-info-url","daniel@widrick.net")
    def BuildGuide(self):
        self.Authenticate()
        self.guideXML = xml.dom.minidom.Document()
        impl = xml.dom.minidom.getDOMImplementation()
        doctype = impl.createDocumentType("tv","","xmltv.dtd")
        self.guideXML.appendChild(doctype)
        self.BuildRootEl()

        addChannels = True;
        times = self.GetGuideTimes()
        loopTime = times[0]
        zipCodes = loadZipCodes()
        while(loopTime < times[1]):
            for zipCode in zipCodes:
                zipCode = str(zipCode)
                zipCode = zipCode.strip()
                zip_json = self.GetData(loopTime,zipCode)
                if addChannels:
                    self.AddChannelsToGuide(zip_json)   
                self.AddEventsToGuide(zip_json)
            addChannels = False
            loopTime += (60 * 60 * 3)
        self.guideXML.appendChild(self.rootEl)
        self.WriteGuide()
        self.CopyHistorical()
        self.CleanHistorical()
    def WriteGuide(self):
        with open(self.outputFile,"wb") as file:
            file.write(self.guideXML.toprettyxml().encode("utf8"))
    def CopyHistorical(self):
        dateTimeObj = datetime.datetime.now()
        timestampStr = "." + dateTimeObj.strftime("%Y%m%d%H%M%S") + '.xmltv'
        histGuideFile = timestampStr.join(optGuideFile.rsplit('.xmltv',1))
        with open(histGuideFile,"wb") as file:
            file.write(self.guideXML.toprettyxml().encode("utf8"))
    def CleanHistorical(self):
        outputFilePath = os.path.abspath(self.outputFile)
        outputDir = os.path.dirname(outputFilePath)
        for item in os.listdir(outputDir):
            fileName = os.path.join(outputDir,item)
            if os.path.isfile(fileName) & item.endswith('.xmltv'):
                histGuideDays = self.config.get("prefs","historicalGuideDays")
                if (time.time() - os.stat(fileName).st_mtime) >= int(histGuideDays) * 86400:
                    os.remove(fileName)

    def showAvailableChannels(self):
        allJSON = []
        self.Authenticate()
        for zipCode in loadZipCodes():
            zipCode = str(zipCode)
            zipCode = zipCode.strip()
            print("Loading available channels for: ",zipCode)
            my_json = guide.GetData(time.time(), zipCode)
            allJSON.append(my_json)
        channelList = {}
        for zip in allJSON:
            for channel in zip["channels"]:
                chanid = channel.get("channelId")
                chanid = int(chanid)
                channelList[chanid] = channel.get("callSign")  + "::" + channel.get("channelNo")
        print(f'{"CHAN ID":<15}|{"name":<40}|',end='')
        for channel in channelList:
            print(f'{channel:<15}|',end='')
            print(f'{channelList[channel]:<40}')

def loadZipCodes():
    zipCodes = guide.config.get("prefs","zipCode")
    try:
        zipCodes = json.loads(zipCodes)
        if not isinstance(zipCodes,list):
            zipCodes = [zipCodes]
    except json.JSONDecodeError:
        zipCodes = [zipCodes] #Support the old format
    print("Loaded Zip Codes: ",zipCodes)
    return zipCodes



#Run the Scraper
optConfigFile = './zap2itconfig.ini'
optGuideFile = 'xmlguide.xmltv'
optLanguage = 'en'


parser = argparse.ArgumentParser("Parse Zap2it Guide into XMLTV")
parser.add_argument("-c","--configfile","-i","--ifile", help='Path to config file')
parser.add_argument("-o","--outputfile","--ofile", help='Path to output file')
parser.add_argument("-l","--language", help='Language')
parser.add_argument("-f","--findid", action="store_true", help='Find Headendid / lineupid')
parser.add_argument("-C","--channels", action="store_true", help='List available channels')

args = parser.parse_args()
print(args)
if args.configfile is not None:
    optConfigFile = args.configfile
if args.outputfile is not None:
    optGuideFile = args.outputfile
if args.language is not None:
    optLanguage = args.language

guide = Zap2ItGuideScrape(optConfigFile,optGuideFile)
if optLanguage != "en":
    guide.lang = optLanguage

if args.findid is not None and args.findid:
    for zipCode in loadZipCodes():
        zipCode = str(zipCode)
        #strip whitespace
        zipCode = zipCode.strip()
        print("Finding IDs for: ",zipCode)
        guide.FindID(zipCode)
    sys.exit()
if args.channels is not None and args.channels:
    guide.showAvailableChannels()
    sys.exit()

guide.BuildGuide()


