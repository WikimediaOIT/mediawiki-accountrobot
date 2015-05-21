#!/usr/bin/python

"""
This script can be used to create a user account on mediawiki wikis using the web API.
https://www.mediawiki.org/wiki/API:Main_page

It only uses two API endpoints (login and createaccount).
It assumes that you need WRITE access (must login) to create an account.

It prompts the user for a password to login.

The flow of the mediawiki API requires an initial call, which returns a token.
The token must be used on a second call to apply the command.

FIXME:
Add 'Block' user ability
Add command line options to select create vs block.
Add command line option to select if we need login or not.
Add command line options to loop over many newuser/useremail pairs.
"""

############################################################
import getpass
import requests
import sys
import argparse

login='OITBot (WMF)'

wikiurls=['https://office.wikimedia.org',
          'https://collab.wikimedia.org',
          'https://wikimediafoundation.org']

# Command line options
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="User Name eg. 'JDoe (WMF)'")
parser.add_argument("-e", "--email", help="User EMail eg. 'jdoe@wikimedia.org'")
parser.add_argument("-d", "--debug", help="Run In Debug Mode -- DOES NOT APPLY CHANGES",
                    action="store_true")

args = parser.parse_args()

if args.debug:
    print('Debug Mode')

print 'Creating New Wiki Accounts'
print 'User:    ', args.user
print 'Email:   ', args.email

# Ask user for OITBOT Password
password = getpass.getpass('Password for %s :' % (login))

for wikiurl in wikiurls:
    # Debug/Prep
    print 'Wiki:    ', wikiurl

    # Use session to persist cookies
    session = requests.Session()

    ############################################################
    # Login
    endpoint='/w/api.php?action=login'
    url='%s/%s' % (wikiurl, endpoint)

    # API Post variables
    payload = {
        'lgname':     login,
        'lgpassword': password,
        'lgtoken':    '',
        'format':     'json',
        }

    # Make initial request
    result = session.post(url, data=payload)

    if args.debug:
        print result.text

    data=result.json()

    # If initial request was successful, make second request using token
    if 'login' in data and 'token' in data['login']:
        # grab token from first post, and add to new post
        payload['lgtoken'] = str(data["login"]["token"])
        result2 = session.post(url, data=payload)
        if args.debug:
            print result2.text
    else:
        print 'Something went wrong'
        continue

    ############################################################
    # Create account

    if args.debug:
        print 'Skipping Creation -- debug mode'
        continue

    endpoint='/w/api.php?action=createaccount'
    url='%s/%s' % (wikiurl, endpoint)

    # API Post variables
    payload = {
        'name': args.user,
        'email': args.email,
        'mailpassword': 'true',
        'reason': 'New Employee',
        'token': '',
        'format': 'json',
        }

    # Make initial request
    result = session.post(url, data=payload)
    print("Response: %s" % (result.text))
    data=result.json()

    # If initial request was successful, make second request using token
    if 'createaccount' in data and 'token' in data['createaccount']:
        # grab token from first post, and add to new post
        payload['token'] = str(data["createaccount"]["token"])
        result2 = session.post(url, data=payload)
        print("Response: %s" % (result2.text))
    else:
        print('Something went wrong')
        continue
        
