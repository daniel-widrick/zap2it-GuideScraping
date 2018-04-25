
#Required libraries
import ConfigParser
import urllib, urllib2
import json
import time
import math
import cgi

def buildXMLChannel(channel):
	xml = ""
	xml = xml + '    <channel id="' +  channel["channelId"] + '">' + "\n"
	xml = xml + '      <display-name>' + channel["channelNo"] + " " + channel["callSign"] + '</display-name>' + "\n"
	xml = xml + '      <display-name>' + channel["channelNo"] + '</display-name>' + "\n"
	xml = xml + '      <display-name>' + channel["callSign"] + '</display-name>' + "\n"
	xml = xml + '    </channel>' + "\n"
	return xml

def buildXMLProgram(event,channelId):
	#2018-04-11T21:00:00Z
	#20180408120000 +0000
	xml = ""
	xml = xml + '    <programme start="' + buildXMLDate(event["startTime"]) + '" '
	xml = xml + 'stop="' + buildXMLDate(event["endTime"]) + '" channel="' + channelId + '">' + "\n"
	xml = xml + '      <title lang="en">' + event["program"]["title"].replace('&','+') + '</title>' + "\n"
	if event["program"]["shortDesc"] is None:
		event["program"]["shortDesc"] = "Unavailable"
	xml = xml + '      <desc lang="en">' + cgi.escape(event["program"]["shortDesc"]) + '</desc>' + "\n"
	xml = xml + '      <length units="minutes">' + event["duration"] + '</length>' + "\n"
	
	xml = xml + '    </programme>'+"\n"
	return xml

def buildXMLDate(inputDateString):
	outputDate = inputDateString.replace('-','')
	outputDate = outputDate.replace('T','')
	outputDate = outputDate.replace(':','')
	outputDate = outputDate.replace('Z',' +0000')
	return outputDate

#Configuration loading
Config = ConfigParser.ConfigParser()
Config
Config.read("./zap2itconfig.ini")

#Build authentication request
url = 'https://tvlistings.zap2it.com/api/user/login'
parameters = {
	'emailid': Config.get("creds","username"),
	'password': Config.get("creds","password"),
	'isfacebookuser': "false",
	'usertype': 0,
	'objectid': ''
}
data = urllib.urlencode(parameters)
req = urllib2.Request(url,data)

#Load Authentication resposne from server
response = ""
response = urllib2.urlopen(req).read()
zapVars = json.loads(response)

#Save authentication token from server
zapToken = "placeHolder"
zapToken = zapVars["token"]



#Find previous half hour from now()
currentTimestamp = time.time()
halfHourOffset = currentTimestamp % (60 * 30)
closestTimestamp = currentTimestamp - halfHourOffset
closestTimestamp = int(closestTimestamp)
endTimestamp = closestTimestamp + (60*60*48)
channelXML = ""
programXML = ""
addChannels = True

while(closestTimestamp < endTimestamp):

	print "Load guide for time: " + str(closestTimestamp)  + ' - ' + str(endTimestamp) + "\n"
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
	data = urllib.urlencode(parameters)
	url = "https://tvlistings.zap2it.com/api/grid?" + data
	req = urllib2.Request(url)
	response = ""
	response = urllib2.urlopen(req).read()
	guide = json.loads(response)
	for channel in guide["channels"]:
		if addChannels == True:
			channelXML = channelXML + buildXMLChannel(channel)
		for event in channel["events"]:
			programXML = programXML + buildXMLProgram(event,channel["channelId"])
	addChannels = False
	closestTimestamp = closestTimestamp + (60*60*3)
	print "Throttling api calls:...."
	time.sleep(3)


guideXML = '<?xml version="1.0" encoding="ISO-8859-1"?>' + "\n"

guideXML = guideXML + '<tv source-info-url="http://tvlistings.zap2it.com/" source-info-name="zap2it.com" generator-info-name="zap2it-GuideScraping" generator-info-url="daniel@widrick.net">' + "\n"

guideXML = guideXML + channelXML
guideXML = guideXML + programXML

guideXML = guideXML + "\n" + '</tv>'

file = open("xmlguide.xmltv","w")
file.write(guideXML.encode('utf8'))
file.close()
