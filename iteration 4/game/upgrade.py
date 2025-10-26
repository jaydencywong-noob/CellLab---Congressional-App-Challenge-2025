import hashlib
import random
import pygame
from config import TYPE_CODON_MAP
from collections import Counter, defaultdict

pygame.init()

# --- Miscleanienoius things

def get_contrasting_color(color):
    r, g, b = color
    luminance = (r * 299 + g * 587 + b * 114) / 1000
    return (0, 0, 0) if luminance > 128 else (255, 255, 255)

def generate_protein_icon(structure, size=40):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    fold_colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200), (200, 200, 50), (200, 50, 200)]
    for i, fold in enumerate(structure.get("folds", [])):
        x = 8 + i * 6
        y = 8 + fold * 6
        pygame.draw.circle(surf, fold_colors[i % len(fold_colors)], (x, y), 5)
    binding_map = {'A': (255, 0, 0), 'B': (0, 255, 0), 'C': (0, 0, 255), 'D': (255, 255, 0)}
    for i, site in enumerate(structure.get("binding_sites", [])):
        color = binding_map.get(site, (150, 150, 150))
        x = size - 12
        y = 8 + i * 10
        pygame.draw.rect(surf, color, (x, y, 8, 8))
    charge = structure.get("charge", 0)
    if charge > 0.3:
        border_color = (100, 255, 255)
    elif charge < -0.3:
        border_color = (255, 100, 100)
    else:
        border_color = (180, 180, 180)
    pygame.draw.rect(surf, border_color, (0, 0, size, size), 2)
    return surf

