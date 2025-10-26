import pygame
import math
import random
from math import cos, sin, pi
from entity import Entity
from molecule import Protein

# Movement types for entities
MOVEMENT_DASHING = "dashing"
MOVEMENT_GLIDING = "gliding"  
MOVEMENT_CHARGING = "charging"

# Behavior types for entities
BEHAVIOR_NEUTRAL = "neutral"
BEHAVIOR_AGGRESSIVE = "aggressive"

class Virus(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 50, 50), (10, 10), 10)
        self.molecules = []  # List of Protein objects
        self.center = self.pos.copy()
        self.radius = 10
        
        # Core stats - Base values (viruses have high strength, low endurance)
        from config import BASE_VIRUS_STATS
        self.base_strength = BASE_VIRUS_STATS['strength']
        self.base_endurance = BASE_VIRUS_STATS['endurance']
        self.base_dexterity = BASE_VIRUS_STATS['dexterity']
        self.base_intelligence = BASE_VIRUS_STATS['intelligence']
        
        # Health system
        self.max_health = 50 + (self.base_endurance * 3)  # +3 HP per endurance
        self.health = self.max_health
        
        # Initialize with base attributes (bonus stats from upgrades/abilities)
        self.attributes = {
            'Strength': 0,     # Physical power and damage
            'Dexterity': 0,    # Speed and precision
            'Endurance': 0,    # Health and stamina
            'Intelligence': 0   # Special abilities and effectiveness
        }
        
        # Combat and targeting system
        from config import VIRUS_VIEW_RANGE
        self.view_range = VIRUS_VIEW_RANGE  # Fixed view range for viruses
        self.target = None  # Current target entity
        self.behavior = BEHAVIOR_AGGRESSIVE  # Viruses are always aggressive
        self.movement_type = MOVEMENT_GLIDING  # Default movement pattern
        self.can_target_all_cell_types = True  # Viruses can target any cell type
        
        # Movement state variables
        self.velocity = pygame.Vector2(0, 0)
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.charge_timer = 0
        self.charge_target_pos = None
        self.is_charging = False
        
        # Attack cooldown system
        self.last_attack_time = 0
        self.attack_cooldown = 1.0  # 1 second between virus attacks
        
        # Damage tracking for regeneration (optional but recommended)
        self.last_damage_time = 0

    def take_damage(self, damage, current_time, attacker=None):
        """
        Deal damage to the virus and update last damage time
        
        Args:
            damage: Amount of damage to deal
            current_time: Current game time in seconds
            attacker: Entity that dealt the damage (optional, for future use)
        """
        self.health = max(0, self.health - damage)
        self.last_damage_time = current_time
        
        # Optional: Track who damaged us for AI behavior
        # Could make viruses more aggressive toward attacker
        if attacker and hasattr(self, 'target'):
            # Viruses could prioritize the attacker
            pass

    def find_nearest_target(self, all_cells):
        """Find the nearest cell within view range"""
        if not all_cells:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for cell in all_cells:
            # Check if we can target this type of cell
            if not self.can_target_all_cell_types and getattr(cell, 'is_player', False):
                continue  # Skip if we can only target players and this isn't one
                
            distance = self.pos.distance_to(cell.center)
            if distance <= self.view_range and distance < min_distance:
                min_distance = distance
                nearest = cell
                
        return nearest

    def update_movement(self, delta_time):
        """Update position based on movement type and target"""
        if self.movement_type == MOVEMENT_DASHING:
            self._update_dashing_movement(delta_time)
        elif self.movement_type == MOVEMENT_GLIDING:
            self._update_gliding_movement(delta_time)
        elif self.movement_type == MOVEMENT_CHARGING:
            self._update_charging_movement(delta_time)
            
        # Update center position for targeting
        self.center = self.pos.copy()

    def _update_dashing_movement(self, delta_time):
        """Dash-based movement pattern"""
        self.dash_cooldown -= delta_time
        
        if self.dash_cooldown <= 0 and self.target:
            # Start a new dash towards target
            direction = (self.target.center - self.pos).normalize() if self.target else pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.velocity = direction * 150  # High dash speed
            self.dash_timer = 0.5  # Dash duration
            self.dash_cooldown = 2.0  # Cooldown between dashes
        
        if self.dash_timer > 0:
            # Continue dashing
            self.pos += self.velocity * delta_time
            self.dash_timer -= delta_time
        else:
            # Not dashing, gradually slow down
            self.velocity *= 0.95
            self.pos += self.velocity * delta_time

    def _update_gliding_movement(self, delta_time):
        """Constant speed gliding movement"""
        if self.target:
            direction = (self.target.center - self.pos).normalize()
            speed = 50  # Constant gliding speed
            self.pos += direction * speed * delta_time
        else:
            # Random wandering if no target
            if random.random() < 0.1:  # Change direction occasionally
                self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 20
            self.pos += self.velocity * delta_time

    def _update_charging_movement(self, delta_time):
        """Charging movement with cooldown cycles"""
        if self.target and not self.is_charging and self.charge_timer <= 0:
            # Start charging at target position
            self.charge_target_pos = self.target.center.copy()
            self.is_charging = True
            self.charge_timer = 1.5  # Charge duration
            
        if self.is_charging and self.charge_target_pos:
            # Move towards charge target
            direction = (self.charge_target_pos - self.pos)
            distance = direction.length()
            if distance > 5:
                direction = direction.normalize()
                speed = 100  # Charge speed
                self.pos += direction * speed * delta_time
            else:
                # Reached target, start cooldown
                self.is_charging = False
                self.charge_timer = 2.0  # Cooldown period
        elif self.charge_timer > 0:
            # Cooldown period
            self.charge_timer -= delta_time

    def update(self, all_cells, delta_time):
        """Main update method for viruses"""
        # Find target if aggressive
        if self.behavior == BEHAVIOR_AGGRESSIVE:
            self.target = self.find_nearest_target(all_cells)
        
        # Update movement
        self.update_movement(delta_time)
        
        # Update molecule positions
        for molecule in self.molecules:
            if hasattr(molecule, 'parent') and molecule.parent == self:
                # Keep molecules relative to virus position
                pass  # Specific virus classes handle this

    def draw(self, surface, camera):
        for molecule in self.molecules:
            molecule.draw(surface, camera)
    
    def attack_cell(self, target_cell, current_time):
        """Handle virus attacking a cell"""
        # Check attack cooldown
        if current_time - self.last_attack_time < self.attack_cooldown:
            return False  # Attack on cooldown
            
        from config import VIRUS_DAMAGE_HIGH_HEALTH, VIRUS_INSTANT_DEATH_CHANCE, VIRUS_SPAWN_ON_KILL
        from entity import calculate_incoming_damage
        import random
        
        # Update attack time
        self.last_attack_time = current_time
        
        # Check for instant death first (5% chance)
        if random.random() < VIRUS_INSTANT_DEATH_CHANCE:
            print(f"Virus instant kill!")
            return self.kill_cell_and_spawn_viruses(target_cell)
        
        health_percentage = target_cell.health / target_cell.max_health
        
        if health_percentage > 0.25:
            # High health: deal damage and consume molecules
            raw_damage = target_cell.max_health * VIRUS_DAMAGE_HIGH_HEALTH
            final_damage, combat_info = calculate_incoming_damage(raw_damage, self, target_cell)
            target_cell.take_damage(final_damage, current_time, attacker=self)
            
            # Consume molecules from central inventory
            self.consume_molecules_from_inventory()
            
            # Combat feedback
            feedback = f"Virus dealt {final_damage:.1f} damage"
            if combat_info['dodged']:
                feedback += " (DODGED)"
            elif combat_info['critical']:
                feedback += " (CRITICAL HIT!)"
            print(f"{feedback} to cell (health: {target_cell.health:.1f}/{target_cell.max_health})")
            return False  # Cell survived
        else:
            # Low health: instant death
            print(f"Virus killed weakened cell!")
            return self.kill_cell_and_spawn_viruses(target_cell)
    
    def consume_molecules_from_inventory(self):
        """Consume molecules from the central player inventory"""
        from main import player_molecules
        
        # Consume a small amount of random molecules
        consume_amount = 5  # Tunable parameter
        molecule_types = ['protein', 'lipid', 'carbohydrate', 'nucleic_acid']
        
        for _ in range(consume_amount):
            mol_type = random.choice(molecule_types)
            if player_molecules.get(mol_type, 0) > 0:
                player_molecules[mol_type] -= 1
        
        print(f"Virus consumed {consume_amount} molecules from inventory")
    
    def kill_cell_and_spawn_viruses(self, target_cell):
        """Kill the target cell and spawn new viruses"""
        from config import VIRUS_SPAWN_ON_KILL
        
        # Mark cell for death
        target_cell.health = 0
        
        # Spawn new viruses at the cell's location
        spawn_pos = target_cell.center.copy()
        
        # Store spawn data to be processed by main loop
        # Import here to avoid circular imports
        import main
        for _ in range(VIRUS_SPAWN_ON_KILL):
            offset = pygame.Vector2(random.randint(-20, 20), random.randint(-20, 20))
            main.pending_virus_spawns.append({
                'type': type(self),
                'pos': spawn_pos + offset,
                'size': getattr(self, 'structure_radius', 20)
            })
        
        return True  # Cell was killed

