import sys, time, os, re
import datetime
import smtplib
import urllib.request
from email.message import EmailMessage

from pathlib import Path
from pymongo import MongoClient



if __name__ == "__main__":

    if not Path(r"../logs").is_dir():
        os.makedirs(r"../logs")
    # ipObtained = False
    # logFile = open(Path(r"../logs/mainLog.log"), 'a')
    # sys.stdout = logFile

    # Mongo Client
    client = MongoClient()

    localDatabase = client.local

    #get gmail login information from local collection
    loginCollection = localDatabase['login']

    gmailList = list(loginCollection.find({"name":"gmail"}))
    myEmail = gmailList[0]['username']
    myPassword = gmailList[0]['password']

    to = ["noahlangat@cmail.carleton.ca"]

    #Email Message
    msg = EmailMessage()
    msg['Subject'] = "IP Address Change"
    msg['From'] = myEmail
    msg['To'] = "noahlangat@cmail.carleton.ca"
    
    # while not ipObtained:
    #     try:
    #         newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    #         ipObtained = True
    #     except Exception as e:
    #         print(e, end='\n')
    #         time.sleep(60)


    #MongoDB IP database '''
 
    # ipCollection = client.local['Ip']
    # cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)
    # currentIP = list(cursor)[0]["IP"]

    # print(currentIP)
    # logFile.close()

    while True:

        
        logFile = open(Path(r"../logs/mainLog.log"), 'a')
        ipObtained = False
        sys.stdout = logFile

        ipCollection = client.local['Ip']
        cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)
        currentIP = list(cursor)[0]["IP"]

        while not ipObtained:
            try:
                newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
                # print("IP as of now is:{0}".format(newIP))
                ipObtained = True
            except Exception as e:
                print(e, end='\n')
                time.sleep(60)


        
        if currentIP != newIP:

            print("Ip has changed from {0} to {1}".format(currentIP, newIP))
            ip = {
                "IP":newIP,
                "datetime": time.mktime(datetime.datetime.now().timetuple()) * 1000
            }
            result = ipCollection.insert_one(ip)
            
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(myEmail, myPassword)
                msg.set_content("Ip has changed from {0} to {1}".format(currentIP, newIP))
                server.send_message(msg)

            except Exception as e:
                print(e)

            finally:
                server.quit()



        ''' WAIT FOR 1 HOUR HOURS BEFORE CHECKING AGAIN '''
        logFile.close()
        time.sleep(3600)
        
        # cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)
        # currentIP = list(cursor)[0]["IP"]

        # while not ipObtained:
        #     try:
        #         newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        #         ipObtained = True
        #     except Exception as e:
        #         print(e, end='\n')
        #         time.sleep(60)
        
        


    