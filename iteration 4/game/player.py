import pygame, math, random
from config import LIPID_COUNT, CELL_RADIUS, MINT
from molecule import Lipid
from entity import SoftBody, Spring, Point, Cell


class PlayerCell(Cell):
    def unequip_protein(self, protein):
        return super().unequip_protein(protein)
    def __init__(self, pos, points=12, radius=CELL_RADIUS):
        # --- Base Cell Initialization ---
        super().__init__(pos, points, radius, Lipid)

        self.body_color = MINT

        self.membrane_molecule = Lipid

        # Player flag
        self.is_player = True  

        # Physics
        self.velocity = pygame.Vector2()

        self.friction     = 5    # Increased for seconds-based delta_time
        self.max_speed    = 100   # Increased for seconds-based delta_time
        self.slowdown_distance = 150


        # Core stats
        self.radius   = radius
        self.health   = 100
        self.center   = self.pos.copy()

        # Targeting (for input/movement)
        #self.initial_pos = pygame.Vector2(pos)
        self.target_pos  = pygame.Vector2(pos)

        # Visual
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 200, 255), (radius, radius), radius)

        # Only store equipped items
        self.organelle_slots = [None] * 10
        self.protein_inventory = []

        # ATP system
        self.max_atp = 100.0
        self.atp = self.max_atp
        self.ATP_DRAIN_PER_ORGANELLE = 0.01

        # Invincibility system for demo mode
        self.invincible_until = 0.0  # Timestamp when invincibility expires

        # Base attributes (permanent stats)
        self.base_attributes = {
            'Strength': 100,     # Physical power and damage
            'Dexterity': 0,    # Speed and precision
            'Endurance': 0,    # Health and stamina
            'Intelligence': 0   # Special abilities and effectiveness
        }
        
        # Current attributes (includes base + upgrades)
        self.attributes = self.base_attributes.copy()

    # ------------------- EQUIP -------------------

    def equip_organelle(self, slot_index, organelle):
        if 0 <= slot_index < len(self.organelle_slots):
            # Remove from central inventory
            from main import player_upgrades
            if organelle in player_upgrades["Organelles"]:
                player_upgrades["Organelles"].remove(organelle)
            self.organelle_slots[slot_index] = organelle
            print(f"Equipped {organelle.name} in slot {slot_index}")

    def equip_protein(self, protein):
        # Call parent class's equip_protein method
        if super().equip_protein(protein):
            print(f"Equipped protein - {protein.name}")
            return True
        return False

    # ------------------- ATP -------------------

    def drain_atp(self):
        count = sum(1 for o in self.organelle_slots if o) + len(self.protein_inventory)
        self.atp -= count * self.ATP_DRAIN_PER_ORGANELLE
        self.atp = max(self.atp, 0)

    def can_act(self):
        return self.atp > 0

    # ------------------- UPGRADES -------------------

    def apply_upgrades(self):
        # Start with base attributes
        self.attributes = self.base_attributes.copy()

        # Apply boosts from equipped proteins
        for protein in self.protein_inventory:
            for boost in getattr(protein, "boosts", []):
                if boost["type"] in self.attributes:  # Only apply if it's a valid attribute
                    self.attributes[boost["type"]] += boost["amount"]
        # Apply boosts from equipped organelles
        for organelle in self.organelle_slots:
            if organelle:  # Skip empty slots
                for boost in getattr(organelle, "boosts", []):
                    if boost["type"] in self.attributes:  # Only apply if it's a valid attribute
                        self.attributes[boost["type"]] += boost["amount"]

    # ------------------- ECONOMY -------------------

    def can_afford(self, cost: dict) -> bool:
        from main import player_molecules
        return all(player_molecules.get(k, 0) >= v for k, v in cost.items())

    def buy_upgrade(self, item: dict, category: str = "Organelles") -> bool:
        if not self.can_afford(item.get("cost", {})):
            return False
        from main import player_molecules, player_upgrades
        for k, v in item["cost"].items():
            player_molecules[k] -= v
        player_upgrades[category].append(item)
        print(f"Purchased {item['name']} in {category}")
        return True

    # ------------------- GAME LOOP -------------------

    def update(self, surface, events, delta_time, camera):
        super().update(surface, events, delta_time, camera)

        # Handle mouse input for movement
        # for event in events:
        #     if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
        #         self.target_pos = camera.screen_to_world(pygame.mouse.get_pos())

        # Calculate movement vector
        force = pygame.Vector2()
        if self.can_act():
            direction = self.target_pos - self.center
            if direction.length_squared() > 0.1:  # Add small threshold
                #self.velocity = direction.normalize() * self.max_speed
                strength = math.atan(direction.length_squared()/self.slowdown_distance)*self.max_speed
                force = direction.normalize() * strength

        self.velocity += (force-self.friction*self.velocity) * delta_time#/total mass of cell if u want it to look cool
    
        self.apply_global_displacement(self.velocity * delta_time)

    def take_damage(self, damage, current_time, attacker=None):
        """Override take_damage to handle invincibility for demo mode"""
        # Check if cell is currently invincible
        if current_time < self.invincible_until:
            print(f"Player cell is invincible! Damage blocked: {damage:.1f}")
            return  # No damage taken while invincible
        
        # Call parent take_damage method if not invincible
        super().take_damage(damage, current_time, attacker)

        

        # Update base cell behavior
