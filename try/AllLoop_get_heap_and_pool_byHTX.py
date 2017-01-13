#!/usr/bin/python
################################################################################
# @file                  $HeadURL: https://wrscmi.inside.nokiasiemensnetworks.com/isource/svnroot/BTS_T_RFMOD/Pegasus/trunk/Integration/PegasusSVN/CI_Tests/Files/Python_Scripts/get_heap_and_pool_size.py $
# @version               $LastChangedRevision: 27964 $
# @date                  $LastChangedDate: 2014-09-25 21:20:23 +0800 ( 25 sep2014) $
# @author                $Author: Roger & Yunpeng
#
# Original author        TBD
# @module                CI
# @owner                 CI
#
# Copyright 2014 Nokia Networks. All rights reserved.
################################################################################

"""
Script collects heap and pool usage data from RF module.
As parameters it takes: RF module IP[:port], RF module name which will be used as log file name, period between command execution in seconds, wanted measurement time in minutes, target directory for storing logs, prompt
Example of use: AllLoop_get_heap_and_pool_byHTX.py 192.168.255.69 FHGA 90 6000 c:\ftproot\ @             means about 4 days
				
Tested with Python 2.7.2
"""

import sys
import os
import time
import datetime
import telnetlib
import string
import re
import xml.dom.minidom
from comtypes.client import CreateObject

HOST = "192.168.255.69"
TELNET_PORT = 2323
FRMON_PORT  = 200

FHGA_BW5 = '<SetItUpRequest><Unit><CommonName>FHGA</CommonName><UnitInChainId>0</UnitInChainId><Pipe id="0" nominalPower="36.99"><Carrier id="0"><Antenna id="0" testModelName="ETM1_1" nominalPower="36.99" scale="0" bw="5" mimoId="-1" cellId="1" ></Antenna></Carrier></Pipe><Pipe id="1" nominalPower="36.99"><Carrier id="0"><Antenna id="0" testModelName="ETM1_1" nominalPower="36.99" scale="0" bw="5" mimoId="-1" cellId="1" ></Antenna></Carrier></Pipe><RadioSpecific><GSM><DlControlPayloadOffset>0</DlControlPayloadOffset><ExtraNumberOfSlotsToCapture>1</ExtraNumberOfSlotsToCapture></GSM></RadioSpecific></Unit><Connections><SM2Unit><DeltaCorrection>202590</DeltaCorrection><SM_MasterPort><IP>192.168.255.16</IP></SM_MasterPort><SlavePort><UnitInChainId>0</UnitInChainId><Id>0</Id><UnitIP>192.168.255.69</UnitIP><FilterIP>192.168.255.70</FilterIP></SlavePort></SM2Unit></Connections></SetItUpRequest>'
FHGA_8X_BW5 = '<SetItUpRequest><Unit><CommonName>FHGA_8X</CommonName><UnitInChainId>0</UnitInChainId><Pipe id="0" nominalPower="36.99"><Carrier id="0"><Antenna id="0" testModelName="ETM1_1" nominalPower="36.99" scale="0" bw="5" mimoId="-1" cellId="1" ></Antenna></Carrier></Pipe><Pipe id="1" nominalPower="36.99"><Carrier id="0"><Antenna id="0" testModelName="ETM1_1" nominalPower="36.99" scale="0" bw="5" mimoId="-1" cellId="1" ></Antenna></Carrier></Pipe><RadioSpecific><GSM><DlControlPayloadOffset>0</DlControlPayloadOffset><ExtraNumberOfSlotsToCapture>1</ExtraNumberOfSlotsToCapture></GSM></RadioSpecific></Unit><Connections><SM2Unit><DeltaCorrection>202560</DeltaCorrection><SM_MasterPort><IP>192.168.255.16</IP></SM_MasterPort><SlavePort><UnitInChainId>0</UnitInChainId><Id>0</Id><UnitIP>192.168.255.69</UnitIP><FilterIP>192.168.255.70</FilterIP></SlavePort></SM2Unit></Connections></SetItUpRequest>'

def setUpHtx():
	global engine
	engine = CreateObject("{A09D5A99-F043-4A67-A71C-584758A527CF}")
	engine.setUnitTypeByName("FHGA_8X")

def setItUp(htx):
	returnStatus = htx.setUpConfiguration(FHGA_BW5)
	#htxHandle = engine
	#status  = 0
	return returnStatus

def FormatAndSaveXml(doc, resultXml):
	prettyDoc = doc.toxml(encoding='utf-8')
	prettyDoc = re.sub('(\n\s+)|(\n)', '', prettyDoc)
	doc = xml.dom.minidom.parseString(prettyDoc)
	prettyDoc = doc.toprettyxml(indent='    ', encoding='utf-8')
	text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
	prettyDoc = text_re.sub('>\g<1></', prettyDoc)
	fXml = open(resultXml, 'w')
	for lineTmp in prettyDoc:
		fXml.write(lineTmp)
	fXml.close()
	
