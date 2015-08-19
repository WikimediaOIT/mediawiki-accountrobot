#!/usr/bin/python

"""
This script can be used to create OR block a user account on mediawiki wikis
using the web APIs.
https://www.mediawiki.org/wiki/API:Main_page

The script users a few api endpoints: login, createaccount, query and block.
Your user login account needs rights to perform the given actions.

The script prompts the user for a password to login.
(all wikis need to use the same password)

The flow of the mediawiki API requires an initial call, which returns a token.
The token must be used on a second call to apply the command.

FIXME:
Add command line options to loop over many newuser/useremail pairs.
"""

############################################################
import getpass
import requests
import sys
import argparse

# List of Wikis to create accounts on
# NOTE: login user password for each must be the same
wikiurls = [
    'https://office.wikimedia.org',
    'https://collab.wikimedia.org',
    'https://wikimediafoundation.org'
#    'https://meta.wikimedia.org',
    ]

# Command line options
parser = argparse.ArgumentParser(
    description='Automating Mediawiki Account Creation')
parser.add_argument(
    "-u", "--user",
    help="New User Mediawiki Account Name eg. 'JDoe (WMF)'",
    required=True)
parser.add_argument(
    "-e", "--email",
    help="User EMail eg. 'jdoe@wikimedia.org'",
    required=True)
parser.add_argument(
    "-l", "--login",
    help="Admin User Mediawiki Account eg. 'AdminUsers'",
    default="JAdmin (WMF)")
parser.add_argument(
    "-b", "--block",
    help="BLOCK account instead of CREATE",
    action="store_true")
parser.add_argument(
    "-d", "--debug",
    help="Run In Debug Mode -- DOES NOT APPLY CHANGES",
    action="store_true")

args = parser.parse_args()

if args.debug:
    print('Debug Mode')

print 'Creating New Wiki Accounts'
print 'User:    ', args.user
print 'Email:   ', args.email

# Ask user for login Password
password = getpass.getpass('Password for %s :' % (args.login))

for wikiurl in wikiurls:
    # Debug/Prep
    print 'Wiki:    ', wikiurl

    # Use session to persist cookies
    session = requests.Session()

    ############################################################
    # Login To MediaWiki as Admin User
    endpoint = '/w/api.php?action=login'
    url = '%s/%s' % (wikiurl, endpoint)

    # API Post variables
    payload = {
        'lgname':     args.login,
        'lgpassword': password,
        'lgtoken':    '',
        'format':     'json',
        }

    # Make initial request
    result = session.post(url, data=payload)

    if args.debug:
        print result.text

    data = result.json()

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

    if args.debug:
        print 'Skipping Creation -- debug mode'
        continue

    # BLOCK
    if args.block:
        # https://www.mediawiki.org/wiki/API:Block
        print 'Blocking'
        endpoint = '/w/api.php?action=query'
        url = '%s/%s' % (wikiurl, endpoint)

        # API Post variables
        payload = {
            'format': 'json',
            'meta': 'tokens'}

        # Make initial request
        result = session.post(url, data=payload)
        print("Response: %s" % (result.text))
        data = result.json()

        # If initial request was successful, make second request using token
        if 'query' in data and 'csrftoken' in data['query']['tokens']:

            # Make a second request using a the token
            payload.pop('meta', None)
            payload['token'] = str(data['query']['tokens']['csrftoken'])
            payload['user'] = args.user
            payload['expiry'] = 'indefinite'
            payload['reason'] = 'No longer employed with WMF'

            endpoint = '/w/api.php?action=block'
            url = '%s/%s' % (wikiurl, endpoint)
            result2 = session.post(url, data=payload)
            print("Response: %s" % (result2.text))
        else:
            print('Something went wrong')
            print data
            continue

    # CREATE
    else:
        # https://www.mediawiki.org/wiki/API:Account_creation
        # Default behavior is to create
        endpoint = '/w/api.php?action=createaccount'
        url = '%s/%s' % (wikiurl, endpoint)

        # API Post variables
        payload = {
            'name': args.user,
            'email': args.email,
            'mailpassword': 'true',
            'reason': 'New Employee',
            'token': '',
            'format': 'json',
            }

        # Make initial request to get a token
        result = session.post(url, data=payload)
        print("Response: %s" % (result.text))
        data = result.json()

        # If initial request was successful, make second request using token
        if 'createaccount' in data and 'token' in data['createaccount']:
            # grab token from first post, and add to new post
            payload['token'] = str(data["createaccount"]["token"])

            # temporary workaround for TitleBlacklist Extension
            payload['wpIgnoreTitleBlacklist'] = 'true'

            # Make second request using token
            result2 = session.post(url, data=payload)
            print("Response: %s" % (result2.text))
        else:
            print('Something went wrong')
            print data
            continue
