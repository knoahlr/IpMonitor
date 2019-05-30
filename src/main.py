import sys, time, os, re
import datetime
import smtplib
import urllib.request
from email.message import EmailMessage

from pathlib import Path
from pymongo import MongoClient
from boto import dynamodb2
from boto.dynamodb2.table import Table
from boto3 import resource
import boto3 
import decimal
import enum


def queryIP():

    ipObtained = False

    while not ipObtained:

            try:
                newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
                # print("IP as of now is:{0}".format(newIP))
                ipObtained = True
            except Exception as e:
                print(e, end='\n')
                time.sleep(60)

    return newIP

class AWSTables(enum.Enum):

    IpTable = 'IpMonitor'

class emailInfo(enum.Enum):

    subject = 'Ip Address Changed AWS'
    to      = ['noahlangat@cmail.carleton.ca']
    ip      = queryIP()
    content = 'Ip Address changed to {0}'.format(queryIP())


def isNumber(s):
        ''' 
        Implemented in validating sample calculation inputs
        '''
        try:
            float(s)
            return (True, None)
        except Exception as e:
            return (False, e)

class session:

    ''' Class to hold all possible Future sessions '''

    def __init__(self):

        self.AWsSession = None
        self.Tables = {} #dict()
        self.localClient = None
        self.initializeSessions()


    def initializeSessions(self):

        self.localClient = MongoClient()
        localDatabase = self.localClient.local
        loginCollection = localDatabase['login']#get gmail login information from local collection

        #Obtaining AWS access and secret Keys
        awsList = list(loginCollection.find({"name":"access"}))
        accessKey = awsList[0]['access_key']
        secretKey = awsList[0]['secret_access_key']

        #Initiating AWS connection
        self.AWsSession = boto3.Session(aws_access_key_id=accessKey, aws_secret_access_key=secretKey)

    def post(self, case, collection=None):

        ''' Should be used to manually update and/or initialize database info '''
        if case == 'ipLocal':
            ip = queryIP()

            ipCollection = self.localClient.local['Ip']
            cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)

            ipInfo = {
                "IP":ip,
                "datetime": time.mktime(datetime.datetime.now().timetuple()) * 1000
            }
            result = ipCollection.insert_one(ipInfo)

        if case == 'ipAWS':

            ip = queryIP()

            ipCollection = self.localClient.local['Ip']
            cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)

            ipInfo = {
                "Ip":ip,
                "Date": str(time.mktime(datetime.datetime.now().timetuple()) * 1000)
            }

            database = self.AWsSession.resource('dynamodb', region_name='us-east-2')
            self.Tables['IpInfo'] = database.Table('IpMonitor')
            self.Tables['IpInfo'].put_item(Item = ipInfo)

    def getTable(self, tables):

        ''' Populates table structure with specified table'''
        for table in tables:

            try:
                database = self.AWsSession.resource('dynamodb', region_name='us-east-2')
                self.Tables[table] = database.Table(table.value)
            except Exception as e:
                print(e.__str__)
                continue

    
def sendEmail(session):

    #Email Login Info
    gmailList = list(session.localClient.local['login'].find({"name":"gmail"})) #Obtains gmail info from
    myEmail = gmailList[0]['username']
    myPassword = gmailList[0]['password']

    to = ["noahlangat@cmail.carleton.ca"]

    #Email Message
    msg = EmailMessage()
    msg['Subject'] = emailInfo.subject.value # "IP Address Change"
    msg['From'] = myEmail #myEmail
    msg['To'] = emailInfo.to.value #"noahlangat@cmail.carleton.ca"

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(myEmail, myPassword)
        msg.set_content(emailInfo.content.value)
        server.send_message(msg)

    except Exception as e:
        print(e)

    finally:
        server.quit()



def databaseLogin():

        #Create Session

        ipSession = session()

        #Obtaining AWS Tables

        database = ipSession.AWsSession.resource('dynamodb', region_name='us-east-2')
        ipSession.Tables['IpInfo'] = database.Table('IpMonitor') #Should rethink name!!



if __name__ == "__main__":

    if not Path(r"../logs").is_dir():
        os.makedirs(r"../logs")
    # ipObtained = False
    logFile = open(Path(r"../logs/mainLog.log"), 'a')
    sys.stdout = logFile

    sess = session()
    sess.getTable([AWSTables.IpTable])
    ipList = sess.Tables[AWSTables.IpTable]
    items = ipList.scan()

    while True:

        newIP = queryIP()

        currentEpochTime = time.mktime(datetime.datetime.now().timetuple()) * 1000
        ipTimeDiff = currentEpochTime


        ''' get the latest IP posted on the server'''
        for item in items['Items']:
            if isNumber(item['Date'])[0]:
                ipEpoch = float(item['Date'])
                if abs(currentEpochTime - ipEpoch) < ipTimeDiff:
                    currentIp = item['Ip']
                    ipTimeDiff = abs(currentEpochTime - ipEpoch)

        if currentIp != newIP:
            
            ''' Create new session to post new IP '''
            newSession = session()
            newSession.post('ipAWS')

            ''' Update Table and items if a new IP is posted '''
            ipList = sess.Tables[AWSTables.IpTable]
            items = ipList.scan()

            ''' Emailing myself '''
            sendEmail(newSession)

        ''' WAIT FOR 1 HOUR BEFORE CHECKING AGAIN '''
        logFile.close()
        time.sleep(3600)
      
        