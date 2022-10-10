# FATE CORE EVENNIA

## Character Sheet

### Skills
This translates very tidily over, using the Traits contrib would be painless.

### Stunts
You can choose from a fixed list of Stunts for each Skill that you have learned, with the same cap on how many you get as usual. And then they're just used as a special action like you'd expect, with hard-coded situation restrictions.

### Aspects
Slightly structured Free Text, or unstructured? I can't think of a kind of structure to implement. However, they can't be changed once set except by a GM or reaching the appropriate milestone.

### Consequences
These should be automatically applied and also automatically rewritten on recovery.

## Aspects

### Game Aspects
These are region-wide or game-wide aspects which the game creators set. *Anyone* can invoke them, the same as invoking your own character aspects.

### Character Aspects
These are free text character attributes.

### Situational Aspects
These are either hard coded or procgen for encounters, or they're added with the *Create An Advantage* action.

### Boosts
Identical to Situational Aspects, mechanically, but they're single-use and always caused by player or NPC actions.


## Groups
This is the actual core unit of gameplay - a _group_ which consists of one or more characters. A solo-player group is viable.

### Aspect Vote
When a player wants to use an aspect on a skill check, it prompts a vote for anyone else in the group. The calling player is automatically counted as one Yes vote.

The command to trigger an aspect has to handle the following information:
* Which Aspect is being triggered
* Which Effect is being desired
* (Optional) How the Aspect applies to the situation

It might need to be tied directly into the skill use command.

NOTE: This should be the same basic functionality for invoking an aspect to _gain_ a fate point as _spending_ one, but instead of a bonus or advantage, you forfeit the check.

## Action!

### Skill Checks
These should be mechanically simple to implement - the only tricky part is designing the situations, which is a "builder" job not a framework task.

### Teamwork
The core _group_ concept means this is integral! Skill checks get claimed by a single player in the group (vote mechanic) and then the other players can either assist or pass, assuming they aren't doing another skill check themselves (such as in a Challenge).

As such, the character needs to have an active task status, as well as the group manager itself recognizing which characters to poll for assistance on skill checks.

> The benefit you can get from teamwork caps at your skill rating. After that, you’re not really able to utilize the additional help. So you can get the benefit of four people helping you if you have a skill at Great (+4), just one person if your skill is Average (+1), and can’t really get help if you have Mediocre (+0).

### Challenges
Basically a complex version of a simple skill check: tying multiple checks into one goal, with different fail states for different combinations of success/fail rolls.

### Contest
This is sort of the "playing alone together" version of PvP? Multiple characters taking turns rolling skill checks until one of them achieves their goal, thus making the other character's goal impossible to achieve.

### Conflicts
Combat will generally fall into this category. This is the most potentially time-consuming mechanic in terms of gameplay, so it needs to be developed to run very smoothly.

- Turn-based. No twitch combat here.
	- In a physical conflict, compare your Notice skill to the other participants. In a mental conflict, compare your Empathy skill. If there’s a tie, compare a secondary or tertiary skill. For physical conflicts, that’s Athletics, then Physique. For mental conflicts, Rapport, then Will.
	- NPCs can be slotted in individually since they're run by a computer. Make good use of implementing mobs (as in groups, not mobiles): https://fate-srd.com/fate-core/creating-and-playing-opposition#mobs
- The Group will _always_ be one side. If players want to fight each other, they need to split into separate groups.
	- NPCs should dynamically group

#### Getting Hit
When an opponent lands a hit on a PC, the player gets a quick option menu for what to do about it: check an available valid Stress box, take one or more Consequences to mitigate it and check a lower Stress box, take only Consequences, or concede. The only options are the ones that are still available to that character and will fully mitigate the hit.

There's no "taken out" option - that's the result if you have no options available.

Taking a Consequence has pre-determined Consequences for each tier level associated with different types of attacks, so you wouldn't write it in yourself.

#### Losing
How should concession be implemented? The idea is usually "maintain control over your character" - perhaps a set of surrender options baked into a conflict type?

## Progression

Fate progression is based on story arcs - this game should work the same. The game dev/GM can design "quests" which act as the different scales of milestones, and completing one of those "quests" triggers the milestone rewards.

Skill progression should possibly be even more limited, to prevent the "newcomers lag behind" issue that Fate as a TTRPG wouldn't have but MMOs are prone to.
