import requests
import base64
import sys
import re
import json
import simplejson as json
import time
import argparse
import mmap
import argcomplete
import argparse
import config
import tokens
import os
from termcolor import colored
from pprint import pprint


def createEmptyBinaryFile(name):
    f = open(name, "wb")
    f.write(1*b'\0')
    f.close()

def initGitUrlFile():
    if not config.GITHUB_URL_FILE or os.path.getsize(config.GITHUB_URL_FILE) == 0:
        createEmptyBinaryFile(config.GITHUB_URL_FILE)

def initWordlist(wordlist):
    if not wordlist or os.path.getsize(wordlist) == 0:
        createEmptyBinaryFile(wordlist)

def checkToken(content, tokensMap):
    tokens = {}
    # For each type of tokens (ie "AWS"...)
    for token in tokensMap.keys():
        googleUrlFound = False
        googleSecretFound = False
        regex_pattern = tokensMap[token]
        # Apply the matching regex on the content of the file downloaded from GitHub
        result = re.search(regex_pattern, content)
        # If the regex matches, add the result of the match to the dict tokens and the token name found
        if result:
            if token == "GOOGLE_URL":
                googleUrlFound = True
            elif token == "GOOGLE_SECRET":
                googleSecretFound = True
            else:
                tokens[result] = token
            if (googleUrlFound and googleSecretFound):
                tokens[result] = "GOOGLE"                
    return tokens

def notifySlack(message):
    if not config.SLACK_WEBHOOKURL:
        print("Please define Slack Webhook URL to enable notifications")
        exit()
    requests.post(config.SLACK_WEBHOOKURL, json={"text": message})

def writeToWordlist(content, wordlist):
    f = open(wordlist, "a+")
    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    filename = content.split('/')[-1]
    if s.find(bytes(filename,'utf-8')) == -1:
        f.write(filename + "\n")

def displayResults(result, tokenResult, rawGitUrl):
    possibleTokenString = "[!] POSSIBLE "+tokenResult[result]+" TOKEN FOUND (keyword used:"+githubQuery+")"
    print(colored(possibleTokenString,"green"))
    urlString = "[+] URL : " + rawGitUrl
    print(urlString)
    clean_token = re.sub(tokens.CLEAN_TOKEN_STEP1, '', result.group(0))
    clean_token2 = re.sub(tokens.CLEAN_TOKEN_STEP2, '', clean_token)
    clean_token2 = clean_token2.replace('\n', ' ').replace('\r', '')
    tokenString = "[+] Token : " + clean_token2
    print(tokenString)
    return possibleTokenString+"\n"+urlString+"\n"+tokenString

def parseResults(content):
    data = json.loads(content)
    contentRaw = {}
    f = open(config.GITHUB_URL_FILE, "a+", encoding='utf-8')
    try:
        for item in data['items']:
            gitUrl = item['url']
            # TODO Centralize header management for token auth here (rate-limit more agressive on Github otherwise)
            headers = {'Accept': 'application/vnd.github.v3.text-match+json',
            'Authorization': 'token ' + config.GITHUB_TOKENS[0]
            }
            response = requests.get(gitUrl,headers=headers)
            data2 = json.loads(response.text)
            rawGitUrl = data2['download_url']
            s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            if s.find(bytes(rawGitUrl,'utf-8')) == -1:
               f.write(rawGitUrl + "\n")
               contentRaw[rawGitUrl] = requests.get(rawGitUrl, headers=headers)
        return contentRaw
    except Exception as e:
        # TODO Catch rate-limit exception EXCEPTION 'download_url' "API rate limit exceeded for x.x.x.x (But here's the good news: Authenticated requests get a higher rate limit. Check out the documentation for more details.)", 'documentation_url': 'https://developer.github.com/v3/#rate-limiting'
        # TODO Catch mmap exception if rawGitUrls is empty (have to be initialized before first use)
        print("Exception "+str(e))
        pass
                                    
def requestGithub(keywordsFile, args):
    keywordSearches = []
    tokenMap = tokens.initTokensMap()
    with open(keywordsFile, "r") as myfile:
        for keyword in myfile:
            for token in config.GITHUB_TOKENS:
                print(colored("[+] Github query : "+config.GITHUB_API_URL + githubQuery +" "+keyword.strip() +config.GITHUB_SEARCH_PARAMS,"yellow"))
                # TODO Centralize header management for token auth here (rate-limit more agressive on Github otherwise)
                headers = {
                    'Accept': 'application/vnd.github.v3.text-match+json',
                    'Authorization': 'token ' + token
                }
                try:
                    response = requests.get(config.GITHUB_API_URL + githubQuery +" "+keyword.strip() +config.GITHUB_SEARCH_PARAMS, headers=headers)
                    print("[i] Status code : " + str(response.status_code))
                    if response.status_code == 200:
                        content = parseResults(response.text)
                        if content:
                            for rawGitUrl in content.keys():
                                tokensResult = checkToken(content[rawGitUrl].text, tokenMap)
                                for token in tokensResult.keys():
                                    displayMessage = displayResults(token, tokensResult, rawGitUrl)
                                    if args.slack:
                                        notifySlack(displayMessage)
                                    if args.wordlist:
                                        writeToWordlist(rawGitUrl, args.wordlist)
                        break
                except UnicodeEncodeError as e:
                    print(e.msg)
                    pass
    return keywordSearches

parser = argparse.ArgumentParser()
argcomplete.autocomplete(parser)
parser.add_argument('-k', action='store', dest='keywordsFile', help='Specify a keywords file (-k keywordsfile.txt)')
parser.add_argument('-q', action='store', dest='query', help='Specify your query (-q "apikey")')
parser.add_argument('-s', '--slack', action='store_true', help='Enable slack notifications', default=False)
parser.add_argument('-w', action='store', dest='wordlist', help='Create a wordlist that fills dynamically with discovered filenames on GitHub')
args = parser.parse_args()

if not args.keywordsFile:
    print("No keywords file is specified")
    exit()

if not args.query:
    print("No query (-q) is specified, default query will be used")
    args.query = " "
    githubQuery = args.query

keywordsFile = args.keywordsFile
githubQuery = args.query
tokenMap = tokens.initTokensMap()
tokensResult = []

# If wordlist, check if file is binary initialized for mmap 
if(args.wordlist):
    initWordlist(args.wordlist)

# Init URL file 
initGitUrlFile()

# Query the GitHub API to get the responses with the specified uniq keywords and keyword files and returns an array of the API responses
responses = requestGithub(keywordsFile, args)
    # For each response from the API 
        # Parsing of the results of the API to get the file specified in the rawGitUrl and returns a dict with URL as keys and content of the file as value
            # For each rawGitUrl in dict keys
                # Check if a token is present in the http response according the token map and returns a dict of regex results as keys and token name as value
                # For each token found, display it on the output 
