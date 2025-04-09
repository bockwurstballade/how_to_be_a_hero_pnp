# How To Be A Hero Combat Handler

Welcome to the **How To Be A Hero Combat Handler**! This Python program assists in managing combat scenarios for tabletop role-playing games under the HTBAH rule set. It handles character and team creation, initiative determination, turn-based combat mechanics, and an optional armor degradation feature triggered by critical hits.

[Official How To Be A Hero Ruleset](https://howtobeahero.de/index.php/Kampf)

Supported Modules:
* [Damage Factor](https://howtobeahero.de/index.php/Kampfsystem_Extension_(Neuzeit))
* [Detailed categorization of rolls](https://howtobeahero.de/index.php/Genauere_Einteilung_von_Proben)
* [Unconsciousness](https://howtobeahero.de/index.php/Lebenspunkte/de)
* [Armor](https://howtobeahero.de/index.php/R%C3%BCstung)


---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Running the Program](#running-the-program)
- [Using the Program](#using-the-program)
  - [Team and Character Creation](#team-and-character-creation)
  - [Initiative Phase](#initiative-phase)
  - [Combat Rounds](#combat-rounds)
  - [Ending the Combat](#ending-the-combat)
- [Armor Degradation Feature](#armor-degradation-feature)
- [Contributing](#contributing)

---

## Prerequisites
- **Python 3.x** installed on your system.
- Basic understanding of command-line interfaces.

---

## Running the Program
To start the program, navigate to the directory containing the script and run:

```bash
python3 how_to_be_a_hero_fight.py [options]
```

**Available Options**

* -i <input_file>: Load teams from a JSON file.
* -o <output_file>: Save teams to a JSON file after character modifications (does not store the end result of the fight).
* -z <result_file>: After each player turn, saves the current status of all characters into a result file. This is useful if the program gets aborted for some reason and you want to continue from where you left off.
* -l <log_file>: Each important message shown on the console is also logged into a text file.
* -r or --break-armor: Enable armor degradation on critical hits.
* -d or --damage-type: Enable damage type based on difference between attribute value and dice roll

### Examples

To load teams from .json file and enable armor degeneration, use

```bash
python3 how_to_be_a_hero_fight.py -i teams.json -r
```

to additionally add new characters manually, and save the new json file to teams_new.json, use

```bash
python3 how_to_be_a_hero_fight.py -i teams.json -o teams_new.json -r
```

To activate both armor degeneration and damage factors, log all events to an exteranl log file and write out the current state to a JSON after every turn, use

```bash
python3 how_to_be_a_hero_fight.py -i teams.json -z current-state.json -l fight.log -rd
```

## Using the program

### Team and Character creation

If no input file is provided, the program prompts you to create teams manually.
You’ll specify the number of teams and input details for each character in those teams.

Character details include:
* Name
* Hit points (Lebenspunkte)
* Armor value (Rüstungswert, 0-9)
* Maximum ignored dice pairs (Maximale ignorierte Augenpaare)
* Action value (Handeln-Wert)
* Parade value (optional, defaults to Action value)
* NPC status (ja/nein)
* Consciousness state (bewusstlos ja/nein)
* If armor degradation is enabled (-r), you’ll also input the current armor condition (Rüstungszustand), which can be set manually or defaults to the armor value.

### Initiative Phase

The program guides you through the initiative phase, where each character rolls for initiative.
NPCs are grouped by their action value for efficiency.
You’ll input dice rolls (1W10) for each group or individual character.
Initiative order is calculated based on the rolls, adjusted by armor value and action value.

### Combat Rounds

Combat proceeds in rounds, with turns based on the initiative order.
For each character’s turn, you’ll:
* Select a target (by name or team). If a team name is entered, a random target will be selected from that team.
* Input the attack ability value and any modifiers.
* Enter the dice roll (2W10) for the attack.

The program determines the success level (e.g., critical success, normal success).
If the attack succeeds, the defender may attempt to parade (if eligible).
Damage is calculated using the weapon’s damage formula, adjusted by the defender’s armor condition.
If armor degradation is enabled, critical hits reduce the defender’s armor condition.

### Ending Combat

After each round, you decide whether to proceed to the next round.
Combat ends when you choose to stop or when all characters on one side (all Players or all NSCs) are defeated (unconscious or dead).
The final status of all characters is displayed.
If an output file is specified, updated team data (hit points, armor condition, etc.) is saved.


## Modes

### Damage Types

Enabled with the -d or --damage-type flag.

In this mode:
* Damage is multiplied based on the difference between the players dice roll and their skilled attack attribute valued
* difference <= 10: You only graze the enemy. Base damage is multiplied by 0.75
* difference >=60: Critical hit. Base Damage is multiplied by 1.15
* Everything in-between: Normal hit. No additional multiplier

### Armor Degradation

Enabled with the -r or --break-armor flag.

In this mode:
* A critical success on a hit reduces the target’s armor condition by 1 (minimum 0).
* Armor condition affects damage calculations by determining which dice are ignored in the roll.

If the flag is not used:
Armor condition stays equal to the armor value and remains unchanged, even on critical hits.

## Contributing

Feel free to fork this repository and submit pull requests for enhancements or bug fixes.
Encounter an issue? Please open an issue on the GitHub repository page.
