#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import zipfile
import StringIO
import os.path
from string import strip,join
import re
import logging  
import logging.handlers
import datetime
import time
import calendar
from abc import ABCMeta
import xml
from xml.etree import ElementTree as ET
import sqlite3

def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    # value为传入的值为时间戳(整形)，如：1332888820
    value = time.localtime(value)
    ## 经过localtime转换后变成
    ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
    # 最后再经过strftime函数转换为正常日期格式。
    dt = time.strftime(format, value)
    return dt
 
def datetime_timestamp(dt):
     #dt为字符串
     #中间过程，一般都需要将字符串转化为时间数组
     time.strptime(dt, '%Y-%m-%d %H:%M:%S')
     ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=-1)
     #将"2012-03-28 06:53:40"转化为时间戳
     s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S'))
     return int(s)

LOG_FILE = 'TimSpan.log'
handler = logging.handlers.RotatingFileHandler(os.path.join( os.path.realpath(os.path.curdir),LOG_FILE), maxBytes = 1024*1024, backupCount = 5)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('sf')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

         
CurrencyCodesRecognized = {
            'AUD':('AUD',	'A',	'Australian Dollar'),
            'GBP':('GBP',	'L',	'British Pound'),
            'CAD':('CAD',	'C',	'Canadian Dollar'),
            'EUR':('EUR',	'E',	'Euro'),
            'FRF':('FRF',	'F',	'French Franc'),
            'DEM':('DEM',	'D',	'German Deutschemark'),
            'HKD':('HKD',	'H',	'Hong Kong Dollar'),
            'HUF':('HUF',	'U',	'Hungarian Forint'),
            'ITL':('ITL',	'I',	'Italian Lira'),
            'JPY':('JPY',	'Y',	'Japanese Yen'),
            'MXN':('MXN',	'P',	'Mexican Peso'),
            'NZD':('NZD',	'Z',	'New Zealand Dollar'),
            'NOK':('NOK',	'N',	'Norwegian Kroner'),
            'SGD':('SGD',	'G',	'Singaporean Dollar'),
            'ESP':('ESP',	'T',	'Spanish Peseta'),
            'ZAR':('ZAR',	'R',	'South African Rand'),
            'SEK':('SEK',	'K',	'Swedish Kroner'),
            'CHF':('CHF',	'S',	'Swiss Franc'),
            'USD':('USD',	'$',	'US Dollar') }        
            
class TypeRecords:
    Title_Type0RecordsStandard = ('Length','From','To','Datatype','Format','Description and Comments')
    def __init__(self,Strut_TypeRecordsStandard):
        self.changeStrut_Type0RecordsStandard(Strut_TypeRecordsStandard)
        
    def __call__(self,line):
        self.lineString = line
        return self.parseRecord()

    def changeStrut_Type0RecordsStandard(self,Strut_TypeRecordsStandard):
        self.Strut_Type0RecordsStandard = Strut_TypeRecordsStandard
        self.recordDict = self.dealRecordDict()
        self.recordTotelLength = self.getFMTTotelLength()
        
    def parseRecord(self):
        raise NotImplementedError( "virtualMethod is virutal! Must be overwrited." )
    
    def getRecordFieldStr(self,idx):
        return strip(self.lineString[self.recordDict[idx]['From']-1:self.recordDict[idx]['To']])
    
    def dealRecordDict(self):
        m_d = {}
        for k,v in self.Strut_Type0RecordsStandard.items():
            m_d[k]= dict(zip(self.Title_Type0RecordsStandard,v))
        return m_d
        
    def getFMTTotelLength(self):
        m_sum = 0
        for i in range(len(self.recordDict)):
            m_sum +=  self.recordDict[i]['Length']
        return m_sum

  
class Type0RecordsS(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', '2.0', 'Record ID - "0 "'),
            1:(6, 3, 8, 'AN', 'X(2)', 'Exchange Complex (Clearing Organization or Cross-Margin Agreement) Acronym'),
            2:(8, 9, 16, 'N', '9(8)', 'Business Date as CCYYMMDD'),
            3:(1, 17, 17, 'AN', 'X', 'Settlement (S) or Intraday (I) Flag'),
            4:(2, 18, 19, 'AN', 'X(2)', 'File Identifier - (E for "Early" Settlement, F for "Final" Settlement, C for "Complete" Settlement, or other value)'),
            5:(4, 20, 23, 'N', '9(4)', 'Business Time as HHMM'),
            6:(8, 24, 31, 'N', '9(8)', 'File Creation Date as CCYYMMDD'),
            7:(4, 32, 35, 'N', '9(4)', 'File Creation Time as HHMM'),
            8:(2, 36, 37, 'AN', 'X(2)', 'File Format - U2 for Expanded Unpacked, UP for Paris Expanded Format'),
            9:(1, 38, 38, 'AN', 'X', 'Gross/Net-Margining Indicator (applies to clearing-level processing)'),
            10:(1, 39, 39, 'AN', 'X', 'Overall Limit Option Value (Cap Available Net Option Value) Flag'),
            11:(5, 40, 44, 'AN', 'X(5)', 'Business Function (CLR or blank for Normal Clearing and XMRGN for Cross Margining)'),
            12:(6, 45, 50, '-', '-', 'Filler'),
            13:(1, 51, 51, 'AN', 'X', 'Clearing or Customer Code - A for Clearing, or blank or C for Customer'),
            14:(1, 52, 52, '-', '-', 'Filler'),
            15:(5, 53, 57, 'AN', 'X(5)', 'Clearing or Customer Acronym - blank or CUST for Customer, or CLR for Clearing'),
            16:(1, 58, 58, '-', '-', 'Filler'),
            17:(1, 59, 59, 'AN', 'X', 'Account Type Code. For Clearing accounts, blank or N for Normal, or M for Member. For Customer accounts, blank or H for Hedger, M for Member, S for Speculator.'),
            18:(1, 60, 60, '-', '-', 'Filler'),
            19:(5, 61, 65, 'AN', 'X(5)', 'Account Type Acronym. For Clearing accounts, blank or NRML for Normal, or MBR for Member. For Customer accounts, blank or HEDGE for Hedger, MBR for Member, SPEC for Speculator.'),
            20:(1, 66, 66, '-', '-', 'Filler'),
            21:(1, 67, 67, 'AN', 'X', 'Performance Bond Class Code - blank or 1 for Core, or 2 for Reserve'),
            22:(1, 68, 68, '-', '-', 'Filler'),
            23:(5, 69, 73, 'AN', 'X(5)', 'Performance Bond Class Acronym - blank or CORE for Core, or RESRV for Reserve'),
            24:(1, 74, 74, '-', '-', 'Filler'),
            25:(1, 75, 75, 'AN', 'X', 'Maintenance or Initial Code - blank or M for Maintenance, or I for Initial'),
            26:(1, 76, 76, '-', '-', 'Filler'),
            27:(5, 77, 81, 'AN', 'X(5)', 'Maintenance or Initial Acronym - blank or MAINT for Maintenance, or INIT for Initial'),
            28:(51, 82, 132, '-', '-', 'Filler'),
            }
    
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)
        
    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Complex Acronym'] = self.getRecordFieldStr(1)
        rt['Business Date'] = self.getRecordFieldStr(2)
        rt['Settlement (S) or Intraday (I) Flag'] = self.getRecordFieldStr(3)
        rt['File Identifier'] = self.getRecordFieldStr(4)
        rt['Business Time'] = self.getRecordFieldStr(5)
        rt['File Creation Date'] = self.getRecordFieldStr(6)
        rt['File Creation Time'] = self.getRecordFieldStr(7)
        rt['File Format'] = self.getRecordFieldStr(8)
        rt['Gross/Net-Margining Indicator'] = self.getRecordFieldStr(9)
        rt['Overall Limit Option Value'] = self.getRecordFieldStr(10)
        rt['Business Function'] = self.getRecordFieldStr(11)
        #rt['Filler'] = self.getRecordFieldStr(12)
        rt['Clearing or Customer Code'] = self.getRecordFieldStr(13)
        #rt['Filler'] = self.getRecordFieldStr(14)
        rt['Clearing or Customer Acronym'] = self.getRecordFieldStr(15)
        #rt['Filler'] = self.getRecordFieldStr(16)
        rt['Account Type Code'] = self.getRecordFieldStr(17)
        #rt['Filler'] = self.getRecordFieldStr(18)
        rt['Account Type Acronym'] = self.getRecordFieldStr(19)
        #rt['Filler'] = self.getRecordFieldStr(20)
        rt['Performance Bond Class Code'] = self.getRecordFieldStr(21)
        #rt['Filler'] = self.getRecordFieldStr(22)
        rt['Performance Bond Class Acronym'] = self.getRecordFieldStr(23)
        #rt['Filler'] = self.getRecordFieldStr(24)
        rt['Maintenance or Initial Code'] = self.getRecordFieldStr(25)
        #rt['Filler'] = self.getRecordFieldStr(26)
        rt['Maintenance or Initial Acronym'] = self.getRecordFieldStr(27)
        #rt['Filler'] = self.getRecordFieldStr(28)
        return rt


class Type1RecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {
            0:(2, 1, 2,'AN','X(2)',     'Record ID - "1 "'),
            1:(3, 3, 5,'AN','X(3)',     'Exchange Acronym'),
            2:(2, 6, 7,'-','-',         'Filler'),
            3:(2, 8, 9,'AN','X(2)',     'Exchange Code'),
            4:(123, 10, 132,'-','-',    'Filler')
    }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Exchange Code'] = self.getRecordFieldStr(3)
        return rt

