"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia.utils import search, create, logger
from evennia.objects.objects import DefaultCharacter
from .objects import ObjectParent

from evennia.contrib.rpg.traits import TraitHandler
from characters.sheet import AspectHandler, StatusHandler, init_skills

class Character(ObjectParent, DefaultCharacter):
	"""
	The Character defaults to reimplementing some of base Object's hook methods with the
	following functionality:

	at_basetype_setup - always assigns the DefaultCmdSet to this object type
					(important!)sets locks so character cannot be picked up
					and its commands only be called by itself, not anyone else.
					(to change things, use at_object_creation() instead).
	at_post_move(source_location) - Launches the "look" command after every move.
	at_post_unpuppet(account) -	when Account disconnects from the Character, we
					store the current location in the pre_logout_location Attribute and
					move it to a None-location so the "unpuppeted" character
					object does not need to stay on grid. Echoes "Account has disconnected"
					to the room.
	at_pre_puppet - Just before Account re-connects, retrieves the character's
					pre_logout_location Attribute and move it back on the grid.
	at_post_puppet - Echoes "AccountName has entered the game" to the room.

	"""

	@property
	def aspects(self):
		"""Stores the character's aspects and refresh."""
		return AspectHandler(self)
	
	@property
	def skills(self):
		"""
		See the Traits contrib for full documentation.
		"""
		return TraitHandler(self, db_attribute_key="skills", db_attribute_category="skills")

	@property
	def status(self):
		"""
		Stores and manages the characters current status: consequences, stress
		"""
		return StatusHandler(self)
	
	def at_object_creation(self):
		"""
		Run once when a Character object is initially created.
		
		This is a useful place to add extra set-up that all Characters need done.
		"""
		super().at_object_creation()


		self.locks.add("getfrom:false();viewcon:true()")
		
		# Add the base skills to the character
		init_skills(self)
	
	def at_post_puppet(self, **kwargs):
		if not self.ndb.group:
			# Add a starting solo group
			free = search.search_tag("empty", "group")
			if len(free) > 0:
				# there are available group scripts, use one
				new_group = free[0]
				new_group.tags.remove("empty", "group")
			else:
				# create a new group script
				new_group = create.script(typeclass="groups.script.GroupScript")

			success = new_group.add(self)

		super().at_post_puppet(**kwargs)