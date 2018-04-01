
import ConfigParser
import urllib, urllib2
import json


Config = ConfigParser.ConfigParser()
Config

Config.read("./zap2itconfig.ini")

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
response = urllib2.urlopen(req).read()

zapVars = json.loads(response)

zapToken = zapVars["token"]
print("Token: " + zapToken)