class CapsidVirus(Virus):
    def __init__(self, pos, radius, points):
        super().__init__(pos)
        # Custom image for CapsidVirus
        self.molecules = []
        
        # Capsid viruses are aggressive and can have different movement patterns
        self.movement_type = random.choice([MOVEMENT_DASHING, MOVEMENT_GLIDING, MOVEMENT_CHARGING])
        # View range is already set in parent class
        
        # Create the capsid structure
        self.structure_radius = radius
        self.structure_points = points
        for i in range(points):
            angle = 2 * pi * i / points
            # Use self.pos which is guaranteed to be a pygame.Vector2
            x = self.pos.x + radius * cos(angle)
            y = self.pos.y + radius * sin(angle)
            self.molecules.append(Protein((x, y), parent=self))

    def update(self, all_cells, delta_time):
        """Update capsid virus with aggressive behavior"""
        # Call parent update for targeting and movement
        super().update(all_cells, delta_time)
        
        # Update molecule positions to maintain capsid structure
        for i, molecule in enumerate(self.molecules):
            if i < self.structure_points:
                angle = 2 * pi * i / self.structure_points
                offset_x = self.structure_radius * cos(angle)
                offset_y = self.structure_radius * sin(angle)
                molecule.pos = pygame.Vector2(self.pos.x + offset_x, self.pos.y + offset_y)

