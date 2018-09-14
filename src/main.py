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
        
    logFile = open(Path(r"../logs/mainLog.log"), 'w')
    # sys.stdout = logFile

    myEmail = "knoah.lr@gmail.com"
    myPassword = "xsltglhjhewyywat" 
    to = ["noahlangat@cmail.carleton.ca"]

    #urllib.request.urlopen('https://ident.me').read().decode('utf8')

    """ Email Message """
    msg = EmailMessage()
    msg['Subject'] = "IP Address Change"
    msg['From'] = myEmail
    msg['To'] = "noahlangat@cmail.carleton.ca"
    
    
    newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')

    ''' MongoDB IP database '''
    client = MongoClient()
    localDatabase = client.local

    ipCollection = client.local['Ip']
    cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)
    currentIP = list(cursor)[0]["IP"]

    # print(currentIP)

    while True:

        

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
        cursor = ipCollection.find().sort([("datetime", -1)]).limit(1)
        currentIP = list(cursor)[0]["IP"]
        newIP = urllib.request.urlopen('https://ident.me').read().decode('utf8')

        time.sleep(14400)