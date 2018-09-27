""" This is a generic file for common functions that are reused """
import settings
import asyncio

permitted_ranks = settings.PERMITTED_RANKS
sleep_time = settings.MESSAGE_DELETE_TIME


""" Check if a given member has admin rights on the server

		Params:
			Member author 		- The member to check the rights agains

		Returns:
			bool is_allowed 	- Whether or not the permission is granted
"""
def has_admin_rights(author):
        is_allowed = False
        for role in author.roles:
            if role.name in permitted_ranks:
                is_allowed = True

        return is_allowed

def has_build_rights(author):
        is_allowed = False
        for role in author.roles:
                if role.name in settings.PERMITTED_BUILDERS:
                        is_allowed = True
        return is_allowed

""" Reply to an accepted command, respond to it and delete both messages after
	waiting the amount of time according to settings

	Params:
		Client client 		- The discord client, i.e. the bot itself
		Message request 	- The message used to invoke the command
		String response 	- Formatted text the bot needs to send as a reply

	Returns:
		void

"""
async def reply_to_command(client, request, response):
	sent_response = await client.send_message(request.channel, response)
	await asyncio.sleep(sleep_time)
	await client.delete_message(request)
	await client.delete_message(sent_response)
	return
