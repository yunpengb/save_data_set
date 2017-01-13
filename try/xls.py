#=====================
#yunpeng draft 
#at 2017-1-9
#=====================

import xlwt
from datetime import datetime
from time import sleep
import xlrd
from xlutils.copy import copy

style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
    num_format_str='#,##0.00')
style1 = xlwt.easyxf(num_format_str='D-MMM-YY,HH:MM:SS')

sheetName = 'Test Results'
xls_now = 'tt5.xls'
aclr_list = [36,-51,-52]
aclr_list2=[40,-41,-42]

def add_empty_xls(sheet_name,xls_name):
    wbook = xlwt.Workbook()
    wsheet = wbook.add_sheet(sheet_name)
    wbook.save(xls_name)
    sleep(5)
    print "create empty xls .."

class ChangeExcel(object):    
    'add information to existing xls to save test results'
        
    def __init__(self,xlss):
        global newbook
        global newsheet
        global xls_in
        xls_in = xlss
        oldbook = xlrd.open_workbook(xls_in,formatting_info=True)
        newbook = copy(oldbook)
        newsheet = newbook.get_sheet(0)
        print 'xls open...'
        
    def add_head_line(self,x):
        newsheet.write(x,0, datetime.now(), style1)
        newsheet.write(x,1, 'Bandwidth')
        newsheet.write(x,2, 'Freq')
        newsheet.write(x,3, 'Tx_Power')
        newsheet.write(x,4, 'Aclr_Low')
        newsheet.write(x,5, 'Aclr_High')
        newsheet.write(x,6, 'Tx_EVM(64QAM)')
        newsheet.write(x,7, 'Rx_EVM')
        newbook.save(xls_in)
        print "add head line.."

    def add_title_ele(self,x,bandwidth,freq_in):
        newsheet.write(x,1,bandwidth)
        newsheet.write(x,2,freq_in)
        print "add config title to line.."

    def add_value(self,input_data,x,type):
        def ACLR():
            for i in range(3):
                newsheet.write(x,3+i,input_data[i])
        def TX_EVM():
            newsheet.write(x,6,input_data)
        def RX_EVM():
            newsheet.write(x,7,input_data)
        def func_None():
            print "cannot find func"
        func_dict = {'aclr':ACLR,'tx_evm':TX_EVM,'rx_evm':RX_EVM}
        def func(x):
            return func_dict.get(x, func_None)()
        func(type)
        print 'add result to line'
        
    def save_xls(self):
        newbook.save(xls_in)
        print "save xls ^_^"

add_empty_xls(sheetName,xls_now)

st = ChangeExcel(xls_now)
sleep(2)
st.add_head_line(0)

st.add_title_ele(1,'5','1932.5')
st.add_value(aclr_list,1,'aclr')
st.add_value(0.03,1,'tx_evm')
st.add_value(0.012,1,'rx_evm')

st.add_title_ele(2,'5','1932.5')
st.add_value(aclr_list,2,'aclr')
st.add_value(0.03,2,'tx_evm')
st.add_value(0.012,2,'rx_evm')

st.save_xls()

sleep(2)
st = ChangeExcel(xls_now)

st.add_head_line(4)
st.add_title_ele(5,'3','1999.5')
st.add_value(aclr_list2,5,'aclr')
st.add_value(0.03,5,'tx_evm')
st.add_value(0.012,5,'rx_evm')
st.save_xls()



