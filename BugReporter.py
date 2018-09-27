import discord

from settings import REPORT_TO_DEVS as dev_list
from functions import reply_to_command, has_admin_rights

from database import engine, Abuser
from sqlalchemy.orm import sessionmaker

# Github issue creation
from github import Github
from github_key import token as access_token

Session = sessionmaker(bind=engine)
session = Session()

class BugReporter(object):

	def __init__(self, client):
		self.client = client

	""" Send a bug report over DM to the developers
	
			Params:
				Message message 	- The message used to invoke the command
				String report 		- The text contents for the bug report

			Returns:
				void
	"""
	async def report_bug(self, message, report):
		server = next(iter(self.client.servers))
		# Check if the person reporting the bug is on the block list
		resultset = session.query(Abuser).filter_by(discord_id = message.author.id)
		count = resultset.count()
		if count == 0:
			msg = "Bugreport from {}: {}".format(message.author.name, report)
			for dev in dev_list:
				user = server.get_member(dev)

				await self.client.send_message(user, msg)

			resp = "{}: HE-ROES NEV-ER DIE, M.O.X. CAN NEV-ER BE CON-QUERED. BUT M.O.X. DOES NEED MAIN-TEN-ANCE. THANK YOU FOR THIS RE-MIN-DER!".format(message.author.mention)
			await reply_to_command(self.client, message, resp)
		return

	""" Adds a discord_id to the abusers table as long as the user is not already included in
		a record.

			Params:
				Message message 		- The message used to invoke the command
				String abuser_mention 	- A mentionable representation of a user as string

			Returns:
				void
	"""
	async def add_abuser(self, message, abuser_mention):
		if has_admin_rights(message.author) or message.author.id in dev_list:
			server = next(iter(self.client.servers))
			abuser_id = abuser_mention[2:-1]
			resultset = session.query(Abuser).filter_by(discord_id = abuser_id)
			count = resultset.count()
			if count == 0:
				# User wasn't in the abuse list yet, so let's add him
				abuser = Abuser(discord_id = abuser_id)
				session.add(abuser)
				session.commit()

			reply = "I THINK THERE-FORE I AT-TACK! {} HAD THEIR PRI-VI-LEGE PURGED.".format(abuser_mention)
			await reply_to_command(self.client, message, reply)
		return

	""" Looks up an abuser record and deletes it if it exists.

			Params:
				Message message 		- A message object containing the message
										used to invoke the command
				String abuser_mention 	- A mentionable representation of a user as string

			Returns:
				void
	"""
	async def remove_abuser(self, message, abuser_mention):
		if has_admin_rights(message.author) or message.author.id in dev_list:
			server = next(iter(self.client.servers))
			abuser_id = abuser_mention[2:-1]
			resultset = session.query(Abuser).filter_by(discord_id = abuser_id)
			count = resultset.count()
			if count == 1:
				# User was in the list, so let's remove him
				session.query(Abuser).filter_by(discord_id = abuser_id).delete()
				session.commit()
			else:
				reply = "{}: TAR-GET COULD NOT GET AC-QUIRED. ALL OP-ER-ATIONS WITH-IN NOR-MAL PA-RA-MA-TERS.".format(message.author.mention)
				await reply_to_command(self.client, message, reply)
				return

			reply = "THE ONLY WIN-NING MOVE IS NOT TO PLAY. FUNC-TIO-NA-LI-TIES RE-STORED FOR {}".format(abuser_mention)
			await reply_to_command(self.client, message, reply)

		return

	""" Creates a github issue.

			Params:
				Message message 		- The message used to invoke the command
				String title 			- The title for the github issue
				String body 			- The body for the github issue

			Returns:
				void 

	"""
	async def create_issue(self, message, title, body):
		if message.author.id in dev_list:
			g = Github(login_or_token=access_token)

			found = None

			# Attempt to find the discord repository
			for repo in g.get_user().get_repos():
				if repo.name == "DiscordBot":
					found = repo

			# Only continue if the repo is found
			if found is not None:
				try:
					issue = found.create_issue(title=title, body=body)
				except:
					raise
					return

				reply = "MAIN-TEN-ANCE RE-PORT UP-LOAD-ED. THANK YOU {}".format(message.author.mention)
				await reply_to_command(self.client, message, reply)
				return

			else:
				reply = "CON-NEC-TION TO EX-TER-NAL SER-VICE FAILED. CHECK API STA-TUS"
				await reply_to_command(self.client, message, reply)
				return