def activateCarrier(htx):
	returnStatus = htx.activateCarrier(0,0,18300,300,-1)
	return returnStatus
	
def deactivateCarrier(htx):
	returnStatus = htx.deactivateCarrier(0,0,-1)
	return returnStatus
	
def SaveStatistics(counter, resultXml, minMaxDict):
	statisticDict = {}
	for keyTmp in minMaxDict.keys():
		statisticDict[keyTmp] = minMaxDict[keyTmp]
	statisticDict['poolaverage'] = statisticDict['poolaverage']/counter
	statisticDict['heapaverage'] = statisticDict['heapaverage']/counter
	doc = xml.dom.minidom.parse(resultXml)
	base = doc.getElementsByTagName('heapUsageTest')[0]
	for subnodeTmp in base.childNodes:
		if subnodeTmp.nodeType == base.ELEMENT_NODE and subnodeTmp.tagName == 'statistics':
			base.removeChild(subnodeTmp)
	statistics = doc.createElement('statistics')
	base.appendChild(statistics)    
	parameterList = ['pool', 'heap']
	for parameter in parameterList:
		xmlParameter = doc.createElement(parameter)
		for tmp in statisticDict.keys():
			if(re.search(parameter, tmp)):
				nodeTmp = re.sub(parameter, '' , tmp)
				tmpParameter = doc.createElement(nodeTmp)
				content = doc.createTextNode(str(statisticDict[tmp]))
				tmpParameter.appendChild(content)
				xmlParameter.appendChild(tmpParameter)
		statistics.appendChild(xmlParameter)
	FormatAndSaveXml(doc, resultXml)

