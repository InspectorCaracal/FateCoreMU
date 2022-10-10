from random import randint
from evennia import CmdSet
from commands.command import Command
from world.skills import SKILL_LIST, THE_LADDER

from .sheet import CmdCharSheet
from .creation import CmdSetAspect

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


# Callbacks

def aspect_reroll(caller, aspect):
	if check := caller.db.current_roll:
		skill, _ = check
		message = [f"You invoke |w{aspect}|n for a reroll."]
		skill_mod = caller.skills[skill.lower()].value
		result_str, result_int = roll()
		result = int(result_int + skill_mod)
		caller.db.current_roll = (skill, result)
		message.append(result_str)
		level = desc(result)
		message.append(f"Your new {skill} check is {level}.")

		caller.msg("\n".join(message))
		caller.location.msg_contents(f"{caller}'s new {skill} check is {level}.", exclude=caller)

	else:
		caller.msg("You don't have a recent check to reroll.")



def aspect_bonus(caller, aspect):
	if check := caller.db.current_roll:
		skill, result = check
		message = [f"You invoke |w{aspect}|n for a +2 bonus."]
		result += 2
		caller.db.current_roll = (skill, result)
		level = desc(result)
		message.append(f"Your new {skill} check is {level}.")

		caller.msg("\n".join(message))
		caller.location.msg_contents(f"{caller}'s new {skill} check is {level}.", exclude=caller)

	else:
		caller.msg("You don't have a recent check to reroll.")

def aspect_assist(caller, aspect, target):
	if check := caller.db.current_roll:
		skill, result = check
	# finish this


# Main commands

class CmdSkillRoll(Command):
	key = "roll"
	aliases = (key.lower() for key in SKILL_LIST)
	locks = "cmd:perm(Player) and not attr(current_roll)"
	auto_help = False
	
	def func(self):
		caller = self.caller
		skill = self.cmdstring

		result_str, result_int = roll()
		message = [f"{result_str}"]
		emote = None
		
		if skill == "roll":
			# just roll 4 fudge dice
			message.append(f"You rolled {result_int}.")

		else:
			if not hasattr(caller, "skills"):
				caller.msg("You can't do that.")
				return

			# target validation here
			args = self.args.strip()
			if any([args.startswith(prep) for prep in ["on ","at ","to "]]):
				_, args = args.split(maxsplit=1)
			
			argslist = args.split(maxsplit=1)
			if len(argslist) > 1:
				# syntax is good
				action = argslist[0].lower()
				target = " ".join(argslist[1:])
			else:
				caller.msg(f"You need to have an action and a target. e.g. {skill} to |wget box|n")
				return

			target = caller.search(target)
			if not target:
				return

			skill_name = caller.skills[skill].name

			if target_checks := target.attributes.get(f"{action}_check"):
				# this object has DCs for this action
				skill_reqs = target_checks.get("skills",[])
				if skill_name not in skill_reqs:
					caller.msg(f"You can't use {skill_name} to {action} the {target.name}")
					caller.location.msg_contents(f"{caller} can't {action} the {target.name} with {skill_name}.", exclude=caller)
					return
				# caller is using a valid skill! let's go!
				caller.db.current_check = {"action": action, "skill": skill, "level": skill_reqs[skill_name], "target": target}
			
			else:
				# there is no DC for this action
				caller.msg(f"You don't need a skill check to {action} the {target.name}.")
				return
		
			skill_mod = caller.skills[skill].value
			result = int(result_int + skill_mod)

			level = desc(result)
			message.append(f"Your {skill} check is {level}.")
			emote = f"{caller} rolls a {level} {skill} check."
			caller.db.current_roll = (skill, result)

		caller.msg("\n".join(message))
		if emote:
			caller.location.msg_contents(emote,exclude=caller)

