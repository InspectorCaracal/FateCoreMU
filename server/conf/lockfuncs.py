"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

def skillcheck(accessing_obj, accessed_obj, action_type, *args, **kwargs):
	"""
	Checks that the accessing object passes the required skill
	check on the accessed object.
	
	Use only for passive checks.
	"""
	if not hasattr(accessing_obj, "skills"):
		# accessing obj isn't part of the skill system at all
		return True

	if skill_check := accessed_obj.attributes.get(action_type):
		# the check data is available
		if skills := skill_check.get("skills"):
			for skill, level in skills.items():
				if accessing_obj.skills[skill.lower()].value >= level:
					# pass the passive check
					return True
			# the loop is through and no skills passed
			return False
		else:
			# for some reason no skills were set
			return True
	
	else:
		# there's no DC to check against, automatically pass
		return True
