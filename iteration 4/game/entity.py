import pygame
import math
import random
from math import cos, sin, pi
from config import (
    SCREEN_HEIGHT, SCREEN_WIDTH, FPS, CELL_RADIUS, LIPID_COUNT, MINT, GOLDEN, REDDISH_GRAY,
    STRENGTH_DAMAGE_MULTIPLIER, ENDURANCE_FLAT_REDUCTION, ENDURANCE_PERCENT_REDUCTION,
    DEXTERITY_DODGE_CHANCE, DEXTERITY_CRIT_CHANCE, CRIT_DAMAGE_MULTIPLIER,
    PROTEIN_CANNON_COOLDOWN, PROTEIN_CANNON_DAMAGE, PROTEIN_CANNON_RANGE, PROTEIN_CANNON_PROJECTILE_SPEED,
    PROTEIN_BOMB_COOLDOWN, PROTEIN_BOMB_DAMAGE, PROTEIN_BURST_RADIUS,
    PROTEIN_BURST_COOLDOWN, PROTEIN_BURST_DAMAGE,
    MOLECULAR_DRILL_COOLDOWN, MOLECULAR_DRILL_DAMAGE, MOLECULAR_DRILL_RANGE,
    ENZYME_STRIKE_COOLDOWN, ENZYME_STRIKE_DAMAGE,
    SPIKES_DAMAGE_REFLECT, BARRIER_MATRIX_SHIELDS, BARRIER_MATRIX_REGEN_TIME,
    ADHESION_WEB_RADIUS, RESONANCE_SHIELD_ABSORPTION,
    TARGET_KEEP_DISTANCE, TARGET_DISTANCE_TOLERANCE, TARGET_APPROACH_SPEED,
    CELL_ROTATION_SPEED
)
from upgrade import Upgrade
#from molecule import Lipid

pygame.init()

def calculate_incoming_damage(raw_damage, attacker, defender):
    """
    Universal damage calculation considering stats
    
    Args:
        raw_damage: Base damage before modifiers
        attacker: Entity dealing damage (has strength, dex, intel)
        defender: Entity receiving damage (has endurance, dex)
    
    Returns:
        final_damage: Actual damage to apply
        combat_info: Dict with dodge/crit status for visual feedback
    """
    combat_info = {'dodged': False, 'critical': False}
    
    # 1. Scale damage by attacker's strength
    attacker_strength = attacker.base_strength + attacker.attributes.get('Strength', 0)
    strength_multiplier = 1.0 + (attacker_strength * STRENGTH_DAMAGE_MULTIPLIER)
    scaled_damage = raw_damage * strength_multiplier
    
    # 2. Apply defender's defense (from endurance)
    defender_endurance = defender.base_endurance + defender.attributes.get('Endurance', 0)
    defense_value = defender_endurance * ENDURANCE_FLAT_REDUCTION
    damage_after_defense = max(1, scaled_damage - defense_value)
    
    # 3. Apply damage reduction percentage (from endurance)
    damage_reduction_percent = min(0.75, defender_endurance * ENDURANCE_PERCENT_REDUCTION)
    damage_after_reduction = damage_after_defense * (1.0 - damage_reduction_percent)
    
    # 4. Dodge chance (from dexterity)
    defender_dexterity = defender.base_dexterity + defender.attributes.get('Dexterity', 0)
    dodge_chance = min(0.50, defender_dexterity * DEXTERITY_DODGE_CHANCE)
    if random.random() < dodge_chance:
        combat_info['dodged'] = True
        return 0, combat_info  # Dodged!
    
    # 5. Critical hit chance (from attacker's dexterity)
    attacker_dexterity = attacker.base_dexterity + attacker.attributes.get('Dexterity', 0)
    crit_chance = min(0.40, attacker_dexterity * DEXTERITY_CRIT_CHANCE)
    if random.random() < crit_chance:
        damage_after_reduction *= CRIT_DAMAGE_MULTIPLIER
        combat_info['critical'] = True
    
    # 6. Apply defense proteins if equipped
    if hasattr(defender, 'protein_inventory'):
        for protein in defender.protein_inventory:
            if hasattr(protein, 'apply_defense'):
                damage_after_reduction = protein.apply_defense(
                    damage_after_reduction, 
                    defender_endurance
                )
    
    return max(1, damage_after_reduction), combat_info  # Minimum 1 damage

class Entity:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, 40, 40)  # Default size
        self.selected = False #WORK ON THIS !!!

    def update(self, *args, **kwargs):
        pass

    def draw(self, surface, camera):
        screen_pos = camera.world_to_screen(self.pos)
        surface.blit(self.get_image(), self.get_image().get_rect(center=screen_pos))

    def get_image(self):
        surf = pygame.Surface((40, 40))
        surf.fill((200, 200, 200))
        return surf

