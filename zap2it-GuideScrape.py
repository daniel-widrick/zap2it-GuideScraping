
#Required libraries
import ConfigParser
import urllib, urllib2
import json
import time
import math


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
