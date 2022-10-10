"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""
from evennia.utils import list_to_string
from evennia.objects.objects import DefaultObject
from world.skills import THE_LADDER

class ObjectParent:
	"""
	Sets and overrides various pre-check hooks to enable skill check requirements.
	"""
	def at_pre_get(self, doer, **kwargs):
		if kwargs.get("passed",False):
			# the skill check was already completed
			return True

		if skillcheck := self.attributes.get("get_check"):
			message = []
			if desc := skillcheck.get("desc"):
				message.append(desc)
			skills = [f"{THE_LADDER[level]} {skill}" for skill, level in skillcheck.get("skills",{}).items()]
			message.append(f"Getting this requires {list_to_string(skills, endsep=' or ')}.")
			doer.msg("\n".join(message))
			return False
		else:
			return True
		
	def at_pre_open(self, doer, **kwargs):
		if not hasattr(self, "at_open") or not callable(self.at_open):
			# this object can't actually be opened
			doer.msg("This can't be opened.")
			return False

		if kwargs.get("passed",False):
			return True
		
		if self.has.tags("open"):
			return True

		if skillcheck := self.attributes.get("open_check"):
			message = []
			if desc := skillcheck.get("desc"):
				message.append(desc)
			skills = [f"{THE_LADDER[level]} {skill}" for skill, level in skillcheck.get("skills",{}).items()]
			message.append(f"Opening this requires {list_to_string(skills, endsep=' or ')}.")
			doer.msg("\n".join(message))
			return False
		else:
			return True
		
	def at_pre_use(self, doer, **kwargs):
		if kwargs.get("passed",False):
			# the skill check was already completed
			return True

		if skillcheck := self.attributes.get("use_check"):
			message = []
			if desc := skillcheck.get("desc"):
				message.append(desc)
			skills = [f"{THE_LADDER[level]} {skill}" for skill, level in skillcheck.get("skills",{}).items()]
			message.append(f"Using this requires {list_to_string(skills, endsep=' or ')}.")
			doer.msg("\n".join(message))
			return False
		else:
			return True

	def at_pre_move(self, destination, **kwargs):
		if kwargs.get("passed",False):
			# the skill check was already completed
			return True

		# check if location requires a skill check to leave
		if skillcheck := self.location.attributes.get("leave_check"):
			message = []
			if desc := skillcheck.get("desc"):
				message.append(desc)
			skills = [f"{THE_LADDER[level]} {skill}" for skill, level in skillcheck.get("skills",{}).items()]
			message.append(f"Leaving here requires {list_to_string(skills, endsep=' or ')}.")
			self.msg("\n".join(message))
			return False

		# check if destination requires a skill check to enter
		elif skillcheck := destination.attributes.get("enter_check"):
			message = []
			if desc := skillcheck.get("desc"):
				message.append(desc)
			skills = [f"{THE_LADDER[level]} {skill}" for skill, level in skillcheck.get("skills",{}).items()]
			message.append(f"Going there requires {list_to_string(skills, endsep=' or ')}.")
			self.msg("\n".join(message))
			return False

		else:
			return True



class Object(ObjectParent, DefaultObject):
	"""
	See Evennia documentation on DefaultObject for more information.
	"""

	def at_object_creation(self):
		"""
		Runs the default creation hook and adds additional locks.
		"""
		super().at_object_creation()
		
		self.locks.add("getfrom:true();viewcon:true()")

	def return_appearance(self, looker, **kwargs):
		"""
		Main callback used by 'look' for the object to describe itself.
		This formats a description. By default, this looks for the `appearance_template`
		string set on this class and populates it with formatting keys
			'name', 'desc', 'exits', 'characters', 'things' as well as
			(currently empty) 'header'/'footer'.

		Args:
			looker (Object): Object doing the looking.
			**kwargs (dict): Arbitrary, optional arguments for users
				overriding the call. This is passed into the helper
				methods and into `get_display_name` calls.

		Returns:
			str: The description of this entity. By default this includes
				the entity's name, description and any contents inside it.

		Notes:
			To simply change the layout of how the object displays itself (like
			adding some line decorations or change colors of different sections),
			you can simply edit `.appearance_template`. You only need to override
			this method (and/or its helpers) if you want to change what is passed
			into the template or want the most control over output.

		"""

		if not looker:
			return ""

		# was this behind a skill check?
		if view_check := self.db.view_check:
			return view_check.get("desc") or "This is hidden."
		
		return super().return_appearance(looker, **kwargs)


	def get_display_name(self, looker=None, **kwargs):
		"""
		Displays the name of the object in a viewer-aware manner.

		Args:
			looker (TypedObject): The object or account that is looking
				at/getting inforamtion for this object.

		Returns:
			name (str): A string containing the name of the object,
				including the DBREF if this user is privileged to control
				said object.

		Notes:
			This function could be extended to change how object names
			appear to users in character, but be wary. This function
			does not change an object's keys or aliases when
			searching, and is expected to produce something useful for
			builders.

		"""
		if looker and self.locks.check_lockstring(looker, "perm(Builder)"):
			name = "{}(#{})".format(self.name, self.id)
		else:
			name = self.name

		# is this behind a skill check?
		if self.db.view_check:
			name = f"{name} (hidden)"
				
		return name
						
	def at_get(self, getter, **kwargs):
		"""
		Called by the default `get` command when this object has been
		picked up.

		Args:
			getter (Object): The object getting this object.
			**kwargs (dict): Arbitrary, optional arguments for users
				overriding the call (unused by default).

		Notes:
			This hook cannot stop the pickup from happening. Use
			permissions or the at_pre_get() hook for that.
		"""
		
		if check := self.db.view_check:
			if lockstring := check.get("lock"):
				self.locks.add(lockstring)
			self.attributes.remove("view_check")

	def at_open(self, doer, **kwargs):
		"""
		Called by the `open` player command after the player successfully
		passes the access checks.
		"""
		if self.tags.has("open"):
			doer.msg("That is already open.")

		elif self.tags.has("locked"):
			if kwargs.get("passed",False):
				self.tags.remove("locked")
			else:
				# this should be handled by skill checks, but just in case you want to require a key
				doer.msg("You can't open that; it's locked.")
				return
		
		if self.tags.has("closed"):
			self.tags.remove("closed")
			self.tags.add("open")
			self.locks.add("getfrom:perm(Player)")

			doer.msg(f"You open the {self.name}.")
			doer.location.msg_contents(f"{doer.name} opens the {self.name}.", exclude=caller)
		
		else:
			doer.msg("That isn't closed.")

	def at_close(self, doer, **kwargs):
		"""
		Called by the `open` player command after the player successfully
		passes the access checks.
		"""
		if self.tags.has("closed"):
			doer.msg("That is already closed.")

		if self.tags.has("open"):
			self.tags.remove("open")
			self.tags.add("closed")
			self.locks.add("getfrom:false()")

			doer.msg(f"You close the {self.name}.")
			doer.location.msg_contents(f"{doer.name} closes the {self.name}.", exclude=caller)
		
		else:
			doer.msg("That isn't open.")