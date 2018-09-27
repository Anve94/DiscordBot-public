# DiscordBot

## Disclaimer
This project has been discontinued. Some API keys required to run this software were removed from the source code.
Source code is provided as-is. Use at your own risk. Do not contact me in any way if you are unable to run this software.
I will not help you set it up. Channel ID's, discord ID's and names were removed from the sourcecode where applicable.
Running a single hosted copy of this software to service multiple discord servers breaks the code.

## About
This bot was used to implement custom features for the SPUD community discord channel.

## Current Features (outdated)
* M.O.X. allows users to set self-assignable ranks by using ```.iam eu/na``` and ```.iamnot eu/na```
* M.O.X. allows moderators to assign certain roles to a group of users using ```.giverole rolename @Mention @Mention``` and ``` .takerole rolename @Mention ```. List can contain one or multiple members. Only mentions are accepted, not names or id.
* M.O.X. will give a hearty welcome when we made a new friend
* M.O.X. will remove the message from where it received a given command where applicable after a few seconds
* M.O.X. deletes its own messages where applicable after a few seconds
* M.O.X. will relay maintenance notifications to [REDACTED] with ```.bug bug report here ```
* Admins can revoke and re-allow access to bugreporting with ```.denyreporting/.allowreporting @Mention```
* M.O.X. will take snapshots of the voice channels several times a day, and reward giveaway entries to those active
* M.O.X. will occasionally remind people that being in voice will enter them in the giveaway
* M.O.X. allows admins to list all giveaway entries in chat with ```.entries```
* M.O.X. is more than happy to send a DM to admins containing all giveaway entries with ```.dmentries```
* M.O.X. will draw a giveaway winner for admins with .draw. Afterwards, all entries from the winning person are reset
* If an admin doesn't want to deny a second chance of winning, the can use the ```--preserve```, i.e. ```.draw --preserve```
* M.O.X. allows admins to reset all giveaway entries with ```.reset```

## Installation and setup

### Requirements
* Python 3.5+
* Discord.py
* asyncio
* SQLalchemy
* pip3 (to install dependencies)
* Some stuff added after initially writing this document. Just run the codebase and you'll find out I suppose, heh.

### Installing dependencies
To install depencies, make sure you have pip installed and it is callable from terminal.
Afterwards, use
* ``` pip install -r requirements.txt ```
* If you have multiple python versions installed, run ```python3.5 -m pip install -r requirements.txt```

### Adding bot to discord server
* Please consult the Discord DevDocs to add the bot the server

### Run
You might want to consider wiping the database first
* ```cd database```
* ```rm database.sqlite```
* ```cd ../```
* ```python/python3.5 database.py```

Afterwards, run the project using
```python/python3.5 main.py```
or through the provided bash script.
