# About gitGraber

gitGraber is a tool developed in Python3 to monitor GitHub to search and find sensitive data for different online services such as: Google, Amazon, Paypal, Github, Mailgun, Facebook, Twitter, Heroku, Stripe...

![demo](https://i.ibb.co/h1rn2KK/example-script-execution.png)

# How it work ?

It's important to understand that gitGraber is not designed to check history of repositoriy, many tools can already doing this great. gitGraber was developed to monitor and to parse last indexed files on GitHub. If gitGraber find something interesting, you will receive a notification on your Slack channel. You can also use it to have results directly on the command line.

Regex are supposed to be the more precise than possible. Sometimes, maybe you will have false-positive, feel free to contribute to improve recon and add new regex for pattern detection.

We prefer to reduce false positive instead to send notification for every "standard" API key which could found by gitGraber but irrelevant for hunter.

# How to use gitGraber ?

``````````
usage: gitGraber.py [-h] [-k KEYWORDSFILE] [-q QUERY] [-s] [-w WORDLIST]

optional arguments:
  -h, --help       show this help message and exit
  -k KEYWORDSFILE  Specify a keywords file (-k keywordsfile.txt)
  -q QUERY         Specify your query (-q "apikey")
  -s, --slack      Enable slack notifications
  -w WORDLIST      Create a wordlist that fills dynamically with discovered filenames on GitHub
``````````

## Dependencies

gitGraber needs some dependencies, to install them on your environment:

``pip3 install -r requirements.txt``

## Configuration

Before to start **gitGraber** you need to modify the configuration file ``config.py`` :

- Add your own Github tokens : ``GITHUB_TOKENS = ['yourToken1Here','yourToken2Here']``
- Add your own Slack Webhook : ``SLACK_WEBHOOKURL = 'https://hooks.slack.com/services/TXXXX/BXXXX/XXXXXXX'``

*[How to create Slack Webhook URL](https://get.slack.help/hc/en-us/articles/115005265063-Incoming-WebHooks-for-Slack)*

To start and use gitGraber : ``python3 gitGraber.py -k wordlists/keywords.txt -q "uber" -s``

_We recommend creating a cron that will execute the script regulary_:

``*/10 * * * * cd /BugBounty/gitGraber/ && /usr/bin/python3 gitGraber.py -k wordlists/keywords.txt -q "uber" -s >/dev/null 2>&1``

## Wordlists & Resources

Some wordlists have been created by us and some others are inspired from other repo/researcher

* Link : https://gist.github.com/nullenc0de/fa23444ed574e7e978507178b50e1057
* Link : https://github.com/streaak/keyhacks

# TODO

- Add more regex & patterns
- Add multi threads
- Add modules to verify the validity of API key
- Add bearer token detections
- Change token cleaning output
- Add user and org names display in notifications

# Authors

- Reptou [Twitter](https://twitter.com/R_Marot)
- Hisxo [Twitter](https://twitter.com/adrien_jeanneau)

# Disclaimer

This project is made for educational and ethical testing purposes only. Usage of this tool for attacking targets without prior mutual consent is illegal. Developers assume no liability and are not responsible for any misuse or damage caused by this tool.
