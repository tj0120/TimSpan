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
import sqlite3 as DBServer
import base64
from SimpleXMLRPCServer import SimpleXMLRPCServer


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

LOG_FILE = 'preDeal.log'
handler = logging.handlers.RotatingFileHandler(os.path.join( os.path.realpath(os.path.curdir),LOG_FILE), maxBytes = 1024*1024, backupCount = 5)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('sf')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

spanFiles  =  {
            'BMDC':('ftp://ftp.cmegroup.com/pub/span/data/bmdc/bmd_YYYYMMDD_s.pa2.zip','BMDC'),
            'CBOT,CME, COMEX and NYMEX':('ftp://ftp.cmegroup.com/pub/span/data/cme/cme.YYYYMMDD.s.pa2.zip','CBOT,CME, COMEX and NYMEX'),
            'IPE':('ftp://ftp.cmegroup.com/pub/span/data/ice/ice.YYYYMMDD.pa5.zip','IPE'),
            'LIFFE':('ftp://ftp.cmegroup.com/pub/span/data/liffe/liffe.YYYYMMDD.s.pa5.zip','LIFFE'),
            'LME-CME':('ftp://ftp.cmegroup.com/pub/span/data/lme/lme.YYYYMMDD.s.dat.zip','LME'),
            'NYBOT':('ftp://ftp.cmegroup.com/pub/span/data/nyb/nyb.YYYYMMDD.x.pa2.zip','NYBOT'),
            'OSAKA_NIKKEI':('ftp://ftp.cmegroup.com/pub/span/data/jsc/jsc.YYYYMMDD.s.zip','OSAKA_NIKKEI'),
            'SIMEX':('ftp://ftp.cmegroup.com/pub/span/data/smx/sgx.YYYYMMDD.s.zip','SIMEX'),
            'TAIFEX':('ftp://ftp.cmegroup.com/pub/span/data/taifex/taifex.YYYYMMDD_1430.zip','TAIFEX'),
            'TOCOM':('ftp://ftp.cmegroup.com/pub/span/data/jcch/jcch.YYYYMMDD.e.zip','TOCOM'),
            'CBOE':('ftp://ftp.cmegroup.com/pub/span/data/cfe/cfe.YYYYMMDD.s.pa2.zip','CBOE'),
            'LME-LCH':('http://www.lynx.hk/span/getlme.asp?file=/MFYYMMDD.zip','LME'),
            'HKEX':('http://www.hkex.com.hk/eng/market/rm/rm_dcrm/riskdata/rpf/rpf_YYMMDD.zip','HKEX')
            }
         
settlePriceFiles = {
            'P-CBOT':('ftp://ftp.cmegroup.com/pub/settle/cbt.settle.YYYYMMDD.s.xml.zip','CBOT'),
            'P-CEU':('ftp://ftp.cmegroup.com/pub/settle/ceu.settle.YYYYMMDD.s.xml.zip','CEU'),
            'P-CME':('ftp://ftp.cmegroup.com/pub/settle/cme.settle.YYYYMMDD.s.xml.zip','CME'),
            'P-CME-FWD':('ftp://ftp.cmegroup.com/pub/settle/cme.settle.fwd.YYYYMMDD.s.xml.zip','CME'),
            'P-COMEX':('ftp://ftp.cmegroup.com/pub/settle/comex.settle.YYYYMMDD.s.xml.zip','COMEX'),
            'P-COMEX-FWD':('ftp://ftp.cmegroup.com/pub/settle/comex.settle.fwd.YYYYMMDD.s.xml.zip','COMEX'),
            'P-DME':('ftp://ftp.cmegroup.com/pub/settle/dme.settle.YYYYMMDD.s.xml.zip','DME'),
            'P-NYMEX':('ftp://ftp.cmegroup.com/pub/settle/nymex.settle.YYYYMMDD.s.xml.zip','NYMEX'),
            #'P-MD-FUT':('ftp://ftp.cmegroup.com/pub/settle/md.commodity.fut.YYYYMMDD.xml.zip','MD'),
            #'P-MD-OPT':('ftp://ftp.cmegroup.com/pub/settle/md.commodity.opt.YYYYMMDD.xml.zip','MD'),
            #'P-holidays':('ftp://ftp.cmegroup.com/pub/settle/cme_holidays-YYYYMMDD.csv','CME'),
            #'VX':('http://cfe.cboe.com/data/DailyVXFuturesEODValues/DownloadFS.aspx','CFE'）
            }        
    
            
