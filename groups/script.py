from evennia import DefaultScript
from evennia.utils import search, create
from evennia.typeclasses.attributes import AttributeProperty
from .commands import GroupCmdSet

class GroupScript(DefaultScript):
	"""
	Global script that manages the members of a group.
	"""
	# mutable AttrProps have issues, so the default empty list is set in creation
	members = AttributeProperty(default=[])
	
	def at_server_start(self):
		"""
		Reloads party membership status on initialization.
		"""
		for player in self.members:
			player.ndb.group = self
			player.cmdset.add(GroupCmdSet)

	def at_script_creation(self):
		# workaround for the mutable AttrProp issue
		self.members = []
		self.at_server_start()

	def add(self, player):
		"""
		Add a new member to the group.
		
		Returns True if player was successfully added or already in the
		group, otherwise False
		"""
		if player in self.members:
			return True
		
		# only active players can be added
		if not player.has_account:
			return False
		
		if player.ndb.group:
			if not player.ndb.group.remove(player):
				return False
		self.members.append(player)
		player.ndb.group = self
		player.cmdset.add(GroupCmdSet)

	def remove(self, player):
		"""
		Remove an existing member to the group.
		
		Returns True if player was successfully removed or not in the
		group, otherwise False
		"""
		if player not in self.members:
			return True

		self.members.remove(player)
		player.ndb.group = None
		player.cmdset.remove(GroupCmdSet)

		if len(self.members) <= 0:
			self.tags.add("empty", category="group")
		
		return True

	def split(self, players):
		"""
		Split one or more players out of the party into a new one.
		
		Returns False if the players could not be split out, otherwise True
		"""
		invalid = [player for player in players if player not in self.members]
		if len(invalid) > 0:
			return False

		if len(players) <= 0 or len(players) == self.members:
			return True
		
		free = search.search_tag("empty", "group")
		if len(free) > 0:
			# there are available group scripts, use one
			new_group = free[0]
			new_group.tags.remove("empty", "group")
		else:
			# create a new group script
			new_group = create.script(typeclass=GroupScript)

		# move the listed players into the new group
		new_group.members = players
		# filter the listed players out of our group members 
		self.members = [player for player in self.members if player not in players]
		# change group assignment for listed players
		for player in new_group.members:
			player.ndb.group = new_group
		
		return True
	
	def poll(self, pollee, action, query):
		"""
		Poll all active (online) players for approval.
		
		Args:
		  pollee (obj)  : the player character triggering the vote
		  action (tuple): a tuple storing the action being voted on
		  query (str)   : a string describing what the player is trying to do

		Returns:
			False if poll could not be run, otherwise True
		"""
		# poll can't be triggered by someone outside the group
		if pollee not in self.members:
			return False
		
		# can't start a new poll if one is already active
		if self.ndb.poll:
			return False

		self.ndb.voters = {player: 0 for player in self.members if player.has_account}
		self.ndb.poll = (pollee, query, action)
		poll_msg = f"{pollee} wants to {query}.\nDo you approve?"

		count = [voter.msg(poll_msg) for voter in self.ndb.voters if voter is not pollee]
		if len(count) > 0:
			pollee.msg(f"You attempt to {query}.")
		# poll-caller always automatically votes Yes
		self.vote(pollee, True, quiet=True)



	def vote(self, voter, value, quiet=False):
		"""
		Record a player's vote and check if all players have voted
		"""
		# can only vote if there's an active poll
		if not self.ndb.poll:
			return False
		
		# can't add new voters after the poll is called
		if voter not in self.ndb.voters:
			return False
		
		if value:
			self.ndb.voters[voter] = 1
		else:
			self.ndb.voters[voter] = -1
		
		self.check_votes(quiet=quiet)
		return True

	def check_votes(self, quiet=False):
		if not self.ndb.voters:
			# there's no vote happening
			return

		no_votes = [player for player, vote in self.ndb.voters.items() if not vote]
		voters = self.ndb.voters.keys()
		
		remaining = len(no_votes)
		if remaining > 0:
			# there are still group members who haven't voted
			if not quiet:
				total = len(voters)
				message = f"{total-remaining}/{total} votes tallied."
				for voter in voters:
					voter.msg(message)

		else:
			# all members have voted
			pollee, query, action = self.ndb.poll
			tally = sum(self.ndb.voters.values())
			if tally > 0:
				# vote is Yes
				approve = True
				message = f"Vote tallied: {pollee} can {query}."
			elif tally < 0:
				# vote is No
				approve = False
				message = f"Vote tallied: {pollee} cannot {query}."
			else:
				# vote is a tie!
				# tiebreaker coin flip
				approve, coin = (True, "Heads") if randint(0,1) else (False, "Tails")
				message = f"The vote for {pollee} to {query} is tied. Heads for Yes, Tails for No.\nThe coin flip says: {coin}."

			if not quiet:
				for voter in voters:
					voter.msg(message)

			if approve:
				# complete the pending action
				callable, kwargs = action
				callable(pollee, **kwargs)

			self.nattributes.remove("poll")
			self.nattributes.remove("voters")
			
