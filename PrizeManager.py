import discord
import asyncio
import settings
import random
import time
from database import Entry
from database import engine, Entry
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, desc
from functions import has_admin_rights, reply_to_command

sleep_time = settings.MESSAGE_DELETE_TIME
devs = settings.REPORT_TO_DEVS

# Setup db session
Session = sessionmaker(bind=engine)
session = Session()

class PrizeManager(object):

    message_counter = 0
    
    def __init__(self, client):
        # Represent the bots discord client
        self.client = client


    """ Takes a snapshot of all non-idle members in any voice channel
        
        params:
            None

        returns:
            List members 		- A list containing all member objects that were not AFK
                                  at the time of the snapshot being taken. List can be empty.
    """
    def take_snapshot(self):
        server = next(iter(self.client.servers))
        members = []
        for channel in server.channels:
            if channel.type == discord.ChannelType.voice and len(channel.voice_members) > 1:
                for member in channel.voice_members:
                    if (not member.self_deaf) and (not member.is_afk):
                        members.append(member)
    
        return members;

    """ Takes in a list of members to be updated in the database

        params:
            List members 	- The list of members to be awarded with ticket entries/score

        returns:
            void
    """
    def award_entries(self, members):
        for member in members:
            # search database for discord ID
            resultset = session.query(Entry).filter_by(discord_id = member.id)
            count = resultset.count()

            if count > 0:
                entry = resultset.first()
                entry.score += 1
                session.add(entry)
                session.commit()

            else:
                entry = Entry(discord_id = member.id, score = 1)
                session.add(entry)
                session.commit()
        return

    def sum_entries(self):
        return session.execute("SELECT SUM(score) FROM entries;").first()[0]

    def avg_entries(self):
        return session.execute("SELECT AVG(score) FROM entries;").first()[0]

    """ Removes a given discord ID from the entries table

            Params:
                String member_id 	- The id of the user to remove

            Returns:
                void

    """
    def remove_entry(self, member_id):
        resultset = session.query(Entry).filter_by(discord_id = member_id)
        count = resultset.count()

        if count > 0:
            session.query(Entry).filter_by(discord_id = member_id).delete()
            session.commit()

        return


    """ Deletes all records from the 'entries' table in the db
        If the user that gave the command has insufficient privileges, nothing happens

        Params:
            Message message 	- The message used to invoke the command

        Returns:
            void 
    """
    async def reset_giveaway_entries(self, message):
        if has_admin_rights(message.author):
            session.query(Entry).delete()
            session.commit()
            # Send reply to channel the message was from
            request, response = message, "{}: COM-MEN-DA-TIONS FROM THE PRE-VI-OUS MONTH HAVE BEEN PURGED SUC-CESS-FULLY.".format(message.author.mention)
            await reply_to_command(self.client, request, response)
        return

    """ Get the ticket entries for the giveaweay as 2 dimensional list

        Params:
            None

        Returns:
            List entries 		- All the entries for the given, each represented
                                as a list: [Member member, ticket_amount]
    """
    def get_entries_as_list(self):
        entries = []
        server = next(iter(self.client.servers))
        # First, get all the entries from the db
        for discord_id, score in session.query(Entry.discord_id, Entry.score).order_by(desc(Entry.score)):
            # Lookup the discord member object from the user_id
            member = server.get_member(discord_id)
                        # If the member has left the server, they can no longer be found during lookup and will result in a NoneType
            if member is not None:
                entries.append([member, score])

        return entries

    """ Send a list of all entries to the channel from where the message was evoked

        Params:
            Message message 		- The message used to invoke the command. Used to grab the channel for the reply

        Returns:
            void
    """
    async def print_entries(self, message):
        if has_admin_rights(message.author):
            entries = self.get_entries_as_list()
            msg = "**THE FOL-LO-WING CI-TI-ZENS ARE EN-DORSED BY M.O.X.: **\n"	# The text to be sent back
            for entry in entries:
                # Constrain the text size since discord has a character limit of 2000
                if len(msg) > 1500:
                    # If the message exceeds 1500 characters, send it prematurely and wipe the text for continuation
                    await self.client.send_message(message.channel, msg)
                    msg = ""
                msg += "{}: {} COM-MEN-DA-TIONS\n".format(entry[0].name, entry[1])

            await self.client.send_message(message.channel, msg)

        return

    """ Send a list of all entries over DM to the user that evoked the message

        Params:
            Message message 		- The message used to invoke the command. Used to grab the author.

        Requires:
            Admin privileges

        Returns:
            void
    """
    async def dm_entries(self, message):
        if has_admin_rights(message.author) or message.author.id in devs:
            entries = self.get_entries_as_list()
            await self.client.delete_message(message)
            msg = "**THE FOL-LO-WING CI-TI-ZENS ARE EN-DORSED BY M.O.X.: **\n"	# The text to be sent back
            for entry in entries:
                # Constrain the text size since discord has a character limit of 2000
                if len(msg) > 1500:
                    # If the message exceeds 1500 characters, send it prematurely and wipe the text for continuation
                    await self.client.send_message(message.author, msg)
                    msg = ""
                msg += "{}: {} COM-MEN-DA-TIONS\n".format(entry[0].name, entry[1])

            await self.client.send_message(message.author, msg)

        return

    """ Draw the winner, and send it to chat and over DM to whoever hands out the prizes

            Params:
                Message message 	- The original message object used to invoke the command
                bool intermediary 	- Whether or not this was an intermediary drawing.
                                      Winners will get redrawn for the next drawing when the drawing is
                                      intermediary. Otherwise they will be purged from the entries table

            Returns:
                void
    """
    async def draw_winner(self, message, intermediary=False):
        if has_admin_rights(message.author):

            server = next(iter(self.client.servers))

            # Grab all the entries
            entries = self.get_entries_as_list()

            if len(entries) == 0:
                return

            # Calculate the sum for all the tickets
            ticket_sum = sum([x[1] for x in entries])
            prize_sender = server.get_member(settings.PRIZE_HANDOUT_NOTIFY)

            # Determine win ranges and win chance
            win_ranges = [] # Will contain a list [Member, min winning value, max winning value, winchance]
            cur_range = 0
            for entry in entries:
                min_range = cur_range 
                max_range = cur_range + entry[1] - 1
                cur_range += entry[1]
                win_chance = entry[1] / ticket_sum * 100
                win_ranges.append([entry[0], min_range, max_range, win_chance])
            
            # Draw the winning number (inclusive start, exclusive end, step)
            lucky_number = random.randrange(0, ticket_sum + 1, 1)
            
            # Check to see who won! So exciting
            for entry in win_ranges:
                if entry[1] <= lucky_number <= entry[2]:
                    msg = "CON-GRA-TU-LATIONS {}, YOU ARE A WIN-NER. (WIN-CHANCE: {:.2f}%)".format(entry[0].mention, entry[3])
                    await self.client.send_message(message.channel, msg)

                    date_str = time.strftime("%d/%m/%Y %H:%M")
                    dm = "{} Won a gem giveaway ({:.2f}% chance) on {}\n".format(entry[0].name, entry[3], date_str)
                    dm += "Their winning range was [{}-{}] (inclusive) and I drew {}\n".format(entry[1], entry[2], lucky_number)
                    dm += "If you feel this drawing is incorrect based on the info above, please contact Anve or Twyki."
                    await self.client.send_message(prize_sender, dm)
                    
                    # Remove the winner from the entries table (assuming 1 drawing/month as default)
                    if not intermediary:
                        self.remove_entry(entry[0].id)

                    return
            return

        return
