from world.skills import SKILL_LIST, THE_LADDER

def menunode_start(caller):
	target = caller.ndb.target
	target.ndb.menu_data = {"target": target.get_display_name(caller)}

	text = f"Editing {target.get_display_name(caller)}.\n\nWhat action do you want to put the skill check on?"
	text += "\n\n(Note: Passive checks do not require rolls and automatically check against the skill level. e.g. a passive Physique check to Get a very heavy object)"
	
	options = []
	actions_list = ["View","Get","Open","Use","Enter","Leave"]
	for action in actions_list:
		options.append({"desc": action, "goto": ("menunode_set_skill", { "action": action.lower() })})
		
	options = [
		{"desc": "View (Passive)",  "goto": ("menunode_set_skill", { "action": "view", "passive": True })},
		{"desc": "Get",             "goto": ("menunode_set_skill", { "action": "get" })},
		{"desc": "Get (Passive)",   "goto": ("menunode_set_skill", { "action": "get", "passive": True })},
		{"desc": "Open",            "goto": ("menunode_set_skill", { "action": "open" })},
		{"desc": "Use",             "goto": ("menunode_set_skill", { "action": "use" })},
		{"desc": "Enter",           "goto": ("menunode_set_skill", { "action": "enter" })},
		{"desc": "Enter (Passive)", "goto": ("menunode_set_skill", { "action": "enter", "passive": True })},
		{"desc": "Leave",           "goto": ("menunode_set_skill", { "action": "leave" })},
		{"desc": "Leave (Passive)", "goto": ("menunode_set_skill", { "action": "leave", "passive": True })},
	]

	return text, options


def menunode_set_skill(caller, raw_string, action, passive=False, **kwargs):
	target = caller.ndb.target
	target.ndb.menu_data["action"] = action
	target.ndb.menu_data["passive"] = passive

	text = "Which skill is required to {action} {target}?".format(**target.ndb.menu_data)

	options = []
	for skill in SKILL_LIST:
		options.append({"desc": skill, "goto": ("menunode_set_level", { "skill": skill, })})
	
	return text, options


def menunode_set_level(caller, raw_string, skill, **kwargs):
	target = caller.ndb.target
	target.ndb.menu_data["skill"] = skill

	text = "How difficult is the {skill} check to {action} {target}?".format(**target.ndb.menu_data)

	options = []
	max_skill = list(THE_LADDER.keys())[-1]
	for level in range(max_skill+1):
		options.append({"key": str(level), "desc": THE_LADDER[level], "goto": (_permanence_check, { "level": level })})
	
	return text, options


def _permanence_check(caller, raw_string, level, **kwargs):
	target = caller.ndb.target
	target.ndb.menu_data["level"] = level

	if target.ndb.menu_data['passive']:
		# passives don't ever clear on success
		return (_desc_check, { "oneshot": oneshot })

	action = target.ndb.menu_data["action"]

	if check := target.attributes.get(f"{action}_check"):
		if oneshot := check.get("oneshot"):
			return (_desc_check, { "oneshot": oneshot })

	return "menunode_permanence"


def menunode_permanence(caller, raw_string, level, **kwargs):
	target = caller.ndb.target


	text = "Should the check to {action} {target} be removed after success?".format(**target.ndb.menu_data)

	options = [
		{"desc": "Yes", "goto": (_desc_check, { "oneshot": True })},
		{"desc": "No", "goto": (_desc_check, { "oneshot": False })},
	]
	return text, options


def _desc_check(caller, raw_string, oneshot, **kwargs):
	target = caller.ndb.target
	target.ndb.menu_data["oneshot"] = oneshot
	action = target.ndb.menu_data["action"]
	
	attr_name = f"{action}_passive_check" if target.ndb.menu_data['passive'] else f"{action}_check"

	if check := target.attributes.get(attr_name):
		if desc := check.get("desc"):
			return ("menunode_done", { "desc": desc })
	
	return "menunode_set_desc"


def menunode_set_desc(caller, raw_string, **kwargs):
	target = caller.ndb.target
	
	text = "Describe why {target} requires a skill check to {action}.\n\n(e.g. It's locked.)".format(**target.ndb.menu_data)

	options = [{"key": "_default", "goto": "menunode_done"}]
	return text, options


def menunode_done(caller, raw_string, **kwargs):
	target = caller.ndb.target
	data = target.ndb.menu_data
	
	action = data['action']
	skill = data['skill']
	level = data['level']
	oneshot = data['oneshot']
	passive = data['passive']

	attr_check = f"{action}_passive_check" if passive else f"{action}_check"

	desc = kwargs.get("desc")
	if not desc:
		desc = raw_string.strip()
	
	if check := target.attributes.get(attr_check):
		if desc:
			check["desc"] = desc
		check["skills"][skill] = level
	else:
		check = {"skills": {}}
		if desc:
			check["desc"] = desc
		check["skills"][skill] = level

	check["oneshot"] = oneshot

	# lockstrings are for passive checks only
	if passive:
		if not check.get("lock"):
			# back up the base lock string
			if old_lockstring := target.locks.get(action):
				lockstring = f"{old_lockstring} and skillcheck({attr_check})"
				check["lock"] = old_lockstring
			else:
				lockstring = f"{action}:skillcheck({attr_check})"
			target.locks.add(lockstring)
		
	target.attributes.add(attr_check, check)
	caller.nattributes.remove("target")

	text = f"The {action} action on {target.get_display_name(caller)} will now require {THE_LADDER[level]} {skill}."
	
	return text, None
