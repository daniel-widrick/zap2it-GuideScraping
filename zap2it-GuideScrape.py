import configparser
import json
import urllib.request, urllib.parse
import time, datetime
import xml.dom.minidom
import sys, os, argparse

class Zap2ItGuideScrape():

    def __init__(self,configLocation="./zap2itconfig.ini",outputFile="xmlguide.xmltv"):
        self.confLocation = configLocation
        self.outputFile=outputFile
        print("Loading config: ", self.confLocation, " and outputting: ", outputFile)
        self.config = configparser.ConfigParser()
        self.config.read(self.confLocation)
        self.lang = self.config.get("prefs","lang")

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
        authResponse = urllib.request.urlopen(authRequest).read()
        authFormVars = json.loads(authResponse)
        self.zapTocken = authFormVars["token"]
    def BuildDataRequest(self,currentTime):
        parameters = {
            'Activity_ID': 1,
            'FromPage': "TV%20Guide",
            'AffiliateId': "gapzap",
            'token': self.zapToken,
            'aid': 'gapzap',
            'lineupId': 'DFLTE',
            'timespan': 3,
            'headendId': 'lineupId',
            'country': self.config.get("prefs", "country"),
            'device': '-',
            'postalCode': self.config.get("prefs", "zipCode"),
            'isOverride': "true",
            'time': currentTime,
            'pref': 'm,p',
            'userId': '-'
        }
        data = urllib.parse.urlencode(parameters)
        url = "https://tvlistings.zap2it.com/api/grid?" + data
        req = urllib.request.Request(url)
        return req
    def GetData(self,time):
        request = self.BuildDataRequest(time)
        print("Load Guide for time: ",str(time))
        response = urllib.request.urlopen(request).read()
        return json.loads(response)
    def AddResultsToGuide(self,json,addChannels=True):
        for channel in json["channels"]:
            if addChannels:
                self.rootEl.appendChild(self.BuildChannelXML(channel))
            for event in channel["events"]:
                self.rootEl.appendChild(self.BuildEventXmL(event,channel["channelId"]))
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

        thumnailEl = self.CreateElementWithData("thumnail","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
        iconEl = self.guideXML.createElement("icon")
        iconEl.setAttribute("src","http://zap2it.tmsimg.com/assets/" + event["thumbnail"] + ".jpg")
        programEl.appendChild(thumnailEl)
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
        dispName2 = self.CreateElementWithData("displayName",channel["channelNo"])
        dispName3 = self.CreateElementWithData("displayName",channel["callSign"])
        dispName4 = self.CreateElementWithData("displayName",channel["affiliateName"].title())
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
        endTimeStamp = currentTimestamp + (60 * 60 * 336)
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
        while(loopTime < times[1]):
            json = self.GetData(loopTime)
            self.AddResultsToGuide(json,addChannels)
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
                if os.stat(fileName).st_mtime < int(histGuideDays) * 86400:
                    os.remove(fileName)



#Run the Scraper
optConfigFile = './zap2itconfig.ini'
optGuideFile = 'xmlguide.xmltv'
optLanguage = 'en'


parser = argparse.ArgumentParser("Parse Zap2it Guide into XMLTV")
parser.add_argument("-c","--configfile","-i","--ifile", help='Path to config file')
parser.add_argument("-o","--outputfile","--ofile", help='Path to output file')
parser.add_argument("-l","--language", help='Language')

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

guide.BuildGuide()


