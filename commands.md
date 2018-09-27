**Here is an overview of the commands**
Public note: the bot only listens to commands from a channel, not DM's.

**Everyone**
*Self-assignable roles*:
.iam eu/na
	Sets the EU/NA role on yourself. Used by GM's for regional event pings
.iamnot eu/na
	Removes the EU/NA role from yourself
.iamn eu/na
	Shorthand version

*General info*:
.copyright
	Sends a copyright notice over DM as per Anet Terms and Service
.commands
	Sends this list of commands.
.bug bug report
	The bot will send a DM to the developers containing your bug report. Abuse of this feature gets you on the blacklist 

**Developers and Admins**
.denyreporting @mention
	Denies access to the bugreporting feature
.allowreporting @mention
	Restores access to the bugreporting feature
.stats
	Sends a DM with bot info, including region distributions and giveaway statistics

**Admin only**
*Giveaways*:
.draw
	Draws a lottery winner for the end-of-month giveaway and resets winners tickets.
.draw --preserve
	Draws a lottery winner, but preserves the winners tickets
.reset
	Resets all giveaway tickets to 0.
.entries
	Prints a list of all giveaway tickets to chat
.dmentries
	Sends a list of all giveaway tickets over DM

*Role management*:
.giverole role @mention @mention
	Mass-assigns a role to given member(s)
.takerole role @mention @mention
	Mass-revoke a role from the given member(s)

*Stuff Happening*:
Note: The weekly message is wiped and rebuild automatically once a week.
.build
	Force a purge and repost of the weekly message. Can be used when the teamup calendar recieved a time change
	Note: does not re-ping users
.modules
	Sends a DM with all the token descriptors in the giveaway message
.addmodule token | position | image link | content
	Adds a content module to the weekly giveaway message with a given token descriptor
.delmodule token
	Deletes a content module from the weekly giveaway message based on the token descriptor