class Type2RecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X', 'Record ID - "2 "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(1, 6, 6, '-', '-', 'Filler'),
            3:(6, 7, 12, 'AN', 'X(6)', 'Combined Commodity Code'),
            4:(1, 13, 13, 'N', '9.0', 'Risk Exponent'),
            5:(3, 14, 16, 'AN', 'X(3)', 'Performance Bond Currency ISO Code'),
            6:(1, 17, 17, 'AN', 'X', 'Performance Bond Currency Code'),
            7:(1, 18, 18, 'AN', 'X', 'Option Margin Style (Valuation Method) -- P for premium-style, F for futures-style, or blank -- if blank, premium-style is assumed.'),
            8:(1, 19, 19, 'AN', 'X', 'Limit Option Value (Cap Available Net Option Value) Flag - Y, N or blank -- if blank, no is assumed.'),
            9:(1, 20, 20, 'AN', 'X', 'Combination Margining Method Flag - S for split-allocation, D for delta-split-allocation, M for modified split-allocation, or blank.'),
            10:(2, 21, 22, '-', '-', 'Filler'),
            11:(10, 23, 32, 'AN', 'X(10)', 'Commodity (Product) Code 1'),
            12:(3, 33, 35, 'AN', 'X', 'Contract Type 1 - FUT, PHY, CMB, OOF, OOP, OOC'),
            13:(1, 36, 36, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            14:(1, 37, 37, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            15:(1, 38, 38, '-', '-', 'Filler'),
            16:(10, 39, 48, 'AN', 'X(10)', 'Commodity (Product) Code 2'),
            17:(3, 49, 51, 'AN', 'X', 'Contract Type 2 - FUT, PHY, CMB, OOF, OOP, OOC'),
            18:(1, 52, 52, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            19:(1, 53, 53, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            20:(1, 54, 54, '-', '-', 'Filler'),
            21:(10, 55, 64, 'AN', 'X(10)', 'Commodity (Product) Code 3'),
            22:(3, 65, 67, 'AN', 'X', 'Contract Type 3 - FUT, PHY, CMB, OOF, OOP, OOC'),
            23:(1, 68, 68, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            24:(1, 69, 69, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            25:(1, 70, 70, '-', '-', 'Filler'),
            26:(10, 71, 80, 'AN', 'X(10)', 'Commodity (Product) Code 4'),
            27:(3, 81, 83, 'AN', 'X', 'Contract Type 4 - FUT, PHY, CMB, OOF, OOP, OOC'),
            28:(1, 84, 84, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            29:(1, 85, 85, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            30:(1, 86, 86, '-', '-', 'Filler'),
            31:(10, 87, 96, 'AN', 'X(10)', 'Commodity (Product) Code 5'),
            32:(3, 97, 99, 'AN', 'X', 'Contract Type 5 - FUT, PHY, CMB, OOF, OOP, OOC'),
            33:(1, 100, 100, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            34:(1, 101, 101, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            35:(1, 102, 102, '-', '-', 'Filler'),
            36:(10, 103, 112, 'AN', 'X(10)', 'Commodity (Product) Code 6'),
            37:(3, 113, 115, 'AN', 'X', 'Contract Type 6 - FUT, PHY, CMB, OOF, OOP, OOC'),
            38:(1, 116, 116, 'N', '9.0', 'Risk Array Value Decimal Locator -- optional, if blank 0 is assumed'),
            39:(1, 117, 117, 'AN', 'X', 'Risk Array Value Decimal Sign -- \'+ \'or \'-\', -- optional, any other value means \'+ \''),
            40:(15, 118, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        #rt['Filler'] = self.getRecordFieldStr(2)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(3)
        rt['Risk Exponent'] = self.getRecordFieldStr(4)
        rt['Performance Bond Currency ISO Code'] = self.getRecordFieldStr(5)
        rt['Performance Bond Currency Code'] = self.getRecordFieldStr(6)
        rt['Option Margin Style (Valuation Method)'] = self.getRecordFieldStr(7)
        rt['Limit Option Value (Cap Available Net Option Value) Flag'] = self.getRecordFieldStr(8)
        rt['Combination Margining Method Flag'] = self.getRecordFieldStr(9)
        #rt['Filler'] = self.getRecordFieldStr(10)
        rt['Commodity (Product) Code 1'] = self.getRecordFieldStr(11)
        rt['Contract Type 1'] = self.getRecordFieldStr(12)
        rt['Risk Array Value Decimal Locator 1'] = self.getRecordFieldStr(13)
        rt['Risk Array Value Decimal Sign 1'] = self.getRecordFieldStr(14)
        #rt['Filler'] = self.getRecordFieldStr(15)
        rt['Commodity (Product) Code 2'] = self.getRecordFieldStr(16)
        rt['Contract Type 2'] = self.getRecordFieldStr(17)
        rt['Risk Array Value Decimal Locator 2'] = self.getRecordFieldStr(18)
        rt['Risk Array Value Decimal Sign 2'] = self.getRecordFieldStr(19)
        #rt['Filler'] = self.getRecordFieldStr(20)
        rt['Commodity (Product) Code 3'] = self.getRecordFieldStr(21)
        rt['Contract Type 3'] = self.getRecordFieldStr(22)
        rt['Risk Array Value Decimal Locator 3'] = self.getRecordFieldStr(23)
        rt['Risk Array Value Decimal Sign 3'] = self.getRecordFieldStr(24)
        #rt['Filler'] = self.getRecordFieldStr(25)
        rt['Commodity (Product) Code 4'] = self.getRecordFieldStr(26)
        rt['Contract Type 4'] = self.getRecordFieldStr(27)
        rt['Risk Array Value Decimal Locator 4'] = self.getRecordFieldStr(28)
        rt['Risk Array Value Decimal Sign 4'] = self.getRecordFieldStr(29)
        #rt['Filler'] = self.getRecordFieldStr(30)
        rt['Commodity (Product) Code 5'] = self.getRecordFieldStr(31)
        rt['Contract Type 5'] = self.getRecordFieldStr(32)
        rt['Risk Array Value Decimal Locator 5'] = self.getRecordFieldStr(33)
        rt['Risk Array Value Decimal Sign 5'] = self.getRecordFieldStr(34)
        #rt['Filler'] = self.getRecordFieldStr(35)
        rt['Commodity (Product) Code 6'] = self.getRecordFieldStr(36)
        rt['Contract Type 6'] = self.getRecordFieldStr(37)
        rt['Risk Array Value Decimal Locator 6'] = self.getRecordFieldStr(38)
        rt['Risk Array Value Decimal Sign 6'] = self.getRecordFieldStr(39)
        #rt['Filler'] = self.getRecordFieldStr(40)
        return rt

class Type3RecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X', 'Record ID - "3 "'),
            1:(6, 3, 8, 'AN', 'X(6)', 'Combined Commodity Code'),
            2:(2, 9, 10, 'AN', 'X(2)', 'Intracommodity (Intermonth) Spread Charge Method Code'),
            3:(2, 11, 12, 'N', '9(2)', 'Tier 1 Tier Number'),
            4:(6, 13, 18, 'N', '9(6)', 'Tier 1 Starting Contract Month as CCYYMM'),
            5:(6, 19, 24, 'N', '9(6)', 'Tier 1 Ending Contract Month as CCYYMM'),
            6:(2, 25, 26, 'N', '9(2)', 'Tier 2 Tier Number'),
            7:(6, 27, 32, 'N', '9(6)', 'Tier 2 Starting Contract Month as CCYYMM'),
            8:(6, 33, 38, 'N', '9(6)', 'Tier 2 Ending Contract Month as CCYYMM'),
            9:(2, 39, 40, 'N', '9(2)', 'Tier 3 Tier Number'),
            10:(6, 41, 46, 'N', '9(6)', 'Tier 3 Starting Contract Month as CCYYMM'),
            11:(6, 47, 52, 'N', '9(6)', 'Tier 3 Ending Contract Month as CCYYMM'),
            12:(2, 53, 54, 'N', '9(2)', 'Tier 4 Tier Number'),
            13:(6, 55, 60, 'N', '9(6)', 'Tier 4 Starting Contract Month as CCYYMM'),
            14:(6, 61, 66, 'N', '9(6)', 'Tier 4 Ending Contract Month as CCYYMM'),
            15:(2, 67, 68, '-', '-', 'Filler'),
            16:(4, 69, 72, 'N', '9V9(3)', 'Initial to Maintenance Ratio -- Member Accounts'),
            17:(4, 73, 76, 'N', '9V9(3)', 'Initial to Maintenance Ratio -- Hedger Accounts'),
            18:(4, 77, 80, 'N', '9V9(3)', 'Initial to Maintenance Ratio -- Speculator Accounts'),
            19:(2, 81, 82, 'AN', 'X(2)', 'Tier 1 Starting Contract Day or Week Code'),
            20:(2, 83, 84, 'AN', 'X(2)', 'Tier 1 Ending Contract Day or Week Code'),
            21:(2, 85, 86, 'AN', 'X(2)', 'Tier 2 Starting Contract Day or Week Code'),
            22:(2, 87, 88, 'AN', 'X(2)', 'Tier 2 Ending Contract Day or Week Code'),
            23:(2, 89, 90, 'AN', 'X(2)', 'Tier 3 Starting Contract Day or Week Code'),
            24:(2, 91, 92, 'AN', 'X(2)', 'Tier 3 Ending Contract Day or Week Code'),
            25:(2, 93, 94, 'AN', 'X(2)', 'Tier 4 Starting Contract Day or Week Code'),
            26:(2, 95, 96, 'AN', 'X(2)', 'Tier 4 Ending Contract Day or Week Code'),
            27:(36, 97, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(1)
        rt['Intracommodity (Intermonth) Spread Charge Method Code'] = self.getRecordFieldStr(2)
        rt['Tier 1 Tier Number'] = self.getRecordFieldStr(3)
        rt['Tier 1 Starting Contract Month'] = self.getRecordFieldStr(4)
        rt['Tier 1 Ending Contract Month'] = self.getRecordFieldStr(5)
        rt['Tier 2 Tier Number'] = self.getRecordFieldStr(6)
        rt['Tier 2 Starting Contract Month'] = self.getRecordFieldStr(7)
        rt['Tier 2 Ending Contract Month'] = self.getRecordFieldStr(8)
        rt['Tier 3 Tier Number'] = self.getRecordFieldStr(9)
        rt['Tier 3 Starting Contract Month'] = self.getRecordFieldStr(10)
        rt['Tier 3 Ending Contract Month'] = self.getRecordFieldStr(11)
        rt['Tier 4 Tier Number'] = self.getRecordFieldStr(12)
        rt['Tier 4 Starting Contract Month'] = self.getRecordFieldStr(13)
        rt['Tier 4 Ending Contract Month'] = self.getRecordFieldStr(14)
        #rt['Filler'] = self.getRecordFieldStr(15)
        rt['Initial to Maintenance Ratio -- Member Accounts'] = self.getRecordFieldStr(16)
        rt['Initial to Maintenance Ratio -- Hedger Accounts'] = self.getRecordFieldStr(17)
        rt['Initial to Maintenance Ratio -- Speculator Accounts'] = self.getRecordFieldStr(18)
        rt['Tier 1 Starting Contract Day or Week Code'] = self.getRecordFieldStr(19)
        rt['Tier 1 Ending Contract Day or Week Code'] = self.getRecordFieldStr(20)
        rt['Tier 2 Starting Contract Day or Week Code'] = self.getRecordFieldStr(21)
        rt['Tier 2 Ending Contract Day or Week Code'] = self.getRecordFieldStr(22)
        rt['Tier 3 Starting Contract Day or Week Code'] = self.getRecordFieldStr(23)
        rt['Tier 3 Ending Contract Day or Week Code'] = self.getRecordFieldStr(24)
        rt['Tier 4 Starting Contract Day or Week Code'] = self.getRecordFieldStr(25)
        rt['Tier 4 Ending Contract Day or Week Code'] = self.getRecordFieldStr(26)
        #rt['Filler'] = self.getRecordFieldStr(27)
        return rt

class Type4RecordsSE(TypeRecords):
    Strut_Type4RecordsStandard10 = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "4 "'),
            1:(2, 9, 10, 'AN', 'X(2)', 'Delivery (Spot) Charge Method Code'),
            2:(6, 3, 8, 'AN', 'X(6)', 'Combined Commodity Code'),
            3:(2, 11, 12, 'N', '9(2)', 'Number of contract months in delivery'),
            4:(2, 13, 14, 'N', '9(2)', 'Delivery Month 1 - Month Number'),
            5:(6, 15, 20, 'N', '9(6)', 'Delivery Month 1 - Contract Month as CCYYMM'),
            6:(7, 21, 27, 'N', '9(7)', 'Delivery Month 1 - Charge Rate Per Delta Consumed By Spreads'),
            7:(7, 28, 34, 'N', '9(7)', 'Delivery Month 1 - Charge Rate Per Delta Remaining In Outrights'),
            8:(2, 35, 36, 'N', '9(2)', 'Delivery Month 2 - Month Number'),
            9:(6, 37, 42, 'N', '9(6)', 'Delivery Month 2 - Contract Month as CCYYMM'),
            10:(7, 43, 49, 'N', '9(7)', 'Delivery Month 2 - Charge Rate Per Delta Consumed By Spreads'),
            11:(7, 50, 56, 'N', '9(7)', 'Delivery Month 2 - Charge Rate Per Delta Remaining In Outrights'),
            12:(6, 57, 62, '-', '-', 'Filler'),
            13:(7, 63, 69, 'N', '9(7)', 'Short Option Minimum Charge Rate'),
            14:(3, 70, 72, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Members'),
            15:(3, 73, 75, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Hedgers'),
            16:(3, 76, 78, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Speculators'),
            17:(1, 79, 79, 'AN', 'X', 'Short Option Minimum Calculation Method -- blank or 2 means the original method, based on the sum of the number of short calls and short puts.  1 means the new method, based on the greater of the number or short calls or short puts.'),
            18:(53, 80, 132, '-', '-', 'Filler')
            }
    Strut_Type4RecordsStandard11 = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "4 "'),
            1:(2, 9, 10, 'AN', 'X(2)', 'Delivery (Spot) Charge Method Code'),
            2:(6, 3, 8, 'AN', 'X(6)', 'Combined Commodity Code'),
            3:(10, 11, 20, 'AN', 'X(10)', 'Spot commodity ( product) code'),
            4:(7, 21, 27, 'N', '9(7)', 'Basis Risk Charge Rate'),
            5:(35, 28, 62, '-', '-', 'Filler'),
            6:(7, 63, 69, 'N', '9(7)', 'Short Option Minimum Charge Rate'),
            7:(3, 70, 72, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Members'),
            8:(3, 73, 75, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Hedgers'),
            9:(3, 76, 78, 'N', '9V9(2)', 'Risk Maintenance Performance Bond Adjustment Factor -- Speculators'),
            10:(1, 79, 79, 'AN', 'X', 'Short Option Minimum Calculation Method -- blank or 2 means the original method, based on the sum of the number of short calls and short puts.  1 means the new method, based on the greater of the number or short calls or short puts.'),
            11:(53, 80, 132, '-', '-', 'Filler')
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type4RecordsStandard10)

    def parseRecord(self):
        if (self.getRecordFieldStr(1) in ['10','02','03','04','05','06','07','08']):
            return self.parse10Record()
        else:
            return self.parse11Record()

    def parse10Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type4RecordsStandard10)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Delivery (Spot) Charge Method Code'] = self.getRecordFieldStr(1)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(2)
        rt['Number of contract months in delivery'] = self.getRecordFieldStr(3)
        rt['Delivery Month 1 - Month Number'] = self.getRecordFieldStr(4)
        rt['Delivery Month 1 - Contract Month'] = self.getRecordFieldStr(5)
        rt['Delivery Month 1 - Charge Rate Per Delta Consumed By Spreads'] = self.getRecordFieldStr(6)
        rt['Delivery Month 1 - Charge Rate Per Delta Remaining In Outrights'] = self.getRecordFieldStr(7)
        rt['Delivery Month 2 - Month Number'] = self.getRecordFieldStr(8)
        rt['Delivery Month 2 - Contract Month'] = self.getRecordFieldStr(9)
        rt['Delivery Month 2 - Charge Rate Per Delta Consumed By Spreads'] = self.getRecordFieldStr(10)
        rt['Delivery Month 2 - Charge Rate Per Delta Remaining In Outrights'] = self.getRecordFieldStr(11)
        #rt['Filler'] = self.getRecordFieldStr(12)
        rt['Short Option Minimum Charge Rate'] = self.getRecordFieldStr(13)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Members'] = self.getRecordFieldStr(14)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Hedgers'] = self.getRecordFieldStr(15)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Speculators'] = self.getRecordFieldStr(16)
        rt['Short Option Minimum Calculation Method'] = self.getRecordFieldStr(17)
        #rt['Filler'] = self.getRecordFieldStr(18)
        return rt

    def parse11Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type4RecordsStandard11)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Delivery (Spot) Charge Method Code'] = self.getRecordFieldStr(1)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(2)
        rt['Spot commodity ( product) code'] = self.getRecordFieldStr(3)
        rt['Basis Risk Charge Rate'] = self.getRecordFieldStr(4)
        #rt['Filler'] = self.getRecordFieldStr(5)
        rt['Short Option Minimum Charge Rate'] = self.getRecordFieldStr(6)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Members'] = self.getRecordFieldStr(7)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Hedgers'] = self.getRecordFieldStr(8)
        rt['Risk Maintenance Performance Bond Adjustment Factor -- Speculators'] = self.getRecordFieldStr(9)
        rt['Short Option Minimum Calculation Method'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        return rt


class Type5RecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X', 'Record ID - "5 "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Combined Commodity Group Code'),
            2:(7, 6, 12, '-', '-', 'Filler'),
            3:(6, 13, 18, 'AN', 'X(6)', 'Combined Commodity Code 1'),
            4:(6, 19, 24, 'AN', 'X(6)', 'Combined Commodity Code 2'),
            5:(6, 25, 30, 'AN', 'X(6)', 'Combined Commodity Code 3'),
            6:(6, 31, 36, 'AN', 'X(6)', 'Combined Commodity Code 4'),
            7:(6, 37, 42, 'AN', 'X(6)', 'Combined Commodity Code 5'),
            8:(6, 43, 48, 'AN', 'X(6)', 'Combined Commodity Code 6'),
            9:(6, 49, 54, 'AN', 'X(6)', 'Combined Commodity Code 7'),
            10:(6, 55, 60, 'AN', 'X(6)', 'Combined Commodity Code 8'),
            11:(6, 61, 66, 'AN', 'X(6)', 'Combined Commodity Code 9'),
            12:(6, 67, 72, 'AN', 'X(6)', 'Combined Commodity Code 10'),
            13:(60, 73, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Combined Commodity Group Code'] = self.getRecordFieldStr(1)
        #rt['Filler'] = self.getRecordFieldStr(2)
        rt['Combined Commodity Code 1'] = self.getRecordFieldStr(3)
        rt['Combined Commodity Code 2'] = self.getRecordFieldStr(4)
        rt['Combined Commodity Code 3'] = self.getRecordFieldStr(5)
        rt['Combined Commodity Code 4'] = self.getRecordFieldStr(6)
        rt['Combined Commodity Code 5'] = self.getRecordFieldStr(7)
        rt['Combined Commodity Code 6'] = self.getRecordFieldStr(8)
        rt['Combined Commodity Code 7'] = self.getRecordFieldStr(9)
        rt['Combined Commodity Code 8'] = self.getRecordFieldStr(10)
        rt['Combined Commodity Code 9'] = self.getRecordFieldStr(11)
        rt['Combined Commodity Code 10'] = self.getRecordFieldStr(12)
        #rt['Filler'] = self.getRecordFieldStr(13)
        return rt

class TypeTempRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {
            0:(0, 0, 0,'AN','X(2)',         ''),
            #1:(0, 0, 0,'AN','X(2)',         '')
    }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        #rt[''] = self.getRecordFieldStr()
        #rt[''] = self.getRecordFieldStr()
        #rt[''] = self.getRecordFieldStr()
        return rt

class TypeVRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(1, 1, 2, 'AN', 'X(2)', 'Record ID - "V "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Product ("commodity") Code'),
            3:(6, 16, 21, 'AN', 'X(6)', 'Futures Contract Month - as CCYYMM'),
            4:(2, 22, 23, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            5:(8, 24, 31, 'AN', 'X(8)', 'Business Date - as CCYYMMDD'),
            6:(13, 32, 44, 'N', '9(5)V9(8)', 'Daily Adjustment Rate - Long'),
            7:(1, 45, 45, 'A', 'X', 'Daily adjustment sign - "-" if premium or "+" if discount'),
            8:(1, 46, 46, 'A', 'X', 'Daily adjustment premium/discount - "P" or "D"'),
            9:(13, 47, 59, 'N', '9(5)V9(8)', 'Daily Adj. Rate-Short, or Cumulative Adjustment Rate'),
            10:(1, 60, 60, 'A', 'X', 'Daily Short or Cumulative Rate sign - "-" if premium or "+" if discount'),
            11:(1, 61, 61, 'A', 'X', 'Daily Short or Cumulative premium/discount - "P" or "D"'),
            12:(1, 62, 62, 'A', 'X', 'Short Rate Flag - S means that the rate in position 48-60 is the Daily Rate for Short positions, blank or any other value indicates that it is the Cumulative Rate for Long positions.'),
            13:(3, 63, 65, 'N', '9V9(2)', 'Long position value maintenance rate - for example, "100" for 1.00'),
            14:(3, 66, 68, 'N', '9V9(2)', 'Short position value maintenance rate - for example, "050" for 0.50'),
            15:(1, 69, 69, 'A', 'X', 'Reset long margin price flag - "Y" or "N"'),
            16:(3, 70, 72, 'N', '9V9(2)', 'Reset long down threshhold'),
            17:(3, 73, 75, 'N', '9V9(2)', 'Reset long up threshhold'),
            18:(1, 76, 76, 'A', 'X', 'Reset short margin price flag - "Y" or "N"'),
            19:(3, 77, 79, 'N', '9V9(2)', 'Reset short down threshhold'),
            20:(3, 80, 82, 'N', '9V9(2)', 'Reset short up threshhold'),
            21:(6, 83, 88, 'AN', 'X(6)', 'Value Maintenance Product Class'),
            22:(44, 89, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Product ("commodity") Code'] = self.getRecordFieldStr(2)
        rt['Futures Contract Month'] = self.getRecordFieldStr(3)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(4)
        rt['Business Date'] = self.getRecordFieldStr(5)
        rt['Daily Adjustment Rate'] = self.getRecordFieldStr(6)
        rt['Daily adjustment sign'] = self.getRecordFieldStr(7)
        rt['Daily adjustment premium/discount'] = self.getRecordFieldStr(8)
        rt['Daily Adj'] = self.getRecordFieldStr(9)
        rt['Daily Short or Cumulative Rate sign'] = self.getRecordFieldStr(10)
        rt['Daily Short or Cumulative premium/discount'] = self.getRecordFieldStr(11)
        rt['Short Rate Flag'] = self.getRecordFieldStr(12)
        rt['Long position value maintenance rate'] = self.getRecordFieldStr(13)
        rt['Short position value maintenance rate'] = self.getRecordFieldStr(14)
        rt['Reset long margin price flag'] = self.getRecordFieldStr(15)
        rt['Reset long down threshhold'] = self.getRecordFieldStr(16)
        rt['Reset long up threshhold'] = self.getRecordFieldStr(17)
        rt['Reset short margin price flag'] = self.getRecordFieldStr(18)
        rt['Reset short down threshhold'] = self.getRecordFieldStr(19)
        rt['Reset short up threshhold'] = self.getRecordFieldStr(20)
        rt['Value Maintenance Product Class'] = self.getRecordFieldStr(21)
        #rt['Filler'] = self.getRecordFieldStr(22)
        return rt

        
class Type9RecordsSE(TypeRecords):
    Strut_Type91RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "91"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(2, 6, 7, '-', '-', 'Filler'),
            3:(10, 8, 17, 'AN', 'X(10)', 'Target Commodity (Product) Code'),
            4:(6, 18, 23, 'N', '9(6)', 'Target Contract Month as CCYYMM'),
            5:(3, 24, 26, '-', '-', 'Filler'),
            6:(3, 27, 29, 'AN', 'X(3)', 'Issuing Country Code'),
            7:(2, 30, 31, '-', '-', 'Filler'),
            8:(15, 32, 46, 'AN', 'X(15)', 'CUSIP or ISIN or other primary instrument ID'),
            9:(3, 47, 49, 'AN', 'X(3)', 'Currency of Denomination - ISO code'),
            10:(1, 50, 50, 'AN', 'X', 'Currency of Denomination - 1-byte code'),
            11:(8, 51, 58, 'N', '9(8)', 'Maturity Date as CCYYMMDD'),
            12:(5, 59, 63, 'N', '9(2)V9(3)', 'Coupon Rate (in percent)'),
            13:(9, 64, 72, 'N', '9(2)V9(7)', 'Physical Conversion Factor'),
            14:(60, 73, 132, '-', '-', 'Filler'),
            }
    Strut_Type92RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "92"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(2, 6, 7, '-', '-', 'Filler'),
            3:(10, 8, 17, 'AN', 'X(10)', 'Target Commodity (Product) Code'),
            4:(6, 18, 23, 'N', '9(6)', 'Target Contract Month as CCYYMM'),
            5:(3, 24, 26, '-', '-', 'Filler'),
            6:(3, 27, 29, 'AN', 'X(3)', 'Issuing Country Code'),
            7:(2, 30, 31, '-', '-', 'Filler'),
            8:(15, 32, 46, 'AN', 'X(15)', 'CUSIP or ISIN or other primary instrument ID'),
            9:(50, 47, 96, 'AN', 'X(50)', 'Instrument Description'),
            10:(10, 97, 106, 'N', '9(4)V9(6)', 'Long-Bond-Equivalence Factor'),
            11:(26, 107, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type91RecordsStandard)

    def parseRecord(self):
        if (self.getRecordFieldStr(0) == '91' ):
            return self.parse91Record()
        if (self.getRecordFieldStr(0) == '92' ):
            return self.parse92Record()
        
    def parse91Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type91RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        #rt['Filler'] = self.getRecordFieldStr(2)
        rt['Target Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Target Contract Month'] = self.getRecordFieldStr(4)
        #rt['Filler'] = self.getRecordFieldStr(5)
        rt['Issuing Country Code'] = self.getRecordFieldStr(6)
        #rt['Filler'] = self.getRecordFieldStr(7)
        rt['CUSIP or ISIN or other primary instrument ID'] = self.getRecordFieldStr(8)
        rt['Currency of Denomination - ISO code'] = self.getRecordFieldStr(9)
        rt['Currency of Denomination - 1-byte code'] = self.getRecordFieldStr(10)
        rt['Maturity Date'] = self.getRecordFieldStr(11)
        rt['Coupon Rate'] = self.getRecordFieldStr(12)
        rt['Physical Conversion Factor'] = self.getRecordFieldStr(13)
        #rt['Filler'] = self.getRecordFieldStr(14)
        return rt
        
    def parse92Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type92RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Filler'] = self.getRecordFieldStr(2)
        rt['Target Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Target Contract Month'] = self.getRecordFieldStr(4)
        #rt['Filler'] = self.getRecordFieldStr(5)
        rt['Issuing Country Code'] = self.getRecordFieldStr(6)
        #rt['Filler'] = self.getRecordFieldStr(7)
        rt['CUSIP or ISIN or other primary instrument ID'] = self.getRecordFieldStr(8)
        rt['Instrument Description'] = self.getRecordFieldStr(9)
        rt['Long-Bond-Equivalence Factor'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        return rt
        
class TypeRRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "R "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(3, 22, 24, 'AN', 'X(3)', 'Alternate Exchange Acronym'),
            3:(6, 16, 21, 'AN', 'X(6)', 'Combined Commodity Code'),
            4:(6, 35, 40, 'AN', 'X(3)', 'Alternate Combined Commodity Code'),
            5:(10, 6, 15, 'AN', 'X(10)', 'Product (Commodity) Code'),
            6:(10, 25, 34, 'AN', 'X(10)', 'Alternate Product (Commodity) Code'),
            7:(90, 41, 132, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Alternate Exchange Acronym'] = self.getRecordFieldStr(2)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(3)
        rt['Alternate Combined Commodity Code'] = self.getRecordFieldStr(4)
        rt['Product (Commodity) Code'] = self.getRecordFieldStr(5)
        rt['Alternate Product (Commodity) Code'] = self.getRecordFieldStr(6)
        #rt['Filler'] = self.getRecordFieldStr(7)
        return rt

class TypeBRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "B "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Commodity Code'),
            3:(3, 16, 18, 'AN', 'X(3)', 'Product Type Code'),
            4:(6, 19, 24, 'N', '9(6)', 'Futures Contract Month as CCYYMM'),
            5:(2, 25, 26, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            6:(1, 27, 27, '-', '-', 'Filler'),
            7:(6, 28, 33, 'N', '9(6)', 'Option Contract Month as CCYYMM'),
            8:(2, 34, 35, 'AN', 'X(2)', 'Option Contract Day or Week Code'),
            9:(1, 36, 36, '-', '-', 'Filler'),
            10:(8, 37, 44, 'N', '9(2)V9(6)', 'Base Volatility (as a decimal fraction)'),
            11:(8, 45, 52, 'N', '9(2)V9(6)', 'Volatility Scan Range (as a decimal fraction)'),
            12:(5, 53, 57, 'N', '9(5)', 'Futures Price Scan Range'),
            13:(5, 58, 62, 'N', '9(2)V9(3)', 'Extreme Move Multiplier'),
            14:(5, 63, 67, 'N', '9V9(4)', 'Extreme Move Covered Fraction'),
            15:(5, 68, 72, 'N', '9V9(4)', 'Interest Rate (as a decimal fraction)'),
            16:(7, 73, 79, 'N', '9V9(6)', 'Time to Expiration (in years)'),
            17:(6, 80, 85, 'N', 'V9(6)', 'Lookahead Time (in years)'),
            18:(6, 86, 91, 'N', '9(2)V9(4)', 'Delta Scaling Factor'),
            19:(8, 92, 99, 'N', '9(8)', 'Expiration (Settlement) Date as CCYYMMDD'),
            20:(10, 100, 109, 'AN', 'X(10)', 'Underlying Commodity Code'),
            21:(2, 110, 111, 'AN', 'X(2)', 'Pricing Model'),
            22:(8, 112, 119, 'N', '9(2)V9(6)', 'Coupon or Dividend Yield, as a decimal fraction'),
            23:(1, 120, 120, 'AN', 'X(1)', 'Option Expiration Reference Price Flag -- see note below'),
            24:(7, 121, 127, 'N', '9(7)', 'Option Expiration Reference Price'),
            25:(1, 128, 128, 'AN', 'X(1)', 'Option Expiration Reference Price Sign (+ or -)'),
            26:(14, 129, 142, 'N', '9(7)V9(7)', 'Swap Value Factor (for interest-rate swaps) or Contract-Specific Contract Value Factor (for normal futures and options)'),
            27:(2, 143, 144, 'N', '9(2)', 'Swap Value Factor Exponent'),
            28:(1, 145, 145, 'AN', 'X', 'Sign for Swap Value Factor Exponent (blank, "+" or "-")'),
            29:(2, 146, 147, 'N', '9(2)', 'Base Volatility Exponent'),
            30:(1, 148, 148, 'AN', 'X', 'Sign for Base Volatility Exponent (blank, "+" or "-")'),
            31:(2, 149, 150, 'N', '9(2)', 'Volatility Scan Range Exponent'),
            32:(1, 151, 151, 'AN', 'X', 'Sign for Volatility Scan Range Exponent (blank, "+" or "-")'),
            33:(12, 152, 163, 'N', '9(2)V9(10)', 'Discount Factor (for discounting back to present value)'),
            34:(1, 164, 164, 'AN', 'X', 'Volatility Scan Range Quotation Method -- blank or A means that the volatility scan range is provided as an absolute value, and P means that it is provided as percentage of the implied volatility.'),
            35:(1, 165, 165, 'AN', 'X', 'Price Scan Range Quotation Method -- blank or A means that the price scan range is provided as an absolute value, and P means that is provided as a percentage of the contract value'),
            36:(2, 166, 167, 'N', '9(2)', 'Futures Price Scan Range Exponent'),
            37:(1, 168, 168, 'AN', 'X', 'Sign for Futures Price Scan Range Exponent (blank, "+" or "-")'),
            38:(5, 169, 173, 'AN', 'X', 'Delivery Margin Method'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Commodity Code'] = self.getRecordFieldStr(2)
        rt['Product Type Code'] = self.getRecordFieldStr(3)
        rt['Futures Contract Month'] = self.getRecordFieldStr(4)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(5)
        #rt['Filler'] = self.getRecordFieldStr(6)
        rt['Option Contract Month'] = self.getRecordFieldStr(7)
        rt['Option Contract Day or Week Code'] = self.getRecordFieldStr(8)
        #rt['Filler'] = self.getRecordFieldStr(9)
        rt['Base Volatility'] = self.getRecordFieldStr(10)
        rt['Volatility Scan Range'] = self.getRecordFieldStr(11)
        rt['Futures Price Scan Range'] = self.getRecordFieldStr(12)
        rt['Extreme Move Multiplier'] = self.getRecordFieldStr(13)
        rt['Extreme Move Covered Fraction'] = self.getRecordFieldStr(14)
        rt['Interest Rate'] = self.getRecordFieldStr(15)
        rt['Time to Expiration'] = self.getRecordFieldStr(16)
        rt['Lookahead Time'] = self.getRecordFieldStr(17)
        rt['Delta Scaling Factor'] = self.getRecordFieldStr(18)
        rt['Expiration (Settlement) Date'] = self.getRecordFieldStr(19)
        rt['Underlying Commodity Code'] = self.getRecordFieldStr(20)
        rt['Pricing Model'] = self.getRecordFieldStr(21)
        rt['Coupon or Dividend Yield'] = self.getRecordFieldStr(22)
        rt['Option Expiration Reference Price Flag'] = self.getRecordFieldStr(23)
        rt['Option Expiration Reference Price'] = self.getRecordFieldStr(24)
        rt['Option Expiration Reference Price Sign'] = self.getRecordFieldStr(25)
        rt['Swap Value Factor or Contract'] = self.getRecordFieldStr(26)
        rt['Swap Value Factor Exponent'] = self.getRecordFieldStr(27)
        rt['Sign for Swap Value Factor Exponent'] = self.getRecordFieldStr(28)
        rt['Base Volatility Exponent'] = self.getRecordFieldStr(29)
        rt['Sign for Base Volatility Exponent'] = self.getRecordFieldStr(30)
        rt['Volatility Scan Range Exponent'] = self.getRecordFieldStr(31)
        rt['Sign for Volatility Scan Range Exponent'] = self.getRecordFieldStr(32)
        rt['Discount Factor'] = self.getRecordFieldStr(33)
        rt['Volatility Scan Range Quotation Method'] = self.getRecordFieldStr(34)
        rt['Price Scan Range Quotation Method'] = self.getRecordFieldStr(35)
        rt['Futures Price Scan Range Exponent'] = self.getRecordFieldStr(36)
        rt['Sign for Futures Price Scan Range Exponent'] = self.getRecordFieldStr(37)
        rt['Delivery Margin Method'] = self.getRecordFieldStr(38)
        return rt

class TypeERecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "E "'),
            1:(6, 3, 8, 'AN', 'X(3)', 'Combined Commodity Code'),
            2:(5, 9, 13, 'N', '9(5)', 'Spread Priority'),
            3:(7, 14, 20, 'N', '9(7)', 'Charge Rate'),
            4:(4, 21, 24, 'N', '9(4)', 'Leg 1 Contract Month as YYMM'),
            5:(3, 25, 27, 'AN', 'X(3)', 'Leg 1 Remaining Part of Contract Period'),
            6:(6, 28, 33, 'N', '9(2)V9(4)', 'Leg 1 Delta Per Spread Ratio'),
            7:(1, 34, 34, 'A', 'A', 'Leg 1 Market Side (A or B)'),
            8:(4, 35, 38, 'N', '9(4)', 'Leg 2 Contract Month as YYMM'),
            9:(3, 39, 41, 'AN', 'X(3)', 'Leg 2 Remaining Part of Contract Period'),
            10:(6, 42, 47, 'N', '9(2)V9(4)', 'Leg 2 Delta Per Spread Ratio'),
            11:(1, 48, 48, 'A', 'A', 'Leg 2 Market Side (A or B)'),
            12:(4, 49, 52, 'N', '9(4)', 'Leg 3 Contract Month as YYMM'),
            13:(3, 53, 55, 'AN', 'X(3)', 'Leg 3 Remaining Part of Contract Period'),
            14:(6, 56, 61, 'N', '9(2)V9(4)', 'Leg 3 Delta Per Spread Ratio'),
            15:(1, 62, 62, 'A', 'A', 'Leg 3 Market Side (A or B)'),
            16:(4, 63, 66, 'N', '9(4)', 'Leg 4 Contract Month as YYMM'),
            17:(3, 67, 69, 'AN', 'X(3)', 'Leg 4 Remaining Part of Contract Period'),
            18:(6, 70, 75, 'N', '9(2)V9(4)', 'Leg 4 Delta Per Spread Ratio'),
            19:(1, 76, 76, 'A', 'A', 'Leg 4 Market Side (A or B)'),
            20:(4, 77, 80, '-', '-', 'Filler'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(1)
        rt['Spread Priority'] = self.getRecordFieldStr(2)
        rt['Charge Rate'] = self.getRecordFieldStr(3)
        rt['Leg 1 Contract Month'] = self.getRecordFieldStr(4)
        rt['Leg 1 Remaining Part of Contract Period'] = self.getRecordFieldStr(5)
        rt['Leg 1 Delta Per Spread Ratio'] = self.getRecordFieldStr(6)
        rt['Leg 1 Market Side'] = self.getRecordFieldStr(7)
        rt['Leg 2 Contract Month'] = self.getRecordFieldStr(8)
        rt['Leg 2 Remaining Part of Contract Period'] = self.getRecordFieldStr(9)
        rt['Leg 2 Delta Per Spread Ratio'] = self.getRecordFieldStr(10)
        rt['Leg 2 Market Side'] = self.getRecordFieldStr(11)
        rt['Leg 3 Contract Month'] = self.getRecordFieldStr(12)
        rt['Leg 3 Remaining Part of Contract Period'] = self.getRecordFieldStr(13)
        rt['Leg 3 Delta Per Spread Ratio'] = self.getRecordFieldStr(14)
        rt['Leg 3 Market Side'] = self.getRecordFieldStr(15)
        rt['Leg 4 Contract Month'] = self.getRecordFieldStr(16)
        rt['Leg 4 Remaining Part of Contract Period'] = self.getRecordFieldStr(17)
        rt['Leg 4 Delta Per Spread Ratio'] = self.getRecordFieldStr(18)
        rt['Leg 4 Market Side'] = self.getRecordFieldStr(19)
        #rt['Filler'] = self.getRecordFieldStr(20)
        return rt



class TypeZRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "Z "'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Combination Product (Commodity) Code'),
            3:(5, 16, 20, 'AN', 'X(5)', 'Combination Type - STRIP for strips such as Eurodollar packs and bundles, CAL for futures calendar spreads, and I/C for futures intercommodity spreads'),
            4:(6, 21, 26, 'N', '9(6)', 'Combination Contract Month - YYYYMM'),
            5:(2, 27, 28, 'AN', 'X(2)', 'Combination Contract Day - typically blank'),
            6:(7, 29, 35, '-', '-', 'Filler'),
            7:(3, 36, 38, 'N', '9(3)', 'Leg Number'),
            8:(1, 39, 39, 'A', 'X', 'Leg Relationship - A or B'),
            9:(3, 40, 42, 'N', '9(3)', 'Leg Ratio'),
            10:(10, 43, 52, 'AN', 'X(10)', 'Leg Product (Commodity) Code'),
            11:(3, 53, 55, 'AN', 'X(3)', 'Leg Product Type'),
            12:(6, 56, 61, 'N', '9(6)', 'Leg Contract Month - YYYYMM'),
            13:(2, 62, 63, 'AN', 'X(2)', 'Leg Contract Day - typically blank'),
            14:(4, 64, 67, 'N', '9(4)', 'Leg Ratio -- Fractional Part.  Blank or any non-numeric value means zero.'),
            15:(1, 68, 68, 'AN', 'X(1)', 'Leg Price Available Flag -- Y means that leg price data is provided for creating transactions in this leg when an option on this combination is exercised or assigned.  N or any other value means that it is not provided.'),
            16:(2, 69, 70, 'AN', 'X(2)', 'Leg Price Usage Flag -- specifies how the value provided is used.  L means that the value provided is the leg price to use.  S+ means that you take the value provided and add the option strike to it to obtain the leg price to use.  S- means that you take the value provided and subtract the option strike from it to obtain the leg price to use.'),
            17:(7, 71, 77, 'N', '9(7)', 'Leg Price -- the specified price value, typically provided as zeros if the Leg Price Available Flag is not Y.'),
            18:(1, 78, 78, 'AN', 'X(1)', 'Leg Price Sign -- sign for the specified price value.  - means negative, + or any other value means positive.'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Combination Product (Commodity) Code'] = self.getRecordFieldStr(2)
        rt['Combination Type'] = self.getRecordFieldStr(3)
        rt['Combination Contract Month'] = self.getRecordFieldStr(4)
        rt['Combination Contract Day'] = self.getRecordFieldStr(5)
        #rt['Filler'] = self.getRecordFieldStr(6)
        rt['Leg Number'] = self.getRecordFieldStr(7)
        rt['Leg Relationship'] = self.getRecordFieldStr(8)
        rt['Leg Ratio'] = self.getRecordFieldStr(9)
        rt['Leg Product (Commodity) Code'] = self.getRecordFieldStr(10)
        rt['Leg Product Type'] = self.getRecordFieldStr(11)
        rt['Leg Contract Month'] = self.getRecordFieldStr(12)
        rt['Leg Contract Day'] = self.getRecordFieldStr(13)
        rt['Leg Ratio Fractional Part'] = self.getRecordFieldStr(14)
        rt['Leg Price Available Flag'] = self.getRecordFieldStr(15)
        rt['Leg Price Usage Flag'] = self.getRecordFieldStr(16)
        rt['Leg Price'] = self.getRecordFieldStr(17)
        rt['Leg Price Sign'] = self.getRecordFieldStr(18)
        return rt


class Type6RecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X', 'Record ID - "6" plus a space'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Commodity Group Code'),
            2:(4, 6, 9, 'N', '9(4)', 'Spread Priority'),
            3:(7, 10, 16, 'N', '9(3)V9(4)', 'Spread Credit Rate, in percent'),
            4:(3, 17, 19, 'AN', 'X(3)', 'Exchange Acronym Leg 1'),
            5:(1, 20, 20, 'AN', 'X(1)', 'Leg 1 Required for Scanning-Based Spread flag ("N" means not required, any other value means required)'),
            6:(6, 21, 26, 'AN', 'X(6)', 'Combined Commodity Code Leg 1'),
            7:(7, 27, 33, 'N', '9(3)V9(4)', 'Delta/Spread Ratio Leg 1'),
            8:(1, 34, 34, 'AN', 'X', 'Spread Side Leg 1 ("A","B")'),
            9:(3, 35, 37, 'AN', 'X(3)', 'Exchange Acronym Leg 2'),
            10:(1, 38, 38, 'AN', 'X(1)', 'Leg 2 Required for Scanning-Based Spread Flag'),
            11:(6, 39, 44, 'AN', 'X(6)', 'Combined Commodity Code Leg 2'),
            12:(7, 45, 51, 'N', '9(3)V9(4)', 'Delta/Spread Ratio Leg 2'),
            13:(1, 52, 52, 'AN', 'X', 'Spread Side Leg 2 ("A","B")'),
            14:(3, 53, 55, 'AN', 'X(3)', 'Exchange Acronym Leg 3'),
            15:(1, 56, 56, 'AN', 'X(1)', 'Leg 3 Required for Scanning-Based Spread Flag'),
            16:(6, 57, 62, 'AN', 'X(6)', 'Combined Commodity Code Leg 3'),
            17:(7, 63, 69, 'N', '9(3)V9(4)', 'Delta/Spread Ratio Leg 3'),
            18:(1, 70, 70, 'AN', 'X', 'Spread Side Leg 3 ("A","B")'),
            19:(3, 71, 73, 'AN', 'X(3)', 'Exchange Acronym Leg 4'),
            20:(1, 74, 74, 'AN', 'X(1)', 'Leg 4 Required for Scanning-Based Spread Flag'),
            21:(6, 75, 80, 'AN', 'X(6)', 'Combined Commodity Code Leg 4'),
            22:(7, 81, 87, 'N', '9(3)V9(4)', 'Delta/Spread Ratio Leg 4'),
            23:(1, 88, 88, 'AN', 'X', 'Spread Side Leg 4 ("A","B")'),
            24:(2, 89, 90, 'N', '9(2)', 'Intercommodity Spread Method Code'),
            25:(3, 91, 93, 'AN', 'X(3)', 'Method 4: Target Exchange Acronym'),
            26:(1, 94, 94, 'AN', 'X(1)', 'Method 4:  Target Leg Required Flag'),
            27:(6, 95, 100, 'AN', 'X(6)', 'Method 4: Target Combined Commodity Code'),
            28:(1, 101, 101, 'AN', 'X(1)', 'Credit Calculation Method: blank or W means regular weighted futures price risk method. F means a flat credit method – in this case Spread Credit Rate is treated as dollar amount and decimal point moves two positions to the right (9(5)V9(2))'),
            29:(2, 102, 103, 'N', '9(2)', 'Tier Number Leg 1'),
            30:(2, 104, 105, 'N', '9(2)', 'Tier Number Leg 2'),
            31:(2, 106, 107, 'N', '9(2)', 'Tier Number Leg 3'),
            32:(2, 108, 109, 'N', '9(2)', 'Tier Number Leg 4'),
            33:(1, 110, 110, 'AN', 'X(1)', 'Spread Group Flag:  blank or N means normal intercommodity or interexchange spread.  S means super-intercommodity or super-interexchange spread -- ie, a spread evaluated before rather than after normal intracommodity spreading.'),
            34:(7, 111, 117, 'N', '9(3)V9(4)', 'Method 4:  Target Leg Delta per Spread Ratio'),
            35:(4, 118, 121, 'N', '9(4)', 'Method 4:  Minimum Number of Legs Required to Form Spread.  If not defined, the default value is two.'),
            36:(1, 122, 122, 'AN', 'X(1)', 'Spread Credit Rate Defined separately for each leg: blank or N means use the same credit rate for all legs. Y means use separate credit rate for each leg (credit rates defined below)'),
            37:(7, 123, 129, 'N', '9(3)V9(4)', 'Spread Credit Rate Leg 1'),
            38:(7, 130, 136, 'N', '9(3)V9(4)', 'Spread Credit Rate Leg 2'),
            39:(7, 137, 143, 'N', '9(3)V9(4)', 'Spread Credit Rate Leg 3'),
            40:(7, 144, 150, 'N', '9(3)V9(4)', 'Spread Credit Rate Leg 4'),
            41:(1, 151, 151, 'AN', 'X(1)', 'Regulatory Status Eligibility Code -- N means not eligible for customer-seg positions -- ie, credits cannot be granted for customer accounts for any leg for which positions quality for segregated customer status.  H means the spread may be evaluated only for house accounts, but not for customer accounts.  Any other value means credits can be granted for all legs and without regard to the origin of the account.'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Commodity Group Code'] = self.getRecordFieldStr(1)
        rt['Spread Priority'] = self.getRecordFieldStr(2)
        rt['Spread Credit Rate'] = self.getRecordFieldStr(3)
        rt['Exchange Acronym Leg 1'] = self.getRecordFieldStr(4)
        rt['Leg 1 Required for Scanning'] = self.getRecordFieldStr(5)
        rt['Combined Commodity Code Leg 1'] = self.getRecordFieldStr(6)
        rt['Delta/Spread Ratio Leg 1'] = self.getRecordFieldStr(7)
        rt['Spread Side Leg 1'] = self.getRecordFieldStr(8)
        rt['Exchange Acronym Leg 2'] = self.getRecordFieldStr(9)
        rt['Leg 2 Required for Scanning'] = self.getRecordFieldStr(10)
        rt['Combined Commodity Code Leg 2'] = self.getRecordFieldStr(11)
        rt['Delta/Spread Ratio Leg 2'] = self.getRecordFieldStr(12)
        rt['Spread Side Leg 2'] = self.getRecordFieldStr(13)
        rt['Exchange Acronym Leg 3'] = self.getRecordFieldStr(14)
        rt['Leg 3 Required for Scanning'] = self.getRecordFieldStr(15)
        rt['Combined Commodity Code Leg 3'] = self.getRecordFieldStr(16)
        rt['Delta/Spread Ratio Leg 3'] = self.getRecordFieldStr(17)
        rt['Spread Side Leg 3'] = self.getRecordFieldStr(18)
        rt['Exchange Acronym Leg 4'] = self.getRecordFieldStr(19)
        rt['Leg 4 Required for Scanning'] = self.getRecordFieldStr(20)
        rt['Combined Commodity Code Leg 4'] = self.getRecordFieldStr(21)
        rt['Delta/Spread Ratio Leg 4'] = self.getRecordFieldStr(22)
        rt['Spread Side Leg 4'] = self.getRecordFieldStr(23)
        rt['Intercommodity Spread Method Code'] = self.getRecordFieldStr(24)
        rt['Method 4: Target Exchange Acronym'] = self.getRecordFieldStr(25)
        rt['Method 4: Target Leg Required Flag'] = self.getRecordFieldStr(26)
        rt['Method 4: Target Combined Commodity Code'] = self.getRecordFieldStr(27)
        rt['Credit Calculation Method'] = self.getRecordFieldStr(28)
        rt['Tier Number Leg 1'] = self.getRecordFieldStr(29)
        rt['Tier Number Leg 2'] = self.getRecordFieldStr(30)
        rt['Tier Number Leg 3'] = self.getRecordFieldStr(31)
        rt['Tier Number Leg 4'] = self.getRecordFieldStr(32)
        rt['Spread Group Flag'] = self.getRecordFieldStr(33)
        rt['Method 4:  Target Leg Delta per Spread Ratio'] = self.getRecordFieldStr(34)
        rt['Method 4:  Minimum Number of Legs Required to Form Spread'] = self.getRecordFieldStr(35)
        rt['Spread Credit Rate Defined separately for each leg'] = self.getRecordFieldStr(36)
        rt['Spread Credit Rate Leg 1'] = self.getRecordFieldStr(37)
        rt['Spread Credit Rate Leg 2'] = self.getRecordFieldStr(38)
        rt['Spread Credit Rate Leg 3'] = self.getRecordFieldStr(39)
        rt['Spread Credit Rate Leg 4'] = self.getRecordFieldStr(40)
        rt['Regulatory Status Eligibility Code'] = self.getRecordFieldStr(41)
        return rt

class Type8RecordsSE(TypeRecords):
    Strut_Type81RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "81"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Commodity (Product) Code'),
            3:(10, 16, 25, 'AN', 'X(10)', 'Underlying Commodity (Product) Code'),
            4:(3, 26, 28, 'AN', 'X(3)', 'Product Type Code'),
            5:(1, 29, 29, 'AN', 'X', 'Option Right Code - for an option only: P for Put or C for Call'),
            6:(6, 30, 35, 'N', '9(6)', 'Futures Contract Month as CCYYMM'),
            7:(2, 36, 37, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            8:(1, 38, 38, '-', '-', 'Filler'),
            9:(6, 39, 44, 'N', '9(6)', 'Option Contract Month as CCYYMM'),
            10:(2, 45, 46, 'AN', 'X(2)', 'Option Contract Day or Week Code'),
            11:(1, 47, 47, '-', '-', 'Filler'),
            12:(7, 48, 54, 'N', '9(7)', 'Option Strike Price'),
            13:(5, 55, 59, 'N', '9(5)', 'Array Value 1: Futures No Change / Volatility Up'),
            14:(1, 60, 60, 'AN', 'X', 'Sign for Array Value 1 ("+" or "-")'),
            15:(5, 61, 65, 'N', '9(5)', 'Array Value 2: Futures No Change / Volatility Down'),
            16:(1, 66, 66, 'AN', 'X', 'Sign for Array Value 2 ("+" or "-")'),
            17:(5, 67, 71, 'N', '9(5)', 'Array Value 3: Futures Up 1/3 / Volatility Up'),
            18:(1, 72, 72, 'AN', 'X', 'Sign for Array Value 3 ("+" or "-")'),
            19:(5, 73, 77, 'N', '9(5)', 'Array Value 4: Futures Up 1/3 / Volatility Down'),
            20:(1, 78, 78, 'AN', 'X', 'Sign for Array Value 4 ("+" or "-")'),
            21:(5, 79, 83, 'N', '9(5)', 'Array Value 5: Futures Down 1/3 / Volatility Up'),
            22:(1, 84, 84, 'AN', 'X', 'Sign for Array Value 5 ("+" or "-")'),
            23:(5, 85, 89, 'N', '9(5)', 'Array Value 6: Futures Down 1/3 / Volatility Down'),
            24:(1, 90, 90, 'AN', 'X', 'Sign for Array Value 6 ("+" or "-")'),
            25:(5, 91, 95, 'N', '9(5)', 'Array Value 7: Futures Up 2/3 / Volatility Up'),
            26:(1, 96, 96, 'AN', 'X', 'Sign for Array Value 7 ("+" or "-")'),
            27:(5, 97, 101, 'N', '9(5)', 'Array Value 8: Futures Up 2/3 / Volatility Down'),
            28:(1, 102, 102, 'AN', 'X', 'Sign for Array Value 8 ("+" or "-")'),
            29:(5, 103, 107, 'N', '9(5)', 'Array Value 9: Futures Down 2/3 / Volatility Up'),
            30:(1, 108, 108, 'AN', 'X', 'Sign for Array Value 9 ("+" or "-")'),
            31:(14, 109, 122, 'N', '9(14)', 'High-Precision Settlement Price'),
            32:(1, 123, 123, 'AN', 'X', 'High-Precision Settlement Price Flag - N means that the High-Precision Settlement Price is populated but the price may be read either from this field or from the regular Settlement Price field, Y means that the High-Precision Settlement Price field is populated and the price can only be read from the high-precision field'),
            }
    Strut_Type82RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "82"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Commodity (Product) Code'),
            3:(10, 16, 25, 'AN', 'X(10)', 'Underlying Commodity (Product) Code'),
            4:(3, 26, 28, 'AN', 'X(3)', 'Product Type Code'),
            5:(1, 29, 29, 'AN', 'X', 'Option Right Code - for an option only: P for Put or C for Call'),
            6:(6, 30, 35, 'N', '9(6)', 'Futures Contract Month as CCYYMM'),
            7:(2, 36, 37, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            8:(1, 38, 38, '-', '-', 'Filler'),
            9:(6, 39, 44, 'N', '9(6)', 'Option Contract Month as CCYYMM'),
            10:(2, 45, 46, 'AN', 'X(2)', 'Option Contract Day or Week Code'),
            11:(1, 47, 47, '-', '-', 'Filler'),
            12:(7, 48, 54, 'N', '9(7)', 'Option Strike Price'),
            13:(5, 55, 59, 'N', '9(5)', 'Array Value 10: Futures Down 2/3 / Volatility Down'),
            14:(1, 60, 60, 'AN', 'X', 'Sign for Array Value 10 ("+" or "-")'),
            15:(5, 61, 65, 'N', '9(5)', 'Array Value 11: Futures Up 3/3 / Volatility Up'),
            16:(1, 66, 66, 'AN', 'X', 'Sign for Array Value 11 ("+" or "-")'),
            17:(5, 67, 71, 'N', '9(5)', 'Array Value 12: Futures Up 3/3 / Volatility Down'),
            18:(1, 72, 72, 'AN', 'X', 'Sign for Array Value 12 ("+" or "-")'),
            19:(5, 73, 77, 'N', '9(5)', 'Array Value 13: Futures Down 3/3 / Volatility Up'),
            20:(1, 78, 78, 'AN', 'X', 'Sign for Array Value 13 ("+" or "-")'),
            21:(5, 79, 83, 'N', '9(5)', 'Array Value 14: Futures Down 3/3 / Volatility Down'),
            22:(1, 84, 84, 'AN', 'X', 'Sign for Array Value 14 ("+" or "-")'),
            23:(5, 85, 89, 'N', '9(5)', 'Array Value 15: Futures Up Extreme - Cover Fraction'),
            24:(1, 90, 90, 'AN', 'X', 'Sign for Array Value 15 ("+" or "-")'),
            25:(5, 91, 95, 'N', '9(5)', 'Array Value 16: Futures Down Extreme - Cover Fraction'),
            26:(1, 96, 96, 'AN', 'X', 'Sign for Array Value 16 ("+" or "-")'),
            27:(5, 97, 101, 'N', '9V9(4)', 'SPAN Composite Delta'),
            28:(1, 102, 102, 'AN', 'X', 'Sign for SPAN Composite Delta ("+" or "-")'),
            29:(8, 103, 110, 'N', '99V9(6)', 'Implied Volatility as decimal fraction'),
            30:(7, 111, 117, 'N', '9(7)', 'Settlement Price'),
            31:(1, 118, 118, 'AN', 'X', 'Sign for Settlement Price (blank, "+" or "-")'),
            32:(1, 119, 119, 'AN', 'X', 'Sign for Strike Price (blank, "+" or "-")'),
            33:(5, 120, 124, 'N', '9V9(4)', 'Current Delta'),
            34:(1, 125, 125, 'AN', 'X', 'Sign for Current Delta (blank, "+" or "-")'),
            35:(1, 126, 126, 'AN', 'X', 'Current Delta Business-Day Flag -- "C" means this is today\'s end-of-day delta, "I" means this is an intraday theoretical delta for today, "P" means this is the previous day\'s end-of-day delta, and "X" or any other value means that no delta is available.'),
            36:(7, 127, 133, 'N', '9(7)', 'Start of Day Price'),
            37:(1, 134, 134, 'AN', 'X', 'Sign for Start of Day Price (blank, "+" or "-")'),
            38:(2, 135, 136, 'N', '9(2)', 'Implied Volatility Exponent'),
            39:(1, 137, 137, 'AN', 'X', 'Sign for Implied Volatility Exponent (blank, "+" or "-")'),
            40:(14, 138, 151, 'N', '9(7)V9(7)', 'Contract-specific Contract Value Factor (for variable tick options only)'),
            41:(2, 152, 153, 'N', '9(2)', 'Contract-specific Contract Value Factor Exponent (for variable tick options only)'),
            42:(1, 154, 154, 'AN', 'X', 'Sign for Contract-specific Contract Value Factor Exponent (blank, "+" or "-") (for variable tick options only)'),
            43:(14, 155, 168, 'N', '9(7)V9(7)', 'Contract-specific Strike Value Factor (for variable tick options only)'),
            44:(2, 169, 170, 'N', '9(2)', 'Contract-specific Strike Value Factor Exponent (for variable tick options only)'),
            45:(1, 171, 171, 'AN', 'X', 'Sign for Contract-specific Strike Value Factor Exponent (blank, "+" or "-") (for variable tick options only)'),
            }
    Strut_Type83RecordsStandard = {
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "83"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Commodity (Product) Code'),
            3:(10, 16, 25, 'AN', 'X(10)', 'Underlying Commodity (Product) Code'),
            4:(3, 26, 28, 'AN', 'X(3)', 'Product Type Code'),
            5:(1, 29, 29, 'AN', 'X', 'Option Right Code - for an option only: P for Put or C for Call'),
            6:(6, 30, 35, 'N', '9(6)', 'Futures Contract Month as CCYYMM'),
            7:(2, 36, 37, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            8:(1, 38, 38, '-', '-', 'Filler'),
            9:(6, 39, 44, 'N', '9(6)', 'Option Contract Month as CCYYMM'),
            10:(2, 45, 46, 'AN', 'X(2)', 'Option Contract Day or Week Code'),
            11:(1, 47, 47, '-', '-', 'Filler'),
            12:(7, 48, 54, 'N', '9(7)', 'Option Strike Price'),
            13:(8, 55, 62, 'N', '9(8)', 'Array Value 1: Futures No Change / Volatility Up'),
            14:(1, 63, 63, 'AN', 'X', 'Sign for Array Value 1 ("+" or "-")'),
            15:(8, 64, 71, 'N', '9(8)', 'Array Value 2: Futures No Change / Volatility Down'),
            16:(1, 72, 72, 'AN', 'X', 'Sign for Array Value 2 ("+" or "-")'),
            17:(8, 73, 80, 'N', '9(8)', 'Array Value 3: Futures Up 1/3 / Volatility Up'),
            18:(1, 81, 81, 'AN', 'X', 'Sign for Array Value 3 ("+" or "-")'),
            19:(8, 82, 89, 'N', '9(8)', 'Array Value 4: Futures Up 1/3 / Volatility Down'),
            20:(1, 90, 90, 'AN', 'X', 'Sign for Array Value 4 ("+" or "-")'),
            21:(8, 91, 98, 'N', '9(8)', 'Array Value 5: Futures Down 1/3 / Volatility Up'),
            22:(1, 99, 99, 'AN', 'X', 'Sign for Array Value 5 ("+" or "-")'),
            23:(8, 100, 107, 'N', '9(8)', 'Array Value 6: Futures Down 1/3 / Volatility Down'),
            24:(1, 108, 108, 'AN', 'X', 'Sign for Array Value 6 ("+" or "-")'),
            25:(8, 109, 116, 'N', '9(8)', 'Array Value 7: Futures Up 2/3 / Volatility Up'),
            26:(1, 117, 117, 'AN', 'X', 'Sign for Array Value 7 ("+" or "-")'),
            27:(8, 118, 125, 'N', '9(8)', 'Array Value 8: Futures Up 2/3 / Volatility Down'),
            28:(1, 126, 126, 'AN', 'X', 'Sign for Array Value 8 ("+" or "-")'),
            29:(8, 127, 134, 'N', '9(8)', 'Array Value 9: Futures Down 2/3 / Volatility Up'),
            30:(1, 135, 135, 'AN', 'X', 'Sign for Array Value 9 ("+" or "-")'),
            31:(14, 136, 149, 'N', '9(14)', 'High-Precision Settlement Price'),
            32:(1, 150, 150, 'AN', 'X', 'High-Precision Settlement Price Flag - N means that the High-Precision Settlement Price is populated but the price may be read either from this field or from the regular Settlement Price field, Y means that the High-Precision Settlement Price field is populated and the price can only be read from the high-precision field. '),
            }
    Strut_Type84RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "84"'),
            1:(3, 3, 5, 'AN', 'X(3)', 'Exchange Acronym'),
            2:(10, 6, 15, 'AN', 'X(10)', 'Commodity (Product) Code'),
            3:(10, 16, 25, 'AN', 'X(10)', 'Underlying Commodity (Product) Code'),
            4:(3, 26, 28, 'AN', 'X(3)', 'Product Type Code'),
            5:(1, 29, 29, 'AN', 'X', 'Option Right Code - for an option only: P for Put or C for Call'),
            6:(6, 30, 35, 'N', '9(6)', 'Futures Contract Month as CCYYMM'),
            7:(2, 36, 37, 'AN', 'X(2)', 'Futures Contract Day or Week Code'),
            8:(1, 38, 38, '-', '-', 'Filler'),
            9:(6, 39, 44, 'N', '9(6)', 'Option Contract Month as CCYYMM'),
            10:(2, 45, 46, 'AN', 'X(2)', 'Option Contract Day or Week Code'),
            11:(1, 47, 47, '-', '-', 'Filler'),
            12:(7, 48, 54, 'N', '9(7)', 'Option Strike Price'),
            13:(8, 55, 62, 'N', '9(8)', 'Array Value 10: Futures Down 2/3 / Volatility Down'),
            14:(1, 63, 63, 'AN', 'X', 'Sign for Array Value 10 ("+" or "-")'),
            15:(8, 64, 71, 'N', '9(8)', 'Array Value 11: Futures Up 3/3 / Volatility Up'),
            16:(1, 72, 72, 'AN', 'X', 'Sign for Array Value 11 ("+" or "-")'),
            17:(8, 73, 80, 'N', '9(8)', 'Array Value 12: Futures Up 3/3 / Volatility Down'),
            18:(1, 81, 81, 'AN', 'X', 'Sign for Array Value 12 ("+" or "-")'),
            19:(8, 82, 89, 'N', '9(8)', 'Array Value 13: Futures Down 3/3 / Volatility Up'),
            20:(1, 90, 90, 'AN', 'X', 'Sign for Array Value 13 ("+" or "-")'),
            21:(8, 91, 98, 'N', '9(8)', 'Array Value 14: Futures Down 3/3 / Volatility Down'),
            22:(1, 99, 99, 'AN', 'X', 'Sign for Array Value 14 ("+" or "-")'),
            23:(8, 100, 107, 'N', '9(8)', 'Array Value 15: Futures Up Extreme - Cover Fraction'),
            24:(1, 108, 108, 'AN', 'X', 'Sign for Array Value 15 ("+" or "-")'),
            25:(8, 109, 116, 'N', '9(8)', 'Array Value 16: Futures Down Extreme - Cover Fraction'),
            26:(1, 117, 117, 'AN', 'X', 'Sign for Array Value 16 ("+" or "-")'),
            27:(5, 118, 122, 'N', '9V9(4)', 'Composite Delta'),
            28:(1, 123, 123, 'AN', 'X', 'Sign for Composite Delta ("+" or "-")'),
            29:(8, 124, 131, 'N', '99V9(6)', 'Implied Volatility as decimal fraction6'),
            30:(7, 132, 138, 'N', '9(7)', 'Settlement Price'),
            31:(1, 139, 139, 'AN', 'X', 'Sign for Settlement Price (blank, "+" or "-")'),
            32:(1, 140, 140, 'AN', 'X', 'Sign for Strike Price (blank, "+" or "-")'),
            33:(5, 141, 145, 'N', '9V9(4)', 'Current Delta'),
            34:(1, 146, 146, 'AN', 'X', 'Sign for Current Delta (blank, "+" or "-")'),
            35:(1, 147, 147, 'AN', 'X', 'Current Delta Business-Day Flag -- "C" means this is today\'s end-of-day delta, "I" means this is an intraday theoretical delta for today, "P" means this is the previous day\'s end-of-day delta, and "X" or any other value means that no delta is available.'),
            36:(7, 148, 154, 'N', '9(7)', 'Start of Day Price'),
            37:(1, 155, 155, 'AN', 'X', 'Sign for Start of Day Price (blank, "+" or "-")'),
            38:(2, 156, 157, 'N', '9(2)', 'Implied Volatility Exponent'),
            39:(1, 158, 158, 'AN', 'X', 'Sign for Implied Volatility Exponent (blank, "+" or "-")'),
            40:(14, 159, 172, 'N', '9(7)V9(7)', 'Contract-specific Contract Value Factor (for variable tick options only)'),
            41:(2, 173, 174, 'N', '9(2)', 'Contract-specific Contract Value Factor Exponent (for variable tick options only)'),
            42:(1, 175, 175, 'AN', 'X', 'Sign for Contract-specific Contract Value Factor Exponent (blank, "+" or "-") (for variable tick options only)'),
            43:(14, 176, 189, 'N', '9(7)V9(7)', 'Contract-specific Strike Value Factor (for variable tick options only)'),
            44:(2, 190, 191, 'N', '9(2)', 'Contract-specific Strike Value Factor Exponent (for variable tick options only)'),
            45:(1, 192, 192, 'AN', 'X', 'Sign for Contract-specific Strike Value Factor Exponent (blank, "+" or "-") (for variable tick options only)'),
            }

    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type81RecordsStandard)

    def parseRecord(self):
        if (self.getRecordFieldStr(0) == '81'):
            return self.parse81Record()
        if (self.getRecordFieldStr(0) == '82'):
            return self.parse82Record()
        if (self.getRecordFieldStr(0) == '83'):
            return self.parse83Record()
        if (self.getRecordFieldStr(0) == '84'):
            return self.parse84Record()
        
    def parse81Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type81RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Commodity (Product) Code'] = self.getRecordFieldStr(2)
        rt['Underlying Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Product Type Code'] = self.getRecordFieldStr(4)
        rt['Option Right Code'] = self.getRecordFieldStr(5)
        rt['Futures Contract Month'] = self.getRecordFieldStr(6)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(7)
        #rt['Filler'] = self.getRecordFieldStr(8)
        rt['Option Contract Month'] = self.getRecordFieldStr(9)
        rt['Option Contract Day or Week Code'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        rt['Option Strike Price'] = self.getRecordFieldStr(12)
        rt['Array Value 1'] = self.getRecordFieldStr(13)
        rt['Sign for Array Value 1'] = self.getRecordFieldStr(14)
        rt['Array Value 2'] = self.getRecordFieldStr(15)
        rt['Sign for Array Value 2'] = self.getRecordFieldStr(16)
        rt['Array Value 3'] = self.getRecordFieldStr(17)
        rt['Sign for Array Value 3'] = self.getRecordFieldStr(18)
        rt['Array Value 4'] = self.getRecordFieldStr(19)
        rt['Sign for Array Value 4'] = self.getRecordFieldStr(20)
        rt['Array Value 5'] = self.getRecordFieldStr(21)
        rt['Sign for Array Value 5'] = self.getRecordFieldStr(22)
        rt['Array Value 6'] = self.getRecordFieldStr(23)
        rt['Sign for Array Value 6'] = self.getRecordFieldStr(24)
        rt['Array Value 7'] = self.getRecordFieldStr(25)
        rt['Sign for Array Value 7'] = self.getRecordFieldStr(26)
        rt['Array Value 8'] = self.getRecordFieldStr(27)
        rt['Sign for Array Value 8'] = self.getRecordFieldStr(28)
        rt['Array Value 9'] = self.getRecordFieldStr(29)
        rt['Sign for Array Value 9'] = self.getRecordFieldStr(30)
        rt['High-Precision Settlement Price'] = self.getRecordFieldStr(31)
        rt['High-Precision Settlement Price Flag'] = self.getRecordFieldStr(32)
        return rt

    def parse82Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type82RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Commodity (Product) Code'] = self.getRecordFieldStr(2)
        rt['Underlying Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Product Type Code'] = self.getRecordFieldStr(4)
        rt['Option Right Code'] = self.getRecordFieldStr(5)
        rt['Futures Contract Month'] = self.getRecordFieldStr(6)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(7)
        #rt['Filler'] = self.getRecordFieldStr(8)
        rt['Option Contract Month'] = self.getRecordFieldStr(9)
        rt['Option Contract Day or Week Code'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        rt['Option Strike Price'] = self.getRecordFieldStr(12)
        rt['Array Value 10'] = self.getRecordFieldStr(13)
        rt['Sign for Array Value 10'] = self.getRecordFieldStr(14)
        rt['Array Value 11'] = self.getRecordFieldStr(15)
        rt['Sign for Array Value 11'] = self.getRecordFieldStr(16)
        rt['Array Value 12'] = self.getRecordFieldStr(17)
        rt['Sign for Array Value 12'] = self.getRecordFieldStr(18)
        rt['Array Value 13'] = self.getRecordFieldStr(19)
        rt['Sign for Array Value 13'] = self.getRecordFieldStr(20)
        rt['Array Value 14'] = self.getRecordFieldStr(21)
        rt['Sign for Array Value 14'] = self.getRecordFieldStr(22)
        rt['Array Value 15'] = self.getRecordFieldStr(23)
        rt['Sign for Array Value 15'] = self.getRecordFieldStr(24)
        rt['Array Value 16'] = self.getRecordFieldStr(25)
        rt['Sign for Array Value 16'] = self.getRecordFieldStr(26)
        rt['SPAN Composite Delta'] = self.getRecordFieldStr(27)
        rt['Sign for SPAN Composite Delta'] = self.getRecordFieldStr(28)
        rt['Implied Volatility as decimal fraction'] = self.getRecordFieldStr(29)
        rt['Settlement Price'] = self.getRecordFieldStr(30)
        rt['Sign for Settlement Price'] = self.getRecordFieldStr(31)
        rt['Sign for Strike Price'] = self.getRecordFieldStr(32)
        rt['Current Delta'] = self.getRecordFieldStr(33)
        rt['Sign for Current Delta'] = self.getRecordFieldStr(34)
        rt['Current Delta Business-Day Flag'] = self.getRecordFieldStr(35)
        rt['Start of Day Price'] = self.getRecordFieldStr(36)
        rt['Sign for Start of Day Price'] = self.getRecordFieldStr(37)
        rt['Implied Volatility Exponent'] = self.getRecordFieldStr(38)
        rt['Sign for Implied Volatility Exponent'] = self.getRecordFieldStr(39)
        rt['Contract-specific Contract Value Factor'] = self.getRecordFieldStr(40)
        rt['Contract-specific Contract Value Factor Exponent'] = self.getRecordFieldStr(41)
        rt['Sign for Contract-specific Contract Value Factor Exponent'] = self.getRecordFieldStr(42)
        rt['Contract-specific Strike Value Factor'] = self.getRecordFieldStr(43)
        rt['Contract-specific Strike Value Factor Exponent'] = self.getRecordFieldStr(44)
        rt['Sign for Contract-specific Strike Value Factor Exponent'] = self.getRecordFieldStr(45)
        return rt

    def parse83Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type83RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Commodity (Product) Code'] = self.getRecordFieldStr(2)
        rt['Underlying Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Product Type Code'] = self.getRecordFieldStr(4)
        rt['Option Right Code'] = self.getRecordFieldStr(5)
        rt['Futures Contract Month'] = self.getRecordFieldStr(6)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(7)
        #rt['Filler'] = self.getRecordFieldStr(8)
        rt['Option Contract Month'] = self.getRecordFieldStr(9)
        rt['Option Contract Day or Week Code'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        rt['Option Strike Price'] = self.getRecordFieldStr(12)
        rt['Array Value 1'] = self.getRecordFieldStr(13)
        rt['Sign for Array Value 1'] = self.getRecordFieldStr(14)
        rt['Array Value 2'] = self.getRecordFieldStr(15)
        rt['Sign for Array Value 2'] = self.getRecordFieldStr(16)
        rt['Array Value 3'] = self.getRecordFieldStr(17)
        rt['Sign for Array Value 3'] = self.getRecordFieldStr(18)
        rt['Array Value 4'] = self.getRecordFieldStr(19)
        rt['Sign for Array Value 4'] = self.getRecordFieldStr(20)
        rt['Array Value 5'] = self.getRecordFieldStr(21)
        rt['Sign for Array Value 5'] = self.getRecordFieldStr(22)
        rt['Array Value 6'] = self.getRecordFieldStr(23)
        rt['Sign for Array Value 6'] = self.getRecordFieldStr(24)
        rt['Array Value 7'] = self.getRecordFieldStr(25)
        rt['Sign for Array Value 7'] = self.getRecordFieldStr(26)
        rt['Array Value 8'] = self.getRecordFieldStr(27)
        rt['Sign for Array Value 8'] = self.getRecordFieldStr(28)
        rt['Array Value 9'] = self.getRecordFieldStr(29)
        rt['Sign for Array Value 9'] = self.getRecordFieldStr(30)
        rt['High-Precision Settlement Price'] = self.getRecordFieldStr(31)
        rt['High-Precision Settlement Price Flag'] = self.getRecordFieldStr(32)
        return rt

    def parse84Record(self):
        self.changeStrut_Type0RecordsStandard(self.Strut_Type84RecordsStandard)
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Commodity (Product) Code'] = self.getRecordFieldStr(2)
        rt['Underlying Commodity (Product) Code'] = self.getRecordFieldStr(3)
        rt['Product Type Code'] = self.getRecordFieldStr(4)
        rt['Option Right Code'] = self.getRecordFieldStr(5)
        rt['Futures Contract Month'] = self.getRecordFieldStr(6)
        rt['Futures Contract Day or Week Code'] = self.getRecordFieldStr(7)
        #rt['Filler'] = self.getRecordFieldStr(8)
        rt['Option Contract Month'] = self.getRecordFieldStr(9)
        rt['Option Contract Day or Week Code'] = self.getRecordFieldStr(10)
        #rt['Filler'] = self.getRecordFieldStr(11)
        rt['Option Strike Price'] = self.getRecordFieldStr(12)
        rt['Array Value 10'] = self.getRecordFieldStr(13)
        rt['Sign for Array Value 10'] = self.getRecordFieldStr(14)
        rt['Array Value 11'] = self.getRecordFieldStr(15)
        rt['Sign for Array Value 11'] = self.getRecordFieldStr(16)
        rt['Array Value 12'] = self.getRecordFieldStr(17)
        rt['Sign for Array Value 12'] = self.getRecordFieldStr(18)
        rt['Array Value 13'] = self.getRecordFieldStr(19)
        rt['Sign for Array Value 13'] = self.getRecordFieldStr(20)
        rt['Array Value 14'] = self.getRecordFieldStr(21)
        rt['Sign for Array Value 14'] = self.getRecordFieldStr(22)
        rt['Array Value 15'] = self.getRecordFieldStr(23)
        rt['Sign for Array Value 15'] = self.getRecordFieldStr(24)
        rt['Array Value 16'] = self.getRecordFieldStr(25)
        rt['Sign for Array Value 16'] = self.getRecordFieldStr(26)
        rt['Composite Delta'] = self.getRecordFieldStr(27)
        rt['Sign for Composite Delta'] = self.getRecordFieldStr(28)
        rt['Implied Volatility as decimal fraction'] = self.getRecordFieldStr(29)
        rt['Settlement Price'] = self.getRecordFieldStr(30)
        rt['Sign for Settlement Price'] = self.getRecordFieldStr(31)
        rt['Sign for Strike Price'] = self.getRecordFieldStr(32)
        rt['Current Delta'] = self.getRecordFieldStr(33)
        rt['Sign for Current Delta'] = self.getRecordFieldStr(34)
        rt['Current Delta Business-Day Flag'] = self.getRecordFieldStr(35)
        rt['Start of Day Price'] = self.getRecordFieldStr(36)
        rt['Sign for Start of Day Price'] = self.getRecordFieldStr(37)
        rt['Implied Volatility Exponent'] = self.getRecordFieldStr(38)
        rt['Sign for Implied Volatility Exponent'] = self.getRecordFieldStr(39)
        rt['Contract-specific Contract Value Factor'] = self.getRecordFieldStr(40)
        rt['Contract-specific Contract Value Factor Exponent'] = self.getRecordFieldStr(41)
        rt['Sign for Contract-specific Contract Value Factor Exponent'] = self.getRecordFieldStr(42)
        rt['Contract-specific Strike Value Factor'] = self.getRecordFieldStr(43)
        rt['Contract-specific Strike Value Factor Exponent'] = self.getRecordFieldStr(44)
        rt['Sign for Contract-specific Strike Value Factor Exponent'] = self.getRecordFieldStr(45)
        return rt


class TypeSRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {            
            0:(2, 1, 2, 'AN', 'X(2)', 'Record ID - "S "'),
            1:(6, 3, 8, 'AN', 'X(6)', 'Combined Commodity Code'),
            2:(2, 9, 10, 'AN', 'X(2)', 'Scanning / Intercommodity Spreading Method Code: - "01" for non-tiered processing (ie, all the contract months together constitute a single tier for both scanning and intercommodity spreading) - "02" for each futures contract month as its own scanning and intercommodity spreading tier - "10" for table-driven tiered scanning with non-tiered intercommodity spreading - "20" for table-driven tiered intercommodity spreading with non-tiered scanning - "21" for table-driven tiered scanning and tiered intercommodity spreading, with identical tier definitions for scanning and intercommodity spreading - "22" for table-driven tiered scanning and tiered intercommodity spreading, with scanning tiers and intercommodity spreading tiers defined independently, and with this record containing scanning tier definitions - "23" for table-driven tiered scanning and tiered intercommodity spreading, with scanning tiers and intercommodity spreading tiers defined independently, and with this record containing intercommodity spreading tier definitions - "30" for short option minimum charge rate tiers'),
            3:(2, 11, 12, 'N', '9(2)', 'Number of Tiers'),
            4:(2, 13, 14, 'N', '9(2)', 'Tier 1 - Tier number'),
            5:(6, 15, 20, 'N', '9(6)', 'Tier 1 - Starting Contract Month as CCYYMM'),
            6:(6, 21, 26, 'N', '9(6)', 'Tier 1 - Ending Contract Month as CCYYMM'),
            7:(2, 27, 28, 'N', '9(2)', 'Tier 2 - Tier number'),
            8:(6, 29, 34, 'N', '9(6)', 'Tier 2 - Starting Contract Month as CCYYMM'),
            9:(6, 35, 40, 'N', '9(6)', 'Tier 2 - Ending Contract Month as CCYYMM'),
            10:(2, 41, 42, 'N', '9(2)', 'Tier 3 - Tier number'),
            11:(6, 43, 48, 'N', '9(6)', 'Tier 3 - Starting Contract Month as CCYYMM'),
            12:(6, 49, 54, 'N', '9(6)', 'Tier 3 - Ending Contract Month as CCYYMM'),
            13:(2, 55, 56, 'N', '9(2)', 'Tier 4 - Tier number'),
            14:(6, 57, 62, 'N', '9(6)', 'Tier 4 - Starting Contract Month as CCYYMM'),
            15:(6, 63, 68, 'N', '9(6)', 'Tier 4 - Ending Contract Month as CCYYMM'),
            16:(2, 69, 70, 'N', '9(2)', 'Tier 5 - Tier number'),
            17:(6, 71, 76, 'N', '9(6)', 'Tier 5 - Starting Contract Month as CCYYMM'),
            18:(6, 77, 82, 'N', '9(6)', 'Tier 5 - Ending Contract Month as CCYYMM'),
            19:(1, 83, 83, 'AN', 'X(1)', 'Weighted Futures Price Risk Calculation Method - 1 for the normal calculation in which price risk is evaluated and then divided by net delta, 2 for the normal method but where the value is capped at the futures price scan range, and 3 for the special method in which the value is set to the futures price scan range'),
            20:(2, 84, 85, 'AN', 'X(2)', 'Tier 1 - Starting Contract Day or Week Code'),
            21:(2, 86, 87, 'AN', 'X(2)', 'Tier 1 - Ending Contract Day or Week Code'),
            22:(2, 88, 89, 'AN', 'X(2)', 'Tier 2 - Starting Contract Day or Week Code'),
            23:(2, 90, 91, 'AN', 'X(2)', 'Tier 2 - Ending Contract Day or Week Code'),
            24:(2, 92, 93, 'AN', 'X(2)', 'Tier 3 - Starting Contract Day or Week Code'),
            25:(2, 94, 95, 'AN', 'X(2)', 'Tier 3 - Ending Contract Day or Week Code'),
            26:(2, 96, 97, 'AN', 'X(2)', 'Tier 4 - Starting Contract Day or Week Code'),
            27:(2, 98, 99, 'AN', 'X(2)', 'Tier 4 - Ending Contract Day or Week Code'),
            28:(2, 100, 101, 'AN', 'X(2)', 'Tier 5 - Starting Contract Day or Week Code'),
            29:(2, 102, 103, 'AN', 'X(2)', 'Tier 5 - Ending Contract Day or Week Code'),
            30:(7, 104, 110, 'N', '9(7)', 'Tier 1 -- Short Option Minimum Charge Rate'),
            31:(7, 111, 117, 'N', '9(7)', 'Tier 2 -- Short Option Minimum Charge Rate'),
            32:(7, 118, 124, 'N', '9(7)', 'Tier 3 -- Short Option Minimum Charge Rate'),
            33:(7, 125, 131, 'N', '9(7)', 'Tier 4 -- Short Option Minimum Charge Rate'),
            34:(7, 132, 138, 'N', '9(7)', 'Tier 5 -- Short Option Minimum Charge Rate'),
            }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Record ID'] = self.getRecordFieldStr(0)
        rt['Combined Commodity Code'] = self.getRecordFieldStr(1)
        rt['Scanning / Intercommodity Spreading Method Code'] = self.getRecordFieldStr(2)
        rt['Number of Tiers'] = self.getRecordFieldStr(3)
        rt['Tier 1 - Tier number'] = self.getRecordFieldStr(4)
        rt['Tier 1 - Starting Contract Month'] = self.getRecordFieldStr(5)
        rt['Tier 1 - Ending Contract Month'] = self.getRecordFieldStr(6)
        rt['Tier 2 - Tier number'] = self.getRecordFieldStr(7)
        rt['Tier 2 - Starting Contract Month'] = self.getRecordFieldStr(8)
        rt['Tier 2 - Ending Contract Month'] = self.getRecordFieldStr(9)
        rt['Tier 3 - Tier number'] = self.getRecordFieldStr(10)
        rt['Tier 3 - Starting Contract Month'] = self.getRecordFieldStr(11)
        rt['Tier 3 - Ending Contract Month'] = self.getRecordFieldStr(12)
        rt['Tier 4 - Tier number'] = self.getRecordFieldStr(13)
        rt['Tier 4 - Starting Contract Month'] = self.getRecordFieldStr(14)
        rt['Tier 4 - Ending Contract Month'] = self.getRecordFieldStr(15)
        rt['Tier 5 - Tier number'] = self.getRecordFieldStr(16)
        rt['Tier 5 - Starting Contract Month'] = self.getRecordFieldStr(17)
        rt['Tier 5 - Ending Contract Month'] = self.getRecordFieldStr(18)
        rt['Weighted Futures Price Risk Calculation Method'] = self.getRecordFieldStr(19)
        rt['Tier 1 - Starting Contract Day or Week Code'] = self.getRecordFieldStr(20)
        rt['Tier 1 - Ending Contract Day or Week Code'] = self.getRecordFieldStr(21)
        rt['Tier 2 - Starting Contract Day or Week Code'] = self.getRecordFieldStr(22)
        rt['Tier 2 - Ending Contract Day or Week Code'] = self.getRecordFieldStr(23)
        rt['Tier 3 - Starting Contract Day or Week Code'] = self.getRecordFieldStr(24)
        rt['Tier 3 - Ending Contract Day or Week Code'] = self.getRecordFieldStr(25)
        rt['Tier 4 - Starting Contract Day or Week Code'] = self.getRecordFieldStr(26)
        rt['Tier 4 - Ending Contract Day or Week Code'] = self.getRecordFieldStr(27)
        rt['Tier 5 - Starting Contract Day or Week Code'] = self.getRecordFieldStr(28)
        rt['Tier 5 - Ending Contract Day or Week Code'] = self.getRecordFieldStr(29)
        rt['Tier 1 -- Short Option Minimum Charge Rate'] = self.getRecordFieldStr(30)
        rt['Tier 2 -- Short Option Minimum Charge Rate'] = self.getRecordFieldStr(31)
        rt['Tier 3 -- Short Option Minimum Charge Rate'] = self.getRecordFieldStr(32)
        rt['Tier 4 -- Short Option Minimum Charge Rate'] = self.getRecordFieldStr(33)
        rt['Tier 5 -- Short Option Minimum Charge Rate'] = self.getRecordFieldStr(34)
        return rt



class TypeTRecordsSE(TypeRecords):
    Strut_Type0RecordsStandard = {
            0:(2, 1, 2,'AN','X(2)',         'Record ID - "T "'),
            1:(3, 3, 5,'AN','X(3)',         'Convert-From Currency ISO Code'),
            2:(1, 6, 6,'AN','X',            'Convert-From Currency One-Byte Code'),
            3:(3, 7, 9,'AN','X(3)',         'Convert-To Currency ISO Code'),
            4:(1, 10, 10,'AN','X',          'Convert-To Currency One-Byte Code'),
            5:(10,11, 20,'N','9(4)V9(6)',   'Conversion Multiplier')
        }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['From Currency ISO Code'] = self.getRecordFieldStr(1)
        rt['From Currency One-Byte Code'] = self.getRecordFieldStr(2)
        rt['To Currency ISO Code'] = self.getRecordFieldStr(3)
        rt['To Currency One-Byte Code'] = self.getRecordFieldStr(4)
        rt['Conversion Multiplier'] = self.getRecordFieldStr(5)
        return rt

class TypePRecordsSE(TypeRecords):
    product_type_code = ('FUT','PHY','CMB','OOF','OOP','OOC')
    Strut_Type0RecordsStandard = {
            0:(2,    1,     2,'AN','X(2)',         'Record ID - "P "'),
            1:(3,    3,      5,'AN','X(3)',         'Exchange Acronym'),
            2:(10,  6,      15,'AN','X(10)',      'Product (Commodity) Code'),
            3:(3,   16,     18,'AN','X(3)',       'Product Type Code'),
            4:(15,  19,     33,'AN','X(15)',     'Product Name (short name)'),
            5:(3,    34,   36,   'N',   '9(3)',    'Settlement Price Decimal Locator.  If negative, put "-" in the first byte.  For example, "-02" means negative two.'),
            6:(3,    37,   39,   'N',   '9(3)',    'Strike Price Decimal Locator (for options only).   If negative, put "-" in the first byte.  For example, "-02" means negative two.'),
            7:(1,    40,   40,   'AN',   'X',    'Settlement Price Alignment Code'),
            8:(1,    41,   41,   'AN',   'X',    'Strike Price Alignment Code (for options only)'),
            9:(14,    42,   55,   'N',   '9(7)V9(7)',    'Contract Value Factor (Multiplier)'),
            10:(8,    56,   63,   'N',   '9(6)V9(2)',    'Standard Cabinet Option Value'),
            11:(2,    64,   65,   'N',   '9(2)',    'Quoted Position Quantity per Contract (CBOT "Futures Per Contract")'),
            12:(3,    66,   68,   'AN',   'X(3)',    'Settlement Currency ISO Code'),
            13:(1,    69,   69,   'AN',   'X',    'Settlement Currency One-Byte Code'),
            14:(3,    70,   72,   'AN',   'X(3)',    'Price Quotation Method - STD for standard physical commodities, IDX for standard indices, such as equity indices, INT for interest-rate indices such as Eurodollars'),
            15:(1,    73,   73,   'AN',   'X',    'Sign for the Contract Value Factor (Multiplier) exponent ("-" is negative, any other value is positive)'),
            16:(2,    74,   75,   'N',   '9(2)',    'Contract Value Factor (Multiplier) exponent'),
            17:(4,    76,   79,   'AN',   'X(4)',    'Exercise Style - AMER for american style options, EURO for european style options (AMER is default)'),
            18:(35,    80,   114,   'AN',   'X(35)',    'Product Long Name (optional field)'),
            19:(1,    115,   115,   'AN',   'X(1)',    'Positionable Product Indicator -- N means non-positionable, in other words contracts in this product family cannot directly hold positions, typically because they are the underlying of an option on a combination, and positions in the combination are immediately broken out into their legs.  Y or blank means positionable.'),
            20:(1,    116,   116,   'AN',   'X(1)',    'Money Calculation Method -- N means "nominal", ie, position quantities are quoted in nominal amounts and variation or premium calculations for this product must use OTC-style rounding, I means interest rate swap method for calculating mark-to-market amounts, and F or blank means "futures-style", where position quantities are in "contract" terms and variation and premium calculations use normal futures-style rounding.'),
            21:(5,    117,   121,   'AN',   'X(5)',    'Valuation Method -- FUT for futures-style (daily banking of mark-to-market amounts), FUTDA for futures-style with a cash adjustment, FWD for forward (collateralization of mark-to-market amounts), or EQTY (equity-style, ie daily payment or collection of price obligation amounts, for example option premium)'),
            22:(5,    122,   126,   'AN',   'X(5)',    'Settlement Method -- CASH for cash-settled, or DELIV for physically delivered.  For futures or forwards, this indicates whether it is cash-settled or physically delivered.  All options on futures are physically delivered because they exercise into an underlying future.'),
            23:(5,    127,   131,   'N',   '9V9(4)',    'This and the following three fields are for Physically Delivered FX forward products only (and will be populated for these only):  FX Spot Date Collateralization Gain Credit Rate (as a decimal fraction) -- percentage credit to be provided for gains, beginning on spot date and continuing through value date'),
            24:(5,    132,   136 ,  'N',   '9V9(4)',    'FX Pre-Spot Date Collateralization Gain Credit Rate (as a decimal fraction) -- percentage credit to be provided for gains, beginning on the specified number of weekdays prior to spot date, and continuing through the weekday prior to spot date'),
            25:(2,    137,   138,   'N',   '99',    'FX Pre-Spot Date Number of Days -- provides that specified number of weekdays.  For example, a value of  4 means that the pre-spot date collateralization gain credit rate applies beginning on the fourth weekday prior to spot date'),
            26:(5,    139,   143,   'N',   '9V9(4)',    'FX Forward Collateralization Gain Credit Rate -- percentage credit to be provided for gains, for contracts which are further forward than the pre-spot number of weekdays.'),
            27:(14,    144,   157,   'N',   '9(7)V9(7)',    'Equivalent Position Factor'),
            28:(2,    158,   159,   'N',   '9(2)',    'Equivalent Position Factor Exponent'),
            29:(1,    160,   160,   'AN',   'X',    'Sign for Equivalent Position Factor Exponent (blank, "+" or "-")'),
            30:(1,    161,   161,   'AN',   'X',    'Variable Tick Option flag -- "1" means this product is a variable tick option, blank or any other value means this is a standard (not a variable) tick option.  Standard options have a contract value factor and strike value factor that are the same for all options in a series, and are defined for the series.  A variable tick option may have a contract value factor and/or strike value factor defined for each individual contract (on the type "8" record), and if defined, the value provided overrides any value defined for the option series.'),
            31:(3,    162,   164,   'AN',   'X(3)',    'Price Quotation Currency - normally, the currency in which the price is quoted is the same as the Settlement Currency (the currency in which the variation or premium are denominated), but for some products these are different. If this field is blank, the Price Quotation Currency is assumed to be the same as the Settlement Currency.')
        }
    def __init__(self):
        TypeRecords.__init__(self,self.Strut_Type0RecordsStandard)

    def parseRecord(self):
        rt = {}
        rt['Exchange Acronym'] = self.getRecordFieldStr(1)
        rt['Product (Commodity) Code'] = self.getRecordFieldStr(2)
        rt['Product Type Code'] = self.getRecordFieldStr(3)
        rt['Product Name (short name)'] = self.getRecordFieldStr(4)
        rt['Settlement Price Decimal Locator'] = float(self.getRecordFieldStr(5))
        rt['Strike Price Decimal Locator'] = float(self.getRecordFieldStr(6))
        rt['Settlement Price Alignment Code'] = self.getRecordFieldStr(7)
        rt['Strike Price Alignment Code'] = self.getRecordFieldStr(8)
        rt['Contract Value Factor (Multiplier)'] = float(self.getRecordFieldStr(9))/10000000
        rt['Standard Cabinet Option Value'] = float(self.getRecordFieldStr(10))/100
        rt['Quoted Position Quantity per Contract'] = self.getRecordFieldStr(11)
        rt['Settlement Currency ISO Code'] = self.getRecordFieldStr(12)
        rt['Settlement Currency One-Byte Code'] = self.getRecordFieldStr(13)
        rt['Price Quotation Method'] = self.getRecordFieldStr(14)
        rt['Sign for the Contract Value Factor'] = self.getRecordFieldStr(15)
        rt['Contract Value Factor (Multiplier) exponent'] = float(self.getRecordFieldStr(16))
        rt['Exercise Style'] = self.getRecordFieldStr(17)
        rt['Product Long Name'] = self.getRecordFieldStr(18)
        rt['Positionable Product Indicator'] = self.getRecordFieldStr(19)
        rt['Money Calculation Method'] = self.getRecordFieldStr(20)
        rt['Valuation Method'] = self.getRecordFieldStr(21)
        rt['Settlement Method'] = self.getRecordFieldStr(22)
        try:
            rt['FX Spot Date Collateralization Gain Credit Rate'] = float(self.getRecordFieldStr(23))/10000
        except ValueError,e:
            rt['FX Spot Date Collateralization Gain Credit Rate'] = 0.0
        try:
            rt['FX Pre-Spot Date Collateralization Gain Credit Rate'] = float(self.getRecordFieldStr(24))/10000
        except ValueError,e:
            rt['FX Pre-Spot Date Collateralization Gain Credit Rate'] =  0.0
        try:
            rt['FX Pre-Spot Date Number of Days'] = float(self.getRecordFieldStr(25))
        except ValueError,e:
            rt['FX Pre-Spot Date Number of Days'] = 0.0
        try:
            rt['FX Forward Collateralization Gain Credit Rate'] = float(self.getRecordFieldStr(26))/10000
        except ValueError,e:
            rt['FX Forward Collateralization Gain Credit Rate'] = 0.0
        try:
            rt['Equivalent Position Factor'] = float(self.getRecordFieldStr(27))/10000000
        except ValueError,e:
            rt['Equivalent Position Factor'] = 0.0
        try:
            rt['Equivalent Position Factor Exponent'] = float(self.getRecordFieldStr(28))
        except ValueError,e:
            rt['Equivalent Position Factor Exponent'] = 0.0
        rt['Sign for Equivalent Position Factor Exponent'] = self.getRecordFieldStr(29)
        rt['Variable Tick Option flag'] = self.getRecordFieldStr(30)
        rt['Price Quotation Currency'] = self.getRecordFieldStr(31)
        return rt

    
            
class TimSpan:     
    TypeFormats = {
                    '0':'Standard Format',
                    '1':'Expanded Format',
                    '2':'Paris Expanded Format',
                    '3':'Expanded Format and Paris Expanded Format',
                    '4':'Standard and Expanded Format',
                    '5':'Standard Formats (both Unpacked and Packed)',
                  }
    TypeRecords = {
                "0":('Exchange Complex Header',('0','3')),
                "1":('Exchange Header',('0','3')),
                "2":('Combined Commodity Definition',('0','1','2')),
                "3":('Intracommodity Spread Charge Parameters',('0','1','2')),
                "4":('Delivery (Spot) Charge Parameters',('0','1','2')),
                "5":('Combined Commodity Groups',('0','1','2')),
                "6":('Intercommodity Spreads',('0','1','2')),
                "8":('Risk Arrays',('5','1','2')),
                "9":('Debt Securities',('0','1')),
                "9":('Liquidation Risk Prices',('3',)),
                "B":('Array Calculation Parameters',('0','1','2')),
                "C":('Tier to Tier Intracommodity Spreads',('0','3')),
                "E":('Series to Series Intracommodity Spreads',('4',)),
                "P":('Price Conversion Parameters',('4','2')),
                "R":('Commodity (Product) Redefinition',('0','1')),
                "S":('Scanning Tiers',('0','3')),
                "T":('Currency Conversion Rates',('4','2')),
                "V":('Daily Adjustment Rates / Value Maintenance Rates',('0','1')),
                "X":('Combination Margining Method',('4',)),
                "Y":('Option on Combination Product Family Definition',('4',)),
                "Z":('Combination Underlying Legs',('4',))
    }
    def __init__(self,p_date):
        self.toDay =  datetime.date.today().strftime('%Y%m%d') 
        self.spanODir = 'span'
        self.priceODir = 'settleprice'
        self.zipFilesDict = {}
        self.initLIST()
        self.initTRC()
        if (p_date):
            self.toDay = p_date
        #self.getHKSettleDailyPrice()
        #self.processDownloadPriceFiles()
        #self.dealPriceFiles()
        self.processDownloadSpanFiles()
        self.dealSpanFiles()

    def initLIST(self):
        self.ExchangeHeader  = {} # 1
        self.CombinedCommodityDefinition  = {} # 2
        self.IntracommoditySpreadChargeParameters = {} # 3
        self.DeliveryChargeParameters = {} # 4
        self.CombinedCommodityGroups = {} # 5
        self.IntercommoditySpreads = {} # 6
        self.RiskArrays = {} # 8
        self.DebtSecurities = {} # 9
        self.LiquidationRiskPrices = {} # 9
        self.ArrayCalculationParameters = {} # B
        self.TiertoTierIntracommoditySpreads = {} # C
        self.SeriestoSeriesIntracommoditySpreads = {} # E
        self.PriceConversionParameters = {} # P
        self.CommodityRedefinition = {} # R
        self.ScanningTiers = {} # S
        self.CurrencyConversionRates = {} # T
        self.DailyAdjustmentRatesValueMaintenanceRates = {} # V
        self.CombinationMarginingMethod = {} # X
        self.OptiononCombinationProductFamilyDefinition = {} # Y
        self.CombinationUnderlyingLegs = {} # Z
        
    def initTRC(self):
        self.ct_0 = Type0RecordsS()
        self.ct_1 = Type1RecordsSE()
        self.ct_2 = Type2RecordsSE()
        self.ct_3 = Type3RecordsSE()
        self.ct_4 = Type4RecordsSE()
        self.ct_5 = Type5RecordsSE()
        self.ct_6 = Type6RecordsSE()
        self.ct_8 = Type8RecordsSE()
        self.ct_9 = Type9RecordsSE()
        self.ct_B = TypeBRecordsSE()
        self.ct_E = TypeERecordsSE()
        self.ct_R = TypeRRecordsSE()
        self.ct_S = TypeSRecordsSE()
        self.ct_T = TypeTRecordsSE()
        self.ct_P = TypePRecordsSE()
        self.ct_V = TypeVRecordsSE()
        self.ct_Z = TypeZRecordsSE()

    def processDownloadPriceFiles(self):
        for k,v in settlePriceFiles.items():
            m_url = v[0].replace('YYYYMMDD',self.toDay)
            m_url = m_url.replace('YYMMDD',self.toDay[2:])
            rt = self.getPriceFile(k,m_url)

    def dealPriceFiles(self):
        priceFKeys = settlePriceFiles.keys()
        if ('P-holidays' in priceFKeys):
            priceFKeys.remove('P-holidays' )
        if (self.zipFilesDict):
            for k in priceFKeys:
                if (self.zipFilesDict.has_key(k)):
                    self.dealPriceXml(self.zipFilesDict[k])
     
    def getPriceFile(self,p_k,p_url):
        import urlparse
        url=urlparse.urlparse(p_url)
        (m_path,m_file) = os.path.split(url.path)
        if (not os.path.exists(self.priceODir)):
            os.makedirs(self.priceODir)
        self.subPODir = os.path.join(self.priceODir,self.toDay)
        if (not os.path.exists(self.subPODir)):
            os.makedirs(self.subPODir)     
        if (url.scheme == 'ftp'):
            self.getPriceFileFTP(p_k,url.netloc,m_path,m_file)
            self.zipFilesDict[p_key]= fn
        if (url.scheme == 'http'):
            self.getPriceFileHTTP(p_k,p_url,os.path.split(p_url)[1])
                    
    def processDownloadSpanFiles(self):
        for k,v in spanFiles.items():
            m_url = v[0].replace('YYYYMMDD',self.toDay)
            m_url = m_url.replace('YYMMDD',self.toDay[2:])
            rt = self.getSpanFile(k,m_url)
        
    def getSpanFile(self,p_k,p_url):
        import urlparse
        url=urlparse.urlparse(p_url)
        (m_path,m_file) = os.path.split(url.path)
        if (not os.path.exists(self.spanODir)):
            os.makedirs(self.spanODir)
        self.subODir = os.path.join(self.spanODir,self.toDay)
        if (not os.path.exists(self.subODir)):
            os.makedirs(self.subODir)
        if (url.scheme == 'ftp'):
            self.getSpanFileFTP(p_k,url.netloc,m_path,m_file)
            self.zipFilesDict[p_key]= fn
        if (url.scheme == 'http'):
            self.getSpanFileHTTP(p_k,p_url,os.path.split(p_url)[1])

    def dealSpanFiles(self):
        if (self.zipFilesDict):
            if (self.zipFilesDict.has_key('CBOT,CME, COMEX and NYMEX')):
                self.dealCMESpan(self.zipFilesDict['CBOT,CME, COMEX and NYMEX'])
            if (self.zipFilesDict.has_key('LME-CME')):
                self.dealLMECMESpan(self.zipFilesDict['LME-CME'])
            if (self.zipFilesDict.has_key('LME-LCH')):
                self.dealLCHCMESpan(self.zipFilesDict['LME-LCH'])
            if (self.zipFilesDict.has_key('SIMEX')):
                self.dealSGXSpan(self.zipFilesDict['SIMEX'])
            if (self.zipFilesDict.has_key('NYBOT')):
                self.dealNYBOTSpan(self.zipFilesDict['NYBOT'])
            if (self.zipFilesDict.has_key('IPE')):
                self.dealIPESpan(self.zipFilesDict['IPE'])
            if (self.zipFilesDict.has_key('CBOE')):
                self.dealCBOESpan(self.zipFilesDict['CBOE'])
            if (self.zipFilesDict.has_key('LIFFE')):
                self.dealLIFFESpan(self.zipFilesDict['LIFFE'])
            if (self.zipFilesDict.has_key('BMDC')):
                self.dealBMDCSpan(self.zipFilesDict['BMDC'])
            if (self.zipFilesDict.has_key('TOCOM')):
                self.dealTOCOMSpan(self.zipFilesDict['TOCOM'])
            if (self.zipFilesDict.has_key('TAIFEX')):
                self.dealTAIFEXSpan(self.zipFilesDict['TAIFEX'])
                
    def dealSpan(self,zfname):
        zf = zipfile.ZipFile(zfname,'r')     
        fn =  zf.namelist()[0]
        f = StringIO.StringIO(zf.read(fn))
        cur_exch = None
        for l in f:
            if (l):
                if (l[0] not in ['0','1','V']):
                    continue
                if (l[0]=='0'):
                    rt = self.ct_0(l)
                if (l[0]=='1'):
                    cur_exch = self.ct_1(l)
                    if (not self.CombinedCommodityDefinition.has_key(cur_exch['Exchange Acronym'])): # 2
                        self.CombinedCommodityDefinition[cur_exch['Exchange Acronym']]= []
                    if (not self.IntracommoditySpreadChargeParameters.has_key(cur_exch['Exchange Acronym'])): # 3
                        self.IntracommoditySpreadChargeParameters[cur_exch['Exchange Acronym']]= []
                    if (not self.DeliveryChargeParameters.has_key(cur_exch['Exchange Acronym'])): # 4
                        self.DeliveryChargeParameters[cur_exch['Exchange Acronym']]= []
                    if (not self.CombinedCommodityGroups.has_key(cur_exch['Exchange Acronym'])): # 5
                        self.CombinedCommodityGroups[cur_exch['Exchange Acronym']]= []
                    if (not self.IntercommoditySpreads.has_key(cur_exch['Exchange Acronym'])): # 6
                        self.IntercommoditySpreads[cur_exch['Exchange Acronym']] = []
                    if (not self.RiskArrays.has_key(cur_exch['Exchange Acronym'])): # 8
                        self.RiskArrays[cur_exch['Exchange Acronym']] = []
                    if (not self.DebtSecurities.has_key(cur_exch['Exchange Acronym'])): # 9
                        self.DebtSecurities[cur_exch['Exchange Acronym']] = []
                    if (not self.ArrayCalculationParameters.has_key(cur_exch['Exchange Acronym'])): # B
                        self.ArrayCalculationParameters[cur_exch['Exchange Acronym']] = []
                    if (not self.SeriestoSeriesIntracommoditySpreads.has_key(cur_exch['Exchange Acronym'])): # E
                        self.SeriestoSeriesIntracommoditySpreads[cur_exch['Exchange Acronym']] = []
                    if (not self.PriceConversionParameters.has_key(cur_exch['Exchange Acronym'])): # P
                        self.PriceConversionParameters[cur_exch['Exchange Acronym']] = []
                    if (not self.CommodityRedefinition.has_key(cur_exch['Exchange Acronym'])): # R
                        self.CommodityRedefinition[cur_exch['Exchange Acronym']] = []
                    if (not self.ScanningTiers.has_key(cur_exch['Exchange Acronym'])): #S
                        self.ScanningTiers[cur_exch['Exchange Acronym']] = []
                    if (not self.DailyAdjustmentRatesValueMaintenanceRates.has_key(cur_exch['Exchange Acronym'])): #V
                        self.DailyAdjustmentRatesValueMaintenanceRates[cur_exch['Exchange Acronym']] = []
                    if (not self.CombinationUnderlyingLegs.has_key(cur_exch['Exchange Acronym'])): #Z
                        self.CombinationUnderlyingLegs[cur_exch['Exchange Acronym']] = []

                if (l[0]=='2'):
                    rt = self.ct_2(l)
                    logger.debug(rt)
                    self.CombinedCommodityDefinition[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='3'): 
                    rt = self.ct_3(l)
                    logger.debug(rt)
                    self.IntracommoditySpreadChargeParameters[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='4'):
                    rt = self.ct_4(l)
                    logger.debug(rt)
                    self.DeliveryChargeParameters[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='5'):
                    rt = self.ct_5(l)
                    logger.debug(rt)
                    self.CombinedCommodityGroups[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='6'):
                    rt = self.ct_6(l)
                    logger.debug(rt)
                    self.IntercommoditySpreads[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='8'):
                    rt = self.ct_8(l)
                    logger.debug(rt)
                    self.RiskArrays[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='9'):
                    rt = self.ct_9(l)
                    logger.debug(rt)
                    self.DebtSecurities[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='B'):
                    rt = self.ct_B(l)
                    logger.debug(rt)
                    self.ArrayCalculationParameters[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='E'): 
                    rt = self.ct_E(l)
                    logger.debug(rt)
                    self.SeriestoSeriesIntracommoditySpreads[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='P'):
                    rt = self.ct_P(l)
                    logger.debug(rt)
                    self.PriceConversionParameters[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='R'):
                    rt = self.ct_R(l)
                    logger.debug(rt)
                    self.CommodityRedefinition[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='S'): 
                    rt = self.ct_S(l)
                    logger.debug(rt)
                    self.ScanningTiers[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='T'):
                    rt = self.ct_T(l)
                    logger.debug(rt)
                    self.CurrencyConversionRates[(rt['From Currency ISO Code'],rt['To Currency ISO Code'])] = rt
                if (l[0]=='V'):
                    rt = self.ct_V(l)
                    logger.debug(rt)
                    self.DailyAdjustmentRatesValueMaintenanceRates[cur_exch['Exchange Acronym']].append(rt)
                if (l[0]=='Z'):
                    rt = self.ct_Z(l)
                    logger.debug(rt)
                    self.CombinationUnderlyingLegs[cur_exch['Exchange Acronym']].append(rt)
        #print self.CurrencyConversionRates
        '''
        for k,v in self.PriceConversionParameters.items():
            for kk,vv in v.items():
                print vv
        '''
    def dealCMESpan(self,zfname):
        print('dealCMESpan')
        logger.debug('begin dealCMESpan...')        
        self.dealSpan(zfname)
        logger.debug('...dealCMESpan end.')        
    def dealLMECMESpan(self,zfname):
        print('dealLMECMESpan')
    def dealLCHCMESpan(self,zfname):
        print('dealLCHCMESpan')
    def dealSGXSpan(self,zfname):
        print('dealSGXSpan')
    def dealNYBOTSpan(self,zfname):
        print('dealNYBOTSpan')
    def dealIPESpan(self,zfname):
        print('dealIPESpan')
    def dealCBOESpan(self,zfname):
        print('dealCBOESpan')
    def dealLIFFESpan(self,zfname):
        print('dealLIFFESpan')
    def dealBMDCSpan(self,zfname):
        print('dealBMDCSpan')
    def dealTOCOMSpan(self,zfname):
        print('dealTOCOMSpan')
    def dealTAIFEXSpan(self,zfname):
        print('dealTAIFEXSpan')

    def dealPriceXml(self,filename):
        def tryMore():
            f.seek(0)
            buf = f.read()
            i = buf.index('?>') + 3
            buf = '<rows>'+buf[i:]+'</rows>'
            try:
                return ET.fromstring(buf)
            except xml.etree.ElementTree.ParseError, e:
                return None
        db = TimDB()
        try:
            zf = zipfile.ZipFile(filename,'r')     
            fn =  zf.namelist()[0]
            f = StringIO.StringIO(zf.read(fn))
        except BadZipfile,e:
            logger.error('ERROR: BadZipfile %s' % filename)   
            return
        logger.info('Begin to parse XML %s.' % filename)
        try:
            doc = ET.parse(f).getroot()
        except xml.etree.ElementTree.ParseError, e:
            logger.error('ERROR: BadXMLfile %s' % fn) 
            logger.error('     : %s' % e) 
            doc = tryMore()
            if (not doc):
                return 
        for Batch in doc:
            if (Batch.tag == 'Batch'):
                m_records = []
                for MktDataFull in Batch:
                    m_record = {'ClearingBusinessDate':MktDataFull.attrib['BizDt']}
                    for child in MktDataFull:
                        if (child.tag == 'Instrmt'):
                            m_record['Symbol'] = child.attrib['Sym']
                            m_record['SecurityID'] = child.attrib['ID']
                            m_record['CFICode'] = child.attrib['CFI']
                            m_record['SecurityType'] = child.attrib['SecTyp']
                            m_record['MaturityMonthYear'] = child.attrib['MMY']
                            m_record['MaturityDate'] = child.attrib['MatDt']
                            m_record['SecurityExchange'] = child.attrib['Exch']
                            if (child.attrib.has_key('StrkPx')):
                                m_record['StrikePrice'] = child.attrib['StrkPx']
                            if (child.attrib.has_key('PutCall')):
                                m_record['PutOrCall'] = child.attrib['PutCall']
                            if (len(child) > 0):
                                for Evnt in child:
                                    if (Evnt.tag == 'Evnt'):
                                        if (Evnt.attrib['EventTyp']=='7'):
                                            m_record['Dt'] = Evnt.attrib['Dt']
                                            m_record['Txt'] = Evnt.attrib['Txt']
                        if (child.tag == 'Undly'):
                            m_record['Undly_CFI'] = child.attrib['CFI']                    
                            m_record['Undly_ID'] = child.attrib['ID']                    
                            m_record['Undly_Exch'] = child.attrib['Exch']                    
                            m_record['Undly_MMY'] = child.attrib['MMY']                    
                            m_record['Undly_SecTyp'] = child.attrib['SecTyp']                    
                            m_record['Undly_Src'] = child.attrib['Src']                    
                        if (child.tag == 'Full'):
                            if (child.attrib['Typ'] == '6'):
                                m_record['SettlementPrice'] = child.attrib['Px']
                                m_record['Mkt'] = child.attrib['Mkt']
                                if (child.attrib.has_key('HighPx')):
                                    m_record['HighPx'] = child.attrib['HighPx']
                                if (child.attrib.has_key('LowPx')):
                                    m_record['LowPx'] = child.attrib['LowPx']
                                if (child.attrib.has_key('PxDelta')):
                                    m_record['PriceDelta'] = child.attrib['PxDelta']
                                if (child.attrib.has_key('PxTyp')):
                                    m_record['PxTyp'] = child.attrib['PxTyp']
                            if (child.attrib['Typ'] == '0'):
                                m_record['BidPrice'] = child.attrib['Px']
                            if (child.attrib['Typ'] == '7'):
                                m_record['DailyHigh'] = child.attrib['Px']
                            if (child.attrib['Typ'] == '8'):
                                m_record['DailyLow'] = child.attrib['Px']
                            if (child.attrib['Typ'] == 'N'):
                                m_record['LowBid'] = child.attrib['Px']
                            if (child.attrib['Typ'] == 'O'):
                                m_record['HighBid'] = child.attrib['Px']
                            if (child.attrib['Typ'] == 'B'):
                                if (child.attrib['OpenClsSettlFlag'] == '4'):
                                    m_record['Volume'] = child.attrib['Sz']
                            if (child.attrib['Typ'] == 'C'):
                                if (child.attrib['OpenClsSettlFlag'] == '4'):
                                    m_record['OpenInterest'] = child.attrib['Sz']
                                    
                    db(m_record)
                    #logger.info('Succeed to DB a record %s.' % m_record['Symbol']+m_record['MaturityMonthYear'])
                    m_records.append(m_record)
            if (Batch.tag == 'FIXML'):
                m_records = []
                for SecDef in Batch:
                    if (SecDef.tag == 'SecDef'):
                        m_record = {'ClearingBusinessDate':SecDef.attrib['BizDt']}
                        for child in SecDef:
                            if (child.tag == 'Instrmt'):
                                if (child.attrib.has_key('Sym')):
                                    m_record['Symbol'] = child.attrib['Sym']
                                else:
                                    if (child.attrib.has_key('SecShortDesc')):
                                        m_record['Symbol'] = child.attrib['SecShortDesc']
                                    else:
                                        m_record['Symbol'] = ''
                                if (child.attrib.has_key('ID')):
                                    m_record['SecurityID'] = child.attrib['ID']
                                else:
                                    m_record['SecurityID'] = ''
                                m_record['CFICode'] = ''
                                m_record['SecurityType'] = child.attrib['SecTyp']
                                m_record['MaturityMonthYear'] = ''
                                m_record['MaturityDate'] = ''
                                m_record['SecurityExchange'] = child.attrib['Exch']
                                m_record['Multiplier'] = child.attrib['Mult']
                                m_record['SecurityDesc'] = child.attrib['Desc']
                                m_record['SecShortDesc'] = child.attrib['SecShortDesc']
                            if (child.tag == 'InstrmtExt'):
                                pass
                            if (child.tag == 'MktSegGrp'):
                                for child2 in child:
                                    if (child.tag == 'SecTrdgRules'):
                                        for child3 in child2:
                                            if (child3.tag == 'BaseTrdgRules'):
                                                for child4 in child3:
                                                    if (child4.tag == 'TickRules'):
                                                        m_record['StartTickPxRng'] = child4.attrib['StartTickPxRng']
                                                        m_record['EndTickPxRng'] = child4.attrib['EndTickPxRng']
                                                        m_record['TickIncr'] = child4.attrib['TickIncr']
                                                        m_record['TickRuleTyp'] = child4.attrib['TickRuleTyp']
                                                        #m_record['SettlementPrice'] = child4.attrib['EndTickPxRng']
                                                    if (child4.tag == 'LotTypRules'):
                                                        pass
                                            if (child3.tag == 'TrdgSesRulesGrp'):
                                                m_record['TrdDtInd'] = child3.attrib['TrdDtInd']
                                                m_record['StartTm'] = child3.attrib['StartTm']
                                                m_record['EndTm'] = child3.attrib['EndTm']
                                                m_record['RTH'] = child3.attrib['RTH']
                                    
                            if (child.tag == 'ProdClsfnGrp'):
                                pass
                        db(m_record)    
            logger.info('Succeed parsed %s XML records.' % len(m_records))

    def getHKSettleDailyPrice(self):
        import lxml
        import lxml.html
        from lxml.cssselect import CSSSelector
        import urllib2
        urlroot = 'https://www.hkex.com.hk'
        url = urlroot + '/eng/market/partcir/hkfe/2014hkfe.htm'
        buf = urllib2.urlopen(url).read()
        html = lxml.html.fromstring(buf)
        selAnchor = CSSSelector('a')
        foundElements = selAnchor(html)
        for Elements in foundElements:
            if (Elements.text == 'Final Settlement Prices'):
                href = Elements.get('href')
                fname = os.path.split(href)[1]
                fns = fname.split('_')
                if (not os.path.exists('HK')):
                    os.makedirs('HK')
                if (not os.path.exists('HK/'+fname)):
                    of = open('HK/'+fname,'w+b')
                    of.write(urllib2.urlopen(urlroot + href).read())                
                    #https://www.hkex.com.hk/eng/market/partcir/hkfe/2014/Documents/DCRM_HKCC_015_2014_e.pdf
            
            
def main():
    import argparse
    __author__ = 'TianJun'
    parser = argparse.ArgumentParser(description='This is a SpanDownload script by TianJun.')
    parser.add_argument('-d','--date', help='Input SettledDate YYYYMMDD,default is today.',required=False)
    args = parser.parse_args()
    m_settledDate = datetime.datetime.now().strftime('%Y%m%d')
    if (args.date):
        m_settledDate = args.date
    logger.info('Start...')
    sf = TimSpan(m_settledDate)
    logger.info('...End.')


if __name__ == '__main__':
    main()            
