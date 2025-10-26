SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60
LIPID_COUNT = 50
CELL_RADIUS = 20

MAX_SPLITS = 3

SILVER = (198, 197, 185)
LIGHT_BLUE = (98, 146, 158)
DARK_BLUE = (74, 109, 124)
BROWN = (57, 58, 16)
GRAY = (71, 86, 87)
MINT = (120, 200, 160)
GOLDEN = (255, 200, 80)
REDDISH_GRAY = (150, 100, 100)

# Combat and Sensing Parameters
VIEW_SCALE = 1.5  # Enemy view range = VIEW_SCALE * enemy.radius
VIRUS_VIEW_RANGE = 500  # Fixed view range for viruses in pixels
VIRUS_DAMAGE_HIGH_HEALTH = 0.10  # 10% of cell health when health > 25%
VIRUS_INSTANT_DEATH_CHANCE = 0.05  # 5% chance of instant death
VIRUS_SPAWN_ON_KILL = 3  # Number of viruses spawned when killing a cell
MEMBRANE_DEDUCTION_ON_COLLISION = 0.5  # Fraction of loser's membrane points deducted from winner

# Entity Base Stats Configuration
# Stats: Strength (damage), Endurance (defense/health), Dexterity (speed/dodge/crit), Intelligence (abilities)
BASE_PLAYER_STATS = {
    'strength': 10,
    'endurance': 10,
    'dexterity': 10,
    'intelligence': 10
}

BASE_ENEMY_STATS = {
    'strength': 8,
    'endurance': 15,
    'dexterity': 6,
    'intelligence': 5
}

BASE_VIRUS_STATS = {
    'strength': 15,
    'endurance': 5,
    'dexterity': 12,
    'intelligence': 3
}

# Stat Scaling Constants
STRENGTH_DAMAGE_MULTIPLIER = 0.05  # +5% damage per strength point
ENDURANCE_FLAT_REDUCTION = 0.8     # Flat damage reduction per endurance point
ENDURANCE_PERCENT_REDUCTION = 0.02  # +2% damage reduction per endurance point (max 75%)
DEXTERITY_DODGE_CHANCE = 0.015     # +1.5% dodge chance per dexterity point (max 50%)
DEXTERITY_CRIT_CHANCE = 0.02       # +2% crit chance per dexterity point (max 40%)
CRIT_DAMAGE_MULTIPLIER = 1.5       # 50% bonus damage on critical hit

# Rotation Constants
CELL_ROTATION_SPEED = 1.0  # Degrees per second for constant cell rotation

# Targeting and Combat Constants
TARGET_KEEP_DISTANCE = 250  # Pixels - cells try to stay this far from targets
TARGET_DISTANCE_TOLERANCE = 50  # Pixels - acceptable distance variance
TARGET_APPROACH_SPEED = 100  # Speed when moving toward/away from target

# Protein System Constants
PROTEIN_CANNON_DAMAGE = 15
PROTEIN_CANNON_COOLDOWN = 1.0  # Seconds
PROTEIN_CANNON_RANGE = 400  # Pixels
PROTEIN_CANNON_PROJECTILE_SPEED = 300

PROTEIN_BOMB_DAMAGE = 40
PROTEIN_BOMB_COOLDOWN = 3.0
PROTEIN_BOMB_TRIGGER_RADIUS = 80  # When enemies get this close, it explodes
PROTEIN_BOMB_EXPLOSION_RADIUS = 120

PROTEIN_BURST_DAMAGE = 60
PROTEIN_BURST_COOLDOWN = 5.0
PROTEIN_BURST_RADIUS = 200

MOLECULAR_DRILL_DAMAGE = 100
MOLECULAR_DRILL_COOLDOWN = 8.0
MOLECULAR_DRILL_RANGE = 350

ENZYME_STRIKE_DAMAGE = 25
ENZYME_STRIKE_COOLDOWN = 2.0
ENZYME_STRIKE_RANGE = 300
ENZYME_STRIKE_DOT_DURATION = 3.0  # Damage over time duration

# Defense Proteins
SPIKES_DAMAGE_REFLECT = 0.3  # Reflect 30% of incoming damage
BARRIER_MATRIX_SHIELDS = 3
BARRIER_MATRIX_REGEN_TIME = 10.0  # Seconds to regenerate one shield
ADHESION_WEB_SLOW = 0.5  # 50% slow effect
ADHESION_WEB_RADIUS = 150
RESONANCE_SHIELD_ABSORPTION = 50  # Absorbs this much damage before breaking

# Spring Physics Constants
SPRING_MAX_STRETCH_MULTIPLIER = 3.0  # Maximum stretch = rest_length * this multiplier

