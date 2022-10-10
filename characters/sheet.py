from evennia.utils import list_to_string
from evennia.contrib.rpg.traits import StaticTrait, TraitException

from world.skills import SKILL_LIST, THE_LADDER

def init_skills(obj):
	"""
	Initialize all of the skills for the game on a character.
	"""
	for skill, actions in SKILL_LIST.items():
		obj.skills.add(skill.lower(), skill, descs=THE_LADDER, trait_type="skill", actions=actions)

class SkillTrait(StaticTrait):
	"""
	A child class of static traits that adds in the level
	description functionality of counter traits.
	"""
	trait_type = "skill"

	default_keys = {
		"base": 0,
		"mod": 0,
		"mult": 1.0,
		"descs": None,
	}

	@staticmethod
	def validate_input(cls, trait_data):
		"""Add extra validation for descs"""
		trait_data = super().validate_input(cls, trait_data)
		# validate descs
		descs = trait_data["descs"]
		if isinstance(descs, dict):
			if any(
				not (isinstance(key, (int, float)) and isinstance(value, str))
				for key, value in descs.items()
			):
				raise TraitException(
					f"Trait descs must be defined on the "
					f"form {{number:str}} (instead found {descs})."
				)
		return trait_data

	def desc(self):
		"""
		Retrieve descriptions of the current value, if available.
		This must be a mapping {upper_bound_inclusive: text},
		ordered from small to big. Any value above the highest
		upper bound will be included as being in the highest bound.
		rely on Python3.7+ dicts retaining ordering to let this
		describe the interval.
		Returns:
			str: The description describing the `value` value.
				If not found, returns the empty string.
		"""
		descs = self._data["descs"]
		if descs is None:
			return ""
		value = self.value
		# we rely on Python3.7+ dicts retaining ordering
		highest = ""
		for bound, txt in descs.items():
			highest = txt
			if value <= bound:
				return txt
		# if we get here we are above the highest bound so
		# we return the latest bound specified.
		return highest


class AspectHandler:
	def __init__(self, obj):
		"""
		Load the handled aspect data into the handler.
		"""
		self.obj = obj
		data = obj.attributes.get("_aspects")
		if not data:
			data = {"refresh": 3, "aspects": {}}
			obj.attributes.add("_aspects",data)

		self.refresh = data["refresh"]
		self.aspects = dict(data["aspects"])
	
	def add(self, slot, text):
		# high concept and trouble.
		# three other aspects
		# should probably do some validation or something here
		self.aspects[slot] = text
		self.obj.db._aspects["aspects"] = self.aspects
	
	def get(self, text):
		"""
		Get all aspects which contain a substring `text`
		
		Returns a list of tuples containing the aspect slot and
		aspect text.
		"""
		text = text.lower()
		result = [(key, value) for key, value in self.aspects.items() if text in value.lower()]
		return result

#	def __getattr__(self, attr):
#		if attr == "refresh":
#			return self.refresh
#		else:
#			return self.aspects.get(attr)


class StatusHandler:
	pass




from commands.command import Command

class CmdCharSheet(Command):
	"""
	Print out your character's sheet.
	
	Usage:
	  sheet
	"""

	key = "sheet"
	aliases = ("stats",)
	locks = "cmd:perm(Player)"

	def func(self):
		if hasattr(self.caller, "skills"):
			skills = [self.caller.skills.get(key) for key in self.caller.skills.all]
			skill_strs = [f"{skill.name}: {skill.desc()}" for skill in skills]
			skills = "\n ".join(skill_strs)
			self.caller.msg(f"Skills:\n {skills}\n")
		else:
			self.caller.msg("You have no skills.\n")

		if hasattr(self.caller, "aspects"):
			aspects = [value for key, value in self.caller.aspects.aspects.items()]
			self.caller.msg(f"Aspects: {list_to_string(aspects)}\n")
		else:
			self.caller.msg("You have no aspects.\n")
