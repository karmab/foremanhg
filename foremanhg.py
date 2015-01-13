#!/usr/bin/python

"""foreman script to create hostgroups, associate classes to them, and override values globally or at hostgroup level"""

import ConfigParser
import json
import optparse
import os
import requests
import simplejson 
import sys
from time import strftime

__author__ = "Karim Boumedhel"
__credits__ = ["Karim Boumedhel"]
__license__ = "GPL"
__version__ = "1.1"
__maintainer__ = "Karim Boumedhel"
__email__ = "karim.boumedhel@gmail.com"
__status__ = "Production"

usage = "foreman script to create hostgroups, associate classes to them, and override values globally or at hostgroup level"
version = "0.1"
parser = optparse.OptionParser("Usage: %prog [options]",version=version)
parser.add_option('-b', '--backup', dest='backup', action='store_true', help='Make backup of the generated key file')
parser.add_option('-c', '--classname', dest='classname', type='string', help='Specify Class')
parser.add_option('-k', '--keyfile', dest='keyfile', type='string', default='foremanhg.keys' , help='Use file as origin of keys (smart class parameters). If not specified, defaults to foremanhg.keys')
parser.add_option('-i', '--initialize', dest='initialize', action='store_true', default=False, help='Set default parameters. Restablish parameters starting with $ to not overriden')
parser.add_option('-l', '--listclients', dest='listclients', action='store_true', help='List clients')
parser.add_option('-n', '--new', dest='new', action='store_true', help='Create hostgroups as specified in the plan file')
parser.add_option('-o', '--override', dest='override', action='store_true', help='Create smart class parameters overrides for keys found in key file and belonging to classes of the hostgroups created as part of the plan file')
parser.add_option('-p', '--planfile', dest='planfile', type='string', default = 'foremanhg.plan', help='Use file as origin of plan. If not specified, defaults to foremanhg.plan')
parser.add_option('-r', '--randomness', dest='randomness', type='int', default = 16, help='Use this length of the randomly generated parameters.Default to 16')
parser.add_option('-d', '--classdetails', dest='classdetails', action='store_true', help='Get details of a given class')
parser.add_option('-C', '--client', dest='client', type='string', help='Specify Client')
parser.add_option('-D', '--delete', dest='delete', action='store_true', help='Delete hostgroups as listed in plan file')
parser.add_option('-9', '--switchclient', dest='switchclient', type="string", help='Switch default client')

(options, args) = parser.parse_args()
backup = options.backup
listclients = options.listclients
switchclient = options.switchclient
client = options.client
classdetails = options.classdetails
classname = options.classname
override = options.override
delete = options.delete
planfile = options.planfile
keyfile = options.keyfile
initialize = options.initialize
randomness = options.randomness
new = options.new
classesbygroup = {}
groups = None

#helper functions
def foremando(url, actiontype=None, postdata=None, user=None, password=None):
    headers = {'content-type': 'application/json', 'Accept': 'application/json' }
    #get environments
    if user and password:
        user     = user.encode('ascii')
        password = password.encode('ascii')
    if actiontype == 'POST':
        r = requests.post(url,verify=False, headers=headers,auth=(user,password),data=json.dumps(postdata))
    elif actiontype == 'DELETE':
        r = requests.delete(url,verify=False, headers=headers,auth=(user,password),data=postdata)
    elif actiontype == 'PUT':
        r = requests.put(url,verify=False, headers=headers,auth=(user,password),data=postdata)
    else:
        r = requests.get(url,verify=False, headers=headers,auth=(user,password))
    try:
        result = r.json()
        result = eval(str(result))
        return result
    except:
        return None

def foremangetid(protocol, host, port, user, password, searchtype, searchname):
    if searchtype == 'puppet':
        url = "%s://%s:%s/api/v2/smart_proxies?type=%s"  % (protocol, host, port, searchtype)
        result = foremando(url)
        return result[0]['smart_proxy']['id']
    else:
        url = "%s://%s:%s/api/v2/%s/%s" % (protocol, host, port, searchtype, searchname)
        result = foremando(url=url, user=user, password=password)
    if searchtype == 'ptables':
        shortname = 'ptable'
    elif searchtype.endswith('es') and searchtype != 'architectures':
        shortname = searchtype[:-2]
    else:
        shortname = searchtype[:-1]
    try:
        return str(result[shortname]['id'])
    except:
        return str(result['id'])