ORGANELLE_DATA = {
    'Universal': [
                {
            'name': 'Cell Membrane Extender',
            'desc': 'Extends a cells membrane by 10',
            'boosts': [
                #{'type': 'Dexterity', 'amount': 15.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 20, 'lipid': 50, 'carbohydrate': 5, 'nucleic_acid': 5},
            'color': (200, 255, 255),
            'symbol': 'Ext'
        },
        {
            'name': 'Cell Membrane+',
            'desc': 'Fortifies membrane to improve selective permeability.',
            'boosts': [
                {'type': 'Endurance', 'amount': 50.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 50, 'lipid': 200, 'carbohydrate': 20, 'nucleic_acid': 10},
            'color': (180, 255, 240),
            'symbol': 'C-M'
        },
        {
            'name': 'Ribosome Cluster',
            'desc': 'Accelerates protein synthesis rate.',
            'boosts': [
                {'type': 'Intelligence', 'amount': 30.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 150, 'lipid': 30, 'carbohydrate': 10, 'nucleic_acid': 5},
            'color': (220, 180, 200),
            'symbol': 'R-C'
        },
        {
            'name': 'Cytoskeleton Reinforcement',
            'desc': 'Improves structural integrity and movement efficiency.',
            'boosts': [
                {'type': 'Dexterity', 'amount': 15.0, 'duration': 'N/A'},
                {'type': 'Endurance', 'amount': 10.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 200, 'lipid': 50, 'carbohydrate': 5, 'nucleic_acid': 5},
            'color': (200, 230, 255),
            'symbol': 'C-R'
        },
        {
            'name': 'Flagella',
            'desc': 'Movement efficiency.',
            'boosts': [
                {'type': 'Dexterity', 'amount': 15.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 50, 'lipid': 50, 'carbohydrate': 25, 'nucleic_acid': 25},
            'color': (200, 255, 255),
            'symbol': 'Fl'
        },        
        {
            'name': 'Zoom Enhancer',
            'desc': 'Increases camera zoom range.',
            'boosts': [
                {'type': 'Dexterity', 'amount': 15.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 100, 'lipid': 0, 'carbohydrate': 250, 'nucleic_acid': 250},
            'color': (200, 255, 255),
            'symbol': 'Z-B'
        },


    ],
    'Prokaryotic': [
        {
            'name': 'Extra Plasmid',
            'desc': 'Grants additional genetic capabilities.',
            'boosts': [
                {'type': 'Intelligence', 'amount': 35.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 20, 'lipid': 10, 'carbohydrate': 5, 'nucleic_acid': 50},
            'color': (180, 255, 180),
            'symbol': 'E-P'
        },
        {
            'name': 'Peptidoglycan Boost',
            'desc': 'Thickens cell wall for greater durability.',
            'boosts': [
                {'type': 'Endurance', 'amount': 30.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 40, 'lipid': 20, 'carbohydrate': 150, 'nucleic_acid': 5},
            'color': (255, 230, 180),
            'symbol': 'P-B'
        }
    ],
    'Plant': [
        {
            'name': 'Chloroplast+',
            'desc': 'Boosts photosynthesis efficiency and energy generation.',
            'boosts': [
                {'type': 'Endurance', 'amount': 30.0, 'duration': 'N/A'},
                {'type': 'Intelligence', 'amount': 15.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 100, 'lipid': 120, 'carbohydrate': 200, 'nucleic_acid': 20},
            'color': (180, 255, 160),
            'symbol': 'Chl'
        },
        {
            'name': 'Central Vacuole Expand',
            'desc': 'Improves water and nutrient storage capacity.',
            'boosts': [
                {'type': 'Endurance', 'amount': 20.0, 'duration': 'N/A'},
                {'type': 'Strength', 'amount': 10.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 10, 'lipid': 30, 'carbohydrate': 180, 'nucleic_acid': 10},
            'color': (120, 220, 240),
            'symbol': 'C-V'
        }
    ],
    'Animal': [
        {
            'name': 'Lysosome Pack',
            'desc': 'Enhances breakdown of waste and foreign material.',
            'boosts': [
                {'type': 'Strength', 'amount': 25.0, 'duration': 'N/A'},
                {'type': 'Endurance', 'amount': 10.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 80, 'lipid': 20, 'carbohydrate': 20, 'nucleic_acid': 5},
            'color': (255, 160, 160),
            'symbol': 'L-P'
        },
        {
            'name': 'Multiple Nuclei',
            'desc': 'Allows parallel cellular operations for faster response.',
            'boosts': [
                {'type': 'Intelligence', 'amount': 55.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 300, 'lipid': 50, 'carbohydrate': 10, 'nucleic_acid': 200},
            'color': (220, 220, 255),
            'symbol': 'M-N'
        },
        {
            'name': 'Centrosome Upgrade',
            'desc': 'Speeds up cell division and regeneration.',
            'boosts': [
                {'type': 'Intelligence', 'amount': 20.0, 'duration': 'N/A'},
                {'type': 'Endurance', 'amount': 10.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 150, 'lipid': 60, 'carbohydrate': 5, 'nucleic_acid': 10},
            'color': (200, 200, 230),
            'symbol': 'C-U'
        }
    ]
}

PROTEIN_DATA = {
    'Structure': [
        {
            'name': 'Protein Core',
            'desc': 'Basic structural protein.',
            'boosts': [
                {'type': 'Endurance', 'amount': 10.0, 'duration': 'N/A'},
                {'type': 'Intelligence', 'amount': 5.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 50, 'lipid': 20, 'carbohydrate': 10, 'nucleic_acid': 5},
            'color': (100, 180, 255),
            'symbol': 'P-C'
        },
        # {
        #     'name': 'Membrane Patch',
        #     'desc': 'Repairs cell membrane.',
        #     'boosts': [
        #         {'type': 'Endurance', 'amount': 35.0, 'duration': 'N/A'}
        #     ],
        #     'cost': {'protein': 30, 'lipid': 40, 'carbohydrate': 5, 'nucleic_acid': 2},
        #     'color': (120, 200, 220),
        #     'symbol': 'M-P'
        # },
        {
            'name': 'Elastin Protein',
            'desc': 'Attaches two cells with a flexible spring connection. Select two points on different cells to connect them.',
            'boosts': [
                {'type': 'Dexterity', 'amount': 10.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 120, 'lipid': 60, 'carbohydrate': 20, 'nucleic_acid': 10},
            'color': (180, 220, 255),
            'symbol': 'S-P'
        },
        {
            'name': 'Collagen Protein',
            'desc': 'Attaches two cells with a nearly rigid solid connection. Select two points on different cells to connect them.',
            'boosts': [
                {'type': 'Endurance', 'amount': 25.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 200, 'lipid': 100, 'carbohydrate': 40, 'nucleic_acid': 20},
            'color': (220, 220, 255),
            'symbol': 'SO-P'
        }
    ],
    'Enzymes': [
        {
            'name': 'Enzymes',
            'desc': 'Catalyzes reactions.',
            'boosts': [
                {'type': 'Intelligence', 'amount': 45.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 60, 'lipid': 10, 'carbohydrate': 10, 'nucleic_acid': 10},
            'color': (180, 120, 255),
            'symbol': 'En'
        },
        {
            'name': 'Receptors',
            'desc': 'Detects signals.',
            'boosts': [
                {'type': 'Dexterity', 'amount': 30.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 40, 'lipid': 10, 'carbohydrate': 20, 'nucleic_acid': 10},
            'color': (200, 180, 80),
            'symbol': 'Re'
        }
    ],
    'Attack': [
        {
            'name': 'Protein Cannon',
            'desc': 'Fires protein projectiles.',
            'boosts': [
                {'type': 'Strength', 'amount': 40.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 80, 'lipid': 20, 'carbohydrate': 10, 'nucleic_acid': 20},
            'color': (255, 100, 100),
            'symbol': 'P-C'
        },
        {
            'name': 'Protein Bomb',
            'desc': 'Leaves behind a damaging protein mine that explodes when enemies approach.',
            'boosts': [
                {'type': 'Strength', 'amount': 40.0, 'duration': 'N/A'},
                {'type': 'Dexterity', 'amount': 20.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 100, 'lipid': 15, 'carbohydrate': 10, 'nucleic_acid': 25},
            'color': (200, 50, 50),
            'symbol': 'P-B'
        },
        {
            'name': 'Protein Burst',
            'desc': 'Releases a sudden explosive wave of proteins damaging nearby foes.',
            'boosts': [
                {'type': 'Strength', 'amount': 85.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 150, 'lipid': 40, 'carbohydrate': 25, 'nucleic_acid': 20},
            'color': (255, 120, 120),
            'symbol': 'P-Bu'
        },
        {
            'name': 'Molecular Drill',
            'desc': 'Forms a spiraling protein drill with a long cooldown but high damage.',
            'boosts': [
                {'type': 'Strength', 'amount': 80.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 140, 'lipid': 20, 'carbohydrate': 20, 'nucleic_acid': 30},
            'color': (240, 80, 160),
            'symbol': 'M-D'
        },
        {
            'name': 'Enzyme Strike',
            'desc': 'Unleashes corrosive protein enzymes that weaken and damage enemies.',
            'boosts': [
                {'type': 'Strength', 'amount': 45.0, 'duration': 'N/A'},
                {'type': 'Endurance', 'amount': 30.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 130, 'lipid': 35, 'carbohydrate': 20, 'nucleic_acid': 25},
            'color': (100, 200, 80),
            'symbol': 'E-S'
        }
    ],
    'Defense': [
        {
            'name': 'Spikes',
            'desc': 'Defensive spikes.',
            'boosts': [
                {'type': 'Endurance', 'amount': 25.0, 'duration': 'N/A'},
                {'type': 'Strength', 'amount': 15.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 70, 'lipid': 10, 'carbohydrate': 10, 'nucleic_acid': 5},
            'color': (255, 180, 60),
            'symbol': 'Sp'
        },
        {
            'name': 'Barrier Matrix',
            'desc': 'Forms 3 fortified protein shield around the user that regenerates over time.',
            'boosts': [
                {'type': 'Endurance', 'amount': 65.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 120, 'lipid': 30, 'carbohydrate': 20, 'nucleic_acid': 10},
            'color': (80, 180, 255),
            'symbol': 'B-M'
        },
        {
            'name': 'Adhesion Web',
            'desc': 'Creates a sticky protein mesh to trap and slow enemies.',
            'boosts': [
                {'type': 'Endurance', 'amount': 50.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 90, 'lipid': 25, 'carbohydrate': 30, 'nucleic_acid': 15},
            'color': (180, 140, 255),
            'symbol': 'A-W'
        },
        {
            'name': 'Resonance Shield',
            'desc': 'Uses vibrating protein structures to absorb and deflect attacks. Destroyed upon use',
            'boosts': [
                {'type': 'Endurance', 'amount': 40.0, 'duration': 'N/A'},
                {'type': 'Strength', 'amount': 20.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 110, 'lipid': 35, 'carbohydrate': 15, 'nucleic_acid': 30},
            'color': (120, 220, 160),
            'symbol': 'R-S'
        },
        {
            'name': 'Chitin Armor',
            'desc': 'Creates a hardened protein exoskeleton for defense.',
            'boosts': [
                {'type': 'Endurance', 'amount': 80.0, 'duration': 'N/A'}
            ],
            'cost': {'protein': 160, 'lipid': 50, 'carbohydrate': 15, 'nucleic_acid': 10},
            'color': (150, 100, 60),
            'symbol': 'C-A'
        }
    ]
}

TYPE_CODON_MAP = {
    'ATT': {'type': 'Strength', 'boost': 10, 'duration': 150},
    'ATC': {'type': 'Strength', 'boost': 20, 'duration': 75},
    'ATA': {'type': 'Strength', 'boost': 15, 'duration': 120},
    'ATG': {'type': 'Dexterity', 'boost': 30, 'duration': 60},
    'TTT': {'type': 'Dexterity', 'boost': 18, 'duration': 105},
    'TTC': {'type': 'Dexterity', 'boost': 22, 'duration': 90},
    'CTT': {'type': 'Endurance', 'boost': 25, 'duration': 135},
    'CTC': {'type': 'Endurance', 'boost': 28, 'duration': 120},
    'CTA': {'type': 'Endurance', 'boost': 20, 'duration': 150},
    'CTG': {'type': 'Endurance', 'boost': 35, 'duration': 90},
    'TTA': {'type': 'Endurance', 'boost': 15, 'duration': 180},
    'TTG': {'type': 'Endurance', 'boost': 32, 'duration': 75},
    'GTT': {'type': 'Dexterity', 'boost': 12, 'duration': 165},
    'GTC': {'type': 'Dexterity', 'boost': 18, 'duration': 135},
    'GTA': {'type': 'Dexterity', 'boost': 22, 'duration': 105},
    'GTG': {'type': 'Dexterity', 'boost': 28, 'duration': 75},
    'TCT': {'type': 'Dexterity', 'boost': 10, 'duration': 180},
    'TCC': {'type': 'Dexterity', 'boost': 15, 'duration': 150},
    'TCA': {'type': 'Dexterity', 'boost': 20, 'duration': 120},
    'TCG': {'type': 'Dexterity', 'boost': 25, 'duration': 90},
    'AGT': {'type': 'Dexterity', 'boost': 30, 'duration': 60},
    'AGC': {'type': 'Dexterity', 'boost': 35, 'duration': 45},
    'CCT': {'type': 'Endurance', 'boost': 12, 'duration': 210},
    'CCC': {'type': 'Endurance', 'boost': 18, 'duration': 180},
    'CCA': {'type': 'Endurance', 'boost': 24, 'duration': 150},
    'CCG': {'type': 'Endurance', 'boost': 30, 'duration': 120},
    'ACT': {'type': 'Intelligence', 'boost': 16, 'duration': 165},
    'ACC': {'type': 'Intelligence', 'boost': 22, 'duration': 135},
    'ACA': {'type': 'Intelligence', 'boost': 28, 'duration': 105},
    'ACG': {'type': 'Intelligence', 'boost': 34, 'duration': 75},
    'GCT': {'type': 'Strength', 'boost': 20, 'duration': 150},
    'GCC': {'type': 'Strength', 'boost': 25, 'duration': 120},
    'GCA': {'type': 'Strength', 'boost': 30, 'duration': 90},
    'GCG': {'type': 'Strength', 'boost': 35, 'duration': 60},
    'TAT': {'type': 'Intelligence', 'boost': 18, 'duration': 135},
    'TAC': {'type': 'Intelligence', 'boost': 24, 'duration': 105},
    'CAT': {'type': 'Intelligence', 'boost': 20, 'duration': 150},
    'CAC': {'type': 'Intelligence', 'boost': 26, 'duration': 120},
    'CAA': {'type': 'Strength', 'boost': 30, 'duration': 90},
    'CAG': {'type': 'Strength', 'boost': 36, 'duration': 60},
    'AAT': {'type': 'Endurance', 'boost': 14, 'duration': 165},
    'AAC': {'type': 'Endurance', 'boost': 19, 'duration': 135},
    'AAA': {'type': 'Strength', 'boost': 22, 'duration': 120},
    'AAG': {'type': 'Strength', 'boost': 28, 'duration': 90},
    'GAT': {'type': 'Endurance', 'boost': 32, 'duration': 75},
    'GAC': {'type': 'Endurance', 'boost': 38, 'duration': 45},
    'GAA': {'type': 'Intelligence', 'boost': 20, 'duration': 150},
    'GAG': {'type': 'Intelligence', 'boost': 26, 'duration': 120},
    'TGT': {'type': 'Endurance', 'boost': 18, 'duration': 180},
    'TGC': {'type': 'Endurance', 'boost': 24, 'duration': 150},
    'TGG': {'type': 'Strength', 'boost': 30, 'duration': 90},
    'CGT': {'type': 'Endurance', 'boost': 16, 'duration': 165},
    'CGC': {'type': 'Endurance', 'boost': 22, 'duration': 135},
    'CGA': {'type': 'Endurance', 'boost': 28, 'duration': 105},
    'CGG': {'type': 'Endurance', 'boost': 34, 'duration': 75},
    'AGA': {'type': 'Endurance', 'boost': 40, 'duration': 45},
    'AGG': {'type': 'Endurance', 'boost': 45, 'duration': 30},
    'GGT': {'type': 'Dexterity', 'boost': 12, 'duration': 180},
    'GGC': {'type': 'Dexterity', 'boost': 18, 'duration': 150},
    'GGA': {'type': 'Dexterity', 'boost': 24, 'duration': 120},
    'GGG': {'type': 'Dexterity', 'boost': 30, 'duration': 90},
    'TAA': {'type': 'Strength', 'boost': 50, 'duration': -30},
    'TAG': {'type': 'Strength', 'boost': 45, 'duration': -45},
    'TGA': {'type': 'Strength', 'boost': 40, 'duration': -60}
}

AMINO_ACID_BOOST_TYPE = {
    'Isoleucine': {
        'type': 'Strength',
        'boost_desc': 'improves physical power and damage',
        'acid_desc': 'Isoleucine is a branched-chain essential amino acid (BCAA) that plays a critical role in muscle metabolism, energy regulation, and tissue repair. It facilitates glucose uptake and contributes to hemoglobin synthesis, serving as a substrate for energy during physical exertion.'
    },
    'Methionine': {
        'type': 'Dexterity',
        'boost_desc': 'improves speed and precision',
        'acid_desc': 'Methionine is an essential amino acid that serves as the initiating residue in protein synthesis. It is also a key source of sulfur and contributes to methylation reactions, influencing metabolism and cellular signaling.'
    },
    'Phenylalanine': {
        'type': 'Intelligence',
        'boost_desc': 'improves speed of attacks',
        'acid_desc': 'Phenylalanine is an aromatic essential amino acid that serves as a precursor to neurotransmitters such as dopamine and norepinephrine. It supports nervous system function and cognitive alertness.'
    },
    'Leucine': {
        'type': 'Endurance',
        'boost_desc': 'improves max ATP and health',
        'acid_desc': 'Leucine is a branched-chain amino acid critical for protein synthesis and energy metabolism. It activates mTOR signaling, which regulates muscle growth and cellular repair, making it vital for endurance and recovery.'
    },
    'Valine': {
        'type': 'Dexterity',
        'boost_desc': 'improves control over movement',
        'acid_desc': 'Valine is a branched-chain essential amino acid involved in muscle coordination, tissue repair, and energy production. It helps maintain mental sharpness and physical agility during intense activity.'
    },
    'Serine': {
        'type': 'Intelligence',
        'boost_desc': 'improves viewing range (zoom)',
        'acid_desc': 'Serine is a polar amino acid important in cellular signaling, metabolism, and the biosynthesis of other biomolecules. It plays a role in nervous system function and synaptic plasticity.'
    },
    'Proline': {
        'type': 'Endurance',
        'boost_desc': 'improves protein duration',
        'acid_desc': 'Proline is a non-essential amino acid with a unique cyclic structure that stabilizes protein folds. It contributes to the structural integrity of collagen and other long-lived proteins.'
    },
    'Threonine': {
        'type': 'Intelligence',
        'boost_desc': 'improves cell reaction time',
        'acid_desc': 'Threonine is an essential amino acid involved in protein balance, immune function, and cell signaling. It supports the dynamic responsiveness of cells to environmental changes.'
    },
    'Alanine': {
        'type': 'Endurance',
        'boost_desc': 'improves ATP regeneration',
        'acid_desc': 'Alanine is a non-essential amino acid that plays a central role in the glucose-alanine cycle, helping transport nitrogen and regenerate glucose, especially during prolonged exercise.'
    },
    'Tyrosine': {
        'type': 'Intelligence',
        'boost_desc': 'improves cell reaction time',
        'acid_desc': 'Tyrosine is a non-essential amino acid derived from phenylalanine. It is a precursor for catecholamines and thyroid hormones, supporting cognitive function and stress response.'
    },
    'Histidine': {
        'type': 'Intelligence',
        'boost_desc': 'improves viewing range (zoom)',
        'acid_desc': 'Histidine is a semi-essential amino acid involved in the synthesis of histamine, a neurotransmitter and immune mediator. It supports pH buffering and visual processing.'
    },
    'Glutamine': {
        'type': 'Strength',
        'boost_desc': 'improves damage of contact-attacks',
        'acid_desc': 'Glutamine is a conditionally essential amino acid that fuels rapidly dividing cells and maintains intestinal integrity. It supports immune responses and cellular radiance under stress.'
    },
    'Asparagine': {
        'type': 'Endurance',
        'boost_desc': 'improves ATP use efficiency',
        'acid_desc': 'Asparagine is a non-essential amino acid important for nitrogen transport and glycoprotein synthesis. It supports cellular homeostasis and resource balance.'
    },
    'Lysine': {
        'type': 'Strength',
        'boost_desc': 'improves damage of attacks',
        'acid_desc': 'Lysine is an essential amino acid vital for protein synthesis, calcium absorption, and hormone production. It promotes tissue repair and muscular strength.'
    },
    'Aspartic Acid': {
        'type': 'Endurance',
        'boost_desc': 'improves max ATP and health',
        'acid_desc': 'Aspartic acid is a non-essential amino acid involved in the urea cycle and energy production through the citric acid cycle. It supports stamina and metabolic efficiency.'
    },
    'Glutamic Acid': {
        'type': 'Intelligence',
        'boost_desc': 'improves protein synthesis time',
        'acid_desc': 'Glutamic acid is a non-essential amino acid acting as a key neurotransmitter and precursor in protein metabolism. It plays a major role in learning, memory, and biosynthetic efficiency.'
    },
    'Cysteine': {
        'type': 'Endurance',
        'boost_desc': 'improves membrane permeability',
        'acid_desc': 'Cysteine is a sulfur-containing amino acid critical for disulfide bond formation, antioxidant defense via glutathione, and maintenance of cellular membrane integrity.'
    },
    'Tryptophan': {
        'type': 'Intelligence',
        'boost_desc': 'improves speed:health ratio',
        'acid_desc': 'Tryptophan is an essential aromatic amino acid that serves as a precursor to serotonin and melatonin. It influences mood, sleep, and the willpower-to-energy tradeoff in organisms.'
    },
    'Arginine': {
        'type': 'Endurance',
        'boost_desc': 'improves membrane permeability',
        'acid_desc': 'Arginine is a semi-essential amino acid involved in nitric oxide synthesis, which regulates blood flow and immune response. It enhances cellular defense and barrier functions.'
    },
    'Glycine': {
        'type': 'Dexterity',
        'boost_desc': 'improves collection range',
        'acid_desc': 'Glycine is the simplest amino acid and a major component of collagen. It acts as an inhibitory neurotransmitter and enhances extracellular matrix flexibility and cellular communication.'
    },
    'Stop Codon': {
        'type': 'Strength',
        'boost_desc': 'attacks have a chance to explode',
        'acid_desc': 'Stop codons do not encode amino acids but signal termination of protein synthesis. In game logic, they represent unpredictable or chaotic effects due to premature halting.'
    }
}

SKILL_TREES = {
    "Plant": {
        "layer_0":{},
        "layer_1":{},
        "layer_2":{}
    }
}

SKILL_TREES["Plant"]["layer_0"] = {
            "photosynthesis_root": {
                "name": "Photosynthetic Spark",
                "desc": "Begin your plant evolution path.",
                "requirements": {
                    "organelles": ["chloroplast", "chloroplast", "protein_core", "protein_core"],
                    "generate_ATP": 500
                },
                "boosts": [{"type": "Charge", "amount": 0.1}],
                "prerequisites": [],
                "branch_to": ["leaf_expansion"]
            }
}

SKILL_TREES["Plant"]["layer_1"] = {
            "leaf_expansion": {
                "name": "Leaf Expansion",
                "desc": "Enhances solar absorption surface area.",
                "requirements": {"generate_ATP": 1000},
                "boosts": [{"type": "Efficiency", "amount": 0.15}],
                "prerequisites": ["photosynthesis_root"],
                "branch_to": ["vascular_growth", "root_development"]
            }
}

SKILL_TREES["Plant"]["layer_2"] = {
            "thylakoid_densification": {
                "name": "Thylakoid Densification",
                "desc": "Increase the density of thylakoid stacks to maximize ATP synthesis efficiency.",
                "requirements": {
                    "organelles": ["chloroplast", "chloroplast"],
                    "generate_ATP": 1500
                },
                "boosts": [{"type": "ATP_Generation", "amount": 0.25}],
                "prerequisites": ["leaf_expansion"],
                "branch_to": ["photosystem_specialization"]
            },
            "intercellular_linking": {
            "name": "Intercellular Linking",
            "desc": "Enable primitive plasmodesmata-like structures to share energy and signals between nearby cells.",
            "requirements": {
                "generate_ATP": 2000,
                "cell_count": 5  # Assuming your game can track this
            },
            "boosts": [
                {"type": "Shared_Resources", "amount": 0.15},
                {"type": "cell_count", "amount": 10}
            ],
            "prerequisites": ["leaf_expansion"],
            "branch_to": ["colony_signaling"]
            },
            "light_harvesting_complex": {
            "name": "Light-Harvesting Complex",
            "desc": "Expand the light spectrum your chloroplasts can absorb, increasing energy intake in varied environments.",
            "requirements": {
                "generate_ATP": 1600,
                "environment": ["low_light"]
            },
            "boosts": [{"type": "Light_Efficiency", "amount": 0.2}],
            "prerequisites": ["leaf_expansion"],
            "branch_to": ["adaptive_photoreceptors"]
        }
}

# World Generation Constants
CELL_VIEW_RANGE = 1  # radius of chunks that cells can view
MAP_SIZE = (1000000, 1000000)  # total world size in pixels
RENDER_DISTANCE = 5  # radius of chunks to render around player
CHUNK_SIZE = (1000, 1000)  # size of each chunk in pixels
WORLD_BOUNDS = (1000000, 1000000)  # actual playable world bounds

# Biome Configuration
BIOMES = {
    "hot": {
        "name": "Hot",
        "color": (255, 100, 100, 80),  # Red tint with alpha
        "temperature": 1.0
    },
    "warm": {
        "name": "Warm", 
        "color": (255, 255, 100, 80),  # Yellow tint with alpha
        "temperature": 0.5
    },
    "cold": {
        "name": "Cold",
        "color": (100, 100, 255, 80),  # Blue tint with alpha  
        "temperature": 0.0
    }
}

# Map UI Constants
MAP_UNDISCOVERED_COLOR = (0, 0, 0)  # Black
MAP_DISCOVERED_COLOR = (64, 64, 64)  # Dark gray
MAP_VIEWED_COLOR = (128, 128, 128)  # Light gray
MAP_RED_ZONE_COLOR = (255, 0, 0, 100)  # Red with alpha

# Scientific Discoveries System
DISCOVERIES = {
    "first_split": {
        "title": "Cell Division Mastery",
        "description": "Successfully divided your first cell! This fundamental process allows cells to reproduce and multiply, creating genetic copies that inherit the parent's characteristics.",
        "trigger": "cell_split",
        "category": "Biology",
        "educational_note": "In real biology, cell division involves complex DNA replication and cytoplasm separation processes.",
        "url": "https://www.khanacademy.org/science/biology/cellular-molecular-biology"
    },
    "100_protein": {
        "title": "Protein Abundance",
        "description": "Collected 100 protein molecules! Proteins are essential macromolecules that perform countless functions including enzymatic reactions, structural support, and cellular transport.",
        "trigger": "collect_molecules",
        "target": {"protein": 100},
        "category": "Biochemistry",
        "educational_note": "Proteins are made of amino acids and their 3D structure determines their function.",
        "url": "https://www.khanacademy.org/science/biology/macromolecules"
    },
    "100_lipid": {
        "title": "Lipid Mastery",
        "description": "Gathered 100 lipid molecules! Lipids form cell membranes, store energy, and act as signaling molecules. They're crucial for maintaining cellular integrity.",
        "trigger": "collect_molecules",
        "target": {"lipid": 100},
        "category": "Biochemistry",
        "educational_note": "Lipids are hydrophobic molecules that create the phospholipid bilayer of cell membranes.",
        "url": "https://www.khanacademy.org/science/biology/macromolecules"
    },
    "100_nucleic_acid": {
        "title": "Genetic Material Collection",
        "description": "Accumulated 100 nucleic acid molecules! These molecules store and transmit genetic information, forming the basis of DNA and RNA.",
        "trigger": "collect_molecules",
        "target": {"nucleic_acid": 100},
        "category": "Genetics",
        "educational_note": "DNA uses four bases (A, T, G, C) while RNA replaces thymine with uracil.",
        "url": "https://www.khanacademy.org/science/biology/macromolecules"
    },
    "100_carbohydrate": {
        "title": "Energy Source Mastery",
        "description": "Collected 100 carbohydrate molecules! Carbohydrates provide immediate energy and structural components for cells.",
        "trigger": "collect_molecules",
        "target": {"carbohydrate": 100},
        "category": "Biochemistry",
        "educational_note": "Glucose is the primary energy currency, while complex carbohydrates provide structure.",
        "url": "https://www.khanacademy.org/science/biology/macromolecules"
    },
    "first_virus_defeat": {
        "title": "Viral Defense Achievement",
        "description": "Defeated your first virus! Understanding viral infections and immune responses is crucial for cellular survival.",
        "trigger": "defeat_virus",
        "category": "Immunology",
        "educational_note": "Real viruses hijack cellular machinery to reproduce, making antiviral defenses essential.",
        "url": "https://www.khanacademy.org/science/biology/biology-of-viruses"
    },
    "first_enemy_defeat": {
        "title": "Competitive Advantage",
        "description": "Overcame your first enemy cell! Competition for resources drives evolution and natural selection.",
        "trigger": "defeat_enemy",
        "category": "Evolution",
        "educational_note": "Natural selection favors organisms better adapted to their environment.",
        "url": "https://www.khanacademy.org/science/biology/her/evolution-and-natural-selection"
    },
    "poi_discovery": {
        "title": "Point of Interest Explorer",
        "description": "Discovered your first Point of Interest! These special locations contain unique resources and challenges.",
        "trigger": "discover_poi",
        "category": "Exploration",
        "educational_note": "Biodiversity hotspots in nature often contain rare species and unique adaptations.",
        "url": "https://www.nationalgeographic.org/encyclopedia/biodiversity-hotspot/"
    },
    "membrane_upgrade": {
        "title": "Membrane Engineering",
        "description": "Enhanced your cell membrane! Membrane composition affects permeability, strength, and cellular functions.",
        "trigger": "upgrade_membrane",
        "category": "Cell Biology",
        "educational_note": "Cell membrane composition varies between organisms and affects survival in different environments.",
        "url": "https://www.khanacademy.org/science/biology/membranes-and-transport"
    },
    "organelle_creation": {
        "title": "Organelle Innovation",
        "description": "Created your first organelle! These specialized structures compartmentalize cellular functions for increased efficiency.",
        "trigger": "create_organelle",
        "category": "Cell Biology",
        "educational_note": "Eukaryotic cells evolved organelles to separate different biochemical processes.",
        "url": "https://www.khanacademy.org/science/biology/cell-structure-and-function"
    },
    "large_cell": {
        "title": "Cellular Gigantism",
        "description": "Grew a cell beyond 200 radius units! Larger cells can perform more functions but face challenges in nutrient transport.",
        "trigger": "large_cell",
        "threshold": 200,
        "category": "Cell Biology",
        "educational_note": "The surface area to volume ratio limits how large cells can grow effectively.",
        "url": "https://www.khanacademy.org/science/biology/cells-and-organelles"
    },
    "ecosystem_explorer": {
        "title": "Biome Specialist",
        "description": "Explored 5 different biomes! Each ecosystem presents unique challenges and opportunities for adaptation.",
        "trigger": "explore_biomes",
        "threshold": 5,
        "category": "Ecology",
        "educational_note": "Biodiversity varies dramatically between different biomes due to climate and resource availability.",
        "url": "https://www.khanacademy.org/science/biology/ecology"
    },
    "symbiosis": {
        "title": "Symbiotic Relationship",
        "description": "Formed a beneficial connection with another cell! Symbiosis drives evolution and creates complex ecosystems.",
        "trigger": "form_symbiosis",
        "category": "Ecology",
        "educational_note": "Symbiotic relationships range from mutualism to parasitism, shaping evolutionary outcomes.",
        "url": "https://www.khanacademy.org/science/biology/ecology-community"
    },
    "speed_demon": {
        "title": "Locomotion Master",
        "description": "Achieved high-speed cellular movement! Efficient locomotion is crucial for finding resources and avoiding threats.",
        "trigger": "high_speed",
        "threshold": 500,
        "category": "Biophysics",
        "educational_note": "Cellular movement mechanisms include flagella, cilia, and pseudopod formation.",
        "url": "https://www.khanacademy.org/science/biology/cells-and-organelles"
    },
    "survivor": {
        "title": "Survival Specialist",
        "description": "Survived for an extended period in harsh conditions! Adaptation and resilience are key to evolutionary success.",
        "trigger": "survival_time",
        "threshold": 300,
        "category": "Evolution",
        "educational_note": "Organisms that survive changing conditions pass their traits to offspring.",
        "url": "https://www.khanacademy.org/science/biology/her/evolution-and-natural-selection"
    },
    "mitochondria_discovery": {
        "title": "Mitochondrial Powerhouse",
        "description": "Your cell has developed mitochondria — the energy-generating organelles responsible for powering life through respiration!",
        "trigger": "create_organelle",
        "target": {"organelle": "Mitochondria"},
        "category": "Cell Biology",
        "educational_note": "Mitochondria convert glucose and oxygen into ATP, the primary energy currency of the cell. They originated from symbiotic bacteria.",
        "url": "https://www.khanacademy.org/science/biology/cellular-respiration"
    },
    "nucleus_formation": {
        "title": "Birth of the Nucleus",
        "description": "You’ve evolved a nucleus — a protective structure that safely houses genetic material and controls cellular processes.",
        "trigger": "create_organelle",
        "target": {"organelle": "Nucleus"},
        "category": "Genetics",
        "educational_note": "The nucleus is a defining feature of eukaryotic cells, separating DNA from the cytoplasm and allowing complex regulation of gene expression.",
        "url": "https://www.khanacademy.org/science/biology/cell-structure-and-function"
    },
    "er_creation": {
        "title": "Endoplasmic Reticulum Formed",
        "description": "Your cell has evolved an endoplasmic reticulum — a folded network that assists in protein and lipid synthesis.",
        "trigger": "create_organelle",
        "target": {"organelle": "Endoplasmic Reticulum"},
        "category": "Cell Biology",
        "educational_note": "The ER is divided into rough (protein synthesis) and smooth (lipid production) regions, essential for complex cellular functions.",
        "url": "https://www.khanacademy.org/science/biology/cells-and-organelles"
    },
    "golgi_formation": {
        "title": "Golgi Apparatus Evolution",
        "description": "A Golgi apparatus has formed within your cell, packaging and modifying proteins for transport — the cellular shipping center.",
        "trigger": "create_organelle",
        "target": {"organelle": "Golgi Apparatus"},
        "category": "Cell Biology",
        "educational_note": "The Golgi apparatus works closely with the ER to process and distribute proteins and lipids throughout the cell.",
        "url": "https://www.khanacademy.org/science/biology/cells-and-organelles"
    },
    "lysosome_discovery": {
        "title": "Lysosomal Development",
        "description": "Your cell can now produce lysosomes — specialized vesicles that digest waste and destroy invaders.",
        "trigger": "create_organelle",
        "target": {"organelle": "Lysosome"},
        "category": "Cell Biology",
        "educational_note": "Lysosomes contain enzymes that break down old cell parts and pathogens, acting as the cell’s recycling and defense system.",
        "url": "https://www.khanacademy.org/science/biology/cells-and-organelles"
    },
    "protein_core_discovery": {
        "title": "Formation of Protein Core",
        "description": "Your cell has synthesized its first structural protein — the backbone of cellular integrity.",
        "trigger": "create_protein",
        "target": {"protein": "Protein Core"},
        "category": "Structural Biology",
        "educational_note": "Protein cores provide the basic framework for cells, maintaining shape and internal stability under environmental stress.",
        "url": "https://www.hhmi.org/biointeractive"
    },
    "elastin_protein_discovery": {
        "title": "Elastic Bonds Formed",
        "description": "You’ve evolved the ability to produce elastin — flexible protein fibers that let cells stretch and connect dynamically.",
        "trigger": "create_protein",
        "target": {"protein": "Elastin Protein"},
        "category": "Structural Biology",
        "educational_note": "Elastin provides flexibility to tissues such as skin and blood vessels, allowing them to return to shape after stretching.",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK557685/"
    },
    "collagen_protein_discovery": {
        "title": "Collagen Framework Synthesized",
        "description": "Your cell can now produce collagen — the toughest structural protein known, ideal for forming durable cellular links.",
        "trigger": "create_protein",
        "target": {"protein": "Collagen Protein"},
        "category": "Structural Biology",
        "educational_note": "Collagen forms strong, fibrous networks that support cell integrity and are vital in connective tissues.",
        "url": "https://www.nature.com/scitable/topicpage/collagen-the-protein-that-holds-us-together-1478/"
    },

    # === ENZYMES ===
    "enzyme_discovery": {
        "title": "Catalytic Enzymes Emerge",
        "description": "You’ve synthesized enzymes — specialized proteins that catalyze biochemical reactions within your cell.",
        "trigger": "create_protein",
        "target": {"protein": "Enzymes"},
        "category": "Biochemistry",
        "educational_note": "Enzymes speed up chemical reactions by lowering activation energy, enabling life-sustaining metabolic processes.",
        "url": "https://www.khanacademy.org/science/biology/energy-and-enzymes"
    },
    "receptor_discovery": {
        "title": "Signal Receptors Developed",
        "description": "Your cell has evolved receptors that can detect and respond to environmental signals.",
        "trigger": "create_protein",
        "target": {"protein": "Receptors"},
        "category": "Cell Communication",
        "educational_note": "Receptors bind to signaling molecules, triggering cellular responses — a key step toward nervous system evolution.",
        "url": "https://www.hhmi.org/biointeractive/cell-communication"
    },

    # === ATTACK PROTEINS ===
    "protein_cannon_discovery": {
        "title": "Offensive Proteins Assembled",
        "description": "You’ve developed the Protein Cannon — a molecular launcher capable of firing protein projectiles at enemies.",
        "trigger": "create_protein",
        "target": {"protein": "Protein Cannon"},
        "category": "Cellular Combat",
        "educational_note": "Cells can use specialized proteins to release toxins or projectiles — an early form of biological defense and offense.",
        "url": "https://www.nature.com/scitable/topicpage/immune-system-introduction-122/"
    },
    "protein_bomb_discovery": {
        "title": "Reactive Protein Cluster",
        "description": "Your cell has evolved the Protein Bomb — unstable molecules that detonate upon detecting threats.",
        "trigger": "create_protein",
        "target": {"protein": "Protein Bomb"},
        "category": "Cellular Combat",
        "educational_note": "Reactive proteins can cause oxidative stress in rival cells — mimicking immune system attack mechanisms.",
        "url": "https://www.nature.com/scitable/topicpage/reactive-oxygen-species-and-oxidative-stress-14234123/"
    },
    "protein_burst_discovery": {
        "title": "Explosive Protein Wave",
        "description": "You’ve created the Protein Burst — an area-wide detonation that damages nearby enemies.",
        "trigger": "create_protein",
        "target": {"protein": "Protein Burst"},
        "category": "Cellular Combat",
        "educational_note": "Mass protein release is similar to degranulation in immune cells, where enzymes and toxins are expelled to neutralize invaders.",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK26827/"
    },
    "molecular_drill_discovery": {
        "title": "Molecular Drill Constructed",
        "description": "You’ve engineered a spiraling protein drill capable of piercing enemy membranes.",
        "trigger": "create_protein",
        "target": {"protein": "Molecular Drill"},
        "category": "Nanobiology",
        "educational_note": "Some bacterial systems use similar rotary mechanisms to penetrate cell membranes — precursors to modern flagella motors.",
        "url": "https://www.khanacademy.org/science/biology/cells/cell-membranes/a/fluid-mosaic-model-of-cell-membranes"
    },
    "enzyme_strike_discovery": {
        "title": "Enzyme Weaponization",
        "description": "You’ve developed Enzyme Strike — corrosive enzymes that dissolve enemy barriers and weaken foes.",
        "trigger": "create_protein",
        "target": {"protein": "Enzyme Strike"},
        "category": "Biochemical Warfare",
        "educational_note": "Certain immune cells use lytic enzymes to digest pathogen walls, demonstrating the power of enzyme-based attacks.",
        "url": "https://www.nature.com/scitable/topicpage/how-do-antibiotics-work-14321465/"
    },

    # === DEFENSE PROTEINS ===
    "spike_discovery": {
        "title": "Protective Spikes Formed",
        "description": "You’ve synthesized sharp protein spikes that deter predators and provide basic protection.",
        "trigger": "create_protein",
        "target": {"protein": "Spikes"},
        "category": "Cell Defense",
        "educational_note": "Protein-based spikes mimic bacterial pili and viral capsid protrusions that enhance defense and attachment.",
        "url": "https://www.hhmi.org/biointeractive/virus-structure"
    },
    "barrier_matrix_discovery": {
        "title": "Barrier Matrix Developed",
        "description": "You’ve created a regenerative protein barrier that absorbs damage and shields the cell.",
        "trigger": "create_protein",
        "target": {"protein": "Barrier Matrix"},
        "category": "Cell Defense",
        "educational_note": "Cells can form dynamic protein barriers, analogous to the extracellular matrix, for enhanced protection and repair.",
        "url": "https://www.nature.com/scitable/topicpage/extracellular-matrix-14064239/"
    },
    "adhesion_web_discovery": {
        "title": "Adhesion Web Spun",
        "description": "Your cell now secretes sticky protein webs that immobilize enemies and slow movement.",
        "trigger": "create_protein",
        "target": {"protein": "Adhesion Web"},
        "category": "Cell Defense",
        "educational_note": "Adhesive proteins function like natural bio-glues, essential for wound healing and microbial trapping.",
        "url": "https://www.khanacademy.org/science/biology/cells/cell-membranes/a/cell-cell-junctions"
    },
    "resonance_shield_discovery": {
        "title": "Resonance Shield Activated",
        "description": "You’ve evolved a vibrating protein shield that absorbs incoming energy through resonance.",
        "trigger": "create_protein",
        "target": {"protein": "Resonance Shield"},
        "category": "Cell Defense",
        "educational_note": "Protein vibrations can dissipate energy at the molecular level — similar to shock absorption mechanisms in biological materials.",
        "url": "https://www.nature.com/scitable/topicpage/biomaterials-and-biomechanics-14468367/"
    },
    "chitin_armor_discovery": {
        "title": "Chitin Armor Evolved",
        "description": "You’ve created a hardened protein armor that forms a durable exoskeleton around your cell.",
        "trigger": "create_protein",
        "target": {"protein": "Chitin Armor"},
        "category": "Structural Biology",
        "educational_note": "Chitin is a protein-polysaccharide composite used in fungi and insects for strength and flexibility.",
        "url": "https://www.hhmi.org/biointeractive/cell-walls-and-chitin"
    }
}