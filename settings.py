BOT_VERSION = "1.4-abandonware"  # Version of this bot

# These roles can be self-set by the user
SELF_ROLES = {
	"na": "NA",
	"eu": "EU"
}

# These roles can only be set by GM's and WP
MOD_ROLES = {
	"na": "NA",
	"eu": "EU",
    "event": "Event Helper",
    "helper": "Event Helper",
    "eventhelper": "Event Helper",
    "events": "Event Helper"
}

# The ranks that are allowed to do the following:
# 	Mass assign ranks
# 	Mass revoke ranks
# 	List voice activity giveaway entries in chat
# 	Draw voice activity giveaway winner
# 	Request DM with a list of voice activity entries
# 	Revoke access to the bugreport feature
# 	Restore access to the bugreport feature
#       Handle the weekly message content modules
PERMITTED_RANKS = [
	"Potato",
	"Games Master"
]

PERMITTED_BUILDERS = [
        "Event Helper"
]

# Time in seconds until both command message and response are deleted from chat
MESSAGE_DELETE_TIME = 6

# Take a voice snapshot after these amount of minutes
TIME_BETWEEN_SNAPSHOTS = 15

# The Discord ID's of the developer(s) bugreports from .bug should be send to
REPORT_TO_DEVS = [
	'[REDACTED]',
]

# REPLACE WITH [REDACTED] ID WHEN LIVE: '[REDACTED]'
# This person will get a message saying who won the giveaway,
# so they can hand out the prize. Should be [REDACTED] ID.
PRIZE_HANDOUT_NOTIFY = '[REDACTED]'

# Amount of minutes that should pass between bot reminders about voice activity
# In this case: 60 minutes * 8 = 8 hours
TIME_BETWEEN_VOICE_REMINDERS = 60*6

# On live, change with [REDACTED]
STUFF_HAPPENING_ID = '[REDACTED]'


EVENT_PING_MESSAGE = "@everyone Here are the scheduled events for the upcoming week!"
EVENT_DIVIDER_IMAGE = '[REDACTED]'