class Point(Entity):
    def __init__(self, pos, parent=None):
        super().__init__(pos)
        self.old_pos = self.pos.copy()
        self.force = pygame.Vector2(0, 0)
        self.mass = 1
        self.color = "blue"
        self.parent = parent
        self.selectable = True
        self.selected = False
        self.upgrade = None  # Store reference to represented upgrade
        self.is_visual = False  # Flag to mark if this point represents an upgrade
        self.radius = 10
        self.image = self.get_image()

    def set_upgrade(self, upgrade):
        """Set this point to represent a specific upgrade"""
        self.upgrade = upgrade
        self.is_visual = True
        # Use icon if available, else fallback to get_image()
        if hasattr(upgrade, 'icon') and upgrade.icon:
            self.image = upgrade.icon
        elif hasattr(upgrade, 'get_image'):
            self.image = upgrade.get_image()
        if hasattr(upgrade, 'name'):
            self.name = upgrade.name
        if hasattr(upgrade, 'desc'):
            self.desc = upgrade.desc

    def update(self, surface, events, delta_time, camera=None):
        mouse_pos = pygame.mouse.get_pos()
        screen_pos = camera.world_to_screen(self.pos) if camera else self.pos


        # Only allow interaction if parent is a PlayerSoftBody
        if self.parent and getattr(self.parent, "is_player", False):
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == pygame.BUTTON_RIGHT:
                        if pygame.Vector2(screen_pos).distance_to(mouse_pos) <= 15:  # Increased click radius
                            # Check if this is a connection protein (Spring or Solid)
                            is_connection_protein = (hasattr(self, 'is_protein') and self.is_protein and 
                                                   hasattr(self, 'upgrade') and self.upgrade and
                                                   self.upgrade.name in ["Spring Protein", "Solid Protein"])
                            
                            if is_connection_protein:
                                # Handle connection protein selection
                                from main import selected_connection_points, external_springs, player_cells
                                
                                if not self.selected:
                                    # Select this connection point
                                    self.selected = True
                                    self.color = "yellow"  # Yellow for connection selection
                                    selected_connection_points.append(self)
                                    print(f"Selected connection point on cell (type: {self.upgrade.name})")
                                    
                                    # If we have 2 selected connection points with matching types
                                    if len(selected_connection_points) >= 2:
                                        point1, point2 = selected_connection_points[-2], selected_connection_points[-1]
                                        
                                        # Check if they're the same protein type and on different cells
                                        if (point1.upgrade.name == point2.upgrade.name and 
                                            point1.parent != point2.parent):
                                            
                                            # Check for existing connection between these points
                                            connection_exists = False
                                            for existing_spring in external_springs:
                                                if ((existing_spring.point1 == point1 and existing_spring.point2 == point2) or
                                                    (existing_spring.point1 == point2 and existing_spring.point2 == point1)):
                                                    connection_exists = True
                                                    break
                                            
                                            if not connection_exists:
                                                # Create the external spring connection
                                                spring_type = "solid" if point1.upgrade.name == "Solid Protein" else "spring"
                                                ext_spring = ExternalSpring(point1, point2, spring_type)
                                                external_springs.append(ext_spring)
                                                print(f"Created {spring_type} connection between cells!")
                                                
                                                # Trigger symbiosis discovery
                                                from main import discovery_tracker
                                                if discovery_tracker:
                                                    discovery_tracker.on_symbiosis_formed()
                                            else:
                                                print("Connection already exists between these points!")
                                            
                                            # Reset selection regardless
                                            point1.selected = False
                                            point1.color = "blue"
                                            point2.selected = False  
                                            point2.color = "blue"
                                            selected_connection_points.clear()
                                        elif len(selected_connection_points) > 2:
                                            # Clear old selections if too many
                                            old_point = selected_connection_points.pop(0)
                                            old_point.selected = False
                                            old_point.color = "blue"
                                else:
                                    # Deselect this connection point
                                    self.selected = False
                                    self.color = "blue"
                                    if self in selected_connection_points:
                                        selected_connection_points.remove(self)
                            else:
                                # Handle normal point selection for cell splitting
                                if not self.selected:
                                    # Select this point
                                    self.selected = True
                                    self.color = "orange"  # Orange for selected
                                    
                                    # Add to split points list
                                    if self not in self.parent.split_points:
                                        self.parent.split_points.append(self)
                                    
                                    # If we now have 2 selected points, mark them for splitting
                                    if len(self.parent.split_points) >= 2:
                                        # Keep only the two most recent selections
                                        if len(self.parent.split_points) > 2:
                                            # Deselect the oldest point
                                            old_point = self.parent.split_points.pop(0)
                                            old_point.selected = False
                                            old_point.color = "blue"
                                        
                                        # Mark the two selected points as ready for split
                                        for point in self.parent.split_points:
                                            point.color = "green"  # Green for split-ready
                                else:
                                    # Deselect this point
                                    self.selected = False
                                    self.color = "blue"
                                    if self in self.parent.split_points:
                                        self.parent.split_points.remove(self)
                                    
                                    # Update colors for remaining selected points
                                    for point in self.parent.split_points:
                                        if len(self.parent.split_points) < 2:
                                            point.color = "orange"  # Back to orange if less than 2
                                        else:
                                            point.color = "green"   # Keep green if still 2
                
                # Check for split trigger key (Space or Enter)
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN] and len(self.parent.split_points) == 2:
                        # Mark for splitting - the main game loop will handle the actual split
                        pass  # Split is handled by the existing logic in main.py

    def verlet_step(self, delta_time):
        """Perform the verlet style integration step using current self.force."""
        temp = self.pos.copy()
        acc = self.force / self.mass
        self.pos += (self.pos - self.old_pos) + acc * (delta_time ** 2)
        self.old_pos = temp


    def draw(self, surface, camera):
        screen_pos = camera.world_to_screen(self.pos)
        
        # Check if collision was detected this frame
        collision_color = (255, 0, 0) if getattr(self, 'collision_detected', False) else self.color
        if hasattr(self, 'collision_detected') and self.collision_detected:
            self.collision_detected = False  # Reset for next frame
        
        if hasattr(self, 'is_protein') and self.is_protein:
            # Draw protein point with icon
            if hasattr(self, 'image') and self.image:
                # Scale image based on zoom while maintaining minimum size
                scale = max(0.4, camera.zoom)
                scaled_size = int(20 * scale)  # Base size of 20 pixels
                img = pygame.transform.scale(self.image, (scaled_size, scaled_size))
                img_rect = img.get_rect(center=screen_pos)
                surface.blit(img, img_rect)
                # Draw outline for visibility (red if collision detected)
                outline_color = (255, 0, 0) if collision_color == (255, 0, 0) else (255, 255, 0)
                pygame.draw.circle(surface, outline_color, screen_pos, scaled_size//2 + 2, 2)
        else:
            # Draw regular membrane point (red if collision detected)
            point_size = max(3, int(5 * camera.zoom))
            pygame.draw.circle(surface, collision_color, screen_pos, point_size)

class Spring(Entity):
    def __init__(self, point1, point2, rest_length, spring_constant):
        self.point1 = point1
        self.point2 = point2
        self.rest_length = rest_length
        self.spring_constant = spring_constant

    def update(self, surface, events, delta_time):
        distance = self.point1.pos.distance_to(self.point2.pos)
        if distance == 0:
            return
        
        # Limit maximum stretch to prevent unrealistic deformation
        from config import SPRING_MAX_STRETCH_MULTIPLIER
        max_length = self.rest_length * SPRING_MAX_STRETCH_MULTIPLIER
        if distance > max_length:
            # Clamp the distance by moving points closer together
            dir_vec = (self.point2.pos - self.point1.pos) / distance
            excess_distance = distance - max_length
            
            # Move both points towards each other by half the excess distance
            correction = dir_vec * (excess_distance * 0.5)
            self.point1.pos += correction
            self.point2.pos -= correction
            
            # Update distance after correction
            distance = max_length
        
        dir_vec = (self.point2.pos - self.point1.pos) / distance
        force = dir_vec * self.spring_constant * (distance - self.rest_length)
        self.point1.force += force
        self.point2.force -= force

    def draw(self, surface, camera):
        if self.point1.parent.is_player:
            pygame.draw.line(surface, "pink", camera.world_to_screen(self.point1.pos), camera.world_to_screen(self.point2.pos), 2)
        else:
            pygame.draw.line(surface, "gray", camera.world_to_screen(self.point1.pos), camera.world_to_screen(self.point2.pos), 1)

class ExternalSpring(Entity):
    """Spring connection between points on different cells"""
    def __init__(self, point1, point2, spring_type="spring"):
        self.point1 = point1  # Point on first cell
        self.point2 = point2  # Point on second cell
        self.rest_length = point1.pos.distance_to(point2.pos)  # Initial distance
        
        # Set spring constant based on type
        if spring_type == "solid":
            self.spring_constant = 5000.0  # Very stiff for solid protein
            self.color = (220, 220, 255)  # Light blue for solid
            self.line_width = 4
        else:  # spring type
            self.spring_constant = 800.0   # Moderate stiffness for spring protein
            self.color = (180, 220, 255)   # Cyan for spring
            self.line_width = 3
            
        self.spring_type = spring_type
        self.active = True

    def update(self, delta_time):
        """Apply spring force between the two points"""
        if not self.active:
            return
            
        # Check if both cells still exist
        if (not hasattr(self.point1, 'parent') or not hasattr(self.point2, 'parent') or
            self.point1.parent is None or self.point2.parent is None):
            self.active = False
            return
            
        # Calculate spring force
        distance = self.point1.pos.distance_to(self.point2.pos)
        if distance == 0:
            return
        
        # Limit maximum stretch to prevent unrealistic deformation
        from config import SPRING_MAX_STRETCH_MULTIPLIER
        max_length = self.rest_length * SPRING_MAX_STRETCH_MULTIPLIER
        if distance > max_length:
            # Clamp the distance by moving points closer together
            direction = (self.point2.pos - self.point1.pos) / distance
            excess_distance = distance - max_length
            
            # Move both points towards each other by half the excess distance
            correction = direction * (excess_distance * 0.5)
            self.point1.pos += correction
            self.point2.pos -= correction
            
            # Update distance after correction
            distance = max_length
            
        direction = (self.point2.pos - self.point1.pos) / distance
        displacement = distance - self.rest_length
        force_magnitude = self.spring_constant * displacement
        
        # Apply forces to both points
        force = direction * force_magnitude
        self.point1.force += force
        self.point2.force -= force

    def draw(self, surface, camera):
        """Draw the external spring connection"""
        if not self.active:
            return
            
        pos1 = camera.world_to_screen(self.point1.pos)
        pos2 = camera.world_to_screen(self.point2.pos)
        
        # Draw the connection line
        pygame.draw.line(surface, self.color, pos1, pos2, self.line_width)
        
        # Draw connection indicators at endpoints
        pygame.draw.circle(surface, self.color, pos1, 6)
        pygame.draw.circle(surface, self.color, pos2, 6)


class CollisionSystem:
    def __init__(self, cell_size=50):
        self.cell_size = cell_size
        self.grid = {}
        
    def clear(self):
        self.grid = {}
    
    def _get_cell(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))
    
    def _get_nearby_cells(self, pos, radius):
        center_cell = self._get_cell(pos)
        cells = []
        cell_radius = int(radius // self.cell_size) + 1
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cells.append((center_cell[0] + dx, center_cell[1] + dy))
        return cells
    
    def add_point(self, point):
        cell = self._get_cell(point.pos)
        if cell not in self.grid:
            self.grid[cell] = {'points': [], 'springs': []}
        self.grid[cell]['points'].append(point)
    
    def add_spring(self, spring):
        p1 = spring.point1.pos
        p2 = spring.point2.pos
        
        min_x = min(p1.x, p2.x)
        max_x = max(p1.x, p2.x)
        min_y = min(p1.y, p2.y)
        max_y = max(p1.y, p2.y)
        
        min_cell_x = int(min_x // self.cell_size)
        max_cell_x = int(max_x // self.cell_size)
        min_cell_y = int(min_y // self.cell_size)
        max_cell_y = int(max_y // self.cell_size)
        
        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1):
                cell = (cell_x, cell_y)
                if cell not in self.grid:
                    self.grid[cell] = {'points': [], 'springs': []}
                if spring not in self.grid[cell]['springs']:
                    self.grid[cell]['springs'].append(spring)
    
    def point_to_point_collision(self, point1, point2, collision_distance=16):
        if point1.parent == point2.parent:
            return
        
        dist_vec = point2.pos - point1.pos
        dist = dist_vec.length()
        
        if 0 < dist < collision_distance:
            overlap = collision_distance - dist
            if dist > 0:
                normal = dist_vec / dist
                separation = normal * (overlap * 0.5)
                
                point1.pos -= separation
                point2.pos += separation
                
                response_force = normal * overlap * 100.0
                point1.force -= response_force
                point2.force += response_force
    
    def point_to_line_distance(self, point, line_start, line_end):
        line_vec = line_end - line_start
        point_vec = point - line_start
        
        line_len_sq = line_vec.length_squared()
        if line_len_sq == 0:
            return point.distance_to(line_start), line_start
        
        t = max(0, min(1, point_vec.dot(line_vec) / line_len_sq))
        projection = line_start + line_vec * t
        
        return point.distance_to(projection), projection
    
    def point_to_spring_collision(self, point, spring, collision_distance=8):
        if point.parent == spring.point1.parent:
            return
        
        dist, closest_point = self.point_to_line_distance(
            point.pos, spring.point1.pos, spring.point2.pos
        )
        
        if 0 < dist < collision_distance:
            overlap = collision_distance - dist
            if dist > 0:
                normal = (point.pos - closest_point) / dist
                
                point.pos += normal * overlap * 0.5
                
                response_force = normal * overlap * 150.0
                point.force += response_force
                
                line_vec = spring.point2.pos - spring.point1.pos
                line_len_sq = line_vec.length_squared()
                if line_len_sq > 0:
                    t = max(0, min(1, (closest_point - spring.point1.pos).dot(line_vec) / line_len_sq))
                    spring.point1.force -= response_force * (1 - t)
                    spring.point2.force -= response_force * t
    
    def detect_and_resolve_collisions(self, softbodies):
        self.clear()
        
        for sb in softbodies:
            for point in sb.points:
                self.add_point(point)
            for spring in sb.springs:
                self.add_spring(spring)
        
        checked_pairs = set()
        for sb in softbodies:
            for point in sb.points:
                cells = self._get_nearby_cells(point.pos, 20)
                
                for cell in cells:
                    if cell not in self.grid:
                        continue
                    
                    for other_point in self.grid[cell]['points']:
                        pair = tuple(sorted([id(point), id(other_point)]))
                        if pair not in checked_pairs:
                            checked_pairs.add(pair)
                            self.point_to_point_collision(point, other_point)
                    
                    for spring in self.grid[cell]['springs']:
                        if point not in [spring.point1, spring.point2]:
                            self.point_to_spring_collision(point, spring)


class SoftBody(Entity):
    def __init__(self, pos, points, radius, membrane_molecule=None):
        super().__init__(pos)
        self.center = pygame.Vector2(pos)
        self.angle = 0.0
        self.ang_vel = 0.0
        self.points = []
        self.springs = []
        self.split_points = []
        self.compressability = 300.0  # Scaled for seconds (was 0.0003 for milliseconds)
        self._dash_cooldown = 10
        self.body_color = REDDISH_GRAY
        self.membrane_molecule = membrane_molecule  # Store for unequip operations

        self.is_player = False  # Default to non-player

        if membrane_molecule:
            for i in range(points):
                x = pos[0] + radius * cos(2 * pi * i / points)
                y = pos[1] + radius * sin(2 * pi * i / points)
                self.points.append(membrane_molecule((x, y), self))

        for i in range(points):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            self.springs.append(Spring(p1, p2, p1.pos.distance_to(p2.pos), self.compressability))

        # Calculate mass and moment of inertia for angular dynamics
        self.mass = sum(p.mass for p in self.points)
        self.initial_shape = self.calculate_shape()
        self.rest_area = self.calculate_area()
        self.inertia = self.compute_polygon_moi(self.initial_shape, self.mass)

    def clear_split_selection(self):
        """Clear all split point selections and reset colors"""
        for point in self.points:
            point.selected = False
            point.color = "blue"
        self.split_points.clear()

    def calculate_com(self):
        vector = pygame.Vector2(0, 0)
        total_mass = 0
        for p in self.points:
            vector += p.pos * p.mass
            total_mass += p.mass
        return vector / total_mass if total_mass > 0 else vector

    def calculate_shape(self):
        com = self.calculate_com()
        return [p.pos - com for p in self.points]

    def calculate_area(self):
        total_area = 0
        for i in range(len(self.points)):
            v1 = self.points[i].pos - self.center
            v2 = self.points[(i + 1) % len(self.points)].pos - self.points[i].pos
            total_area += v1.cross(v2)
        return abs(total_area)

    @staticmethod
    def compute_polygon_area_and_centroid(pts):
        """Compute signed area and centroid for polygon pts (list of Vector2)"""
        A = 0.0
        Cx = 0.0
        Cy = 0.0
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i].x, pts[i].y
            x1, y1 = pts[(i + 1) % n].x, pts[(i + 1) % n].y
            cross = x0 * y1 - x1 * y0
            A += cross
            Cx += (x0 + x1) * cross
            Cy += (y0 + y1) * cross
        A *= 0.5
        if abs(A) < 1e-9:
            return 0.0, pygame.Vector2(0, 0)
        Cx /= (6.0 * A)
        Cy /= (6.0 * A)
        return A, pygame.Vector2(Cx, Cy)

    @staticmethod
    def compute_polygon_moi(relative_pts, mass):
        """
        Compute moment of inertia I_z about polygon centroid for a uniform lamina polygon.
        """
        n = len(relative_pts)
        if n < 3:
            return 1.0
        A = 0.0
        for i in range(n):
            x0, y0 = relative_pts[i].x, relative_pts[i].y
            x1, y1 = relative_pts[(i + 1) % n].x, relative_pts[(i + 1) % n].y
            A += x0 * y1 - x1 * y0
        A *= 0.5
        if abs(A) < 1e-9:
            return 1.0
        summ = 0.0
        for i in range(n):
            x0, y0 = relative_pts[i].x, relative_pts[i].y
            x1, y1 = relative_pts[(i + 1) % n].x, relative_pts[(i + 1) % n].y
            cross = x0 * y1 - x1 * y0
            term = (x0 * x0 + x0 * x1 + x1 * x1) + (y0 * y0 + y0 * y1 + y1 * y1)
            summ += cross * term
        I = (mass / (12.0 * A)) * summ
        return abs(I)

    def apply_global_force(self, force):
        """Apply a global force spread evenly to each point (optional helper)."""
        per = force / len(self.points)
        for p in self.points:
            p.force += per

    def apply_global_displacement(self, displacement):
        """Apply a global displacement spread evenly to each point (optional helper)."""
        for p in self.points:
            p.pos += displacement

    def set_center(self, vector):
        for i, p in enumerate(self.points):
            p.pos = self.initial_shape[i] + vector

    def update(self, surface, events, delta_time, camera=None):
        # Handle point input (but don't let them drag points around)
        for p in self.points:
            p.update(surface, events, delta_time, camera=camera)

        # Update center of mass
        com = self.calculate_com()
        self.center = com

        # Calculate net torque from all forces acting on points
        net_tau = 0.0
        for p in self.points:
            r = p.pos - com
            net_tau += r.cross(p.force)

        # Update angular motion
        if self.inertia <= 0:
            alpha = 0.0
        else:
            alpha = net_tau / self.inertia
        self.ang_vel += alpha * delta_time
        
        # Add constant rotation of 1 degree per second
        from config import CELL_ROTATION_SPEED
        self.ang_vel += math.radians(CELL_ROTATION_SPEED) * delta_time
        
        self.angle += self.ang_vel * delta_time

        # Update springs
        for s in self.springs:
            s.update(surface, events, delta_time)

        # Perform Verlet integration for all points
        for p in self.points:
            p.verlet_step(delta_time)

        # Apply shape restoration forces
        for i, p in enumerate(self.points):
            target = com + self.initial_shape[i].rotate(self.angle)
            restore_force = (target - p.pos) * 200.0
            p.force += restore_force

            # Also apply some direct position correction for stability
            rel = self.initial_shape[i]
            target_pos = com + rel.rotate(math.degrees(self.angle))
            p.pos += (target_pos - p.pos) * 0.1

        # Clear forces for next frame
        for p in self.points:
            p.force = pygame.Vector2(0, 0)

    def draw(self, surface, camera):
        from main import selected_entities
        # Use the cell's body_color; slightly lighten when selected
        try:
            base_rgb = tuple(self.body_color)
        except Exception:
            base_rgb = (180, 255, 180)
        if self in selected_entities:
            base_color = tuple(min(255, int(c * 1.15)) for c in base_rgb)
        else:
            base_color = base_rgb
        vertices = [camera.world_to_screen(p.pos) for p in self.points]
        
        if len(vertices) >= 3:  # need at least a triangle
            # Draw the main polygon
            pygame.draw.polygon(surface, base_color, vertices)
            
            # Draw colored segments to show point selection states
            for i, point in enumerate(self.points):
                if point.selected or point.color in ["orange", "green"]:
                    # Get this vertex and the next one to draw a colored edge
                    v1 = vertices[i]
                    v2 = vertices[(i + 1) % len(vertices)]
                    
                    # Convert point color to RGB
                    if point.color == "orange":
                        edge_color = (255, 165, 0)  # Orange
                    elif point.color == "green":
                        edge_color = (0, 255, 0)    # Green
                    elif point.color == "red":
                        edge_color = (255, 0, 0)    # Red
                    else:
                        edge_color = (100, 100, 255)  # Blue
                    
                    # Draw thicker colored line for this edge
                    pygame.draw.line(surface, edge_color, v1, v2, 4)
                    
                    # Draw a small colored circle at the vertex to make it more visible
                    pygame.draw.circle(surface, edge_color, v1, 6)
        
        # Show split status text if player cell has selected points
        if getattr(self, "is_player", False) and len(self.split_points) > 0:
            center_screen = camera.world_to_screen(self.center)
            font = pygame.font.Font(None, 24)
            
            if len(self.split_points) == 1:
                text = font.render("1 point selected", True, (255, 165, 0))
            elif len(self.split_points) == 2:
                text = font.render("Press SPACE to split", True, (0, 255, 0))
            
            text_rect = text.get_rect(center=(center_screen.x, center_screen.y - 40))
            # Draw background for better visibility
            pygame.draw.rect(surface, (0, 0, 0, 128), text_rect.inflate(10, 5))
            surface.blit(text, text_rect)
        
        for s in self.springs:
            s.draw(surface, camera)
        for p in self.points:
            p.draw(surface, camera)

    # --- Splitting ---
    def make_cell_more_circular(self, cell):
        """Adjust point positions to make the cell more circular while maintaining some irregularity"""
        import math
        
        center = cell.calculate_com()
        num_points = len(cell.points)
        
        # Calculate average radius
        total_radius = 0
        for point in cell.points:
            total_radius += point.pos.distance_to(center)
        avg_radius = total_radius / num_points if num_points > 0 else 50
        
        # Adjust each point to be more circular but not perfectly circular
        for i, point in enumerate(cell.points):
            # Target angle for this point in a perfect circle
            target_angle = 2 * math.pi * i / num_points
            
            # Current angle and radius
            current_vector = point.pos - center
            current_radius = current_vector.length()
            current_angle = math.atan2(current_vector.y, current_vector.x)
            
            # Blend between current position and circular position
            circular_pos = center + pygame.Vector2(
                avg_radius * math.cos(target_angle),
                avg_radius * math.sin(target_angle)
            )
            
            # Use 70% circular, 30% original shape for natural look
            blend_factor = 0.7
            new_pos = point.pos.lerp(circular_pos, blend_factor)
            
            # Add small random variation to avoid perfect circles
            import random
            variation = pygame.Vector2(
                random.uniform(-avg_radius * 0.1, avg_radius * 0.1),
                random.uniform(-avg_radius * 0.1, avg_radius * 0.1)
            )
            
            point.pos = new_pos + variation
            # Update old_pos to maintain velocity
            point.old_pos = point.pos - (point.pos - point.old_pos)
        
        # Recalculate shape and center after adjustments
        cell.center = cell.calculate_com()
        cell.initial_shape = cell.calculate_shape()

    def split_body(self):
        if len(self.split_points) < 2:
            return None

        point1, point2 = self.split_points[:2]

        # build two segments
        seg1, seg2 = [], []
        for i in range(self.points.index(point1), len(self.points) + self.points.index(point1)):
            p = self.points[i % len(self.points)]
            seg1.append(p)
            if p == point2:
                break
        for i in range(self.points.index(point2), len(self.points) + self.points.index(point2)):
            p = self.points[i % len(self.points)]
            seg2.append(p)
            if p == point1:
                break

        def clone_points(pts, parent, molecule=Point):
            clones = []
            for p in pts:
                clone = molecule(p.pos.copy(), parent=parent)
                clone.mass = p.mass
                clone.force = p.force.copy()
                clone.old_pos = p.old_pos.copy()
                clone.selected = p.selected
                clone.color = p.color
                clone.radius = getattr(p, 'radius', 10)
                # Don't copy protein properties - split cells start fresh with clean membrane points
                # This ensures both cells have full membrane capacity for new protein equipping
                clone.is_protein = False
                clone.upgrade = None
                clone.image = clone.get_image()
                clones.append(clone)
            return clones

        cls = self.__class__
        parent_molecule_type = self.points[0].__class__ if self.points else Point

        def create_split_cell(points, original):
            """Create a properly initialized split cell that matches the original's type and properties"""
            # Create new cell of same type as original with proper constructor
            if hasattr(original, 'is_player') and original.is_player:
                # Import PlayerCell to create proper player cell
                from player import PlayerCell
                new_cell = PlayerCell(original.center, len(points), original.radius)
            else:
                # Create regular Cell
                new_cell = Cell(original.center, len(points), original.radius, original.membrane_molecule)
            
            # Replace the auto-generated points with our specific split points
            new_cell.points = clone_points(points, new_cell, molecule=parent_molecule_type)
            
            # Recreate springs with same properties as original
            new_cell.springs = []
            for i in range(len(new_cell.points)):
                next_i = (i + 1) % len(new_cell.points)
                p1, p2 = new_cell.points[i], new_cell.points[next_i]
                rest_length = self.points[0].pos.distance_to(self.points[1].pos)  # Approximate from original
                spring = Spring(p1, p2, rest_length, original.compressability)
                new_cell.springs.append(spring)
            
            # Update shape and position based on new points
            new_cell.initial_shape = new_cell.calculate_shape()
            new_cell.center = pygame.Vector2(new_cell.calculate_com())
            new_cell.pos = new_cell.center.copy()
            if hasattr(new_cell, 'target_pos'):
                new_cell.target_pos = new_cell.center.copy()
            
            # Copy essential properties from original
            new_cell.compressability = original.compressability
            new_cell.body_color = original.body_color
            new_cell.health = original.health // 2  # Split health between cells
            
            # Reset split-specific properties
            new_cell.selected = False
            new_cell.split_points = []
            
            return new_cell

        # Create split cells using proper constructors
        sb1 = create_split_cell(seg1, self)
        sb2 = create_split_cell(seg2, self)

        # --- Update protein_inventory for both split cells and refund remaining proteins ---
        def extract_proteins(points):
            # Return a list of unique protein upgrades from protein points
            proteins = []
            for p in points:
                if hasattr(p, 'is_protein') and p.is_protein and hasattr(p, 'upgrade') and p.upgrade:
                    if p.upgrade not in proteins:
                        proteins.append(p.upgrade)
                        # Reset the point to normal membrane point
                        p.is_protein = False
                        p.upgrade = None
                        p.image = p.get_image()
                        if hasattr(p, 'name'):
                            delattr(p, 'name')
                        if hasattr(p, 'desc'):
                            delattr(p, 'desc')
            return proteins

        # Extract proteins from both new cells
        proteins1 = extract_proteins(sb1.points)
        proteins2 = extract_proteins(sb2.points)
        
        # Return all proteins to central inventory
        try:
            from main import player_upgrades
            for protein in proteins1 + proteins2:
                category = "Crafted Proteins" if hasattr(protein, 'is_crafted') else "Proteins"
                if protein not in player_upgrades[category]:
                    player_upgrades[category].append(protein)
        except ImportError:
            # Handle case where main.py isn't available (e.g., during testing)
            pass

        # drift apart
        com1, com2 = sb1.calculate_com(), sb2.calculate_com()
        direction = (com2 - com1).normalize() if com1 != com2 else pygame.Vector2(1, 0)
        kick = self.radius * 0.2  # separation distance
        speed = 2.0               # outward velocity

        for p in sb1.points:
            # push positions apart
            p.pos -= direction * kick
            # shift old_pos less so it thinks it's moving away
            p.old_pos = p.pos + direction * speed  

        for p in sb2.points:
            p.pos += direction * kick
            p.old_pos = p.pos - direction * speed  

        # Return equipped proteins to the central inventory
        if hasattr(self, 'protein_inventory'):
            try:
                from main import player_upgrades
                for protein in self.protein_inventory:
                    category = "Crafted Proteins" if hasattr(protein, 'is_crafted') else "Proteins"
                    if protein not in player_upgrades[category]:
                        player_upgrades[category].append(protein)
                self.protein_inventory.clear()
            except ImportError:
                # Handle case where main.py isn't available (e.g., during testing)
                self.protein_inventory.clear()

        # Make split cells more circular by adjusting point positions
        self.make_cell_more_circular(sb1)
        self.make_cell_more_circular(sb2)
        
        # Clear split points and reset colors for both new cells
        sb1.clear_split_selection()
        sb2.clear_split_selection()
        
        return sb1, sb2, self


    # --- SoftBody Collision Handling ---
    @staticmethod
    def point_in_polygon(point, polygon_points):
        """
        Ray casting algorithm to determine if a point is inside a polygon.
        Returns True if point is inside, False if outside.
        """
        x, y = point.x, point.y
        n = len(polygon_points)
        inside = False
        
        p1x, p1y = polygon_points[0].pos.x, polygon_points[0].pos.y
        for i in range(1, n + 1):
            p2x, p2y = polygon_points[i % n].pos.x, polygon_points[i % n].pos.y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def get_closest_edge_point(point, polygon_points, padding=5.0):
        """
        Find the closest point on the polygon edge to the given point,
        then move it outside by padding distance.
        """
        min_dist = float('inf')
        closest_point = None
        closest_edge_normal = None
        
        # Check each edge of the polygon
        for i in range(len(polygon_points)):
            p1 = polygon_points[i].pos
            p2 = polygon_points[(i + 1) % len(polygon_points)].pos
            
            # Vector from p1 to p2
            edge = p2 - p1
            edge_length = edge.length()
            
            if edge_length == 0:
                continue
                
            # Vector from p1 to point
            to_point = point - p1
            
            # Project point onto edge
            t = max(0, min(1, to_point.dot(edge) / (edge_length * edge_length)))
            projection = p1 + edge * t
            
            # Distance from point to projection
            dist = point.distance_to(projection)
            
            if dist < min_dist:
                min_dist = dist
                closest_point = projection
                # Normal pointing outward from edge
                edge_normal = pygame.Vector2(-edge.y, edge.x).normalize()
                # Make sure normal points away from polygon center
                center = sum([p.pos for p in polygon_points], pygame.Vector2(0, 0)) / len(polygon_points)
                if (closest_point - center).dot(edge_normal) < 0:
                    edge_normal = -edge_normal
                closest_edge_normal = edge_normal
        
        if closest_point and closest_edge_normal:
            # Move point outside by padding distance
            return closest_point + closest_edge_normal * padding
        
        return point
    
    @staticmethod
    def resolve_polygon_collisions(cells, padding=8.0):
        """
        New collision system using ray casting (point-in-polygon test).
        More stable with Verlet integration than force-based approach.
        """
        # Check each cell against every other cell
        for i in range(len(cells)):
            for j in range(len(cells)):
                if i == j:
                    continue
                    
                cell_a, cell_b = cells[i], cells[j]
                
                # Quick distance check first
                center_dist = cell_a.center.distance_to(cell_b.center)
                if center_dist > (cell_a.radius + cell_b.radius + padding * 2):
                    continue
                
                # Check if any points of cell_a are inside cell_b
                for point in cell_a.points:
                    if SoftBody.point_in_polygon(point.pos, cell_b.points):
                        # Point is inside the other cell, move it outside
                        new_pos = SoftBody.get_closest_edge_point(point.pos, cell_b.points, padding)
                        
                        # Update both current position and old position to maintain velocity
                        velocity = point.pos - point.old_pos
                        point.pos = new_pos
                        point.old_pos = new_pos - velocity * 0.8  # Slight damping
                        
                        # Mark point for debug visualization
                        point.collision_detected = True
    
    @staticmethod
    def resolve_point_collisions(cells, min_dist=15.0, stiffness=0.8, damping=0.95):
        """
        Legacy method - now calls the new polygon collision system
        """
        SoftBody.resolve_polygon_collisions(cells, padding=min_dist)
    
    @staticmethod
    def resolve_softbody_collisions(softbodies, min_dist=15.0, stiffness=0.8):
        """
        Legacy collision method - now calls the improved point collision system
        """
        SoftBody.resolve_point_collisions(softbodies, min_dist, stiffness)

class Cell(SoftBody):
    def add_point(self):
        """Add a new point to the cell membrane for Cell Membrane Extender"""
        if len(self.points) == 0:
            return
            
        # Find a good position to insert the new point (between two existing points)
        # Choose the two points that are furthest apart
        max_distance = 0
        best_idx = 0
        
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            distance = p1.pos.distance_to(p2.pos)
            if distance > max_distance:
                max_distance = distance
                best_idx = i
        
        # Create new point between the two furthest points
        p1 = self.points[best_idx]
        p2 = self.points[(best_idx + 1) % len(self.points)]
        
        # Position new point at midpoint
        new_pos = (p1.pos + p2.pos) / 2
        
        # Create the new membrane point
        molecule_type = self.membrane_molecule if self.membrane_molecule else Point
        new_point = molecule_type(new_pos, self)
        
        # Insert the new point into the points list
        self.points.insert(best_idx + 1, new_point)
        
        # Update springs - remove the old spring and add two new ones
        for i, spring in enumerate(self.springs):
            if (spring.point1 == p1 and spring.point2 == p2) or (spring.point1 == p2 and spring.point2 == p1):
                # Remove the old spring
                self.springs.pop(i)
                break
        
        # Add two new springs
        rest_length = max_distance / 2  # Half the original distance
        self.springs.append(Spring(p1, new_point, rest_length, self.compressability))
        self.springs.append(Spring(new_point, p2, rest_length, self.compressability))
        
        print(f"Added new membrane point! Cell now has {len(self.points)} points.")

    def extend_membrane(self, num_points):
        """Extend the cell membrane by adding multiple points evenly distributed"""
        if len(self.points) == 0 or num_points <= 0:
            return
            
        # Calculate current circumference and add points evenly
        for _ in range(num_points):
            # Find the largest gap between consecutive points
            max_distance = 0
            best_idx = 0
            
            for i in range(len(self.points)):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % len(self.points)]
                distance = p1.pos.distance_to(p2.pos)
                if distance > max_distance:
                    max_distance = distance
                    best_idx = i
            
            # Add a point in the largest gap
            p1 = self.points[best_idx]
            p2 = self.points[(best_idx + 1) % len(self.points)]
            
            # Position new point at midpoint
            new_pos = (p1.pos + p2.pos) / 2
            
            # Create the new membrane point
            molecule_type = self.membrane_molecule if self.membrane_molecule else Point
            new_point = molecule_type(new_pos, self)
            
            # Insert the new point into the points list
            self.points.insert(best_idx + 1, new_point)
            
            # Update springs - remove the old spring and add two new ones
            for i, spring in enumerate(self.springs):
                if (spring.point1 == p1 and spring.point2 == p2) or (spring.point1 == p2 and spring.point2 == p1):
                    # Remove the old spring
                    self.springs.pop(i)
                    break
            
            # Add two new springs
            rest_length = max_distance / 2  # Half the original distance
            self.springs.append(Spring(p1, new_point, rest_length, self.compressability))
            self.springs.append(Spring(new_point, p2, rest_length, self.compressability))
    
    def redistribute_points_to_circle(self, new_radius):
        """Redistribute all points evenly around a circle of new_radius while preserving proteins"""
        if len(self.points) == 0:
            return
        
        # Get current center
        center = self.calculate_com()
        
        # Separate membrane points from protein points
        # Protein points have is_protein attribute set to True
        membrane_points = []
        protein_data = []  # Store protein points with their relative angular position
        
        for i, point in enumerate(self.points):
            if getattr(point, 'is_protein', False):
                # Calculate current angle relative to center
                rel_pos = point.pos - center
                angle = math.atan2(rel_pos.y, rel_pos.x)
                protein_data.append({
                    'point': point,
                    'angle': angle,
                    'index': i
                })
            else:
                membrane_points.append(point)
        
        # Calculate minimum radius needed to ensure springs are at least 25 pixels
        # Circumference = num_points * min_spring_length
        # 2 * pi * radius = num_points * 25
        # radius = (num_points * 25) / (2 * pi)
        min_spring_length = 25
        total_points = len(self.points)
        min_required_radius = (total_points * min_spring_length) / (2 * math.pi)
        
        # Use the larger of the requested radius or the minimum required
        actual_radius = max(new_radius, min_required_radius)
        
        # If we had to increase the radius, update the cell's radius attribute
        if actual_radius > new_radius:
            self.radius = actual_radius
            print(f"Adjusted radius from {new_radius:.1f} to {actual_radius:.1f} to maintain minimum spring length of {min_spring_length}px")
        
        # Clear all springs
        self.springs.clear()
        
        # Redistribute membrane points evenly around the circle
        num_membrane = len(membrane_points)
        if num_membrane > 0:
            angle_step = (2 * math.pi) / num_membrane
            for i, point in enumerate(membrane_points):
                angle = i * angle_step
                new_x = center.x + actual_radius * math.cos(angle)
                new_y = center.y + actual_radius * math.sin(angle)
                point.pos = pygame.Vector2(new_x, new_y)
                point.old_pos = point.pos.copy()  # Reset velocity
        
        # Position protein points at their relative angles on the new circle
        for pdata in protein_data:
            point = pdata['point']
            angle = pdata['angle']
            new_x = center.x + actual_radius * math.cos(angle)
            new_y = center.y + actual_radius * math.sin(angle)
            point.pos = pygame.Vector2(new_x, new_y)
            point.old_pos = point.pos.copy()  # Reset velocity
        
        # Rebuild springs connecting all points in sequence
        # Calculate new rest length based on circumference
        circumference = 2 * math.pi * actual_radius
        rest_length = circumference / len(self.points)
        
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            self.springs.append(Spring(p1, p2, rest_length, self.compressability))

    def unequip_protein(self, protein):
        # Find a point with this protein equipped
        for idx, p in enumerate(self.points):
            if hasattr(p, 'is_protein') and p.is_protein and getattr(p, 'upgrade', None) == protein:
                # Clean up any external spring connections involving this point
                from main import external_springs
                for spring in external_springs[:]:  # Use slice for safe removal
                    if spring.point1 == p or spring.point2 == p:
                        spring.active = False  # Mark for removal in main update loop
                        print(f"Removed connection involving unequipped {protein.name}")
                
                # Replace with a normal membrane point using the correct molecule type
                molecule_type = self.membrane_molecule if self.membrane_molecule else Point
                new_point = molecule_type(p.pos.copy(), self)
                new_point.mass = p.mass
                new_point.force = p.force.copy()
                new_point.old_pos = p.old_pos.copy()
                new_point.selected = p.selected
                new_point.color = p.color
                new_point.radius = getattr(p, 'radius', 10)
                new_point.is_visual = False
                new_point.is_protein = False
                new_point.upgrade = None
                new_point.image = new_point.get_image()
                # Safely remove protein-specific attributes if they exist
                for attr in ['name', 'desc']:
                    if hasattr(new_point, attr):
                        delattr(new_point, attr)
                self.points[idx] = new_point
                # Update springs to point to the new point
                for spring in self.springs:
                    if spring.point1 == p:
                        spring.point1 = new_point
                    if spring.point2 == p:
                        spring.point2 = new_point
                # Remove from protein inventory
                if protein in self.protein_inventory:
                    self.protein_inventory.remove(protein)
                # Add back to central inventory
                from main import player_upgrades
                category = "Crafted Proteins" if hasattr(protein, 'is_crafted') else "Proteins"
                if protein not in player_upgrades[category]:
                    player_upgrades[category].append(protein)
                return True
        return False
    def __init__(self, pos, points=12, radius=CELL_RADIUS, membrane_molecule=None):
        super().__init__(pos, points, radius, membrane_molecule=membrane_molecule)

        self.velocity   = pygame.Vector2(0, 0)
        self.radius     = radius
        self.is_player  = False   # overridden in PlayerCell

        self.initial_pos = pygame.Vector2(pos)
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180, 255, 180), (radius, radius), radius)

        # Core stats - Base values (not modified by upgrades)
        from config import BASE_PLAYER_STATS
        self.base_strength = BASE_PLAYER_STATS['strength']
        self.base_endurance = BASE_PLAYER_STATS['endurance']
        self.base_dexterity = BASE_PLAYER_STATS['dexterity']
        self.base_intelligence = BASE_PLAYER_STATS['intelligence']
        
        self.max_health = 100 + (self.base_endurance * 5)  # +5 HP per endurance
        self.health = self.max_health
        self.max_atp = 100.0
        self.atp     = self.max_atp
        self.ATP_DRAIN_PER_ORGANELLE = 0.01
        
        # Health regeneration system
        self.last_damage_time = 0
        self.health_regen_delay = 1.5  # 1.5 seconds before regen starts (reduced from 3.0)
        self.health_regen_rate = 10.0  # 10 health per second
        
        # Attack cooldown system
        self.last_attack_time = 0
        self.attack_cooldown = 0.5  # 0.5 seconds between attacks
        
        # Targeting system
        self.current_target = None
        self.damaged_by = None  # Track who damaged us last for priority targeting
        self.target_lock_time = 0  # How long we've been targeting damaged_by
        self.target_lock_duration = 5.0  # Lock onto attacker for 5 seconds
        
        # Protein ability system
        self.active_projectiles = []  # Projectiles fired by this cell
        self.active_mines = []  # Protein bombs placed by this cell
        self.active_shields = []  # Barrier shields orbiting this cell
        self.active_webs = []  # Adhesion webs placed by this cell
        self.protein_cooldowns = {}  # Track cooldowns for each protein type
        self.resonance_shield_active = False  # Single-use shield status
        self.resonance_shield_health = 0

        # Upgrades/inventory
        self.upgrades = {"Proteins": [], "Organelles": []}
        self.organelle_slots   = [None] * 10
        self.protein_inventory = []

        self.visual_upgrades = []

        # Molecules/resources
        self.molecules = {
            "protein":       0,
            "lipid":         0,
            "nucleic_acid":  0,
            "carbohydrate":  0
        }

        # Attributes (bonus stats from upgrades, reset each frame)
        self.attributes = {
            'Strength': 0,     # Physical power and damage
            'Dexterity': 0,    # Speed and precision
            'Endurance': 0,    # Health and stamina
            'Intelligence': 0   # Special abilities and effectiveness
        }

    def take_damage(self, damage, current_time, attacker=None):
        """Deal damage to the cell and update last damage time and targeting"""
        original_damage = damage
        
        # Check Resonance Shield first (single-use)
        if self.resonance_shield_active and self.resonance_shield_health > 0:
            if damage <= self.resonance_shield_health:
                self.resonance_shield_health -= damage
                print(f"Resonance Shield absorbed {damage:.1f} damage ({self.resonance_shield_health:.1f} remaining)")
                damage = 0
            else:
                damage -= self.resonance_shield_health
                print(f"Resonance Shield absorbed {self.resonance_shield_health:.1f} damage and broke!")
                self.resonance_shield_health = 0
                self.resonance_shield_active = False
        
        # Check Barrier Shields
        for shield in self.active_shields[:]:  # Use slice to allow removal during iteration
            if damage <= 0:
                break
            remaining_damage = shield.absorb_damage(damage)
            if not shield.active:
                self.active_shields.remove(shield)
            damage = remaining_damage
        
        # Check Spikes (reflect damage back to attacker)
        has_spikes = any(p.name == 'Spikes' for p in self.protein_inventory if hasattr(p, 'name'))
        if has_spikes and attacker and damage > 0:
            reflected = original_damage * SPIKES_DAMAGE_REFLECT
            if hasattr(attacker, 'take_damage'):
                attacker.take_damage(reflected, current_time, attacker=self)
                print(f"Spikes reflected {reflected:.1f} damage back to attacker!")
        
        # Apply remaining damage to health
        self.health = max(0, self.health - damage)
        self.last_damage_time = current_time
        
        # Update targeting system - prioritize entity that damaged us
        if attacker and self.is_player:
            self.damaged_by = attacker
            self.current_target = attacker
            self.target_lock_time = current_time
    
    def update_targeting(self, current_time, all_enemies):
        """
        Update targeting based on priority system:
        1. Entity that damaged us (for target_lock_duration seconds)
        2. Nearest enemy within range (250 pixels + cell radius)
        
        Args:
            current_time: Current game time in seconds
            all_enemies: List of potential enemy entities (viruses, enemy cells, etc.)
        """
        if not self.is_player:
            return  # Only player cells auto-target
        
        # Calculate maximum targeting range (250 pixels + our cell radius)
        max_targeting_range = 250 + self.radius
        
        # Check if we should clear the damaged_by lock
        if self.damaged_by:
            time_since_lock = current_time - self.target_lock_time
            if time_since_lock >= self.target_lock_duration:
                self.damaged_by = None
            else:
                # Keep targeting the entity that damaged us
                # Check if it's still alive/valid and within range
                if self.damaged_by in all_enemies:
                    enemy_pos = self.damaged_by.center if hasattr(self.damaged_by, 'center') else self.damaged_by.pos
                    distance = self.center.distance_to(enemy_pos)
                    
                    # Only keep targeting if still in range
                    if distance <= max_targeting_range:
                        self.current_target = self.damaged_by
                        return
                
                # Target out of range or invalid, clear it
                self.damaged_by = None
        
        # Find nearest enemy within range
        if not all_enemies:
            self.current_target = None
            return
        
        nearest = None
        min_distance = float('inf')
        
        for enemy in all_enemies:
            # Skip if enemy is dead or invalid
            if hasattr(enemy, 'health') and enemy.health <= 0:
                continue
            
            # Calculate distance from cell center
            enemy_pos = enemy.center if hasattr(enemy, 'center') else enemy.pos
            distance = self.center.distance_to(enemy_pos)
            
            # Only consider enemies within targeting range
            if distance <= max_targeting_range and distance < min_distance:
                min_distance = distance
                nearest = enemy
        
        self.current_target = nearest
    
    def maintain_target_distance(self, delta_time):
        """
        Keep optimal distance from current target
        Move closer if too far, move away if too close
        """
        if not self.is_player or not self.current_target:
            return
        
        target_pos = (self.current_target.center if hasattr(self.current_target, 'center') 
                     else self.current_target.pos)
        
        # Calculate distance to target
        distance = self.center.distance_to(target_pos)
        
        # Check if we need to adjust position
        if distance > TARGET_KEEP_DISTANCE + TARGET_DISTANCE_TOLERANCE:
            # Too far - move closer
            direction = (target_pos - self.center).normalize()
            move_force = direction * TARGET_APPROACH_SPEED * delta_time
            
            # Apply force to all points
            for point in self.points:
                point.force += move_force
                
        elif distance < TARGET_KEEP_DISTANCE - TARGET_DISTANCE_TOLERANCE:
            # Too close - back away
            direction = (self.center - target_pos).normalize()
            move_force = direction * TARGET_APPROACH_SPEED * delta_time
            
            # Apply force to all points
            for point in self.points:
                point.force += move_force
    
    def use_attack_protein(self, protein_name, current_time):
        """
        Activate an attack protein ability
        Returns True if ability was used, False if on cooldown or no target
        """
        if not self.current_target:
            return False
        
        # Check cooldown
        last_use = self.protein_cooldowns.get(protein_name, 0)
        cooldowns = {
            'Protein Cannon': PROTEIN_CANNON_COOLDOWN,
            'Protein Bomb': PROTEIN_BOMB_COOLDOWN,
            'Protein Burst': PROTEIN_BURST_COOLDOWN,
            'Molecular Drill': MOLECULAR_DRILL_COOLDOWN,
            'Enzyme Strike': ENZYME_STRIKE_COOLDOWN
        }
        
        cooldown = cooldowns.get(protein_name, 1.0)
        if current_time - last_use < cooldown:
            return False  # On cooldown
        
        # Use ability based on type
        from protein_abilities import Projectile, ProteinBomb
        
        if protein_name == 'Protein Cannon':
            # Fire projectile at target
            projectile = Projectile(
                self.center.copy(),
                self.current_target,
                PROTEIN_CANNON_DAMAGE,
                PROTEIN_CANNON_PROJECTILE_SPEED,
                self,
                color=(255, 100, 100)
            )
            self.active_projectiles.append(projectile)
            print(f"Protein Cannon fired!")
            
        elif protein_name == 'Protein Bomb':
            # Place mine at current position
            bomb = ProteinBomb(self.center.copy(), self)
            self.active_mines.append(bomb)
            print(f"Protein Bomb placed!")
            
        elif protein_name == 'Protein Burst':
            # AOE damage around cell
            self._protein_burst_damage(current_time)
            
        elif protein_name == 'Molecular Drill':
            # High damage projectile
            projectile = Projectile(
                self.center.copy(),
                self.current_target,
                MOLECULAR_DRILL_DAMAGE,
                PROTEIN_CANNON_PROJECTILE_SPEED * 0.7,  # Slower but stronger
                self,
                color=(240, 80, 160)
            )
            self.active_projectiles.append(projectile)
            print(f"Molecular Drill launched!")
            
        elif protein_name == 'Enzyme Strike':
            # Corrosive projectile with DOT
            projectile = Projectile(
                self.center.copy(),
                self.current_target,
                ENZYME_STRIKE_DAMAGE,
                PROTEIN_CANNON_PROJECTILE_SPEED * 0.9,
                self,
                color=(100, 200, 80)
            )
            self.active_projectiles.append(projectile)
            print(f"Enzyme Strike released!")
        
        # Update cooldown
        self.protein_cooldowns[protein_name] = current_time
        return True
    
    def _protein_burst_damage(self, current_time):
        """Deal AOE damage around the cell"""
        # Get all entities from main (we'll need to pass this in)
        # For now, this is a placeholder
        print(f"Protein Burst activated! Damaging enemies in {PROTEIN_BURST_RADIUS}px radius")
        
    def use_defense_protein(self, protein_name, current_time):
        """
        Activate a defense protein ability
        """
        from protein_abilities import BarrierShield, AdhesionWeb
        
        if protein_name == 'Barrier Matrix':
            # Create 3 orbiting shields if not already active
            if len(self.active_shields) == 0:
                for i in range(BARRIER_MATRIX_SHIELDS):
                    shield = BarrierShield(self, i, BARRIER_MATRIX_SHIELDS)
                    self.active_shields.append(shield)
                print(f"Barrier Matrix activated! {BARRIER_MATRIX_SHIELDS} shields deployed")
                return True
                
        elif protein_name == 'Adhesion Web':
            # Create slowing web at current position
            web = AdhesionWeb(self.center.copy(), self)
            self.active_webs.append(web)
            print(f"Adhesion Web deployed!")
            return True
            
        elif protein_name == 'Resonance Shield':
            # Activate one-time damage absorption shield
            if not self.resonance_shield_active:
                self.resonance_shield_active = True
                self.resonance_shield_health = RESONANCE_SHIELD_ABSORPTION
                print(f"Resonance Shield activated! Absorbs {RESONANCE_SHIELD_ABSORPTION} damage")
                return True
        
        return False
    
    def update_protein_abilities(self, delta_time, all_entities, current_time):
        """Update all active protein abilities"""
        # Update projectiles
        self.active_projectiles = [p for p in self.active_projectiles 
                                   if p.update(delta_time, all_entities)]
        
        # Update mines
        self.active_mines = [m for m in self.active_mines 
                            if m.update(delta_time, all_entities)]
        
        # Update shields
        self.active_shields = [s for s in self.active_shields 
                              if s.update(delta_time)]
        
        # Update webs
        self.active_webs = [w for w in self.active_webs 
                           if w.update(delta_time, all_entities)]
        
        # Auto-fire attack proteins if we have a target
        if self.is_player and self.current_target:
            # Check equipped attack proteins and fire them automatically
            for protein in self.protein_inventory:
                if hasattr(protein, 'name'):
                    if protein.name in ['Protein Cannon', 'Molecular Drill', 'Enzyme Strike']:
                        self.use_attack_protein(protein.name, current_time)
    
    def draw_protein_abilities(self, surface, camera):
        """Draw all active protein effects"""
        # Draw projectiles
        for projectile in self.active_projectiles:
            projectile.draw(surface, camera)
        
        # Draw mines
        for mine in self.active_mines:
            mine.draw(surface, camera)
        
        # Draw shields
        for shield in self.active_shields:
            shield.draw(surface, camera)
        
        # Draw webs
        for web in self.active_webs:
            web.draw(surface, camera)
        
        # Draw resonance shield indicator
        if self.resonance_shield_active and self.resonance_shield_health > 0:
            screen_pos = camera.world_to_screen(self.center)
            shield_radius = int((self.radius + 15) * camera.zoom)
            alpha = int(150 * (self.resonance_shield_health / RESONANCE_SHIELD_ABSORPTION))
            pygame.draw.circle(surface, (150, 220, 255, alpha), screen_pos, shield_radius, 3)
        
    def update_health_regeneration(self, current_time, delta_time):
        """Handle health regeneration after not taking damage for a while"""
        if self.health < self.max_health:
            time_since_damage = current_time - self.last_damage_time
            if time_since_damage >= self.health_regen_delay:
                # Regenerate health
                regen_amount = self.health_regen_rate * delta_time
                self.health = min(self.max_health, self.health + regen_amount)
                
    def get_health_percentage(self):
        """Get health as a percentage for UI display"""
        if self.max_health <= 0:
            return 0
        return int((self.health / self.max_health) * 100)
    
    def get_membrane_point_count(self):
        """Get the number of membrane points (non-protein points)"""
        return len([p for p in self.points if not getattr(p, 'is_protein', False)])
    
    def handle_collision_combat(self, other_cell, current_time):
        """Handle combat when two cells collide"""
        # Check attack cooldown for both cells
        if (current_time - self.last_attack_time < self.attack_cooldown or
            current_time - other_cell.last_attack_time < other_cell.attack_cooldown):
            return None, None  # Combat on cooldown
            
        from config import MEMBRANE_DEDUCTION_ON_COLLISION
        
        my_points = self.get_membrane_point_count()
        other_points = other_cell.get_membrane_point_count()
        
        winner = None
        loser = None
        
        # Determine winner based on membrane points
        if my_points > other_points:
            winner = self
            loser = other_cell
        elif other_points > my_points:
            winner = other_cell
            loser = self
        else:
            # Tie-break by radius
            if self.radius > other_cell.radius:
                winner = self
                loser = other_cell
            elif other_cell.radius > self.radius:
                winner = other_cell
                loser = self
            else:
                # Equal points and radius - attacker wins (self is attacker)
                winner = self
                loser = other_cell
        
        # Apply combat effects
        loser_membrane_points = loser.get_membrane_point_count()
        deduction_amount = int(MEMBRANE_DEDUCTION_ON_COLLISION * loser_membrane_points)
        
        # Remove membrane points from winner
        winner.remove_membrane_points(deduction_amount)
        
        # Deal damage to loser using new damage calculation system
        raw_damage = 25  # Base collision damage
        final_damage, combat_info = calculate_incoming_damage(raw_damage, winner, loser)
        loser.take_damage(final_damage, current_time, attacker=winner)
        
        # Update attack cooldowns for both cells
        self.last_attack_time = current_time
        other_cell.last_attack_time = current_time
        
        # Print combat feedback
        feedback = f"Cell collision: {winner.__class__.__name__} wins!"
        if combat_info['dodged']:
            feedback += " (DODGED)"
        elif combat_info['critical']:
            feedback += f" (CRITICAL HIT! {final_damage:.1f} damage)"
        else:
            feedback += f" ({final_damage:.1f} damage)"
        print(feedback)
        
        return winner, loser
    
    def remove_membrane_points(self, count):
        """Remove a specified number of membrane points from the cell"""
        if count <= 0:
            return
            
        # Find non-protein membrane points to remove
        membrane_points = [p for p in self.points if not getattr(p, 'is_protein', False)]
        
        # Don't remove all points - leave at least 3
        max_removable = max(0, len(membrane_points) - 3)
        actual_remove = min(count, max_removable)
        
        # Remove points and their springs
        for _ in range(actual_remove):
            if not membrane_points:
                break
                
            point_to_remove = membrane_points.pop()
            
            # Remove springs connected to this point
            springs_to_remove = []
            for spring in self.springs:
                if spring.point1 == point_to_remove or spring.point2 == point_to_remove:
                    springs_to_remove.append(spring)
            
            for spring in springs_to_remove:
                if spring in self.springs:
                    self.springs.remove(spring)
            
            # Remove point from points list
            if point_to_remove in self.points:
                self.points.remove(point_to_remove)
        
        print(f"Removed {actual_remove} membrane points, {len(self.points)} points remaining")

    # -------- EQUIP LOGIC --------
    def equip_organelle(self, slot_index, organelle):
        # Special handling for Cell Membrane Extender: apply effect AND equip persistently
        if organelle.name == 'Cell Membrane Extender':
            # Apply effect once upon first equip for this specific organelle instance
            if not getattr(organelle, "_membrane_extender_applied", False):
                self.extend_membrane(10)
                self.radius += 5
                organelle._membrane_extender_applied = True
                print(f"Cell Membrane Extender equipped! Cell now has {len(self.points)} points and radius {self.radius}")
            else:
                print("Cell Membrane Extender already applied; equipping without reapplying effect.")
            # Continue to equip it in the designated slot (not consumed)
            # fall through to slot equip logic below
        
        if 0 <= slot_index < len(self.organelle_slots):
            # Equip to slot and remove from inventory
            from main import player_upgrades
            if organelle in player_upgrades["Organelles"]:
                player_upgrades["Organelles"].remove(organelle)
            self.organelle_slots[slot_index] = organelle

    def equip_protein(self, protein):
        from main import player_upgrades
        category = "Crafted Proteins" if hasattr(protein, 'is_crafted') else "Proteins"
        if protein not in player_upgrades[category]:
            print("Don't have this protein to equip!")
            return False
            
        # Get list of available membrane points (not already proteins)
        available_points = [p for p in self.points if not getattr(p, 'is_protein', False)]
        
        # Check if we have any points left to replace
        if not available_points:
            print("No available membrane points for protein equipping!")
            return False
        
        # Remove from central inventory first
        player_upgrades[category].remove(protein)
        
        # Choose a random membrane point to replace
        replace_point = random.choice(available_points)
        idx = self.points.index(replace_point)
        
        # Create new point with protein properties
        new_point = Point(replace_point.pos.copy(), self)
        new_point.is_visual = False  # Ensure it's marked as a membrane point first
        new_point.is_protein = True  # Mark as protein point
        new_point.set_upgrade(protein)  # Set visual properties
        
        # Replace the point and maintain its springs
        self.points[idx] = new_point
        for spring in self.springs:
            if spring.point1 == replace_point:
                spring.point1 = new_point
            if spring.point2 == replace_point:
                spring.point2 = new_point
        
        self.protein_inventory.append(protein)
        return True

    # -------- ATP / RESOURCES --------
    def drain_atp(self):
        count = sum(1 for o in self.organelle_slots if o) + sum(1 for p in self.protein_inventory if p)
        self.atp -= count * self.ATP_DRAIN_PER_ORGANELLE
        self.atp = max(0, self.atp)

    def can_act(self):
        return self.atp > 0

    def can_afford(self, cost: dict):
        return all(self.molecules.get(k, 0) >= v for k, v in cost.items())

    def buy_upgrade(self, item, category="Organelles"):
        if not self.can_afford(item.get("cost", {})):
            return False
        for key, amt in item["cost"].items():
            self.molecules[key] -= amt
        from main import player_upgrades
        if item not in player_upgrades[category]:
            player_upgrades[category].append(item)
        return True

    # -------- UPGRADES / ATTRIBUTES --------
    def apply_upgrades(self):
        for attr in self.attributes:  # reset
            self.attributes[attr] = 0
        # Apply boosts from equipped proteins
        for protein in self.protein_inventory:
            for boost in getattr(protein, "boosts", []):
                if boost["type"] in self.attributes:
                    self.attributes[boost["type"]] += boost["amount"]
        # Apply boosts from equipped organelles
        for organelle in self.organelle_slots:
            if organelle:  # Skip empty slots
                for boost in getattr(organelle, "boosts", []):
                    if boost["type"] in self.attributes:
                        self.attributes[boost["type"]] += boost["amount"]

    # -------- COLLISION --------
    def is_colliding(self, molecule):
        for lipid in self.points:
            if lipid.pos.distance_to(molecule.pos) < lipid.radius + 5:
                return True
        return False

    def collect(self, molecule):
        self.molecules[molecule.type] += molecule.value

    def update_visual_upgrades(self):
        # This method is kept as a placeholder for future organelle visualization
        # Currently only proteins are visualized as part of the membrane
        pass
        
        self.initial_shape = self.calculate_shape()
        self.rest_area = self.calculate_area()
        # # Only use membrane points for shape calculations
        # if len(membrane_points) == n_membrane_points:  # Only update if membrane points count hasn't changed
        #     self.initial_shape = [p.pos - self.center for p in membrane_points]
        #     self.rest_area = self.calculate_area()

    # -------- SPLIT (Mitosis) --------
    def drop_upgrade_molecules(self):
        """Drop molecules worth 75% of equipped upgrades' cost when cell dies"""
        from config import ORGANELLE_DATA, PROTEIN_DATA
        from molecule import Protein, Lipid, NucleicAcid, Carbohydrate
        import random
        
        total_cost = {"protein": 0, "lipid": 0, "carbohydrate": 0, "nucleic_acid": 0}
        
        # Calculate total cost of equipped organelles
        for organelle in self.organelle_slots:
            if organelle and hasattr(organelle, 'name'):
                # Find organelle data in config
                organelle_cost = None
                for category_list in ORGANELLE_DATA.values():
                    for organelle_data in category_list:
                        if organelle_data['name'] == organelle.name:
                            organelle_cost = organelle_data.get('cost', {})
                            break
                    if organelle_cost:
                        break
                
                # Add to total cost
                if organelle_cost:
                    for resource, amount in organelle_cost.items():
                        if resource in total_cost:
                            total_cost[resource] += amount
        
        # Calculate total cost of equipped proteins
        for protein in self.protein_inventory:
            if hasattr(protein, 'name'):
                # Find protein data in config
                protein_cost = None
                for category_list in PROTEIN_DATA.values():
                    for protein_data in category_list:
                        if protein_data['name'] == protein.name:
                            protein_cost = protein_data.get('cost', {})
                            break
                    if protein_cost:
                        break
                
                # Add to total cost
                if protein_cost:
                    for resource, amount in protein_cost.items():
                        if resource in total_cost:
                            total_cost[resource] += amount
        
        # Calculate 75% of total cost
        drop_amounts = {}
        for resource, amount in total_cost.items():
            drop_amounts[resource] = int(amount * 0.75)
        
        # Group molecules to avoid excessive clutter (create fewer, higher-value molecules)
        dropped_molecules = []
        molecule_classes = {
            "protein": Protein,
            "lipid": Lipid,
            "carbohydrate": Carbohydrate,
            "nucleic_acid": NucleicAcid
        }
        
        for resource, total_amount in drop_amounts.items():
            if total_amount > 0:
                # Create fewer molecules with higher values (group by 3-10 per molecule)
                while total_amount > 0:
                    # Determine how much this molecule should be worth (3-10, but not more than remaining)
                    molecule_value = min(random.randint(3, 10), total_amount)
                    
                    # Create position near the cell center with some spread
                    offset_x = random.uniform(-50, 50)
                    offset_y = random.uniform(-50, 50)
                    drop_pos = self.center + pygame.Vector2(offset_x, offset_y)
                    
                    # Create the molecule
                    molecule_class = molecule_classes[resource]
                    molecule = molecule_class(drop_pos)
                    molecule.value = molecule_value  # Override the random value
                    
                    dropped_molecules.append(molecule)
                    total_amount -= molecule_value
        
        return dropped_molecules

    # -------- UPDATE --------
    def update(self, surface, events, dt, camera=None):
        super().update(surface, events, dt, camera=camera)
        self.apply_upgrades()
        
        # Update health regeneration
        import time
        current_time = time.time()
        delta_time = dt  # dt is already in seconds from main.py
        self.update_health_regeneration(current_time, delta_time)

        if not self.is_player:
            from main import player_cells
            # Use .center for all position logic
            nearest_player = min(player_cells, key=lambda c: c.center.distance_to(self.center), default=None)

            if nearest_player:
                # Get direction toward nearest player
                direction = nearest_player.center - self.center
                dist = direction.length()

                if dist > 1:
                    direction = direction.normalize()
                else:
                    direction = pygame.Vector2(0, 0)

                # Move toward player (diagonals work because both axes are set)
                speed = 1.0
                move_vec = direction * speed * (dt / 16.67)
                self.center += move_vec

                # Keep within bounds
                # self.center.x = max(0, min(self.center.x, 2000))
                # self.center.y = max(0, min(self.center.y, 2000))

