import inflect

from evennia import CmdSet
from evennia.utils import list_to_string
from evennia.commands.default.muxcommand import MuxCommand

_INFLECT = inflect.engine()

# Custom Look command expanding the look syntax to view objects contained
# within other objects. Supports Room details, as well
class CmdLook(MuxCommand):
	"""
	look

	Usage:
	  look
	  look <obj>
		look in <obj>
		look <container>'s <obj>
		look <obj> in <container>

	Observes your location, details at your location or objects in your vicinity.
	"""
	key = "look"
	aliases = ["l", "look at"]
	locks = "cmd:all()"
	arg_regex = r"\s|$"
	rhs_split = (" in ", " on ") 

	def func(self):
		"""
		Handle the looking
		"""
		caller = self.caller
		location = caller.location

		if not self.args:
			target = location
			if not target:
				caller.msg("You have no location to look at.")
				return
			self.msg((caller.at_look(target), {"type": "look"}), options=None)
			return

		# parse for possessive 's
		if not self.rhs and ("'s " in self.args):
			# split at the first possessive and swap
			self.rhs, self.lhs = self.args.strip().split("'s ", maxsplit=1)

		# at this point, `lhs` is the target and `rhs` is the container
		holder = None
		target = None
		look_in = False

		# if there's a rhs, get the container and its access
		if self.rhs:
			holder = caller.search(self.rhs)
			# if len(result) == 0:
				# caller.msg("You can't see any |w%s|n." % self.rhs)
				# return
			# elif len(result) > 1:
				# caller.multimatch_msg(self.rhs, result)
				# index = yield("Enter a number (or |wc|n to cancel):")
				# holder = caller.process_multimatch(index, result)
			# else:
				# holder = result[0]
			if not holder:
				caller.msg(f"You don't see any {self.rhs}.")
				return
			if not holder.access(caller, "viewcon") and not holder.access(caller, "getfrom"):
				self.msg("You can't look there.")
				return

		# if there's a lhs, get the target
		if self.lhs:
			candidates = holder.contents if holder else caller.contents + location.contents
			target = caller.search(self.lhs, candidates=candidates)
			# if len(result) == 0:
				# caller.msg("You can't see any |w%s|n." % self.lhs)
				# return
			# elif len(result) > 1:
				# caller.multimatch_msg(self.lhs, result)
				# index = yield("Enter a number (or |wc|n to cancel):")
				# target = caller.process_multimatch(index, result)
			# else:
				# target = result[0]
			if not target:
				caller.msg(f"You don't see any {self.lhs}.")
				return

		# at this point, all needed objects have been found
		# if "target" isn't specified, the container IS the target
		if holder and not target:
			look_in = True
			target = holder
		
		self.msg((caller.at_look(target, look_in=look_in), {"type": "look"}), options=None)

# Custom Get command allowing you to get objects from within other objects.
class CmdGet(MuxCommand):
	"""
	pick up something

	Usage:
	    get <obj>
	    get <obj> from <obj>

	Picks up an object from your location or another object you have permission
	to get (or get from) and puts it in your inventory.
	"""

	key = "get"
	aliases = "grab"
	locks = "cmd:all()"
	arg_regex = r"\s|$"
	rhs_split = (" from ",) 

	def func(self):
		caller = self.caller

		passed = False
		bonus = None
		holder = None
			

		if hasattr(self,"passed"):
			# this has already passed a skill check
			passed = self.passed
			obj = self.target
			bonus = self.bonus if hasattr(self,"bonus") else None

		else:
			if not self.args or not self.lhs:
				caller.msg("Get what?")
				return

			if self.rhs:
				holder = caller.search(self.rhs)
				# if len(result) == 0:
					# caller.msg("You can't see any |w%s|n." % self.rhs)
					# return
				# elif len(result) > 1:
					# caller.multimatch_msg(self.rhs, result)
					# index = yield("Enter a number (or |wc|n to cancel):")
					# holder = caller.process_multimatch(index, result)
				# else:
					# holder = result[0]
				if not holder:
					caller.msg(f"You don't see any {self.rhs}.")
					return
				if not holder.access(caller, "getfrom"):
					self.msg("You can't get things from there.")
					return

			candidates = holder.contents if holder else caller.contents + caller.location.contents

			# add support for a csl here
			obj = caller.search(self.lhs, candidates=candidates)
			# if len(result) == 0:
				# caller.msg("You can't see any |w%s|n." % self.lhs)
				# return
			# elif len(result) > 1:
				# caller.multimatch_msg(self.lhs, result)
				# index = yield("Enter a number (or |wc|n to cancel):")
				# obj = caller.process_multimatch(index, result)
			# else:
				# obj = result[0]
			if not obj:
				caller.msg(f"You don't see any {self.lhs}.")
				return

			if caller == obj:
				caller.msg("You can't get yourself.")
				return
			if not obj.access(caller, "get"):
				if obj.db.get_err_msg:
					caller.msg(obj.db.get_err_msg)
				else:
					caller.msg("You can't get that.")
				return

		# calling at_before_get hook method
		if not obj.at_pre_get(caller, passed=passed):
