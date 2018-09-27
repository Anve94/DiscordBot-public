#/bin/python3
import discord
import logging
import settings
import asyncio
import sys
import re
import urllib.request
import json
import random

from RoleManager import RoleManager
from PrizeManager import PrizeManager
from BugReporter import BugReporter
from MessageBuilder import MessageBuilder

from key import API_KEY
from functions import has_admin_rights, reply_to_command
from functions import has_build_rights

from database import engine, Entry, Giveaway
from sqlalchemy.orm import sessionmaker

from datetime import datetime, time
from configparser import SafeConfigParser

logging.basicConfig(level=logging.INFO)

# import settings
version, self_roles, mod_roles = settings.BOT_VERSION, settings.SELF_ROLES, settings.MOD_ROLES
permitted_ranks = settings.PERMITTED_RANKS
devs = settings.REPORT_TO_DEVS
sleep_time = settings.MESSAGE_DELETE_TIME

# Keeps track whether or not a giveaway is running
giveaway_is_running = False

# Setup the database connection session
# N.B. @Twyki add objects to the session using session.add(obj) and commit changes with session.commit()
Session = sessionmaker(bind=engine)
session = Session()

# Create a new discord client
client = discord.Client()

# Create an about message, just because
about_msg = "Hello! Just a friendly notification that the bot is running and was configured succesfully. \n"
about_msg += "Here is some more information about me... \n"
about_msg += "**Bot Version: ** {} \n".format(version)
about_msg += "**Wrapper Version: ** {} \n".format(discord.__version__)
about_msg += "**Self-assignable roles key->value pairs: ** \n"
for key in self_roles:
    about_msg += "\t \t \t{} => {} \n".format(key, self_roles[key])
about_msg += "**Mod-assignable roles key->value pairs: ** \n"
for key in mod_roles:
    about_msg += "\t \t \t{} => {} \n".format(key, mod_roles[key])
about_msg += "\nCreated with :heart: by Anve"

async def minute_counter():
    await client.wait_until_ready()

    server = next(iter(client.servers))
    minutes = 1
    weekly_is_posted = False

    while not client.is_closed:
        

        # Reward entries every 12 minutes
        # This is a backup in case chat is dead
        if minutes % settings.TIME_BETWEEN_SNAPSHOTS == 0:
            pm = PrizeManager(client)
            members =  pm.take_snapshot()
            pm.award_entries(members)

        # Keep the background task looping
        
        # Check if bot needs to send lottery reminder
        now = datetime.now()
        if (time(20, 0) < now.time()< time(20, 1)) or (time(2, 0) < now.time() < time(2, 1)):
            msg = "WANT TO GET RICH O-VER-NIGHT?\n"
            msg += "CHECK OUT THE SPUD LOT-TE-RY: <http://tinyurl.com/LotteryRules>"
            await client.send_message(server, msg)

        now = datetime.now()
        if (time(17, 0) < now.time() < time(17, 1)) or (time(4, 0) < now.time() < time(4, 1)):
            msg = "DO YOU HAVE IDEAS TO MAKE SPUD A BET-TER PLACE? CON-TACT A GM!.\n"
            msg += "WANT TO FILE FEED-BACK ANON-YMOUS-LY? USE THE FORM: <https://tinyurl.com/spud-feedback>"
            await client.send_message(server, msg)

        # Check if the bot needs to send out a voice reminder for giveaway
        if minutes % settings.TIME_BETWEEN_VOICE_REMINDERS == 0:
            msg = "**GREETINGS, CI-TI-ZENS.** \n"
            msg += "PLEASE CON-SI-DER JOIN-ING A VOICE CHAN-NEL FOR A CHA-NCE TO WIN A FOUR HUN-DRED GEM RE-WARD "
            msg += "BY THE END OF THIS MONTH!"
            await client.send_message(server, msg)
            minutes = 0

        # Check if the weekly message should be posted
        now = datetime.now()
        if (time(0, 0) <= now.time() <= time(0, 5)) and now.weekday() == 0:
            if not weekly_is_posted:
                # Print the message
                mb = MessageBuilder(client)
                await mb.print_stuff_happening(keep_mentions = False)
                weekly_is_posted = True
        else:
            weekly_is_posted = False

        await asyncio.sleep(60)
        minutes += 1


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print(about_msg)

    # Create giveaway section in config if it doesn't exist
    config = SafeConfigParser()
    config.read('config.ini')
    if not config.has_section('giveaway'):
        config.add_section('giveaway')
        config.set('giveaway', 'rank_restriction', 'False')

        with open('config.ini', 'w') as f:
            config.write(f)

    gw2 = discord.Game(name="Guild Wars 2", type=0)
    status = discord.Status("online")
    await client.change_presence(game=gw2, status=status)

    # Check if a giveaway was going on before the previous boot
    global giveaway_is_running
    resultset = session.query(Giveaway)
    if resultset.count() > 0:
        giveaway_is_running = True