# Visual upgrade functionality now integrated into Point class

# Movement and behavior constants (duplicated to avoid circular imports)
MOVEMENT_DASHING = "dashing"
MOVEMENT_GLIDING = "gliding"  
MOVEMENT_CHARGING = "charging"
BEHAVIOR_NEUTRAL = "neutral"
BEHAVIOR_AGGRESSIVE = "aggressive"

class EnemyCell(Cell):
    """Enhanced enemy cell with configurable behavior and movement patterns"""
    
    def __init__(self, pos, points=12, radius=40, membrane_molecule=None):
        super().__init__(pos, points, radius, membrane_molecule)
        
        # Override base stats with enemy stats (tank-like: high endurance)
        from config import BASE_ENEMY_STATS
        self.base_strength = BASE_ENEMY_STATS['strength']
        self.base_endurance = BASE_ENEMY_STATS['endurance']
        self.base_dexterity = BASE_ENEMY_STATS['dexterity']
        self.base_intelligence = BASE_ENEMY_STATS['intelligence']
        
        # Recalculate health based on enemy stats
        self.max_health = 100 + (self.base_endurance * 5)
        self.health = self.max_health
        
        # Combat and targeting system
        from config import VIEW_SCALE
        self.view_range = VIEW_SCALE * radius  # View range based on radius
        self.target = None  # Current target entity
        self.behavior = random.choice([BEHAVIOR_NEUTRAL, BEHAVIOR_AGGRESSIVE])
        self.movement_type = random.choice([MOVEMENT_DASHING, MOVEMENT_GLIDING, MOVEMENT_CHARGING])
        
        # Movement state variables
        self.velocity = pygame.Vector2(0, 0)
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.charge_timer = 0
        self.charge_target_pos = None
        self.is_charging = False
        
        # Visual distinction for enemy cells
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        color = (255, 100, 100) if self.behavior == BEHAVIOR_AGGRESSIVE else (255, 180, 100)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

    def find_nearest_target(self, all_cells):
        """Find the nearest player cell within view range"""
        if not all_cells:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for cell in all_cells:
            # Only target player cells
            if not getattr(cell, 'is_player', False):
                continue
                
            distance = self.center.distance_to(cell.center)
            if distance <= self.view_range and distance < min_distance:
                min_distance = distance
                nearest = cell
                
        return nearest

    def update_enemy_movement(self, delta_time):
        """Update position based on movement type and target"""
        if self.movement_type == MOVEMENT_DASHING:
            self._update_dashing_movement(delta_time)
        elif self.movement_type == MOVEMENT_GLIDING:
            self._update_gliding_movement(delta_time)
        elif self.movement_type == MOVEMENT_CHARGING:
            self._update_charging_movement(delta_time)

    def _update_dashing_movement(self, delta_time):
        """Dash-based movement pattern"""
        self.dash_cooldown -= delta_time
        
        if self.dash_cooldown <= 0 and self.target:
            # Start a new dash towards target
            direction = (self.target.center - self.center).normalize() if self.target else pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.velocity = direction * 120  # High dash speed
            self.dash_timer = 0.8  # Dash duration
            self.dash_cooldown = 3.0  # Cooldown between dashes
        
        if self.dash_timer > 0:
            # Continue dashing - move all points together
            movement = self.velocity * delta_time
            self.center += movement
            for point in self.points:
                point.pos += movement
            self.dash_timer -= delta_time
        else:
            # Not dashing, gradually slow down
            self.velocity *= 0.92

    def _update_gliding_movement(self, delta_time):
        """Constant speed gliding movement"""
        if self.target:
            direction = (self.target.center - self.center).normalize()
            speed = 40  # Constant gliding speed
            movement = direction * speed * delta_time
        else:
            # Random wandering if no target
            if random.random() < 0.05:  # Change direction occasionally
                self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 15
            movement = self.velocity * delta_time
        
        # Move all points together
        self.center += movement
        for point in self.points:
            point.pos += movement

    def _update_charging_movement(self, delta_time):
        """Charging movement with cooldown cycles"""
        if self.target and not self.is_charging and self.charge_timer <= 0:
            # Start charging at target position
            self.charge_target_pos = self.target.center.copy()
            self.is_charging = True
            self.charge_timer = 1.2  # Charge duration
            
        if self.is_charging and self.charge_target_pos:
            # Move towards charge target
            direction = (self.charge_target_pos - self.center)
            distance = direction.length()
            if distance > 10:
                direction = direction.normalize()
                speed = 80  # Charge speed
                movement = direction * speed * delta_time
                self.center += movement
                for point in self.points:
                    point.pos += movement
            else:
                # Reached target, start cooldown
                self.is_charging = False
                self.charge_timer = 2.5  # Cooldown period
        elif self.charge_timer > 0:
            # Cooldown period
            self.charge_timer -= delta_time

    def update(self, surface, events, dt, camera=None):
        """Override the update method to use new enemy behavior"""
        # Call parent update for physics and base functionality
        SoftBody.update(self, surface, events, dt, camera=camera)
        self.apply_upgrades()
        
        if not self.is_player:
            from main import player_cells, enemy_cells
            all_cells = player_cells + enemy_cells
            
            # Find target based on behavior
            if self.behavior == BEHAVIOR_AGGRESSIVE:
                self.target = self.find_nearest_target(all_cells)
            elif self.behavior == BEHAVIOR_NEUTRAL:
                # Only target if being attacked (not implemented yet)
                pass
            
            # Update movement based on type
            delta_time = dt / 1000.0  # Convert to seconds
            self.update_enemy_movement(delta_time)