#VM CREATION IN FOREMAN
class Foreman:
    def __init__(self, host, port, user, password,secure=False):
        host = host.encode('ascii')
        port = str(port).encode('ascii')
        user = user.encode('ascii')
        password = password.encode('ascii')
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        if secure:
            self.protocol = 'https'
        else:
            self.protocol = 'http'

    def override(self, name, parameter, parameterid=None ):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        if not parameterid:
            url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, name)
            res= foremando(url=url, user=user, password=password)
            classparameters = res['smart_class_parameters']
            for param in classparameters:
                if param['parameter'] == parameter:
                    parameterid = param['id']
                    break
            if parameterid == None:
                print "parameterid for parameter %s of class %s not found" % (parameter, name)
                return False
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parameter)
            postdata = {}
            postdata["smart_class_parameter"] = { "override": True }
            postdata = simplejson.dumps(postdata)
            res = foremando(url=parameterurl, actiontype="PUT", postdata=postdata, user=user, password=password)
            print "parameter %s of class %s set overriden" % (parameter, name)

    def removeoverride(self, name, parameter, parameterid=None ):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        if not parameterid:
            url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, name)
            res= foremando(url=url, user=user, password=password)
            classparameters = res['smart_class_parameters']
            for param in classparameters:
                if param['parameter'] == parameter:
                    parameterid = param['id']
                    break
            if parameterid == None:
                print "parameterid for parameter %s of class %s not found" % (parameter, name)
                return False
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parameter)
            postdata = {}
            postdata["smart_class_parameter"] = { "override": False }
            postdata = simplejson.dumps(postdata)
            res = foremando(url=parameterurl, actiontype="PUT", postdata=postdata, user=user, password=password)
            print "parameter %s of class %s set as not overriden" % (parameter, name)

    def getparameterid(self, classname, parameter):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, classname)
        res= foremando(url=url, user=user, password=password)
        classparameters = res['smart_class_parameters']
        for param in classparameters:
            if param['parameter'] == parameter:
                parameterid = param['id']
                break
        return parameterid

    def getclassid(self, classname):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, classname)
        res= foremando(url=url, user=user, password=password)
        return res['id']

    def addclass(self, hostname, classname):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        hostid = self.gethostid(hostname)
        classid = self.getclassid(classname)
        url = "%s://%s:%s/api/v2/hosts/%s/puppetclass_ids" % (protocol, host, port, hostid)
        postdata = { "puppetclass_id": classid ,  "hostgroup_id" : hostid }
        foremando(url=url, actiontype="POST", postdata=postdata, user=user, password=password)
        print "class %s added to host %s " % (classname, hostname)

    def gethostgroupid(self, hostgroup):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/hostgroups/%s" % (protocol, host, port, hostgroup)
        res= foremando(url=url, user=user, password=password)
        return res['id']

    def gethostid(self, hostname):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/hosts/%s" % (protocol, host, port, hostname)
        res= foremando(url=url, user=user, password=password)
        return res['id']

    def getpuppetclassid(self, puppetclass):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        url = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, puppetclass)
        res= foremando(url=url, user=user, password=password)
        return res['id']

    def createhostgroup(self, hostgroup, classes=None):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        hostgroupurl = "%s://%s:%s/api/v2/hostgroups" % (protocol, host, port)
        postdata = {}
        if '/' in hostgroup:
            parent,son = hostgroup.split('/')
            parentid = self.gethostgroupid(parent)
            postdata["hostgroup"] =  { "name" : son , "parent_id" : parentid }
        else:
            postdata["hostgroup"] =  { "name" : hostgroup }
        res  = foremando(url=hostgroupurl, actiontype="POST", postdata=postdata, user=user, password=password)
        if not 'id' in res.keys():
            print "hostgroup %s allready existing" % hostgroup  
            return None
        hostgroupid =res['id']
        print "hostgroup %s created" % hostgroup
        if classes:
            #for classname in map(str.strip, classes.split(';')):
            for classname in classes:
                classid = self.getclassid(classname)
                url = "%s://%s:%s/api/v2/hostgroups/%s/puppetclass_ids" % (protocol, host, port, hostgroupid)
                postdata = { "puppetclass_id": classid ,  "hostgroup_id" : hostgroupid }
                res  = foremando(url=url, actiontype="POST", postdata=postdata, user=user, password=password)
                print "class %s added to hostgroup %s " % (classname, hostgroup)
        return hostgroupid

    def deletehostgroup(self, hostgroup):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        hostgroupurl = "%s://%s:%s/api/v2/hostgroups/%s" % (protocol, host, port, hostgroup)
        foremando(url=hostgroupurl, actiontype="DELETE", user=user, password=password)
        print "hostgroup %s deleted" % (hostgroup)

    def getclassparameters(self, classname):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        parametersinfo = {}
        parametersurl = "%s://%s:%s/api/v2/puppetclasses/%s" % (protocol, host, port, classname)
        res = foremando(url=parametersurl, user=user, password=password)
        parameters = res['smart_class_parameters']
        for parameter in parameters:
            parametername, parameterid = parameter['parameter'],parameter['id']
            parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parametername)
            res = foremando(url=parameterurl, user=user, password=password)
            parametertype = res['parameter_type']
            defaultvalue  = res['default_value']
            parametersinfo[parametername]={ 'id':parameterid,'defaultvalue':defaultvalue, 'type':parametertype}
        return parametersinfo

    def overridehostgroupparameter(self, hostgroup, parametername, parameterid, value):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        overrideurl = "%s://%s:%s/api/v2/smart_class_parameters/%s/override_values" % (protocol, host, port, parameterid)
        postdata = { "override_value": { "match":"hostgroup=%s" % hostgroup } }
        postdata["override_value"]["value"] = value
        foremando(url=overrideurl, actiontype="POST", postdata=postdata, user=user, password=password)
        print "hostgroup:%s parameter:%s value:%s" % (hostgroup, parametername,value)

    def overridehostparameter(self, hostname, parametername, parameterid, value):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        overrideurl = "%s://%s:%s/api/v2/smart_class_parameters/%s/override_values" % (protocol, host, port, parametername)
        postdata = { "override_value": { "match":"fqdn=%s" % hostname } }
        postdata["override_value"]["value"] = value
        foremando(url=overrideurl, actiontype="POST", postdata=postdata, user=user, password=password)
        print "parameter %s overriden for %s with value %s" % (parametername, hostname, value)

    def setdefaultvalue(self, parameter, parameterid, value):
        host, port, user , password, protocol = self.host, self.port, self.user, self.password, self.protocol
        parameterurl = "%s://%s:%s/api/v2/smart_class_parameters/%s-%s" % (protocol, host, port, parameterid, parameter)
        postdata = {}
        postdata["smart_class_parameter"] = { "default_value": value}
        postdata = simplejson.dumps(postdata)
        foremando(url=parameterurl, actiontype="PUT", postdata=postdata, user=user, password=password)
        print "parameter %s set to value %s" % (parameter, value)

