#!/usr/bin/env python3
"""
Forked from https://github.com/daniel-widrick/zap2it-GuideScraping
All credit goes to daniel-widrick.

Updated to use python3. Switching to python3 improved CPU usage and reduced A
processing time to generate xmlguide.xmltv.
"""
#Required libraries
import configparser
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import json
import time
import math
import html
#Additional Libraries for Parameter Parsing
import sys, getopt
#Libraries for historical copies
import datetime, os
from xml.sax.saxutils import escape

def sanitizeData(data):
	#https://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
	data = data.replace('&','&amp;')
	data = data.replace('"','&quot;')
	data = data.replace("'",'&apos;')
	data = data.replace('<','&lt;')
	data = data.replace('>','&gt;')
	return data;

def buildXMLChannel(channel):
	xml = ""
	xml = xml + "\t" + '<channel id="' +  html.unescape(channel["channelId"]) + '">' + "\n"
	xml = xml + "\t\t" + '<display-name>' + html.unescape(channel["channelNo"] + " " + channel["callSign"]) + '</display-name>' + "\n"
	xml = xml + "\t\t" + '<display-name>' + html.unescape(channel["channelNo"]) + '</display-name>' + "\n"
	xml = xml + "\t\t" + '<display-name>' + html.unescape(channel["callSign"]) + '</display-name>' + "\n"
	xml = xml + "\t\t" + '<display-name>' + escape(html.unescape(channel["affiliateName"].title())) + '</display-name>' + "\n"
	xml = xml + "\t\t" + '<icon src="http:' + channel["thumbnail"].partition('?')[0] + '" />' + "\n"
	xml = xml + "\t" + '</channel>' + "\n"
	return xml

def buildXMLProgram(event,channelId):
	#2018-04-11T21:00:00Z
	#20180408120000 +0000
	xml = ""
	season = "0"
	episode = "0"

	xml = xml + "\t" + '<programme start="' + buildXMLDate(event["startTime"]) + '" '
	xml = xml + 'stop="' + buildXMLDate(event["endTime"]) + '" channel="' + html.unescape(channelId) + '">' + "\n"
	xml = xml + "\t\t" + '<title lang="' + optLanguage + '">' + sanitizeData(event["program"]["title"]) + '</title>' + "\n"
	if event["program"]["episodeTitle"] is not None:
		xml = xml + "\t\t" + '<sub-title lang="' + optLanguage + '">' + sanitizeData(event["program"]["episodeTitle"]) + '</sub-title>' + "\n"
	if event["program"]["shortDesc"] is None:
		event["program"]["shortDesc"] = "Unavailable"
	xml = xml + "\t\t" + '<desc lang="' + optLanguage + '">' + sanitizeData(event["program"]["shortDesc"]) + '</desc>' + "\n"
	xml = xml + "\t\t" + '<length units="minutes">' + html.unescape(event["duration"]) + '</length>' + "\n"
	if event["thumbnail"] is not None:
		xml = xml + "\t\t" + '<thumbnail>http://zap2it.tmsimg.com/assets/' + event["thumbnail"] + '.jpg</thumbnail>' + "\n"
		xml = xml + "\t\t" + '<icon src="http://zap2it.tmsimg.com/assets/' + event["thumbnail"] + '.jpg" />' + "\n"

	xml = xml + "\t\t" + '<url>https://tvlistings.zap2it.com//overview.html?programSeriesId=' + event["seriesId"] + '&amp;tmsId=' + event["program"]["id"] + '</url>' + "\n"

	try:
	#if "season" in event:
		if event["program"]["season"] is not None:
			season = str(event["program"]["season"])
		if event["program"]["episode"] is not None:
			episode = str(event["program"]["episode"])

	except KeyError:
		print("no season for:" + event["program"]["title"])

	for category in event["filter"]:
		xml = xml + "\t\t" + '<category lang="en">' + html.unescape(category.replace('filter-','')) + '</category>' + "\n"

	#print season + "." + episode
	if ((int(season) != 0) and (int(episode) != 0)):
		xml = xml + "\t\t" + '<category lang="en">Series</category>' + "\n"
		xml = xml + "\t\t" + '<episode-num system="common">S' + str(season).zfill(2) + "E" + str(episode).zfill(2) + "</episode-num>" + "\n"
		xml = xml + "\t\t" + '<episode-num system="xmltv_ns">' + str(int(season) - 1) + "." + str(int(episode) - 1) + ".</episode-num>" + "\n"

	if event["program"]["id"][-4:] == "0000":
		xml = xml + "\t\t" + '<episode-num system="dd_progid">' + event["seriesId"] + '.' + event["program"]["id"][-4:] + '</episode-num>' + "\n"
	else:
		xml = xml + "\t\t" + '<episode-num system="dd_progid">' + event["seriesId"].replace('SH','EP') + '.' + event["program"]["id"][-4:] + '</episode-num>' + "\n"

	for flag in event["flag"]:
		if (flag == "New"):
			xml = xml + "\t\t<new />\n"
		elif (flag == "Finale"):
			xml = xml + "\t\t<last-chance />\n"
		elif (flag == "Premiere"):
			xml = xml + "\t\t<premiere />\n"

	for tag in event["tags"]:
		if (tag == "CC"):
			xml = xml + "\t\t" + '<subtitles type="teletext" />' + "\n"

	if event["rating"] is not None:
		xml = xml + "\t\t" + '<rating>' + "\n"
		xml = xml + "\t\t\t" + '<value>' + event["rating"] + '</value>' + "\n"
		xml = xml + "\t\t" + '</rating>' + "\n"

	xml = xml + "\t" + '</programme>'+"\n"
	return xml

