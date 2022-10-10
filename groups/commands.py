from evennia import CmdSet

from commands.command import Command


class CmdVoteYesNo(Command):
	key="vote"
	aliases=("yes","y","no","n")
	locks = "cmd:perm(Player)"

	def func(self):
		caller = self.caller
		group = caller.ndb.group
		
		# can't vote if not in a group
		if not group:
			return
		
		vote = self.cmdstring.split()
		if vote == "vote":
			vote = vote.split(maxsplit=1)[1]
		
		if vote in ("yes","y"):
			vote = True
		elif vote in ("no", "n"):
			vote = False

		voted = group.vote(caller, vote)

		if not voted:
			# fall back to "command not found" class, later
			caller.msg("Nothing happens.")
			return

		

class GroupCmdSet(CmdSet):
	key = "GroupCmdSet"


	def at_cmdset_creation(self):
		super().at_cmdset_creation()
		
		self.add(CmdVoteYesNo())