#!/usr/bin/python

"""
This script can be used to create OR block a user account on mediawiki wikis
using the web APIs.
https://www.mediawiki.org/wiki/API:Main_page

The script uses a few api endpoints: login, createaccount, query and block.
Your user login account needs access rights to perform the given actions.

The script prompts the user for a password to login.
(for simplicty, all wikis need to use the same password)

The flow of the mediawiki API requires an initial call, which returns a token.
The token must be used on a second call to apply the command.

FIXME:
Add command line options to loop over many newuser/useremail pairs. (read csv?)
"""

############################################################
import getpass
import requests
import sys
import argparse
import json

# List of Wikis to create accounts on
# NOTE: login user password for each must be the same
# wikiurls = [
#     # 'https://office.wikimedia.org',
#     # 'https://collab.wikimedia.org',
#     'https://wikimediafoundation.org',
#     # 'https://meta.wikimedia.org',
#     ]

# Command line options
parser = argparse.ArgumentParser(
    description='Automating Mediawiki Account Creation or Blocks')
parser.add_argument(
    "-n", "--name",
    help="New User Full Name (use as a shortcut INSTEAD of --user and --email)"
    )
parser.add_argument(
    "-u", "--user",
    help="New User Mediawiki Account Name eg. 'JDoe (WMF)'"
    )
parser.add_argument(
    "-e", "--email",
    help="New User EMail eg. 'jdoe@wikimedia.org'"
    )
parser.add_argument(
    "-l", "--login",
    help="Admin User Mediawiki Account eg. 'AdminUsers'",
    default="JAdmin (WMF)")
parser.add_argument(
    "-w", "--wiki",
    help="Which wiki's to manage",
    default="office, collab, wikimediafoundation, meta")
parser.add_argument(
    "-b", "--block",
    help="BLOCK account instead of CREATE",
    action="store_true")
parser.add_argument(
    "-L", "--Lock",
    help="LOCK account instead of CREATE",
    action="store_true")
parser.add_argument(
    "-d", "--debug",
    help="Run In Debug Mode -- DOES NOT APPLY CHANGES",
    action="store_true")

args = parser.parse_args()

if args.debug:
    print('Debug Mode')

# Test for required option combinations

if args.name:
    (first, last) = args.name.split()
    args.user = "%s%s (WMF)" % (first[0], last)
    args.email = "%s%s@wikimedia.org" % (first[0].lower(), last.lower())
else:
    if not args.user:
        print 'ERROR: User or Name not given.'
        sys.exit(2)
    elif not args.email:
        if not args.block:
            print 'ERROR: Email or Name not given.'
            sys.exit(2)

if args.wiki:
    wikis = args.wiki.split(',')

wikis = [x.strip() for x in wikis]

wikiurls = []

for wiki in wikis:
    if wiki == 'office':
        wikiurls.append('https://office.wikimedia.org')
    if wiki == 'collab':
        wikiurls.append('https://collab.wikimedia.org')
    if wiki == 'meta':
        wikiurls.append('https://meta.wikimedia.org')
    if wiki == 'wikimediafoundation':
        wikiurls.append('https://wikimediafoundation.org')

print 'Creating New Wiki Accounts'
print 'User:    ', args.user
print 'Email:   ', args.email
print 'Wikis:'
for wiki in wikiurls: print '   ', wiki

# Ask user for login Password
password = getpass.getpass('Password for %s :' % (args.login))