def generate_static_icon(color, symbol=None, size=40):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (4, 4, size-8, size-8), border_radius=8)

    if symbol:
        # pick a contrasting color
        text_color = get_contrasting_color(color)

        font = pygame.font.SysFont("calibri", 20, bold=True)
        txt = font.render(symbol, True, text_color)
        rect = txt.get_rect(center=(size // 2, size // 2))
        surf.blit(txt, rect)

    return surf

# --- Algorithm things ---
def get_quality_descriptor(boost):
    # Nonlinear tiers: higher boosts needed for higher quality
    if boost < 25:
        tier = "x1"
    elif boost < 50:
        tier = "x2"
    elif boost < 75:
        tier = "x3"
    elif boost < 125:
        tier = "x4"
    else:
        tier = "x5"

    tiers_map = {
        "x1": ["Mediocre", "Poor", "Misfolded", "Malformed"],
        "x2": ["Decent", "Good", "Functional"],
        "x3": ["Fine", "Great", "Rare", "High-Grade"],
        "x4": ["Refined", "Elite", "Exceptional"],
        "x5": ["Mythic", "Legendary", "Transcendent"]
    }

    return random.choice(tiers_map[tier])

def parse_codons(sequence):
    return [sequence[i:i+3] for i in range(0, len(sequence) - 2, 3)]

def compute_balance_metrics(codons, type_map):
    types = []
    boost_totals = Counter()
    for codon in codons:
        entry = type_map.get(codon)
        if entry:
            t = entry["type"]
            types.append(t)
            boost_totals[t] += entry["boost"]
        else:
            types.append("Existence")
    return boost_totals, len(set(types))

def compute_stats(codon, type_map):
    entry = type_map.get(codon)
    if not entry:
        return 0, 0
    return entry["boost"], entry["duration"]

def generate_protein_desc(sequence, type_map):
    codons = parse_codons(sequence)
    if not codons:
        return "Invalid sequence."

    durations = []
    boost_types = []
    for codon in codons:
        entry = type_map.get(codon)
        if entry:
            durations.append(entry["duration"])
            if not entry["type"] in boost_types:
                boost_types.append(entry["type"])

    if not durations:
        return "No valid codons found."

    avg_duration = sum(durations) / len(durations)
    complexity_penalty = max(0, 3**(len(codons)-1) + 8.5**(len(boost_types)-1))  # Reduce 1s per extra codon and 60^total boost types.
    total_duration = max(0, int(avg_duration * len(codons) - complexity_penalty))

    return (
        f"This protein enhances your cell’s performance across {len(set(type_map[c]['type'] for c in codons if c in type_map))} traits, "
        f"with a balanced duration of approximately {total_duration} seconds."
    )

def generate_protein_boosts(sequence, type_map):
    codons = parse_codons(sequence)
    boost_data = defaultdict(list)

    for codon in codons:
        entry = type_map.get(codon)
        if entry:
            t = entry["type"]
            boost_data[t].append((entry["boost"], entry["duration"]))

    output = []
    for t, values in boost_data.items():
        total_boost = sum(v[0] for v in values)
        avg_duration = int(sum(v[1] for v in values) / len(values))
        output.append({"type": t, "amount": total_boost, "duration": avg_duration})

    return output

def generate_protein_name(sequence, type_map):
    codons = parse_codons(sequence)
    type_boosts = defaultdict(int)

    for codon in codons:
        entry = type_map.get(codon)
        if entry:
            t = entry["type"]
            type_boosts[t] += entry["boost"]

    if not type_boosts:
        return "Unstable NullFactor"

    max_boost = max(type_boosts.values())
    count_descriptor = get_quality_descriptor(max_boost)

    sorted_types = sorted(type_boosts.items(), key=lambda x: (-x[1], x[0]))
    fragments = [f"{t.capitalize()} (+{b})" for t, b in sorted_types[:3]]

    return f"{count_descriptor} {'-'.join(fragments)} Protein"

def craft_protein(player, sequence):
    name = generate_protein_name(sequence, TYPE_CODON_MAP)
    desc = generate_protein_desc(sequence, TYPE_CODON_MAP)
    boosts = generate_protein_boosts(sequence, TYPE_CODON_MAP)
    protein = CraftedProteinUpgrade(sequence, desc, boosts, name)
    #player.upgrades.setdefault("Custom", []).append(protein)
    if "Crafted Proteins" not in player.upgrades:
        player.upgrades["Crafted Proteins"] = []
    player.upgrades["Crafted Proteins"].append(protein)
    return protein

# --- Shop Things ---

def can_afford(player, item):
    for resource, amount in item["cost"].items():
        if player.molecules.get(resource, 0) < amount:
            return False
    return True

def buy_protein(player, protein_info, free=False):
    # protein_info: dict with keys 'name', 'desc', 'color', 'symbol'
    if not can_afford(player, protein_info) and not free:
        print("Cannot afford protein:", protein_info['name'])
        return None

    if not free:
        for res_type, amount in protein_info["cost"].items():
            player.molecules[res_type] -= amount

    protein = BuyableProteinUpgrade(
        protein_info['name'],
        protein_info.get('desc', '') or protein_info.get('desc', ''),
        protein_info['boosts'],
        protein_info.get('color', (100, 180, 255)),
        protein_info.get('symbol', None)
    )
    
    # Add to central inventory
    from main import player_upgrades
    player_upgrades["Proteins"].append(protein)
    return protein

def buy_organelle(player, organelle_info, free=False):
    # organelle_info: dict with keys 'name', 'boost_type', 'boost_amount', 'color', 'symbol'
    if not can_afford(player, organelle_info) and not free:
        print("Cannot afford organelle:", organelle_info['name'])
        return None

    if not free:
        for res_type, amount in organelle_info["cost"].items():
            player.molecules[res_type] -= amount

# Cell Membrane Extender is now handled in the equip_organelle method
    
    organelle = OrganelleUpgrade(
        organelle_info['name'],
        organelle_info.get('desc', '') or organelle_info.get('desc', ''),
        organelle_info['boosts'],
        organelle_info.get('color', (180, 255, 100)),
        organelle_info.get('symbol', None)
    )

    # Add to central inventory
    from main import player_upgrades
    player_upgrades["Organelles"].append(organelle)
    return organelle

class Upgrade:
    def __init__(self, name, desc, category, icon=None):
        self.name = name
        self.desc = desc
        self.category = category
        self.icon = icon

    def draw_icon(self, surface, pos):
        if self.icon:
            surface.blit(self.icon, pos)
        else:
            pygame.draw.rect(surface, (200, 200, 200), (*pos, 40, 40))

# --- Protein Upgrades ---

class CraftedProteinUpgrade(Upgrade):
    def __init__(self, nucleotide_sequence, desc, boosts, name=None):
        self.sequence = nucleotide_sequence.upper()
        self.structure_data = self.generate_structure(self.sequence)
        name = name or f"Protein-{self.sequence[:3]}"
        self.boosts = boosts
        desc = desc
        icon = generate_protein_icon(self.structure_data)
        super().__init__(name, desc, "Crafted Proteins", icon=icon)

    def generate_structure(self, sequence):
        hash_val = hashlib.sha256(sequence.encode()).hexdigest()
        random.seed(int(hash_val[:8], 16))
        structure = {
            "folds": [random.randint(0, 4) for _ in range(5)],
            "binding_sites": [random.choice(['A', 'B', 'C', 'D']) for _ in range(3)],
            "charge": random.uniform(-1.0, 1.0),
        }
        return structure

class BuyableProteinUpgrade(Upgrade):
    def __init__(self, name, desc, boosts, color=(100, 180, 255), symbol=None):
        desc = desc
        icon = generate_static_icon(color, symbol)
        super().__init__(name, desc, "Proteins", icon=icon)
        self.boosts = boosts

# --- Organelle Upgrades ---

class OrganelleUpgrade(Upgrade):
    def __init__(self, name, desc, boosts, color=(180, 255, 100), symbol=None):
        #desc = f"Boosts {boost_type} by {boost_amount}."
        icon = generate_static_icon(color, symbol)
        super().__init__(name, desc, "Organelles", icon=icon)
        self.boosts = boosts


