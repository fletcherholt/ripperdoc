"""Build presets and best-in-slot cyberware reference (patch 2.x / Phantom
Liberty). Attribute values used by presets respect the in-game cap of 20.

The cyberware list is guidance shown in the app: a shopping/equip checklist for
each archetype. Auto-injecting the items into the save is intentionally not done
in this version because the inventory format is the highest brick-risk area.
"""

# Each preset front-loads the attributes that the archetype scales with, while
# keeping every value within the legitimate 3-20 range so the game does not
# clamp or glitch.
PRESETS = {
    "netrunner": {
        "title": "Netrunner",
        "blurb": "Sit in the dark, fry every gonk in the building through the walls. Intelligence does the killing.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "Intelligence": 20,
            "Cool": 20,
            "TechnicalAbility": 18,
            "Reflexes": 9,
            "Strength": 9,
        },
        "cyberware": {
            "Operating System": "Tetratronic Rippler Mk.5 cyberdeck (quickhack spread + combat RAM regen)",
            "Frontal Cortex": "Camillo RAM Manager + Mechatronic Core (RAM cost/regen)",
            "Circulatory System": "Second Heart + Bioconductor (cooldown / survive)",
            "Hands": "Smart Link (if running smart sidearm backup)",
            "Nervous System": "Kerenzikov",
            "Integumentary System": "Pain Editor (flat damage reduction)",
            "Face": "Kiroshi 'The Oracle' Optics",
            "Skeleton": "Bionic Joints",
            "Legs": "Reinforced Tendons (double jump)",
            "Arms": "Monowire (quickhack-scaling melee fallback)",
        },
    },
    "sandevistan": {
        "title": "Sandevistan Solo",
        "blurb": "Hit the Sande, time stops, everyone's already dead. Blades or a clean headshot. Reflexes + Cool.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "Reflexes": 20,
            "Cool": 20,
            "TechnicalAbility": 18,
            "Strength": 9,
            "Intelligence": 9,
        },
        "cyberware": {
            "Operating System": "Militech 'Apogee' Sandevistan (max slow + damage) or QianT 'Warp Dancer' Mk.5 (uptime)",
            "Frontal Cortex": "Newton Module to Axolotl (cooldown reduction on kill)",
            "Circulatory System": "Second Heart + Heal-on-Kill",
            "Hands": "Smart Link (smart weapons) or Microgenerator",
            "Nervous System": "Kerenzikov + Reaction Tuner",
            "Integumentary System": "Pain Editor + Subdermal Armor",
            "Face": "Kiroshi 'The Oracle' Optics",
            "Skeleton": "Titanium / Carbon-myomar bones",
            "Legs": "Reinforced Tendons (double jump)",
            "Arms": "Mantis Blades (scales with Sandevistan)",
        },
    },
    "tech": {
        "title": "Tech Engineer",
        "blurb": "Charge a tech shot through three walls and a gonk's skull. Chromed to the eyeballs. Tech + Reflexes.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "TechnicalAbility": 20,
            "Reflexes": 20,
            "Cool": 18,
            "Strength": 9,
            "Intelligence": 9,
        },
        "cyberware": {
            "Operating System": "Militech Berserk Mk.5 or QianT Sandevistan (Tech checks open more)",
            "Frontal Cortex": "Newton Module to Axolotl + Bioconductor",
            "Circulatory System": "Second Heart + Blood Pump",
            "Hands": "Smart Link",
            "Nervous System": "Kerenzikov + Adrenaline Converter",
            "Integumentary System": "Pain Editor + Chitin (armor)",
            "Face": "Kiroshi 'The Oracle' Optics",
            "Skeleton": "Rara Avis + Bionic Joints",
            "Legs": "Reinforced Tendons",
            "Arms": "Projectile Launch System or Gorilla Arms",
        },
    },
    "tank": {
        "title": "Solo Tank",
        "blurb": "Walk through the gunfire, rip their arms off, go home. Big dumb Body bruiser and proud of it.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "Strength": 20,
            "Reflexes": 18,
            "TechnicalAbility": 18,
            "Cool": 9,
            "Intelligence": 9,
        },
        "cyberware": {
            "Operating System": "Militech Berserk Mk.5 'Falcon' (near-invuln window)",
            "Frontal Cortex": "Newton Module to Axolotl",
            "Circulatory System": "Second Heart + Bioplastic Blood Vessels",
            "Hands": "Microgenerator (electroshock on reload)",
            "Nervous System": "Kerenzikov",
            "Integumentary System": "Pain Editor + Chitin + Subdermal Armor",
            "Face": "Kiroshi 'The Oracle' Optics",
            "Skeleton": "Titanium bones + Bionic Joints + Dense Marrow",
            "Legs": "Fortified Ankles (charged jump) or Reinforced Tendons",
            "Arms": "Gorilla Arms (blunt + Body checks)",
        },
    },
    "stealth": {
        "title": "Stealth Katana",
        "blurb": "One with the shadows, one swing one kill. Sneak past the whole gig or leave a pile of bodies nobody heard drop. Cool + Reflexes.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "Cool": 20,
            "Reflexes": 20,
            "Intelligence": 15,
            "TechnicalAbility": 9,
            "Strength": 9,
        },
        "cyberware": {
            "Operating System": "QianT 'Warp Dancer' Sandevistan Mk.5 (short cooldown for silent bursts)",
            "Frontal Cortex": "Newton Module to Axolotl + Mnemonic Ram Extractor",
            "Circulatory System": "Second Heart + Sensory Amplifier (crit from stealth)",
            "Hands": "Ambush hands (ranged sneak damage) or Smart Link",
            "Nervous System": "Kerenzikov + Reaction Tuner",
            "Integumentary System": "Optical Camo + Pain Editor",
            "Face": "Kiroshi 'The Oracle' Optics (threat + enemy scan)",
            "Skeleton": "Bionic Joints + Microrotors (fast attack)",
            "Legs": "Lynx Paws (silent movement) + Reinforced Tendons",
            "Arms": "Mantis Blades (stealth finishers) or a Cool-scaling katana",
        },
    },
    "smartgun": {
        "title": "Smart Gunner",
        "blurb": "Let the bullets do the aiming. Curve rounds round cover into three skulls at once. Tech + Cool, chrome-heavy.",
        "level": 50,
        "street_cred": 50,
        "attributes": {
            "TechnicalAbility": 20,
            "Cool": 20,
            "Reflexes": 18,
            "Intelligence": 9,
            "Strength": 9,
        },
        "cyberware": {
            "Operating System": "Militech 'Apogee' Sandevistan or Berserk (whichever fits your trigger finger)",
            "Frontal Cortex": "Newton Module to Axolotl + Kiroshi target analysis",
            "Circulatory System": "Second Heart + Adreno-Trigger (heal on crit)",
            "Hands": "Smart Link (mandatory, no smart targeting without it)",
            "Nervous System": "Kerenzikov + Atypical Reflexes",
            "Integumentary System": "Pain Editor + Subdermal Armor",
            "Face": "Kiroshi 'The Oracle' Optics with Threat Detector",
            "Skeleton": "Rara Avis + Bionic Joints",
            "Legs": "Reinforced Tendons",
            "Arms": "Projectile Launch System (backup burst) or empty for weapon grip",
        },
    },
}

# Items everyone should run regardless of build.
UNIVERSAL = [
    "Second Heart (auto-revive once per fight)",
    "Pain Editor (flat incoming-damage reduction)",
    "Reinforced Tendons (double jump mobility)",
    "Kerenzikov (slow-mo on dodge/aim)",
    "A cooldown-reducer Frontal Cortex (Axolotl or Bioconductor)",
    "Smart Link in Hands if you run any smart weapon",
]
