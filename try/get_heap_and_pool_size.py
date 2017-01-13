#!/usr/bin/python
################################################################################
# @file                  $HeadURL: https://wrscmi.inside.nokiasiemensnetworks.com/isource/svnroot/BTS_T_RFMOD/Pegasus/trunk/Integration/PegasusSVN/CI_Tests/Files/Python_Scripts/get_heap_and_pool_size.py $
# @version               $LastChangedRevision: 27964 $
# @date                  $LastChangedDate: 2014-09-25 21:20:23 +0800 (周四, 25 九月 2014) $
# @author                $Author: jszczepa $
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
Example of use: get_heap_and_pool_size.py 192.168.255.69 FRGQ 30 10 c:\ftproot\ $
                get_heap_and_pool_size.py 192.168.255.69:2323 FRGQ 30 10 c:\ftproot\ $
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
    host_port = argv[1].split(':')
    rfName = argv[2]
    period = int(sys.argv[3])
    duration = (60*int(sys.argv[4]))/period;
    logDir = argv[5]
    prompt = argv[6]
    loop_count = 0
    try:
        host = host_port[0]
        port = host_port[1]
    except IndexError:
        port = '2323'
    outputXml = '%s%s.xml' % (logDir, rfName)
    minMaxDict = {'poolmin':0, 'poolmax':0, 'poolaverage':0, 'heapmin':0, 'heapmax':0, 'heapaverage':0}
    try:
        tn = telnetlib.Telnet(host, port)
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
        command = 'dumph -m ' + mainHeapAddress + '\n'
    testStartTime = time.time()
    for i in range(0, duration):
        timeBefore = int(time.time())
        try:
            tn.write(command)
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
    of.close()

if __name__ == '__main__':
    if(len(sys.argv) != 7):
        print('ERROR: Wrong number of parameters %d. Required six: RF module IP, RF module name which will be used as log file name, period between command execution in seconds, wanted measurement time in minutes, target directory for storing logs, prompt. Exiting script.' % (len(sys.argv)))
        sys.exit(1)
    HeapPoolSize(sys.argv)