#			caller.msg("That can't be picked up.")
			return

		success = obj.move_to(caller, quiet=True)
		if not success:
			if obj.db.get_err_msg:
				caller.msg(obj.db.get_err_msg)
			else:
				caller.msg("That can't be picked up.")
			return

		message = "{player} gets {obj} from {target}." if holder else "{player} picks up {obj}."
		message = message.format(player=caller.name, obj=_INFLECT.an(obj.name), target=_INFLECT.an(holder.name) if holder else "")
		caller.location.msg_contents(message)

		# calling at_get hook method
		obj.at_get(caller, bonus=bonus)


class CmdPut(MuxCommand):
	"""
	put something down

	Usage:
	    put <obj> on <obj>
	    put <obj> in <obj>

	Lets you place an object in your inventory into another object,
	or your current location
	"""

	key = "put"
#	aliases = "place"
	locks = "cmd:all()"
	arg_regex = r"\s|$"

	def func(self):
		"""Implement command"""

		caller = self.caller
		if not self.args:
			caller.msg("Put down what?")
			return

		target = None

		# remember command split syntax
		if " on " in self.args:
			self.lhs, self.rhs = self.args.strip().split(" on ", maxsplit=1)
			syntax = "on"
		elif " in " in self.args:
			self.lhs, self.rhs = self.args.strip().split(" in ", maxsplit=1)
			syntax = "in"
		else:
			# "put" requires two arguments
			caller.msg("Put it where?")
			return

		# add support for a csl here
		obj = caller.search(self.lhs, candidates=caller.contents)
		# if len(result) == 0:
			# caller.msg("You can't see any |w%s|n." % self.lhs)
			# return
		# elif len(result) > 1:
			# caller.multimatch_msg(self.lhs, result)
			# index = yield("Enter a number (or |wc|n to cancel):")
			# obj = caller.process_multimatch(index, result)
		# else:
			# obj = result[0]
		if not obj:
			return

		target = caller.search(self.rhs)
		# if len(result) == 0:
			# caller.msg("You can't see any |w%s|n." % self.lhs)
			# return
		# elif len(result) > 1:
			# caller.multimatch_msg(self.lhs, result)
			# index = yield("Enter a number (or |wc|n to cancel):")
			# target = caller.process_multimatch(index, result)
		# else:
			# target = result[0]
		if not target:
			return
		if not target.access(caller, 'getfrom'):
			caller.msg("You can't put things there.")
			return

		# Call the object script's at_before_drop() method.
		if not obj.at_before_drop(caller):
			caller.msg("You can't put that down.")
			return

		success = obj.move_to(target, quiet=True)

		if not success:
			caller.msg("This couldn't be put down.")
			return

		message = "{player} puts {obj} {on} {target}."
		message = message.format(player=caller.name, obj=_INFLECT.an(obj.name), on=syntax, target=_INFLECT.an(target.name))
		caller.location.msg_contents(message)

		# Call the object script's at_drop() method.
		obj.at_drop(caller)


class CmdGive(MuxCommand):
	"""
	give away something to someone

	Usage:
		give <inventory obj> to <target>

	Gives an items from your inventory to another character,
	placing it in their inventory.
	"""

	key = "give"
	rhs_split = ("=", " to ")  # allow = as a delimiter
	locks = "cmd:all()"
	arg_regex = r"\s|$"

	def func(self):
		"""Implement give"""

		caller = self.caller
		if not self.args:
			caller.msg("Usage: give <inventory object> to <target>")
			return
		to_give = caller.search(
			to_give,
			location=caller,
			nofound_string="You aren't carrying %s." % to_give,
			multimatch_string="You carry more than one %s:" % to_give,
		)
		target = caller.search(target)
		if not (to_give and target):
			return
		if not to_give.location == caller:
			caller.msg("You are not holding %s." % _INFLECT.an(to_give.name))
			return
		if target == caller:
			caller.msg("You keep %s to yourself." % _INFLECT.an(to_give.name))
			return

		# calling at_before_give hook method
		if not to_give.at_before_give(caller, target):
			return
		
		success = to_give.move_to(target, quiet=True)
		if not success:
			caller.msg("This could not be given.")
			return

		# give object, using sdescs
		caller.msg("You give %s to %s." % (_INFLECT.an(to_give.name), target.get_display_name(caller)))
		target.msg("%s gives you %s." % (caller.get_display_name(target), _INFLECT.an(to_give.name)))
		# Call the object script's at_give() method.
		to_give.at_give(caller, target)


