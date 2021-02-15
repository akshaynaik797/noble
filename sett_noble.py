import pickle
import base64
import os.path
from random import randint
from datetime import datetime, timedelta
from time import sleep

from pytz import timezone, utc
from dateutil.parser import parse


import mysql.connector
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pdfkit
from make_log import log_exceptions
if not os.path.exists('new_attach'):
    os.mkdir('new_attach')
if not os.path.exists('logs'):
    os.mkdir('logs')

conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
             'user': "admin",
             'password': "Welcome1!",
             'database': 'python_rep'}

config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def file_no(len):
    return str(randint((10 ** (len - 1)), 10 ** len)) + '_'


def file_blacklist(filename):
    fp = filename
    filename, file_extension = os.path.splitext(fp)
    ext = ['.pdf', '.htm', '.html']
    if file_extension not in ext:
        return False
    if fp.find('ATT00001') != -1:
        return False
    if (fp.find('MDI') != -1) and (fp.find('Query') == -1):
        return False
    if (fp.find('knee') != -1):
        return False
    if (fp.find('KYC') != -1):
        return False
    if fp.find('image') != -1:
        return False
    if (fp.find('DECLARATION') != -1):
        return False
    if (fp.find('Declaration') != -1):
        return False
    if (fp.find('notification') != -1):
        return False
    if (fp.find('CLAIMGENIEPOSTER') != -1):
        return False
    if (fp.find('declar') != -1):
        return False
    if (fp.find('PAYMENT_DETAIL') != -1):
        return False
    return True


def fetch(after, before):
    after, before = str(after), str(before)
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('noble_token.pickle'):
        with open('noble_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_noble.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('noble_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    q = f"after:{after} before:{before}"
    results = service.users().messages().list(userId='me', labelIds=['INBOX'],
                                              q=q).execute()
    messages = results.get('messages', [])
    with open('logs/mail_stat.log', 'a') as fp:
        print(datetime.fromtimestamp(int(after)), datetime.fromtimestamp(int(before)), str(len(messages)), sep=', ',
              file=fp)
    if not messages:
        pass
        #print("No messages found.")
    else:
        print("Message snippets:")
        for message in messages[::-1]:
            try:
                id, subject, date, filename, sender = '', '', '', '', ''
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                id = msg['id']
                for i in msg['payload']['headers']:
                    if i['name'] == 'Subject':
                        subject = i['value']
                    if i['name'] == 'From':
                        sender = i['value']
                        sender = sender.split('<')[-1].replace('>', '')
                    if i['name'] == 'Date':
                        date = i['value']
                        print(date)
                        date = date.split(',')[-1].strip()
                        format = '%d %b %Y %H:%M:%S %z'
                        if '(' in date:
                            date = date.split('(')[0].strip()
                        try:
                            date = datetime.strptime(date, format)
                        except:
                            try:
                                date = parse(date)
                            except:
                                with open('logs/date_err.log', 'a') as fp:
                                    print(date, file=fp)
                                raise Exception
                        date = date.astimezone(timezone('Asia/Kolkata')).replace(tzinfo=None)
                        format1 = '%d/%m/%Y %H:%M:%S'
                        date = date.strftime(format1)
                    if i['name'] == 'X-Failed-Recipients':
                        with open('logs/fail_mails.log', 'a') as fp:
                            print(id, subject, date, sep=',', file=fp)
                        raise Exception
                flag = 0
                if 'parts' in msg['payload']:
                    for j in msg['payload']['parts']:
                        if 'attachmentId' in j['body']:
                            filename = j['filename']
                            filename = filename.replace('.PDF', '.pdf')
                            filename = 'new_attach/' + file_no(4) + filename
                            if file_blacklist(filename):
                                filename = filename.replace(' ', '')
                                a_id = j['body']['attachmentId']
                                attachment = service.users().messages().attachments().get(userId='me', messageId=id,
                                                                                          id=a_id).execute()
                                data = attachment['data']
                                with open(filename, 'wb') as fp:
                                    fp.write(base64.urlsafe_b64decode(data))
                                print(filename)
                                flag = 1
                else:
                    data = msg['payload']['body']['data']
                    filename = 'new_attach/' + file_no(8) + '.pdf'
                    with open('new_attach/' + 'temp.html', 'wb') as fp:
                        fp.write(base64.urlsafe_b64decode(data))
                    print(filename)
                    pdfkit.from_file('new_attach/temp.html', filename, configuration=config)
                    flag = 1
                if flag == 0:
                    if 'data' in msg['payload']['parts'][-1]['body']:
                        data = msg['payload']['parts'][-1]['body']['data']
                        filename = 'new_attach/' + file_no(8) + '.pdf'
                        with open('new_attach/' + 'temp.html', 'wb') as fp:
                            fp.write(base64.urlsafe_b64decode(data))
                        print(filename)
                        pdfkit.from_file('new_attach/temp.html', filename, configuration=config)
                        flag = 1
                    else:
                        if 'data' in msg['payload']['parts'][0]['parts'][-1]['body']:
                            data = msg['payload']['parts'][0]['parts'][-1]['body']['data']
                            filename = 'new_attach/' + file_no(8) + '.pdf'
                            with open('new_attach/' + 'temp.html', 'wb') as fp:
                                fp.write(base64.urlsafe_b64decode(data))
                            print(filename)
                            pdfkit.from_file('new_attach/temp.html', filename, configuration=config)
                            flag = 1
                        else:
                            data = msg['payload']['parts'][0]['parts'][-1]['parts'][-1]['body']['data']
                            filename = 'new_attach/' + file_no(8) + '.pdf'
                            with open('new_attach/' + 'temp.html', 'wb') as fp:
                                fp.write(base64.urlsafe_b64decode(data))
                            print(filename)
                            pdfkit.from_file('new_attach/temp.html', filename, configuration=config)
                            flag = 1
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    q = "insert into noble_mails (`id`,`subject`,`date`,`sys_time`,`attach_path`,`completed`, `sender`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    data = (id, subject, date, str(datetime.now()), os.path.abspath(filename), '', sender)
                    cur.execute(q, data)
                    con.commit()
            except:
                log_exceptions(id=id)


def run():
    now = datetime.now()
    after = int((now - timedelta(minutes=1)).timestamp())
    before = int(now.timestamp())
    flag = False
    while 1:
        if os.path.exists('stop_noble_mails'):
            os.remove('stop_noble_mails')
            break
        if flag:
            after = before
            before = now
        flag = True
        #print(datetime.fromtimestamp(int(after)), datetime.fromtimestamp(int(before)))
        fetch(after, before)
        sleep(10)
        now = int(datetime.now().timestamp())


if __name__ == '__main__':
    while 1:
        try:
            fetch('1608470383', '1611580783')
            break
        except:
            log_exceptions()
        pass
    print('=======================================================')