foremanconffile = "%s/foreman.ini" %(os.environ['HOME'])
if not os.path.exists(foremanconffile):
    print "Missing %s in your  home directory.Check documentation" % foremanconffile
    sys.exit(1)
try:
    c = ConfigParser.ConfigParser()
    c.read(foremanconffile)
    foremans = {}
    default = {}
    for cli in c.sections():
        for option in  c.options(cli):
            if cli=="default":
                default[option] = c.get(cli,option)
                continue
            if not foremans.has_key(cli):
                foremans[cli] = {option : c.get(cli,option)}
            else:
                foremans[cli][option] = c.get(cli,option)
except:
    print 'Error parsing foreman.ini'
    os._exit(1)

if listclients:
    print "Available Clients:"
    for cli in  sorted(foremans):
        print cli
    if default.has_key("client"):
        print "Current default client is: %s" % (default["client"])
    sys.exit(0)

if switchclient:
    if switchclient not in foremans.keys():
        print "Client not defined...Leaving"
    else:
        mod = open(foremanconffile).readlines()
        f = open(foremanconffile, "w")
        for line in mod:
            if line.startswith("client"):
                f.write("client=%s\n" % switchclient)
            else:
                f.write(line)
        f.close()
        print "Default Client set to %s" % (switchclient)
    sys.exit(0)