class DownSpanFiles:     
    def __init__(self, date=None, filter = [], env = []):
        self.toDay =  datetime.date.today().strftime('%Y%m%d') 
        self.spanODir = 'span'
        self.priceODir = 'settleprice'
        self.dealFilter = ['0','1'] + filter
        self.zipFilesDict = {}
        self.initLIST()
        self.initTRC()
        if (env):
            self.initENV(env)
        if (date):
            self.toDay = date
        #self.getHKSettleDailyPrice()
        #self.processDownloadPriceFiles()
        #self.dealPriceFiles()
        self.processDownloadSpanFiles()
        self.saveSpanToDB()
        self.dealSpanFiles()

    def saveSpanToDB(self):
        db = TimSpanDB()
        for key,fname in self.zipFilesDict.items():
            zipfiledata = base64.encodestring(open(fname,'rb').read())
            values = {'ClearingBusinessDate':self.toDay,'ExchangeAcronym':key,'FileName':fname,'SpanData':zipfiledata}
            db(values)

    def initENV(self, env):
        import argparse
        __author__ = 'TianJun'
        logger.debug('Start argparse...')
        parser = argparse.ArgumentParser(description='This is a SpanDownload script by TianJun.')
        parser.add_argument('-d','--date', help='Input SettledDate YYYYMMDD,default is today.',required=False)
        args = parser.parse_args(env)
        logger.debug('end argparse.')
        if (args.date):
            toDay = args.date

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
        if (url.scheme == 'http'):
            self.getPriceFileHTTP(p_k,p_url,os.path.split(p_url)[1])

    def getPriceFileHTTP(self,p_key,p_url,p_ofilename):
        import urllib2
        try:
            fn = os.path.join(self.subPODir,p_ofilename)
            if (os.path.exists(fn)):
                self.zipFilesDict[p_key]= fn
                return
            zf = urllib2.urlopen(p_url)
            of = open(fn,'w+b')
            of.write(zf.read())
            of.close()
            if (os.path.getsize(fn) == 0):
                os.remove(fn)
                logger.error('ERROR: RETR %s, 0 size' % p_ofilename)      
                return
            logger.debug('SUCCEED: GET %s' % p_ofilename)
            self.zipFilesDict[p_key]= fn
        except Exception,e:
            logger.error('ERROR: GET %s' % p_ofilename)      

        
    def getPriceFileFTP(self,p_key,p_host,p_path,p_ofilename):
        import ftplib
        fn = os.path.join(self.subPODir,p_ofilename)       
        if (os.path.exists(fn)):
            self.zipFilesDict[p_key]= fn
            return
        of = open(fn,'w+b')
        ftp = ftplib.FTP(p_host)
        ftp.login()
        ftp.cwd(p_path)
        try:
            ftp.retrbinary('RETR %s' % p_ofilename, of.write)
            of.close()
            logger.debug('SUCCEED: RETR %s' % p_ofilename)
            self.zipFilesDict[p_key]= fn
        except Exception,e:
            logger.error('ERROR: RETR %s' % p_ofilename)      
        if (os.path.getsize(fn) == 0):
            os.remove(fn)
            logger.error('ERROR: RETR %s, 0 size' % p_ofilename)      

                    
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
        if (url.scheme == 'http'):
            self.getSpanFileHTTP(p_k,p_url,os.path.split(p_url)[1])
            

            
    def getSpanFileHTTP(self,p_key,p_url,p_ofilename):
        import urllib2
        try:
            fn = os.path.join(self.subODir,p_ofilename)
            if (os.path.exists(fn)):
                self.zipFilesDict[p_key]= fn
                return
            zf = urllib2.urlopen(p_url)
            of = open(fn,'w+b')
            of.write(zf.read())
            of.close()
            if (os.path.getsize(fn) == 0):
                os.remove(fn)
                logger.error('ERROR: RETR %s, 0 size' % p_ofilename)      
                return
            logger.debug('SUCCEED: GET %s' % p_ofilename)
            self.zipFilesDict[p_key]= fn
        except Exception,e:
            logger.error('ERROR: GET %s' % p_ofilename)      


    def getSpanFileFTP(self,p_key,p_host,p_path,p_ofilename):
        import ftplib
        fn = os.path.join(self.subODir,p_ofilename)       
        if (os.path.exists(fn)):
            self.zipFilesDict[p_key]= fn
            return
        of = open(fn,'w+b')
        ftp = ftplib.FTP(p_host)
        ftp.login()
        ftp.cwd(p_path)
        try:
            ftp.retrbinary('RETR %s' % p_ofilename, of.write)
            of.close()
            logger.debug('SUCCEED: RETR %s' % p_ofilename)
            self.zipFilesDict[p_key]= fn
        except Exception,e:
            logger.error('ERROR: RETR %s' % p_ofilename)      
        if (os.path.getsize(fn) == 0):
            os.remove(fn)
            logger.error('ERROR: RETR %s, 0 size' % p_ofilename)      

        