class CmdInvoke(Command):
	"""
	Invoke an Aspect to gain a bonus.
	
	You can invoke an aspect for one of four different effects:
	  * +2 to your last skill check
		* Reroll your last skill check
		* +2 to another player's last skill check
		* +2 to passively oppose (not implemented)
	"""
	key = "invoke"
	#aliases = None
	locks = "cmd:perm(Player)"
	
	def func(self):
		caller = self.caller
		if not hasattr(caller,"aspects"):
			caller.msg("You cannot invoke anything.")
			return

		aspect, effect = self.args.strip().rsplit(" for ",1)
		aspect_list = caller.aspects.get(aspect)
		if len(aspect_list) <= 0:
			caller.msg("No aspects matching that text.")
		if len(aspect_list) > 1:
			caller.msg("Multimatch here later.")
		aspect = aspect_list[0][1]

		if effect == "reroll":
			if check := caller.db.current_roll:
				skill, result = check
				action = (aspect_reroll, {"aspect": aspect})
				caller.ndb.group.poll(caller, action, f"invoke |w{aspect}|n to reroll {skill}")
			else:
				caller.msg("You don't have any check to add a bonus to.")
			
		elif effect == "bonus":
			if check := caller.db.current_roll:
				skill, result = check
				action = (aspect_bonus, {"aspect": aspect})
				caller.ndb.group.poll(caller, action, f"invoke |w{aspect}|n for a +2 bonus on {skill}")
				
			else:
				caller.msg("You don't have any check to add a bonus to.")
		
		else:
			target = caller.search(effect)
			if not target:
				caller.msg("You cannot assist that.")
				return
			if not hasattr(target,"skills"):
				caller.msg("You cannot assist that.")
				return
			
			if check := caller.db.current_roll:
				skill, result = check
				result += 2
				message = [f"Your new {skill} check is {desc(result)}."]
				
			else:
				caller.msg(f"{target} doesn't have any check to add a bonus to.")
			
#		caller.msg("\n".join(message))


class CmdCommitSkill(Command):
	key = "done"
	locks = "cmd:perm(Player) and attr(current_roll)"
	
	def func(self):
		caller = self.caller

		check_dict = caller.db.current_check
		skill, result = caller.db.current_roll

		success = result - check_dict["level"]

		# this will eventually check success/failure effects

		if success >= 3:
			# success with style
			message = yield("You succeed with style! Describe how that looks:")
			caller.location.msg_contents(message)
			self.do_cmd(caller, check_dict["action"], target=check_dict["target"], bonus=True)

		elif success > 0:
			# normal success
			message = yield("You succeed. Describe how that looks:")
			caller.location.msg_contents(message)
			self.do_cmd(caller, check_dict["action"], target=check_dict["target"], bonus=None)

		elif success == 0:
			# success at a cost
			message = yield("You succeed, but at a cost. Describe how that looks:")
			caller.location.msg_contents(message)
			self.do_cmd(caller, check_dict["action"], target=check_dict["target"], bonus=False)

		else:
			# fail
			# later, this will instead check the target object for what to do on fail
			# possibilities: nothing happens, the command passes but at a serious cost, or something goes wrong
			caller.location.msg_contents(f"{caller.name} failed the check.")

		caller.attributes.remove("current_roll")
		caller.attributes.remove("current_check")

	def do_cmd(self, caller, action, target, bonus):
		"""
		Actually execute the command and do any necessary cleanup.
		"""
		target_checks = target.attributes.get(f"{action}_check")
		caller.execute_cmd(action, passed=True, target=check_dict["target"], bonus=bonus)

		if target_checks.get("oneshot",False):
			target.attributes.remove(f"{action}_check")


class FateCharCmdSet(CmdSet):
	"""
	Collect all of the Fate character commands in one place,
	to add to the default command set.
	"""
	def at_cmdset_creation(self):
		self.add(CmdCharSheet())
		self.add(CmdSetAspect())
		self.add(CmdSkillRoll())
		self.add(CmdInvoke())
		self.add(CmdCommitSkill())
