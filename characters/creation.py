
from commands.command import Command

class CmdSetAspect(Command):
	"""
	Set a new aspect on your character.
	
	Usage:
	  aspect <slot> <aspect text>
	
	Example:
		aspect concept Wizard for Hire
		aspect 3 There Can Only Be One
	"""
	key = "aspect"
	aliases = ("setaspect",)
	locks = "cmd:perm(Player)"

	def func(self):
		if not hasattr(self.caller, "aspects"):
			self.caller.msg("You cannot have aspects.")
			return
		
		args = self.args.strip().split(' ',maxsplit=1)
		
		if len(args) <= 1:
			self.caller.msg("Usage: aspect <slot> <aspect text>")
			return
		
		self.caller.aspects.add(*args)
		self.caller.msg(f"Added aspect \"{args[1]}\" in slot {args[0]}.")
