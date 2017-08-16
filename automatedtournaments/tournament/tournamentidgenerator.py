import random

CHARS = [chr(i) for i in range(ord('A'), ord('Z'))] + [chr(i) for i in range(ord('a'), ord('z'))]
NAMES = [
    "Arbiter",
    "Archon",
    "Carrier",
    "Corsair",
    "Dark Archon",
    "Dark Templar",
    "Dragoon",
    "High Templar",
    "Observer",
    "Photon Cannon",
    "Probe",
    "Reaver",
    "Scout",
    "Shuttle",
    "Zealot",
    "Battlecruiser",
    "Dropship",
    "Firebat",
    "Ghost",
    "Goliath",
    "Marine",
    "Medic",
    "Missile Turret",
    "Science Vessel",
    "SCV",
    "Siege Tank",
    "Valkyrie",
    "Vulture",
    "Wraith",
    "Broodling",
    "Defiler",
    "Devourer",
    "Drone",
    "Guardian",
    "Hydralisk",
    "Infested Terran",
    "Larva",
    "Lurker",
    "Mutalisk",
    "Overlord",
    "Queen",
    "Scourge",
    "Spore Colony",
    "Sunken Colony",
    "Ultralisk",
    "Zergling",
]

class TournamentIdGenerator:

    @staticmethod
    def next_id() -> str:
        return "".join(random.choice(CHARS) for _ in range(8))

    @staticmethod
    def next_name() -> str:
        return "The {} Cup".format(random.choice(NAMES))