def HeapPoolSize(argv):
	host = argv[1]
	rfName = "AllLoop_byRP1_" + argv[2]
	period = int(sys.argv[3])
	duration = (60*int(sys.argv[4]))/period;
	logDir = argv[5]
	prompt = argv[6]
	loop_count = 0
	outputXml = '%s%s.xml' % (logDir, rfName)
	minMaxDict = {'poolmin':0, 'poolmax':0, 'poolaverage':0, 'heapmin':0, 'heapmax':0, 'heapaverage':0}
	
	#build txt & makesure the mainHeapAddress
	try: 
		tn = telnetlib.Telnet(host, TELNET_PORT)
		tn.read_until('%s' % (prompt))
	except IOError:
		print 'Couldn`t connect to RFM by Telnet.'
		sys.exit('Telnet connection error!')
	of = open('%s%s.txt' % (logDir, rfName), 'w')
	doc = xml.dom.minidom.Document()
	base = doc.createElement('heapUsageTest')
	base.attributes['timestamp'] = re.sub(' ', 'T', re.sub('\.\d+','',str(datetime.datetime.now())))
	doc.appendChild(base)
	data = doc.createElement('data')
	base.appendChild(data)
	mainHeapAddress = '0'
	tn.write('dumph -l\n')
	s = tn.read_until('%s' % (prompt))
	s = s.split('\n')
	for line in s:
		if line.find('main') == -1:
			continue
		else:
			line2 = line.split()
			mainHeapAddress = line2[0]
		checkmainheap = 'dumph -m ' + mainHeapAddress + '\n'
	tn.close()
	
	#step0: Initialize HTX and write recode in txt
	try:
			setUpHtx()
		
			time.sleep(10)
		
			htxStatus = setItUp(engine)
			if(htxStatus == 0):
				print "\nHtx setup successfully!\n"
				of.write("********************* step 0:Initialize & Set_it_up HTX successfully! *********************\n")
		
	except:
			of.write("Exception ocurred in Initialize and Set_it_up HTX.\n")
			sys.exit('Exception ocurred in Initialize and Set_it_up HTX！')
	
	# loop begin
	testStartTime = time.time()
	for i in range(0, duration):
		timeBefore = int(time.time())
		
		#step1: active carrier in pipe1 by HTX and write recode in txt
		of.write('********************* begin loop %d *********************\n' % (i+1))
		try:
			of.write('********************* loop %d time, step 1:active carrier in pipe1 by HTX *********************\n' % (i+1))
			ActStatus = activateCarrier(engine)  
			of.write('ActStatus value is %s *********************\n' % ActStatus)
			
		except IOError:
			print 'Active carrier in pipe1 by HTX failed!'
			sys.exit('Active carrier in pipe1 by HTX failed!')
		
		time.sleep(10)
		
		#step2: check TxPower in Shell and write record in txt
		try: 
			tn = telnetlib.Telnet(host, TELNET_PORT)  
			#tn.set_debuglevel(2)
			tn.read_until('@')
		except IOError:
			print 'Couldn`t connect to RFM_Shell by Telnet.'
			sys.exit('Telnet to Shell connection error!')
		
		of.write('********************* loop %d time, step 2:check TxPower *********************\n' % (i+1),)
		check = "rfctrl txPower\n"  #check TxPower
		tn.write(check)
		pw = tn.read_until('@')
		of.write('Shell_input: %s\n' % check)
		of.write('Shell_output:\n %s \n' % pw)
		time.sleep(3)
		tn.close()
		
		#step3: deactive and destory carrier in pipe1 by HTX and write recode in txt
		try:  
			of.write('********************* loop %d time, step 3:Deactive carrier in pipe1 by HTX *********************\n' % (i+1))
			DeactStatus = deactivateCarrier(engine)
			of.write('DeactStatus value is %s *********************\n' % DeactStatus)
			
		except IOError:
			print 'Deactive carrier in pipe1 by HTX failed!'
			sys.exit('Deactive carrier in pipe1 by HTX failed!')
		
		#step4: check heap and pool on Shell
		try: 
			tn = telnetlib.Telnet(host, TELNET_PORT)  
			#tn.set_debuglevel(2)
			tn.read_until('%s' % (prompt))
		except IOError:
			print 'Couldn`t connect to RFM_Shell by Telnet.'
			sys.exit('Telnet to Shell connection error!')
		
		try:
			tn.write(checkmainheap)
			s = tn.read_until('%s' % (prompt))
			s = s.split('\n')
		except IOError:
			print 'Couldn`t execute shell command on RFM. Check Telnet connection.'
			break
		if(i != 0):
			doc = xml.dom.minidom.parse(outputXml)
			data = doc.getElementsByTagName('data')[0]
		item = doc.createElement('item')
		data.appendChild(item)
		elementDict = {}
		t = datetime.datetime.now()
		of.write('********************* loop %d time, step 4:check heap and pool useage *********************\n' % (i+1))
		of.write('%s;' % (re.sub('\.\d+','',str(t))))
		elementDict['time'] = str(int(time.time() - testStartTime))
		for line in s:
			if line.startswith('Total used'):
				line = line.strip()
				list = line.split()
				el = list[2]
				el = el.strip(',')
				of.write(el)
				elementDict['heapTotalUsed'] = el
				tn.write('pool\n')
				s = tn.read_until('%s' % (prompt))
				s = s.split('\n')
				for line in s:
					if line.strip().find('Max used')!=-1:
						line = string.replace(line, 'Max used  :', '').strip()
						line = line.split(' ')
						elementDict['poolMaxUsed'] = line[0]
						if(i==0):
							for keyTemp in minMaxDict.keys():
								if(re.search('pool', keyTemp)):
									minMaxDict[keyTemp] = int(line[0])
								elif(re.search('heap', keyTemp)):
									minMaxDict[keyTemp] = int(el)
						else:
							if(int(line[0]) < minMaxDict['poolmin']):
								minMaxDict['poolmin'] = int(line[0])
							if(int(line[0]) > minMaxDict['poolmax']):
								minMaxDict['poolmax'] = int(line[0])
							if(int(el) < minMaxDict['heapmin']):
								minMaxDict['heapmin'] = int(el)
							if(int(el) > minMaxDict['heapmax']):
								minMaxDict['heapmax'] = int(el)
							minMaxDict['poolaverage'] += int(line[0])
							minMaxDict['heapaverage'] += int(el)
						elementDict['poolMaxUsedPercent'] = re.sub('%', '', line[1].strip('(').strip(')'))
						line = ';' + line[0] + ';' + line[1].strip('(').strip(')')
						print('%s;%s%s' % (re.sub('\.\d+','',str(t)), el, line))
						of.write(line)
						for element in elementDict.keys():
							elementTmp = doc.createElement(element)
							elementTmpContent = doc.createTextNode(elementDict[element])
							elementTmp.appendChild(elementTmpContent)
							item.appendChild(elementTmp)
						FormatAndSaveXml(doc, outputXml)
						of.write('\n')
		os.fsync(of.fileno())
		of.flush()
		loop_count += 1
		SaveStatistics(loop_count, outputXml, minMaxDict)
		timeAfter = int(time.time())
		timeDiff = timeAfter - timeBefore
		if(period > timeDiff):
			time.sleep(period - timeDiff)
		else:
			time.sleep(1)
		tn.close()
		of.write('********************* End loop %d *********************\n' % (i+1))
	of.close()
	

if __name__ == '__main__':
	if(len(sys.argv) != 7):
		print('ERROR: Wrong number of parameters %d. Required six: RF module IP, RF module name which will be used as log file name, period between command execution in seconds, wanted measurement time in minutes, target directory for storing logs, prompt. Exiting script.' % (len(sys.argv)))
		sys.exit(1)
	HeapPoolSize(sys.argv)