class CmdDrop(MuxCommand):
	"""
	drop something

	Usage:
		drop <obj>

	Lets you drop an object from your inventory into the
	location you are currently in.
	"""

	key = "drop"
	locks = "cmd:all()"
	arg_regex = r"\s|$"

	def func(self):
		"""Implement command"""

		caller = self.caller
		if not self.args:
			caller.msg("Drop what?")
			return

		# Because the DROP command by definition looks for items
		# in inventory, call the search function using location = caller
		obj = caller.search(
			self.args,
			location=caller,
			nofound_string="You aren't carrying %s." % self.args,
			multimatch_string="You carry more than one %s:" % self.args,
		)
		if not obj:
			return

		# Call the object script's at_before_drop() method.
		if not obj.at_before_drop(caller):
			return

		success = obj.move_to(caller.location, quiet=True)
		if not success:
			caller.msg("This couldn't be dropped.")
			return
		caller.msg("You drop {}.".format(_INFLECT.an(obj.name)))
		caller.location.msg_contents("{player} drops {obj}".format(player=caller.name, obj=_INFLECT.an(obj.name)))
		# Call the object script's at_drop() method.
		obj.at_drop(caller)


class CmdUse(MuxCommand):
	"""
	use something

	Usage:
		use <obj>
		use <obj> on <target>

	Lets you use a particular item, for whatever its intended purpose is.
	"""

	key = "use"
	locks = "cmd:all()"
	rhs_split = (" on ", "=")
	arg_regex = r"\s|$"

	def func(self):
		"""Implement command"""

		caller = self.caller
		if not self.args:
			caller.msg("Use what?")
			return


		obj = caller.search(self.lhs)
		# if len(result) == 0:
			# caller.msg("You can't see any |w%s|n." % self.lhs)
			# return
		# elif len(result) > 1:
			# caller.multimatch_msg(self.lhs, result)
			# index = yield("Enter a number (or |wc|n to cancel):")
			# obj = caller.process_multimatch(index, result)
		# else:
			# obj = result[0]
		if not obj:
			return

		if self.rhs:
			target = caller.search(self.rhs)
			# if len(result) == 0:
				# caller.msg("You don't see any |w%s|n." % self.rhs)
				# return
			# elif len(result) > 1:
				# caller.multimatch_msg(self.rhs, result)
				# index = yield("Enter a number (or |wc|n to cancel):")
				# target = caller.process_multimatch(index, result)
			# else:
				# target = result[0]
			if not target:
				return
		else:
			target = None

		# Call the object script's at_before_use() method.
		if not obj.at_pre_use(caller):
			return

		try:
			obj.at_use(caller, target=target)
		except AttributeError:
			caller.msg("This is not usable.")
			return

class CmdICOpen(MuxCommand):
	"""
	open something

	Usage:
		open <obj>

	Ppen any openable object.
	"""

	key = "open"
	locks = "cmd:all()"
	arg_regex = r"\s|$"

	def func(self):
		caller = self.caller

		passed = False
		bonus = None

		if hasattr(self,"passed"):
			# this has already passed a skill check
			passed = self.passed
			obj = self.target
			bonus = self.bonus if hasattr(self,"bonus") else None

		else:
			if not self.args:
				caller.msg("Open what?")
				return

			obj = caller.search(self.lhs)
			# if len(result) == 0:
				# caller.msg("You can't see any |w%s|n." % self.lhs)
				# return
			# elif len(result) > 1:
				# caller.multimatch_msg(self.lhs, result)
				# index = yield("Enter a number (or |wc|n to cancel):")
				# obj = caller.process_multimatch(index, result)
			# else:
				# obj = result[0]
			if not obj:
				return

		# Call the object script's at_before_use() method.
		if not obj.at_pre_open(caller,passed=passed):
			return

		obj.at_open(caller, passed=passed, bonus=bonus)


# CmdSet for extended commands

class BasicsCmdSet(CmdSet):
	"""
	Groups the extended basic commands.
	"""

	def at_cmdset_creation(self):
		self.add(CmdLook)
		self.add(CmdGet)
		self.add(CmdPut)
		self.add(CmdDrop)
		self.add(CmdGive)
		self.add(CmdUse)
		self.add(CmdICOpen)
