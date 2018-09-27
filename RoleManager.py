import asyncio
import settings
import discord

sleep_time = settings.MESSAGE_DELETE_TIME

class RoleManager:

    def __init__(self, client, message):
        self.client = client
        self.message = message
        self.server = message.server

    """ Returns a role object from a given name

        params:
            String name - The name of the role to look up
        returns:
            Role role   - The Role object that was found
            None        - or None if no role was found
    """
    def fetch_role_by_name(self, name):
        role = next((r for r in self.server.roles if r.name == name), None)
        return role

    """ Attempts to attach a role to given user

        params:
            Role role       - The role to be attached
            Member member   - The member to attach the role to

        returns:
            bool            - Whether or not the role was added
    """
    async def give_role(self, role, member):
        # Check if role exists on server
        if role not in self.server.roles:
            return False

        # Check if member already owns role
        if role not in member.roles:
            # If user doesn't own the role yet, give it to them.
            await self.client.add_roles(member, role)
            sent_msg = await self.client.send_message(self.message.channel, "{}: {} MOD-ULE HAS BEEN ADD-ED TO SYS-TEM OPE-RA-TIONS.".format(member.mention, role.name))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return True
        else:
            # If user already owns role, give error and return
            sent_msg = await self.client.send_message(self.message.channel, "{}: ERROR. ERROR. {} MO-DULE DE-TEC-TED DURING SYS-TEM OPE-RA-TIONS CHECK.".format(member.mention, role.name))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return False

    """ Attempts to remove a role from a given user

        params:
            Role role       - The role to be detached
            Member member   - The member to detach the role from

        returns:
            bool            - Whether or not the role was removed
    """
    async def take_role(self, role, member):
        # Check if role exists on server
        if role not in self.server.roles:
            return False

        if role in member.roles:
            # If the user has the role, we can safely remove it
            await self.client.remove_roles(member, role)
            sent_msg = await self.client.send_message(self.message.channel, "{}: {} MOD-ULE HAS BEEN PURGED FROM SYS-TEM OPE-RA-TIONS.".format(member.mention, role.name))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return True
        else:
            # If the user doesn't have the role, it cannot be removed
            sent_msg = await self.client.send_message(self.message.channel, "{}: ERROR. ERROR. {} MOD-ULE NOT DE-TEC-TED DURING SYS-TEM OPE-RA-TIONS CHECK.".format(member.mention, role.name))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return False

    """ Attempt to mass-assign a single role to one or multiple members

        params:
            Role role       - The role to be attached
            Member *member  - A list of Member objects to assign the role to

        returns:
            bool            - Wheter or not the role was attached
        
    """
    async def mass_give_role(self, role, members):
        changed_cnt = 0;
        for member in members:
            if role not in member.roles:
                await self.client.add_roles(member, role)
                changed_cnt += 1

        if changed_cnt == 0:
            sent_msg = await self.client.send_message(self.message.channel,
                "{}: PLEASE STAND BY FOR THE MOD-ULE UP-GRADE PROC-CESS... ERROR. UP-GRADE COMPLETION: 0%... TER-MI-NA-TING UP-GRADE PROC-CESS".format(self.message.author.mention))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return False
        else:
            sent_msg = await self.client.send_message(self.message.channel,
                "{}: PLEASE STAND BY FOR THE MOD-ULE UP-GRADE PROC-CESS... {} TARGET(S) RE-ASSEM-BLED".format(self.message.author.mention, changed_cnt))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return True
            

    """ Attempt to mass-detach a single role from one or multiple members

        params:
            Role role       - The role to detach
            Member members  - A list of Member objects to detach the role from

        returns:
            bool            - Whether or not the role was attached
    """
    async def mass_take_role(self, role, members):
        changed_cnt = 0;
        for member in members:
            if role in member.roles:
                await self.client.remove_roles(member, role)
                changed_cnt += 1

        if changed_cnt == 0:
            sent_msg = await self.client.send_message(self.message.channel,
                "{}: PLEASE STAND BY FOR THE MOD-ULE DOWN-GRADE PROC-CESS... ERROR. DOWN-GRADE COMPLETION: 0%... TER-MI-NA-TING DOWN-GRADE PROC-CESS".format(self.message.author.mention))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return False
        else:
            sent_msg = await self.client.send_message(self.message.channel,
                "{}: PLEASE STAND BY FOR THE MOD-ULE DOWN-GRADE PROC-CESS... {} TARGET(S) RE-ASSEM-BLED".format(self.message.author.mention, changed_cnt))
            await asyncio.sleep(sleep_time)
            await self.client.delete_message(self.message)
            await self.client.delete_message(sent_msg)
            return True