class FilamentousVirus(Virus):
    """Long rod-like virus (cylindrical filament)."""
    def __init__(self, pos, length=120, spacing=8, radius=30):
        super().__init__(pos)
        self.molecules = []

        self._t = random.uniform(0, 1000)  # phase offset for sine wave
        
        # Filamentous viruses are slow and always glide
        self.movement_type = MOVEMENT_GLIDING
        # View range is set in parent class
        
        # Store structure info
        self.length = length
        self.spacing = spacing

        # line of proteins centered at pos
        start_x = self.pos.x - length // 2
        for i in range(0, length, spacing):
            p = Protein((start_x + i, self.pos.y), parent=self)
            self.molecules.append(p)

    def update(self, player_cells, delta_time):
        """Update filamentous virus with slow gliding movement"""
        # Call parent update but override movement for sine wave pattern
        if self.behavior == BEHAVIOR_AGGRESSIVE:
            self.target = self.find_nearest_target(player_cells)
        
        # Sine wave movement (slow and constant)
        self._t += delta_time
        amplitude = 20  # Reduced amplitude
        freq = 0.8      # Reduced frequency
        
        if self.target:
            # Move towards target with sine wave pattern
            direction = (self.target.center - self.pos).normalize()
            speed = 25  # Slow movement
            base_movement = direction * speed * delta_time
            
            # Add sine wave oscillation perpendicular to movement
            perpendicular = pygame.Vector2(-direction.y, direction.x)
            oscillation = perpendicular * math.sin(self._t * freq) * amplitude * delta_time
            
            self.pos += base_movement + oscillation
        else:
            # Default sine wave wandering
            self.pos.y += math.sin(self._t * freq) * 1.0
            self.pos.x += math.cos(self._t * freq) * 0.3
        
        # Update center
        self.center = self.pos.copy()
        
        # Update molecule positions to maintain filament structure
        start_x = self.pos.x - self.length // 2
        for i, molecule in enumerate(self.molecules):
            molecule.pos = pygame.Vector2(start_x + i * self.spacing, self.pos.y)
        