""" Handles events fired because a message was sent in any channel """
@client.event
async def on_message(message):

    global giveaway_is_running

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Log all recieved commands, even if it came from DM
    if message.content.startswith('.'):
        # Don't log if second character is ., _ or " "
        char_2 = message.content[1]
        if  char_2 not in [" ", "_", ".", "-"]:
            delta = datetime.now()
            username = message.author.name
            channel = message.channel.name
            msg = message.content

            log_message = "{} - {}@{}: {}".format(delta, username, channel, message.content) + "\n"

            with open("command_log", "a") as log_file:
                log_file.write(log_message)

    # Check if the message was recieved over DM
    if message.channel.type == discord.ChannelType.private:
        return

    # Check for the next (expected) patch date for GW2
    if message.content.startswith('.patch'):
        link = 'https://www.thatshaman.com/tools/countdown/'
        json_link = link + '?format=json'
        with urllib.request.urlopen(json_link) as url:
            s = url.read()
            response = s.decode('utf-8')

        json_obj = json.loads(response)

        date = json_obj['date'].split("T")[0]

        if json_obj['confirmed']:
            status = "Confirmed"
        else:
            status = "Expected"

        output = "Here's what I could find...\n"
        output += "**Status**: {}\n".format(status)
        output += "**Date**: {}\n".format(date)
        output += "Based on info from that_shaman: <{}>".format(link)

        await client.send_message(message.channel, output)
        return

    # Test for voice access
    if message.content.startswith('.listchannelacces'):
        if message.author.id in devs:
            server = next(iter(client.servers))
            channels = []
            for channel in server.channels:
                if not channel.is_private:
                    if channel.type == discord.ChannelType.text:
                        typename = "text"
                    elif channel.type == discord.ChannelType.voice:
                        typename = "voice"
                    else:
                        typename = "unknown"
                    channels.append("{} ({}),".format(channel.name, typename))
            msg = ""
            for c in channels:
                msg += c
            await client.send_message(message.channel, msg)

    # Show given permissions


    # COMMUNITY GIVEAWAYS!
    if message.content.startswith('.giveaway --check-rank'):
        if not giveaway_is_running:
            if has_admin_rights(message.author) or message.author.id in devs:
                # Set config rank restriction to True
                config = SafeConfigParser()
                config.read('config.ini')
                config.set('giveaway', 'rank_restriction', 'True')
                with open('config.ini', 'w') as f:
                    config.write(f)

                giveaway_is_running = True
                await client.send_message(message.channel, "{} has started a giveaway! This giveaway is restricted to Little Sprouts and higher (lvl 2+)! Type .enter to enter the giveaway!".format(message.author.mention))


        return

    if message.content.startswith('.giveaway'):
        if not giveaway_is_running:
            if has_admin_rights(message.author) or message.author.id in devs:
                # Set the rank restriction in config to false
                config = SafeConfigParser()
                config.read('config.ini')
                config.set('giveaway', 'rank_restriction', 'False')
                with open('config.ini', 'w') as f:
                    config.write(f)
                
                giveaway_is_running = True
                await client.send_message(message.channel, "{} has started a giveaway! This giveaway is open to all! Type .enter to enter the giveaway!".format(message.author.mention))
                return

    if message.content.startswith('.enter'):
        if giveaway_is_running:
            discord_id = message.author.id

            # Check if user is entered, either manually by admin or by the user himself
            resultset = session.query(Giveaway).filter_by(discord_id = discord_id)
            if resultset.count() > 0:
                sent_msg = await client.send_message(message.channel, "{}, you are already entered in the giveaway!".format(message.author.mention))
                await asyncio.sleep(5)
                await client.delete_message(sent_msg)
                await client.delete_message(message)
                return

            # Check if the giveaway is rank restricted
            config = SafeConfigParser()
            config.read('config.ini')

            rank_restricted = config.getboolean('giveaway', 'rank_restriction')
            # If the rank is restricted, and the user doesn't match the rank
            # They get a DM and the function is exited because it doesn't need to check the rest
            if rank_restricted:
                # Check if the user has the required rank
                member = message.author
                has_rank = False
                for role in member.roles:
                    if role.name == "Little Sprout":
                        has_rank = True

                if not has_rank:
                    explain = ""
                    explain += "The giveaway you tried to enter has a rank restriction.\n\n"
                    explain += "**Why is there a rank restriction?**\n"
                    explain += "We have two types of giveaways. There's global giveaways set up by the GM's and WP, and "
                    explain += "there are giveaways set up by individual members. Global giveaways are open to all. However, when an "
                    explain += "individual member gives away something, they can choose to put this rank restriction in place. Usually this is "
                    explain += "to prevent people generally not really engaging with the community snatching away keys from more active members. "
                    explain += "You should see this type of giveaway as a giveaway where a community member gives away something personal to another (active) community member.\n\n"
                    explain += "**So how do these ranks work?**\n"
                    explain += "The ranks are tied in to the Mee6 leveling system. When you post a message on the discord server, Mee6 gives you XP. "
                    explain += "When you've accumulated enough XP, Mee6 will give you a new level, and at certain levels also a new rank. You need to be "
                    explain += "at least level 2 (which is the Little Sprout rank on discord) to enter this giveaway.\n\n"
                    explain += "**Can I still enter the giveaway if I manage to get the required rank before the giveaway ends?**\n"
                    explain += "Absolutely! Just be aware that it might take several minutes for Mee6 to give you the rank once you hit level 2.\n\n"
                    explain += "**So I should just spam all day to get my rank up huh?**\n"
                    explain += "Mee6 only gives you XP once every minute. Spamming will not help to get your rank any faster.\n\n"
                    explain += "**I still engage with the community through other means. Shouldn't I still be allowed to enter?**\n"
                    explain += "It depends. If you are not active through chat but active through other means, send a message to the member facilitating "
                    explain += "this giveaway. Ultimately, since they are giving away the goods, it's their decision. If they agree with you, you can be "
                    explain += "entered in the giveaway manually!"

                    await client.send_message(member, explain)
                    await client.delete_message(message)

                    return
                
            new_record = Giveaway(discord_id = discord_id)
            session.add(new_record)
            session.commit()
            sent_msg = await client.send_message(message.channel, "{}, you have succesfully entered the giveaway!".format(message.author.mention))
            await asyncio.sleep(5)
            await client.delete_message(sent_msg)
            await client.delete_message(message)

            return
        else:
            await client.send_message(message.author, "You attempted to enter a giveaway, but there isn't one running. If you believe this is in error, please ask in chat or contact the bot owner or a server admin.")
            await client.delete_message(message)
            return

    if message.content.startswith('.roll'):
        if has_admin_rights(message.author) or message.author.id in devs:
            giveaway_is_running = False
            # Check if there are any entries
            resultset = session.query(Giveaway)
            if resultset.count() <= 0:
                await client.send_message(message.channel, "There were no entries (left) so no winner was drawn.")
                return

            # Fetch all entries as a list
            entries = []
            server = next(iter(client.servers))
            # First, get all the entries from the db
            for instance in session.query(Giveaway):
                # Lookup the discord member object from the user_id
                member = server.get_member(instance.discord_id)
                # If the member has left the server, they can no longer be found during lookup and will result in a NoneType
                if member is not None:
                    entries.append(member)

            win_chance = 1 / len(entries) * 100
            winner = random.choice(entries)

            msg = "Congratulations {}! You won the giveaway (win chance {:.2f}%).".format(winner.mention, win_chance)

            # Remove the winner from the giveaway table
            session.query(Giveaway).filter_by(discord_id = winner.id).delete()
            session.commit()

            await client.send_message(message.channel, msg)
            return

    if message.content.startswith('.end'):
        if has_admin_rights(message.author) or message.author.id in devs:
            session.query(Giveaway).delete()
            session.commit()
            giveaway_is_running = False
            await client.send_message(message.channel, "The current giveaway has ended!")
        return

    if message.content.startswith('.approve'):
        if has_admin_rights(message.author) or message.author.id in devs:
            if giveaway_is_running:
                member = message.mentions[0]
                resultset = session.query(Giveaway).filter_by(discord_id = member.id)
                # Don't save a new record if the person already entered
                if resultset.count() > 0:
                    sent_msg = await client.send_message(message.channel, "This user has already entered the giveaway!")
                    await asyncio.sleep(5)
                    await client.delete_message(sent_msg)
                    await client.delete_message(message)
                else:
                    new_record = Giveaway(discord_id = member.id)
                    session.add(new_record)
                    session.commit()
                    sent_msg = await client.send_message(message.channel, "{} has approved {} for the giveaway manually!".format(message.author.mention, member.mention))
                    await asyncio.sleep(5)
                    await client.delete_message(message)
                return
            else:
                await client.send_message(message.author, "You attempted to manually approve someone for the giveaway, but I couldn't find a giveaway running at this time.")

            return

    # POLLS!
    if message.content.startswith('.poll'):
        if has_admin_rights(message.author) or message.author.id in devs:
            split_message = message.content.split()
            poll_body = "**POLL TIME BA-BY!** \n"
            poll_body += " ".join(split_message[1:])
            poll = await client.send_message(message.channel, poll_body)
            await client.add_reaction(poll, '\U0001F44D')
            await client.add_reaction(poll, '\U0001F44E')
        else:
            return

    # Remove self-assignable role
    if message.content.startswith('.iamn'):
        author = message.author
        split_message = message.content.split()
        try:
            role_cmd = split_message[1].lower()
            if role_cmd in self_roles:
                role_to_set = self_roles[role_cmd]
                rm = RoleManager(client, message)
                role = rm.fetch_role_by_name(role_to_set)
                await rm.take_role(role, author)
                return
            else:
                return
        except:
            return

    # Add self-assignable role
    if message.content.startswith('.iam'):
        author = message.author
        split_message = message.content.split()
        try:
            role_cmd = split_message[1].lower()
            if role_cmd in self_roles:
                role_to_set = self_roles[role_cmd]
                rm = RoleManager(client, message)
                role = rm.fetch_role_by_name(role_to_set)
                await rm.give_role(role, author)
                return
            else:
                raise
                return
        except:
            return

    # Add moderator assignable roles
    # i.e. .giverole Role MemberMention MemberMention (as *args)
    if message.content.startswith('.giverole'):
        author = message.author
        rm = RoleManager(client, message)
        # Check if message author has access to command
        if has_admin_rights(author) or message.author.id in devs:
            # Parse the given command arguments.
            try:
                arguments = message.content.split()
                role_txt = arguments[1].lower()
                # Find the role, see if it is a mass-assignable role and fetch the role object
                if role_txt in mod_roles:
                    role_name = mod_roles[role_txt]
                    role = rm.fetch_role_by_name(role_name)
                else:
                    return

                # Parse all the members given to the command
                member_mentions = arguments[2:]
                members = [] # Keep track of the fetched member objects
                for mention in member_mentions:
                    if '!' in mention:
                        member_id = mention[3:-1]
                    else:
                        member_id = mention[2:-1]
                    member = message.server.get_member(member_id)
                    members.append(member)
                    

                # Hand over all parsed data to the RoleManager
                await rm.mass_give_role(role, members)
                return

            except:
                raise
                return
        else:
            return

    # Remove moderator assignable role
    if message.content.startswith('.takerole'):
        author = message.author
        rm = RoleManager(client, message)
        # Check if message author has access to command
        if has_admin_rights(author) or message.author.id in devs:
            # Parse the given command arguments.
            try:
                arguments = message.content.split()
                role_txt = arguments[1].lower()
                # Find the role, see if it is a mass-assignable role and fetch the role object
                if role_txt in mod_roles:
                    role_name = mod_roles[role_txt]
                    role = rm.fetch_role_by_name(role_name)
                else:
                    return

                # Parse all the members given to the command
                member_mentions = arguments[2:]
                members = [] # Keep track of the fetched member objects
                for mention in member_mentions:
                    if '!' in mention:
                        member_id = mention[3:-1]
                    else:
                        member_id = mention[2:-1]
                    member = message.server.get_member(member_id)
                    members.append(member)
                    

                # Hand over all parsed data to the RoleManager
                await rm.mass_take_role(role, members)
                return

            except:
                raise
                return
        else:
            return

    # Reset the giveaway entries table
    if message.content.startswith('.reset'):
        pm = PrizeManager(client)
        await pm.reset_giveaway_entries(message)
        return

    # List the entries for the giveaway
    if message.content.startswith('.entries'):
        pm = PrizeManager(client)
        await pm.print_entries(message)
        return

    # DM the list of giveaway entries
    if message.content.startswith('.dmentries'):
        pm = PrizeManager(client)
        await pm.dm_entries(message)
        return

    # MAKE SURE THIS STAYS ABOVE .DRAW OR IT WILL NOT FIRE
    if message.content.startswith('.draw --preserve'):
        pm = PrizeManager(client)
        await pm.draw_winner(message, intermediary=True)
        return

    if message.content.startswith('.draw'):
        pm = PrizeManager(client)
        await pm.draw_winner(message)
        return

    if message.content.startswith('.bug'):
        report = " ".join(message.content.split()[1:])
        br = BugReporter(client)
        await br.report_bug(message, report)
        return

    if message.content.startswith('.denyreporting'):
        br = BugReporter(client)
        await br.add_abuser(message, abuser_mention=message.content.split()[1])
        return

    if message.content.startswith('.allowreporting'):
        br = BugReporter(client)
        await br.remove_abuser(message, abuser_mention=message.content.split()[1])
        return

    if message.content.startswith('.issue'):
        command = message.content[6:]
        try:
            title, body = command.split("|")
            br = BugReporter(client)
            await br.create_issue(message, title, body)
        except:
            return
        return

    # Send copyright notice
    if message.content.startswith('.copyright'):
        msg = "All Guildwars-related texts, names and images are © 2015 ArenaNet, "
        msg += "LLC. All rights reserved. NCSOFT, the interlocking NC logo, ArenaNet, Guild Wars, "
        msg += "Guild Wars Factions, Guild Wars Nightfall, Guild Wars: Eye of the North, Guild Wars 2, "
        msg += "Heart of Thorns, and all associated logos and designs are trademarks or registered "
        msg += "trademarks of NCSOFT Corporation. All other trademarks are the property of their "
        msg += "respective owners."

        await client.send_message(message.author, msg)
        await client.delete_message(message)
        return

    if message.content.startswith('.build'):
        if has_admin_rights(message.author) or has_build_rights(message.author):
            mb = MessageBuilder(client)
            await mb.print_stuff_happening()

        await client.delete_message(message)
        return

    # Dm the evoker a list of all token positions in the event modules
    if message.content.startswith('.modules'):
        mb = MessageBuilder(client)
        await mb.dm_modules(message)
        return

    if message.content.startswith('.delmodule'):
        try:
            token = message.content.split(" ")[1]
            mb = MessageBuilder(client)
            await mb.delete_module(message, token)
        except:
            raise
        return

    if message.content.startswith('.addmodule'):
        if has_admin_rights(message.author):
            try:
                mb = MessageBuilder(client)
                contents = message.content[11:]
                commands = contents.split("|")
                token = commands[0].strip() # Strip leading and trailing spaces
                if not mb.token_in_use(token):
                    position = commands[1].strip()
                    image_link = commands[2].strip()
                    contents = commands[3].strip()

                    await mb.add_module(message, token, position, image_link, contents)
                else:
                    resp = "Sorry, the token you have given me already exists. "
                    resp += "Please find your original message below:\n{}".format(message.content)
                    await client.send_message(message.author, resp)

            except:
                resp = "I'm sorry, but I could not understand you command. Contact the hoster of this bot if you have any questions. "
                resp += "Original message: \n{}".format(message.content)
                await client.send_message(message.author, resp)
                raise

        await client.delete_message(message)

        
        return

    if message.content.startswith('.commands'):
        file = open("commands.md", "r")
        msg = ""
        for line in file:
            msg += line
        await client.send_message(message.author, msg)
        await client.delete_message(message)
        return

    # Sends some bot stats over DM
    if message.content.startswith('.stats'):
        if message.author.id in settings.REPORT_TO_DEVS or has_admin_rights(message.author):
            server = next(iter(client.servers))

            msg = "**Bot Version**\n"
            msg += "Bot version: {}\n".format(settings.BOT_VERSION)
            msg += "Lib version: {}\n\n".format(discord.__version__)

            cnt_eu = 0
            cnt_na = 0
            cnt_no_role = 0
            cnt_any = 0
            for member in server.members:
                valid_roles = 0
                for role in member.roles:
                    if role.name == 'NA':
                        cnt_na += 1
                        valid_roles += 1
                    elif role.name == "EU":
                        cnt_eu += 1
                        valid_roles += 1

                if valid_roles == 0:
                    cnt_no_role += 1
                else:
                    cnt_any += valid_roles

            total_found = len(server.members)
            percent_eu = cnt_eu / total_found * 100 if cnt_eu > 0 else 0
            percent_na = cnt_na / total_found * 100 if cnt_na > 0 else 0
            percent_none = cnt_no_role / total_found * 100 if cnt_no_role > 0 else 0
            msg += "**Region role distribution** (of entire population) \n"
            msg += "Total discord members: {}\n".format(total_found)
            msg += "EU role percentage: {:.2f}%  \n".format(percent_eu)
            msg += "NA role percentage: {:.2f}% \n".format(percent_na)
            msg += "No role percentage: {:.2f}% \n".format(percent_none)
            msg += "\n"

            percent_eu = cnt_eu / cnt_any * 100 if cnt_eu > 0 else 0
            percent_na = cnt_na / cnt_any * 100 if cnt_na > 0 else 0
            msg += "**Region role distribution amongst distributed roles**\n"
            msg += "EU role percentage: {:.2f}% ({} members)\n".format(percent_eu, cnt_eu)
            msg += "NA role percentage: {:.2f}% ({} members)\n\n".format(percent_na, cnt_na)

            msg += "**Assignable roles allowed** \n"
            msg += "Self-assignable roles list: \n"
            for key in self_roles:
                msg += "\t{} => {} \n".format(key, self_roles[key])
        
            msg += "\nGM-assignable roles list:  \n"
            for key in mod_roles:
                msg += "\t{} => {} \n".format(key, mod_roles[key])

            msg += "\n"
            pm = PrizeManager(client)
            sum_tickets = pm.sum_entries()
            avg_tickets = pm.avg_entries()
            participants = len(pm.get_entries_as_list())
            msg += "**Giveaway Stats**\n"
            msg += "Giveaway entries distributed this month: {}\n".format(sum_tickets)
            msg += "Average giveaway entries/entered member: {:.2f}\n".format(avg_tickets)
            msg += "Total giveaway participants: {}\n".format(participants)
            await client.send_message(message.author, msg)
            await client.delete_message(message)
        return

""" Event handler for a new person joins the server """
@client.event
async def on_member_join(member):
    
    # This is a stupid idea, but the live bot only has 1 server so it is feasable
    server = next(iter(client.servers))

    about_channel = None

    for channel in server.channels:
        if channel.name == "about_the_club":
            about_channel = channel
            break

    msg = "CI-TI-ZENS: PLEASE WEL-COME {} TO THE SPUD CLUB.\n".format(member.mention)

    if channel is not None:
        msg += "YOU CAN FIND YOUR O-PE-RA-TIONS MA-NUAL IN {}. TO-PICS IN-CLUDE ".format(about_channel.mention)
    else:
        msg += "YOU CAN FIND YOUR O-PE-RA-TIONS MA-NUAL IN #about_the_club. TO-PICS IN-CLUDE "

    msg += "HOW TO JOIN THE IN-GAME GUILD AND WHAT THIS PLACE IS."

    await client.send_message(server, msg)

    return

client.loop.create_task(minute_counter())
client.run(API_KEY)
