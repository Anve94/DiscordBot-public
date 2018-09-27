import discord
import settings
from database import EventMessage

import http.client
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import json
import pytz
import calendar

import key
from functions import reply_to_command, has_admin_rights

from database import engine, EventMessage
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, asc

# Setup db session
Session = sessionmaker(bind=engine)
session = Session()


class MessageBuilder:
    
    def __init__(self, client):
        self.client = client
        self.channel_id = settings.STUFF_HAPPENING_ID
        self.event_div = settings.EVENT_DIVIDER_IMAGE
        self.ping = settings.EVENT_PING_MESSAGE

    async def add_module(self, message, token, position, image_url, content):
        # Note: function does not check admin rights because this is checked during command parsing
        
        # First, check if any higher positions/prio exist
        resultset = session.query(EventMessage).filter(EventMessage.position >= position)
        for row in resultset:
            # Only update all higher position if the given position exists. If it doesn't, there's a
            # gap so there's no need.
            if session.query(EventMessage).filter_by(position=position).count() > 0:
                row.position += 1
                session.add(row)
                session.commit()

        if image_url == "None" or image_url == "none":
            image_url = None

        new_record = EventMessage(token=token, content=content, image_url=image_url, position=position)
        session.add(new_record)
        session.commit()

        # Generate response message and add a preview
        await self.client.send_message(message.author, "The content module has been updated. You can review it below:\n")
        if image_url is not None:
            embed = discord.Embed(url=image_url)
            embed.set_image(url=image_url)
            await self.client.send_message(message.author, embed=embed)

        await self.client.send_message(message.author, content)

        return

    async def delete_module(self, message, token):
        
        if has_admin_rights(message.author):        
            resultset = session.query(EventMessage).filter_by(token = token)

            if resultset.count() > 0:
                row = resultset.first()

                # Save the old position and delete the record
                old_position = row.position
                session.delete(row)
                session.commit()

                # Iterate over higher positions and lower by one, then store back
                resultset = session.query(EventMessage).filter(EventMessage.position > old_position)
                for row in resultset:
                    row.position -= 1
                    session.add(row)
                    session.commit()

                response = "RE-MOVED TEXT FOR DES-IG-NA-TED TO-KEN."


            else:
                response = "COULD NOT FIND TEXT FOR DES-IG-NA-TED TO-KEN."

            await reply_to_command(self.client, message, response)

        return


    def suffix(self, d):
        return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

    async def print_stuff_happening(self, keep_mentions=True):

        # First, delete all messages if it doesn't have a mention
        server = next(iter(self.client.servers))
        channel = server.get_channel(self.channel_id)

        async for message in self.client.logs_from(channel):
            if (len(message.role_mentions) > 0 or message.mention_everyone) and keep_mentions:
                continue
            else: 
                await self.client.delete_message(message)

        # Send the ping if needs be
        if not keep_mentions:
            await self.client.send_message(channel, self.ping)

        # Send the community divider image
        embed = discord.Embed(url=self.event_div)
        embed.set_image(url=self.event_div)
        await self.client.send_message(channel, embed=embed)

        # Generate and send timetable
        timetable = self.fetch_timetable(key.CALENDAR_KEY, key.TEAMUP_API_KEY)
        #await self.client.send_message(channel, "**Temporarily disabled until calendar link is fixed.**")
        await self.client.send_message(channel, timetable)

        if session.query(EventMessage).count() > 0:
            resultset = session.query(EventMessage).order_by(EventMessage.position)
            for row in resultset:
                if row.image_url is not None:
                    embed = discord.Embed(url=row.image_url)
                    embed.set_image(url=row.image_url)
                    await self.client.send_message(channel, embed=embed)
                await self.client.send_message(channel, row.content)

        return

    async def dm_modules(self, message):

        if has_admin_rights(message.author):
            resultset = session.query(EventMessage).order_by(EventMessage.position)

            if resultset.count() > 0:
                dm = "**Here are all the tokens and positions:** \n"

                for row in resultset:
                    dm += "Position {}: {}\n".format(row.position, row.token)

            else:
                dm = "**No tokens found**"

            await self.client.send_message(message.author, dm)
            await self.client.delete_message(message)

        return


    """ Generates a Timetable for the current week
        Params:
                String cal      - Calender key
                String key      - API key
        Returns:
                String
    """
    def fetch_timetable(self, cal, key):
        con = http.client.HTTPSConnection('api.teamup.com')
        header = {'Teamup-Token': key}
        start = datetime.now() - timedelta(days=datetime.now().weekday())
        end = start + timedelta(days=7)
        request = '/' + cal + '/events?startDate=' + start.strftime("%Y-%m-%d") + '&endDate=' + end.strftime(
            "%Y-%m-%d")
        requestS = '/' + cal + '/subcalendars'
        con.request('GET', request, None, header)
        data = con.getresponse().read().decode("utf-8")
        parsed_json = json.loads(data)
        con.request('GET',requestS,None,header)
        dataS = con.getresponse().read().decode("utf-8")
        parsed_Cal = json.loads(dataS)
        dictC = {}
        for dd in parsed_Cal['subcalendars']:
            dictC[dd['id']]= dd['name']
        tablestring = ""
        olddate = ""
        for dd in parsed_json['events']:
            if dictC[dd['subcalendar_id']] == 'Community Events':
                continue
            if dictC[dd['subcalendar_id']] == 'NA Region Events':
                local_tz = pytz.timezone("America/New_York")
                date = dateutil.parser.parse(dd['start_dt'])
                #.astimezone(pytz.timezone("America/New_York"))
                if date.tzinfo is None:
                    date = local_tz.localize(date)
                else:
                    date = date.astimezone(local_tz)
            else:
                local_tz = pytz.timezone("UTC")
                date = dateutil.parser.parse(dd['start_dt'])
                #.astimezone(pytz.timezone("Europe/Paris"))
                if date.tzinfo is None:
                    date = local_tz.localize(date)
                else:
                    date = date.astimezone(local_tz)
            if olddate != date.day:
                tablestring += "\n__" + calendar.day_name[date.weekday()] + ", "\
                               + str(date.day) + self.suffix(date.day) + " of " \
                               + date.strftime('%B') + "__" + "\n"
            olddate = date.day
            if dictC[dd['subcalendar_id']] == 'EU Region Events':
                tablestring += "**[EU]"+ " " + dd['title']+ "** - "+ date.time().strftime('%H:%M') + " UTC | " \
                                + date.astimezone(pytz.timezone("Europe/Paris")).strftime('%H:%M %Z') + "\n"
            else:
                # + date.astimezone(pytz.timezone("UTC")).strftime('%H:%M') + " UTC | "\
                # ^ Removed from below += tablestring
                if dictC[dd['subcalendar_id']] == 'NA Region Events':
                    tablestring += "**[US]" + " " + dd['title'] + "** - " \
                        + date.astimezone(pytz.timezone("America/New_York")).strftime('%H:%M %Z') + " | "\
                        + date.astimezone(pytz.timezone("America/Los_Angeles")).strftime('%H:%M %Z') + "\n"
                else:
                    # + date.time().strftime('%H:%M') + " UTC | " \
                    tablestring += "**" + dd['title'] + "** - " \
                        + date.astimezone(pytz.timezone("Europe/Paris")).strftime('%H:%M %Z') + " | "\
                        + date.astimezone(pytz.timezone("America/New_York")).strftime('%H:%M %Z') + "  | "\
                        + date.astimezone(pytz.timezone("America/Los_Angeles")).strftime('%H:%M %Z') + "\n"
        return tablestring

    # Checks if the given token is in use
    def token_in_use(self, token):
        resultset = session.query(EventMessage).filter_by(token=token)
        return (resultset.count() > 0)