if not client:
    try:
        client = default['client']
    except:
        print "No client defined as default in your ini file or specified in command line"
        os._exit(1)

try:
	foremanhost     = foremans[client]["host"]
	foremanport     = foremans[client]["port"]
	foremanuser     = foremans[client]["user"]
	foremanpassword = foremans[client]["password"]
except KeyError,e:
	print "Problem parsing foreman ini file:Missing parameter %s" % e
	os._exit(1)

try:
	foremanhgplan=open(planfile).readlines()
except IOError:
	print "Unable to open plan file"
	os._exit(1)

classesbygroup = {}
for item in foremanhgplan:
	if not item.startswith('#') and not item.startswith(';') and not item.startswith('//') and len(item.split('=')) == 2:
                key, value = item.split('=')[0].strip(), item.split('=')[1].strip()
		if key == 'basegroup':
			basegroup = value
		elif key == 'groups':
			groups = [x.strip() for x in value.split(';')]
               	elif key in groups:
                        classesbygroup[key] = [x.strip() for x in value.split(';')]

f = Foreman(foremanhost,foremanport,foremanuser, foremanpassword,secure=True)

if classdetails and classname:
    parameters = f.getclassparameters(classname)
    for p in sorted(parameters):
        print "%s %s %s %s" % ( p, parameters[p]['id'], parameters[p]['type'], parameters[p]['defaultvalue'] )
    sys.exit(0)

#OVERRIDE FOR CLASS
if override and classname:
    parameters = f.getclassparameters(classname)
    for p in sorted(parameters):
        f.override(classname, p)
    sys.exit(0)

#INCLUDE BASEGROUP
if groups and basegroup:
	newgroups = []
	for group in groups:
		newgroup = "%s/%s" % (basegroup, group)
		newgroups.append(newgroup)
		if classesbygroup.has_key(group):
			classesbygroup[newgroup] = classesbygroup[group]
			del classesbygroup[group]
	groups = newgroups

if delete and groups:
	for group in groups:
		f.deletehostgroup(group)
	sys.exit(0)

if groups and new:
	for group in groups:
		classes = None
		if classesbygroup.has_key(group):
			classes = classesbygroup[group]
        	f.createhostgroup(group, classes)


if groups and override:
	providedparams = {}
	if os.path.isfile(keyfile):
		foremanhgkeys=open(keyfile).readlines()
		for item in foremanhgkeys:
			if not item.startswith('#') and not item.startswith(';') and not item.startswith('//') and '=' in item :
				key = item.split('=')[0].strip()
				value = '='.join(item.split('=')[1:]).strip().replace('\n','')
				if value == '':
					value = os.urandom(randomness).encode('hex')
				elif value == "BLANK":
					value = ''
				providedparams[key] = value.replace('\n','')	
		for group in groups:
			if classesbygroup.has_key(group):
				classnames = classesbygroup[group]
				for classname in classnames:
					parameters = f.getclassparameters(classname)
		        		for parameter in parameters:
						parameterid, parametertype = parameters[parameter]['id'], parameters[parameter]['type']
						defaultvalue = parameters[parameter]['defaultvalue']
						if str(defaultvalue).startswith('$') and not parameter in providedparams.keys():
							f.removeoverride(classname,parameter)
							continue
						f.override(classname,parameter)
						if parameter in providedparams.keys():
							defaultvalue       = providedparams[parameter] 
							if initialize:
								f.setdefaultvalue(parameter ,parameterid, defaultvalue)
							else:
								f.overridehostgroupparameter(group, parameter, parameterid, defaultvalue)

if backup and groups and override and len(providedparams) > 0:
	print "generating backup file foremanhg.keys_%s" % strftime("%Y%m%d_%H%M") 
	#GENERATE PARAMETERS USED 
	f = open("foremanhg.keys_%s" % strftime("%Y%m%d_%H%M"),'w')
	for parameter in sorted(providedparams):
		f.write("%s=%s\n" % (parameter, providedparams[parameter]))
	f.close()