def buildXMLDate(inputDateString):
	outputDate = inputDateString.replace('-','')
	outputDate = outputDate.replace('T','')
	outputDate = outputDate.replace(':','')
	outputDate = outputDate.replace('Z',' +0000')
	return outputDate

#Add Paramter options for config file and guide file
optConfigFile = './zap2itconfig.ini'
optGuideFile = 'xmlguide.xmltv'
optLanguage = 'en'
try:
	opts, args = getopt.getopt(sys.argv[1:],"hi:o:l:",["ifile=","ofile=","language="])
except getopt.GetoptError:
	print("zap2it-GuideScrape.py [-i <inputfile> ] [-o <outputfile>] [-l <language>")
	sys.exit()

for opt, arg in opts:
	if opt == '-h':
		print("zap2it-GuideScrape.py [-i <inputfile> ] [-o <outputfile>]")
		sys.exit()
	elif opt in ("-i","--ifile"):
		optConfigFile = arg
	elif opt in ("-o","--ofile"):
		optGuideFile = arg
	elif opt in ("-l","--language"):
		optLanguage = arg

print("Loading config: ", optConfigFile, " and outputting: ", optGuideFile)

#Configuration loading
Config = configparser.ConfigParser()
Config
Config.read(optConfigFile)


#Build authentication request
url = 'https://tvlistings.zap2it.com/api/user/login'
parameters = {
	'emailid': Config.get("creds","username"),
	'password': Config.get("creds","password"),
	'isfacebookuser': "false",
	'usertype': 0,
	'objectid': ''
}
data = urllib.parse.urlencode(parameters)
data = data.encode('ascii') # data should be bytes
req = urllib.request.Request(url,data)

#Load Authentication resposne from server
response = ""
response = urllib.request.urlopen(req).read()
zapVars = json.loads(response)

#Save authentication token from server
zapToken = "placeHolder"
zapToken = zapVars["token"]



#Find previous half hour from now()
currentTimestamp = time.time() - 60 * 60 * 24
halfHourOffset = currentTimestamp % (60 * 30)
closestTimestamp = currentTimestamp - halfHourOffset
closestTimestamp = int(closestTimestamp)
endTimestamp = closestTimestamp + (60*60*336)
channelXML = ""
programXML = ""
addChannels = True

while(closestTimestamp < endTimestamp):

	print("Load guide for time: " + str(closestTimestamp)  + ' - ' + str(endTimestamp))
	#build parameters for grid call
	parameters = {
		'Activity_ID': 1,
		'FromPage': "TV%20Guide",
		'AffiliateId': "gapzap",
		'token': zapToken,
		'aid': 'gapzap',
		'lineupId':'DFLTE',
		'timespan':3,
		'headendId': 'lineupId',
		'country': Config.get("prefs","country"),
		'device': '-',
		'postalCode': Config.get("prefs","zipCode"),
		'isOverride': "true",
		'time': closestTimestamp,
		'pref': 'm,p',
		'userId': '-'
	}
	data = urllib.parse.urlencode(parameters)
	url = "https://tvlistings.zap2it.com/api/grid?" + data
	req = urllib.request.Request(url)
	response = ""
	response = urllib.request.urlopen(req).read()
	guide = json.loads(response)
	for channel in guide["channels"]:
		if addChannels == True:
			channelXML = channelXML + buildXMLChannel(channel)
		for event in channel["events"]:
			programXML = programXML + buildXMLProgram(event,channel["channelId"])
	addChannels = False
	closestTimestamp = closestTimestamp + (60*60*3)

guideXML = '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
guideXML = guideXML + '<!DOCTYPE tv SYSTEM "xmltv.dtd">' + "\n\n"

guideXML = guideXML + '<tv source-info-url="http://tvlistings.zap2it.com/" source-info-name="zap2it.com" generator-info-name="zap2it-GuideScraping" generator-info-url="daniel@widrick.net">' + "\n"

guideXML = guideXML + channelXML
guideXML = guideXML + programXML

guideXML = guideXML + '</tv>' + "\n"

file = open(optGuideFile,"wb")
file.write(guideXML.encode('utf8'))
file.close()

#Write a Copy of the file with the current timestamp
dateTimeObj = datetime.datetime.now()
timestampStr = "." + dateTimeObj.strftime("%Y%m%d%H%M%s") + '.xmltv'
histGuideFile = timestampStr.join(optGuideFile.rsplit('.xmltv',1))
file = open(histGuideFile,"wb")
file.write(guideXML.encode('utf8'))
file.close()

#Clean old files
outputFilePath = os.path.abspath(optGuideFile)
outputDir = os.path.dirname(outputFilePath)
for item in os.listdir(outputDir):
	fileName = os.path.join(outputDir,item)
	if os.path.isfile(fileName) & item.endswith('.xmltv') & (os.stat(fileName).st_mtime < time.time() - (int(Config.get("prefs","historicalGuideDays")) * 86400)):
		os.remove(fileName)
sys.exit()