class PhageVirus(Virus):
    """Bacteriophage with icosahedral head + tail fibers."""
    def __init__(self, pos, radius=30, points=12):
        super().__init__(pos)
        self.molecules = []

        # Phage viruses don't move, they drift passively
        self.movement_type = None  # Special case for passive drift
        self.view_range = 0  # Don't target anything
        self.behavior = BEHAVIOR_NEUTRAL  # Passive
        
        # Passive drift variables
        self.drift_velocity = pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
        self.drift_timer = 0
        
        # Store structure info
        self.head_radius = radius
        self.head_points = points
        self.tail_length = 50
        self.tail_spacing = 10

        # --- Icosahedral head (circle approximation) ---
        for i in range(points):
            angle = 2 * math.pi * i / points
            x = self.pos.x + radius * math.cos(angle)
            y = self.pos.y + radius * math.sin(angle)
            self.molecules.append(Protein((x, y), parent=self))

        # --- Tail shaft (straight line downwards) ---
        tail_segments = self.tail_length // self.tail_spacing
        for i in range(1, tail_segments + 1):
            x = self.pos.x
            y = self.pos.y + self.head_radius + i * self.tail_spacing
            self.molecules.append(Protein((x, y), parent=self))

        # --- Tail fibers (short diagonals at bottom) ---
        fiber_length = 20
        angles = [math.radians(a) for a in (45, 135, -45, -135)]
        base = pygame.Vector2(self.pos.x, self.pos.y + self.head_radius + self.tail_length)
        for angle in angles:
            dx, dy = fiber_length * math.cos(angle), fiber_length * math.sin(angle)
            fiber_pos = (base.x + dx, base.y + dy)
            self.molecules.append(Protein(fiber_pos, parent=self))

    def update(self, all_cells, delta_time):
        """Update phage virus with passive drift movement"""
        # Phage viruses drift passively, no targeting
        self.drift_timer += delta_time
        
        # Change drift direction occasionally
        if self.drift_timer > 5.0:  # Every 5 seconds
            self.drift_velocity = pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
            self.drift_timer = 0
        
        # Apply drift movement
        self.pos += self.drift_velocity * delta_time
        self.center = self.pos.copy()
        
        # Update molecule positions to maintain phage structure
        molecule_idx = 0
        
        # Head molecules
        for i in range(self.head_points):
            if molecule_idx < len(self.molecules):
                angle = 2 * math.pi * i / self.head_points
                x = self.pos.x + self.head_radius * math.cos(angle)
                y = self.pos.y + self.head_radius * math.sin(angle)
                self.molecules[molecule_idx].pos = pygame.Vector2(x, y)
                molecule_idx += 1
        
        # Tail shaft molecules
        tail_segments = self.tail_length // self.tail_spacing
        for i in range(1, tail_segments + 1):
            if molecule_idx < len(self.molecules):
                x = self.pos.x
                y = self.pos.y + self.head_radius + i * self.tail_spacing
                self.molecules[molecule_idx].pos = pygame.Vector2(x, y)
                molecule_idx += 1
        
        # Tail fiber molecules
        fiber_length = 20
        angles = [math.radians(a) for a in (45, 135, -45, -135)]
        base = pygame.Vector2(self.pos.x, self.pos.y + self.head_radius + self.tail_length)
        for angle in angles:
            if molecule_idx < len(self.molecules):
                dx, dy = fiber_length * math.cos(angle), fiber_length * math.sin(angle)
                self.molecules[molecule_idx].pos = pygame.Vector2(base.x + dx, base.y + dy)
                molecule_idx += 1