for wikiurl in wikiurls:
    # Debug/Prep
    print '-'*80
    print 'Wiki:    ', wikiurl

    # Use session to persist cookies
    session = requests.Session()

    ## First get a token

    token_endpoint = '/w/api.php?action=query'
    token_url = '%s/%s' % (wikiurl, token_endpoint)


    token_request = {
        'meta' : 'tokens',
        'type' : 'login',
        'format':     'json',
    }

    token_result = session.post(token_url, data=token_request)

    # Print Token result
    print "TOKEN RESULT"
    print token_result.text

    token_data = token_result.json()

    login_token = str(token_data["query"]["tokens"]["logintoken"])


    ############################################################
    # Login To MediaWiki as Admin User
    endpoint = '/w/api.php?action=clientlogin'
    url = '%s/%s' % (wikiurl, endpoint)


    # API Post variables
    payload = {
        'username':     args.login,
        'password': password,
        'logintoken':    login_token,
        'loginreturnurl': url,
        'format':     'json',
        }

    # Make initial request
    result = session.post(url, data=payload)

    if args.debug:
        print result.text

    data = result.json()

    # # If initial request was successful, make second request using token
    # if 'login' in data and 'token' in data['login']:
    #     # grab token from first post, and add to new post
    #     payload['logintoken'] = str(data["login"]["token"])
    #     result2 = session.post(url, data=payload)
    #     if args.debug:
    #         print result2.text
    # else:
    #     print 'Something went wrong with LOGIN'
    #     continue

    print "hello?!"

    if args.debug:
        print 'Skipping Creation -- debug mode'
        continue

    # LOCK Account
    if args.Lock:

        token_endpoint = '/w/api.php?action=query'
        token_url = '%s/%s' % (wikiurl, token_endpoint)


        token_request = {
            'meta' : 'tokens',
            'type' : 'setglobalaccountstatus',
            'format':     'json',
        }

        token_result = session.post(token_url, data=token_request)

        # Print Token result
        print "TOKEN RESULT"
        print token_result.text

        token_data = token_result.json()

        setglobalaccountstatus_token = str(token_data["query"]["tokens"]["setglobalaccountstatustoken"])

        print setglobalaccountstatus_token

        lock_payload = {}

        lock_payload['token'] = setglobalaccountstatus_token
        lock_payload['user'] = args.user
        lock_payload['locked'] = "lock"
        lock_payload['reason'] = 'No longer employed with WMF'
        lock_payload['format'] = 'json'

        endpoint = '/w/api.php?action=setglobalaccountstatus'
        url = '%s/%s' % (wikiurl, endpoint)
        result2 = session.post(url, data=lock_payload)
        print("Response: %s" % (result2.text))

        continue

    # BLOCK
    if args.block:

        # First get a CSRF Token

        token_endpoint = '/w/api.php?action=query'
        token_url = '%s/%s' % (wikiurl, token_endpoint)


        token_request = {
            'meta' : 'tokens',
            'type' : 'csrf',
            'format':     'json',
        }

        token_result = session.post(token_url, data=token_request)

        # Print Token result
        print "TOKEN RESULT"
        print token_result.text

        token_data = token_result.json()

        csrf_token = str(token_data["query"]["tokens"]["csrftoken"])

        print csrf_token

        # https://www.mediawiki.org/wiki/API:Block
        print 'Blocking'
        endpoint = '/w/api.php?action=query'
        url = '%s/%s' % (wikiurl, endpoint)

        # if 'meta' in wikiurl:
        #     print "WARNING: meta/sul does not support block, use a lock"
        #     continue

        # API Post variables
        payload = {
            'format': 'json',
            'meta': 'tokens'}

        # # Make initial request
        # result = session.post(url, data=payload)
        # if args.debug:
        #     print("Response: %s" % (result.text))
        # data = result.json()
        #
        # # If initial request was successful, make second request using token
        # if 'query' in data and 'csrftoken' in data['query']['tokens']:

            # Make a second request using the token
        payload.pop('meta', None)
        payload['token'] = str(token_data['query']['tokens']['csrftoken'])
        payload['user'] = args.user
        payload['expiry'] = 'indefinite'
        payload['reason'] = 'No longer employed with WMF'

        endpoint = '/w/api.php?action=block'
        url = '%s/%s' % (wikiurl, endpoint)
        result2 = session.post(url, data=payload)
        print("Response: %s" % (result2.text))
        # else:
        #     print('Something went wrong with BLOCK')
        #     print data
        #     continue

    # CREATE
    else:
        ## First get a token

        token_endpoint = '/w/api.php?action=query'
        token_url = '%s/%s' % (wikiurl, token_endpoint)


        token_request = {
            'meta' : 'tokens',
            'type' : 'createaccount',
            'format':     'json',
        }

        token_result = session.post(token_url, data=token_request)

        # Print Token result
        print "TOKEN RESULT"
        print token_result.text

        token_data = token_result.json()

        createaccount_token = str(token_data["query"]["tokens"]["createaccounttoken"])

        print createaccount_token
        # https://www.mediawiki.org/wiki/API:Account_creation
        # Default behavior is to create
        endpoint = '/w/api.php?action=createaccount'
        url = '%s/%s' % (wikiurl, endpoint)

        # API Post variables
        payload = {
            'username': args.user,
            'email': args.email,
            'mailpassword': 'true',
            'reason': 'New Employee',
            'createtoken': createaccount_token,
            'createreturnurl': url,
            'format': 'json',
            }

        print payload


        # Make initial request to get token
        result = session.post(url, data=payload)

        if args.debug:
            print("Auth Response: %s" % (result.text))
        data = result.json()

        # If initial request was successful, make second request using token
        # if 'createaccount' in data and 'token' in data['createaccount']:
            # grab token from first post, and add to new post
            # payload['token'] = str(data["createaccount"]["token"])

            # temporary workaround for TitleBlacklist Extension
        payload['ignoreTitleBlacklist'] = 'true'

        # Make second request using token
        result2 = session.post(url, data=payload)
        print json.dumps(result2.json(), sort_keys=True, indent=4)
        # else:
        #     print('Something went wrong with CREATE')
        #     print json.dumps(result2.json(), sort_keys=True, indent=4)
        #     continue