class TimSpanDB:
    updateSQL = '''INSERT INTO SpanData(ClearingBusinessDate,ExchangeAcronym,FileName,SpanData) 
                                    VALUES(:ClearingBusinessDate,:ExchangeAcronym,:FileName,:SpanData)
                '''
    def __init__(self):
        if (not os.path.exists('data')):
            os.makedirs('data')
        self.dbpath = 'data/TimSpanDB'
        self.connectDB()
        
    def __call__(self,values):
        return self.update(values)
        
    def update(self,values):
        rt = self.checkRecord(values)
        try:
            self.cursor.execute(self.updateSQL,rt)
            self.db.commit()
        except DBServer.IntegrityError, e:
            if ('UNIQUE constraint failed' in e.message):
                logger.info(e.message)
            else:
                raise e
            
    
    def checkRecord(self,values):
        m_record = values
        if (not m_record.has_key('ClearingBusinessDate')):
                            m_record['ClearingBusinessDate'] = ''
        if (not m_record.has_key('ExchangeAcronym')):
                            m_record['ExchangeAcronym'] = ''
        if (not m_record.has_key('FileName')):
                            m_record['FileName'] = ''
        if (not m_record.has_key('SpanData')):
                            m_record['SpanData'] = ''
        return m_record

    def connectDB(self):
        self.db = DBServer.connect(self.dbpath)
        logger.info("Opened database successfully")
        self.cursor = self.db.cursor()
        self.testDB()
        
    def testDB(self):
        testSQL = ''' SELECT name FROM sqlite_master 
                                  WHERE type='table' AND name='SpanData'
                  ''' 
        ctSQL = '''
                CREATE TABLE SpanData( 
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ClearingBusinessDate TEXT NOT NULL,
                    ExchangeAcronym TEXT NOT NULL,
                    FileName TEXT NOT NULL,
                    SpanData BLOB NOT NULL)
                '''
        cidxSQL = 'create  unique index SpanDataIndex on SpanData  (FileName)'
        self.cursor.execute(testSQL)
        SettlePrice = self.cursor.fetchone()
        if (not SettlePrice): 
            logger.error('No Table SpanData, I will Create it!')
            self.cursor.execute(ctSQL)
            self.cursor.execute(cidxSQL)
            self.db.commit()
            logger.info('Table SpanData created.')
        
        
class DealSpanServer(SimpleXMLRPCServer):
    def __init__(self,dest,env):
        SimpleXMLRPCServer.__init__(dest)
        self.env = env
        logger.info('Start...')
        sf = SpanFiles(self.m_settledDate,['Y'])
        logger.info('...End.')
        
    def _dispatch(self, method, params):
        try:
            # We are forcing the 'export_' prefix on methods that are
            # callable through XML-RPC to prevent potential security
            # problems
            func = getattr(self, 'export_' + method)
        except AttributeError:
            raise Exception('method "%s" is not supported' % method)
        else:
            return func(*params)
 
    def export_getSpanZipFile(self, filename):
        return 1

    def export_getSpanZipFile(self, ClearingBusinessDate,ExchangeAcronym):
        return 1

def initENV(self, env):
    import argparse
    __author__ = 'TianJun'
    logger.debug('Start argparse...')
    parser = argparse.ArgumentParser(description='This is a SpanDownload script by TianJun.')
    parser.add_argument('-d','--date', help='Input SettledDate YYYYMMDD,default is today.',required=False)
    args = parser.parse_args(env)
    logger.debug('end argparse.')
    toDay = datetime.datetime.now().strftime('%Y%m%d')
    if (args.date):
        toDay = args.date
    return toDay

if __name__ == '__main__':         
    server = DealSpanServer(("localhost", 8000),sys.argv)
    server.serve_forever()
 
