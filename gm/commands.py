from evennia import CmdSet
from evennia.utils.evmenu import EvMenu
from commands.command import Command
from world.skills import SKILL_LIST, THE_LADDER

# Helper functions
def roll():
	roll_list = [randint(-1,1) for i in range(4)]
	strings = []
	for result in roll_list:
		if result == -1:
			strings.append('[|r-|n]')
		elif result == 0:
			strings.append('[ ]')
		elif result == 1:
			strings.append('[|g+|n]')
		
	return (" ".join(strings), sum(roll_list))

def desc(value):
		highest = ""
		for bound, txt in THE_LADDER.items():
			highest = txt
			if value <= bound:
				return txt
		return highest


class CmdSetSkillcheck(Command):
	"""
	Open a menu for defining a skill check requirement to
	interact with an object in some way.
	
	Usage:
	  skillcheck <target>
	
	Example:
	"""
	key = "skillcheck"
	#aliases = None
	locks = "cmd:perm(Builder)"
	
	def func(self):
		caller = self.caller

		if not self.args:
			caller.msg("Usage: skillcheck <target>")
			return
		
		target = caller.search(self.args)
		if not target:
			caller.msg(f"Can't set a check on {self.args}.")
			return

		caller.ndb.target = target
		EvMenu(caller, 'gm.check_menu', startnode="menunode_start", cmd_on_exit=None)


class FateGMCmdSet(CmdSet):
	"""
	Collect all of the Fate character commands in one place,
	to add to the default command set.
	"""
	def at_cmdset_creation(self):
		self.add(CmdSetSkillcheck())
