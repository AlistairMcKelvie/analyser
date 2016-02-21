#!/usr/bin/env python2.7
'''
Send mail via gmail. Requires google account OAuth2 setup (see
https://code.google.com/p/google-mail-oauth2-tools/wiki/OAuth2DotPyRunThrough).
Can be called directly from the command line, or as a python funtion with sendmail.

Alistair McKelvie May 2015
'''

import smtplib
import base64
import urllib
import urllib2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from os import listdir
import json
from argparse import ArgumentParser
import sys
import traceback
from kivy.network.urlrequest import UrlRequest

user = 'spot.analyser.test@gmail.com'

clientId = '295062602032-6r0oveu3e3mnar9k42rh7en2pbtfpdsg.apps.googleusercontent.com'
clientSecret = 'y56y3ZvHvgbYERdVjA3M2_gm'
refreshToken = '1/UFaIEi9-wOzhbCBwROlCtXlVOS98-hxQJNOd9HKTGg4'


def sendMail(toList, subject, message, attachmentDir):
    '''toList is a list of email address strings. subject and message are strings'''
    try:
        token = RefreshToken(clientId, clientSecret, refreshToken)
        print token 
        msg = MIMEMultipart(message)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = ', '.join(toList)
        msg.attach(MIMEText(message))
        for attachment in listdir(attachmentDir):
            with open(attachmentDir + attachment, 'rb') as f:
                part = MIMEApplication(f.read())
                part.add_header('Content-Disposition',
                                'attachment; filename="{}"'.format(attachment))
            msg.attach(part)

        con = smtplib.SMTP('smtp.gmail.com', 587)

        con.set_debuglevel(True)
        con.starttls()
        authString = ('user={0}\1auth=Bearer {1}\1\1').format(user, token)
        
        con.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(authString))
        con.sendmail(user, toList, msg.as_string())
        print "Message '{}' sent.".format(subject)
    except:
        print traceback.format_exc()
    finally:
        try:
            con.close()
        except UnboundLocalError:
            pass


def RefreshToken(client_id, client_secret, refresh_token):
    """
    Taken from Google OAuth script.

    Obtains a new token given a refresh token.

    See https://developers.google.com/accounts/docs/OAuth2InstalledApp#refresh

    Args:
    client_id: Client ID obtained by registering your app.
    client_secret: Client secret obtained by registering your app.
    refresh_token: A previously-obtained refresh token.
    Returns:
    The decoded response from the Google Accounts server, as a dict. Expected
    fields include 'access_token', 'expires_in', and 'refresh_token'.
    """
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = 'https://accounts.google.com/o/oauth2/token'
    print request_url
    print urllib.urlencode(params)
    try:
        urllib.urlopen(request_url, urllib.urlencode(params))
    except:
        print traceback.format_exc()
    response = urllib2.urlopen(request_url, urllib.urlencode(params)).read()
    return json.loads(response)['access_token']


def main(argv):
    parser = ArgumentParser()
    parser.add_argument('-t', '--to_addresses', nargs='+', help='Email addresses to send to')
    parser.add_argument('-s', '--subject', nargs=1, help='Email subject')
    parser.add_argument('-m', '--message', nargs=1, help='Email body text')
    args = parser.parse_args()
    
    sendMail(args.to_addresses, args.subject[0], args.message[0])
    

if __name__ == '__main__':
    main(sys.argv)

