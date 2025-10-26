"""
Visual Effects System for Cell Evolution Game

This module handles all visual effects including:
1. Cohesive Color Palettes
2. Transparency Layers for Depth (Blob Maps)
3. Particle Effects
4. Trails and Motion Blur
"""

import pygame
import random
import math
import time
from typing import Tuple, List, Optional

class ColorPalette:
    """Generates and manages cohesive color palettes based on oceanic themes"""
    
    def __init__(self, base_hue: int = 180, saturation_range: Tuple[int, int] = (60, 90), 
                 lightness_range: Tuple[int, int] = (30, 70)):
        """
        Initialize color palette generator
        Args:
            base_hue: Base hue (0-360), default 180 (cyan/teal)
            saturation_range: Min/max saturation values (0-100)
            lightness_range: Min/max lightness values (0-100)
        """
        self.base_hue = base_hue
        self.saturation_range = saturation_range
        self.lightness_range = lightness_range
        self.colors = self._generate_palette()
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """Convert HSL to RGB color"""
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _generate_palette(self) -> List[Tuple[int, int, int]]:
        """Generate a cohesive color palette"""
        colors = []
        
        # Primary colors (5 variations of base hue)
        for i in range(5):
            hue = (self.base_hue + random.randint(-30, 30)) % 360
            sat = random.randint(*self.saturation_range)
            light = random.randint(*self.lightness_range)
            colors.append(self._hsl_to_rgb(hue, sat, light))
        
        # Complementary colors (2 variations)
        comp_hue = (self.base_hue + 180) % 360
        for i in range(2):
            hue = (comp_hue + random.randint(-20, 20)) % 360
            sat = random.randint(40, 70)  # Lower saturation for complements
            light = random.randint(20, 50)  # Darker for contrast
            colors.append(self._hsl_to_rgb(hue, sat, light))
        
        return colors
    
    def get_color(self, index: int = None) -> Tuple[int, int, int]:
        """Get a color from the palette"""
        if index is None:
            return random.choice(self.colors)
        return self.colors[index % len(self.colors)]
    
    def get_color_with_alpha(self, index: int = None, alpha: int = 255) -> Tuple[int, int, int, int]:
        """Get a color with alpha channel"""
        color = self.get_color(index)
        return (*color, alpha)


class BlobMap:
    """Simple noise-based blob map for organic depth layers"""
    
    def __init__(self, width: int, height: int, scale: float = 0.02, time_scale: float = 0.001):
        """
        Initialize blob map
        Args:
            width: Map width
            height: Map height  
            scale: Noise scale (smaller = larger blobs)
            time_scale: Animation speed
        """
        self.width = width
        self.height = height
        self.scale = scale
        self.time_scale = time_scale
        self.start_time = time.time()
    
    def _simple_noise(self, x: float, y: float, t: float) -> float:
        """Simple pseudo-noise function (replace with Perlin if available)"""
        # Simple sinusoidal noise as fallback
        return (math.sin(x * 0.1 + t) + math.sin(y * 0.1 + t) + 
                math.sin((x + y) * 0.05 + t * 0.5)) / 3.0
    
    def get_blob_value(self, x: float, y: float) -> float:
        """Get blob intensity at position (0.0 to 1.0)"""
        current_time = time.time() - self.start_time
        noise_val = self._simple_noise(x * self.scale, y * self.scale, current_time * self.time_scale)
        return max(0.0, min(1.0, (noise_val + 1.0) / 2.0))  # Normalize to 0-1
    
    def get_depth_layer(self, x: float, y: float, layer_count: int = 3) -> int:
        """Get which depth layer (0 to layer_count-1) this position belongs to"""
        blob_val = self.get_blob_value(x, y)
        return int(blob_val * layer_count)


class ParticleSystem:
    """Manages organic floating particles"""
    
    def __init__(self, max_particles: int = 50):
        self.max_particles = max_particles
        self.particles = []
    
    def add_particle(self, pos: Tuple[float, float], color: Tuple[int, int, int] = (255, 255, 255),
                    size: float = 2.0, lifetime: float = 3.0, velocity: Tuple[float, float] = None):
        """Add a new particle"""
        if len(self.particles) >= self.max_particles:
            return
        
        if velocity is None:
            velocity = (random.uniform(-10, 10), random.uniform(-10, 10))
        
        particle = {
            'pos': list(pos),
            'color': color,
            'size': size,
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'velocity': list(velocity),
            'alpha': 255
        }
        self.particles.append(particle)
    
    def update(self, dt: float):
        """Update all particles"""
        for particle in self.particles[:]:  # Copy list to avoid modification during iteration
            # Update position
            particle['pos'][0] += particle['velocity'][0] * dt
            particle['pos'][1] += particle['velocity'][1] * dt
            
            # Update lifetime and alpha
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
                continue
            
            # Fade alpha based on lifetime
            fade_factor = particle['lifetime'] / particle['max_lifetime']
            particle['alpha'] = int(255 * fade_factor)
            
            # Add some organic drift
            particle['velocity'][0] += random.uniform(-5, 5) * dt
            particle['velocity'][1] += random.uniform(-5, 5) * dt
            
            # Damping
            particle['velocity'][0] *= 0.98
            particle['velocity'][1] *= 0.98
    
    def draw(self, surface: pygame.Surface, camera=None):
        """Draw all particles"""
        for particle in self.particles:
            if camera:
                screen_pos = camera.world_to_screen(particle['pos'])
            else:
                screen_pos = particle['pos']
            
            # Create particle surface with alpha
            size = max(1, int(particle['size']))
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (*particle['color'], particle['alpha'])
            pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
            
            # Blit with position centered
            surface.blit(particle_surf, (screen_pos[0] - size, screen_pos[1] - size))


class TrailSystem:
    """Manages motion trails for entities"""
    
    def __init__(self):
        self.trails = {}  # entity_id -> trail data
    
    def update_trail(self, entity_id: str, pos: Tuple[float, float], max_length: int = 8):
        """Update trail for an entity"""
        if entity_id not in self.trails:
            self.trails[entity_id] = []
        
        trail = self.trails[entity_id]
        trail.append(pos)
        
        # Limit trail length
        if len(trail) > max_length:
            trail.pop(0)
    
    def draw_trail(self, surface: pygame.Surface, entity_id: str, color: Tuple[int, int, int], 
                  width: int = 3, camera=None):
        """Draw trail for an entity"""
        if entity_id not in self.trails or len(self.trails[entity_id]) < 2:
            return
        
        trail = self.trails[entity_id]
        
        for i in range(len(trail) - 1):
            # Calculate alpha based on position in trail
            alpha = int(255 * (i + 1) / len(trail))
            
            if camera:
                start_pos = camera.world_to_screen(trail[i])
                end_pos = camera.world_to_screen(trail[i + 1])
            else:
                start_pos = trail[i]
                end_pos = trail[i + 1]
            
            # Create line surface with alpha
            line_surf = pygame.Surface((abs(end_pos[0] - start_pos[0]) + width * 2, 
                                      abs(end_pos[1] - start_pos[1]) + width * 2), pygame.SRCALPHA)
            
            # Draw line on the surface
            relative_start = (width, width) if start_pos[0] <= end_pos[0] else (line_surf.get_width() - width, width)
            relative_end = (line_surf.get_width() - width, line_surf.get_height() - width) if start_pos[0] <= end_pos[0] else (width, line_surf.get_height() - width)
            
            pygame.draw.line(line_surf, (*color, alpha), relative_start, relative_end, width)
            
            # Blit to main surface
            blit_x = min(start_pos[0], end_pos[0]) - width
            blit_y = min(start_pos[1], end_pos[1]) - width
            surface.blit(line_surf, (blit_x, blit_y), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def clear_trail(self, entity_id: str):
        """Clear trail for an entity"""
        if entity_id in self.trails:
            del self.trails[entity_id]


# Global instances
color_palette = ColorPalette()
blob_map = BlobMap(2000, 2000)  # Large enough for game world
particle_system = ParticleSystem()
trail_system = TrailSystem()


def draw_cell_with_effects(surface: pygame.Surface, cell, camera, delta_time: float, enable_effects: bool = True):
    """Draw a cell with visual effects applied"""
    if not enable_effects or not hasattr(cell, 'center') or not hasattr(cell, 'points'):
        # Fallback to basic drawing
        cell.draw(surface, camera)
        return
    
    # Get base color with stable variation based on cell's unique ID
    # Use object id which remains constant even as the cell moves
    cell_hash = hash(id(cell)) % len(color_palette.colors)
    base_color = color_palette.get_color(cell_hash)
    
    # Apply smooth color oscillation using sin/cos functions - restored to original values
    time_factor = (time.time() * 0.5)  # Slow oscillation
    brightness_mod = (math.sin(time_factor) * 0.3 + 1.0)  # Oscillate between 0.7 and 1.3
    
    # Apply brightness modulation to base color
    oscillated_color = tuple(max(0, min(255, int(c * brightness_mod))) for c in base_color)
    
    # Convert points to screen coordinates
    screen_points = []
    for point in cell.points:
        if hasattr(point, 'pos'):
            screen_points.append(camera.world_to_screen(point.pos))
    
    if len(screen_points) < 3:
        # Not enough points to draw polygon, fallback to basic drawing
        cell.draw(surface, camera)
        return
    
    # Draw multiple transparency layers for depth using the actual cell shape
    for layer in range(3):
        alpha = 40 + (layer * 30)  # Varying alpha for depth
        size_multiplier = 1.0 + (layer * 0.05)
        
        # Adjust color slightly for each layer using oscillated base color
        layer_color = tuple(max(0, min(255, c + layer * 15)) for c in oscillated_color)
        
        # Calculate expanded points for this layer
        if size_multiplier != 1.0:
            center_screen = camera.world_to_screen(cell.center)
            expanded_points = []
            for point in screen_points:
                # Expand outward from center
                dx = point[0] - center_screen[0]
                dy = point[1] - center_screen[1]
                expanded_x = center_screen[0] + dx * size_multiplier
                expanded_y = center_screen[1] + dy * size_multiplier
                expanded_points.append((expanded_x, expanded_y))
        else:
            expanded_points = screen_points
        
        # Create surface for this layer
        min_x = min(p[0] for p in expanded_points) - 10
        max_x = max(p[0] for p in expanded_points) + 10
        min_y = min(p[1] for p in expanded_points) - 10
        max_y = max(p[1] for p in expanded_points) + 10
        
        layer_width = int(max_x - min_x)
        layer_height = int(max_y - min_y)

        MAX_LAYER_SIZE = 2048  # Prevent out-of-memory by limiting surface size
        if 0 < layer_width <= MAX_LAYER_SIZE and 0 < layer_height <= MAX_LAYER_SIZE:
            layer_surf = pygame.Surface((layer_width, layer_height), pygame.SRCALPHA)
            # Adjust points relative to surface
            relative_points = [(p[0] - min_x, p[1] - min_y) for p in expanded_points]

            try:
                pygame.draw.polygon(layer_surf, (*layer_color, alpha), relative_points)
                surface.blit(layer_surf, (min_x, min_y), special_flags=pygame.BLEND_ALPHA_SDL2)
            except ValueError:
                # If polygon drawing fails, skip this layer
                pass
        # If layer is too large, skip drawing to avoid memory crash
    
    # Draw the cell's individual points with effects
    for point in cell.points:
        if hasattr(point, 'pos'):
            point_screen_pos = camera.world_to_screen(point.pos)
            point_radius = max(1, int(getattr(point, 'radius', 3) * camera.zoom))

            # If this point is a protein, draw its image/icon
            if (hasattr(point, 'type') and point.type == 'protein') or (hasattr(point, 'is_protein') and point.is_protein):
                # Draw protein image with alpha and scaling
                if hasattr(point, 'image') and point.image:
                    scale = max(0.4, camera.zoom)
                    scaled_size = int(20 * scale)
                    img = pygame.transform.scale(point.image, (scaled_size, scaled_size))
                    img.set_alpha(200)
                    img_rect = img.get_rect(center=point_screen_pos)
                    surface.blit(img, img_rect)
                    # Draw outline for visibility
                    pygame.draw.circle(surface, (150, 200, 255), point_screen_pos, scaled_size//2 + 2, 2)
                else:
                    # Fallback to accent color if no image
                    point_color = color_palette.get_color(5)
                    point_color = tuple(max(0, min(255, int(c * brightness_mod))) for c in point_color)
                    pygame.draw.circle(surface, (*point_color, 200), point_screen_pos, point_radius)
            else:
                # Draw regular membrane point with oscillated color and glow
                point_color = oscillated_color
                if point_radius > 0:
                    point_surf = pygame.Surface((point_radius * 4, point_radius * 4), pygame.SRCALPHA)
                    pygame.draw.circle(point_surf, (*point_color, 200), (point_radius * 2, point_radius * 2), point_radius)
                    pygame.draw.circle(point_surf, (*point_color, 80), (point_radius * 2, point_radius * 2), point_radius * 2)
                    surface.blit(point_surf, (point_screen_pos[0] - point_radius * 2, point_screen_pos[1] - point_radius * 2))


def update_visual_systems(dt: float):
    """Update all visual systems"""
    particle_system.update(dt)  # dt is already in seconds


def draw_visual_systems(surface: pygame.Surface, camera):
    """Draw all visual system elements"""
    particle_system.draw(surface, camera)


def draw_molecule_with_effects(surface: pygame.Surface, molecule, camera, delta_time: float, enable_effects: bool = True):
    """Draw a molecule with visual effects applied"""
    if not enable_effects or not hasattr(molecule, 'pos'):
        # Fallback to basic drawing
        molecule.draw(surface, camera)
        return
    
    screen_pos = camera.world_to_screen(molecule.pos)
    
    # Get base color from palette based on molecule type with more variation
    if hasattr(molecule, 'type'):
        if molecule.type == 'protein':
            base_color = color_palette.get_color(0)
        elif molecule.type == 'lipid':
            base_color = color_palette.get_color(1)
        elif molecule.type == 'nucleic_acid':
            base_color = color_palette.get_color(2)
        else:
            base_color = color_palette.get_color(3)
    else:
        base_color = color_palette.get_color(0)
    
    # Apply smooth color oscillation using sin/cos functions
    time_factor = (time.time() * 0.3)  # Slightly different speed for molecules
    brightness_mod = (math.cos(time_factor) * 0.25 + 1.0)  # Oscillate between 0.75 and 1.25
    
    # Apply brightness modulation to base color
    oscillated_color = tuple(max(0, min(255, int(c * brightness_mod))) for c in base_color)
    
    # Get molecule radius
    radius = getattr(molecule, 'radius', 15)
    screen_radius = max(1, int(radius * camera.zoom))
    
    # Draw multiple transparency layers for depth
    for layer in range(2):  # Fewer layers for molecules
        alpha = 80 + (layer * 60)  # Higher alpha than cells
        size_multiplier = 1.0 + (layer * 0.15)
        
        # Adjust color slightly for each layer using oscillated color
        layer_color = tuple(max(0, min(255, c + layer * 20)) for c in oscillated_color)
        
        # Calculate layer radius
        layer_radius = int(screen_radius * size_multiplier)
        
        if layer_radius > 0:
            layer_surf = pygame.Surface((layer_radius * 2, layer_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(layer_surf, (*layer_color, alpha), (layer_radius, layer_radius), layer_radius)
            surface.blit(layer_surf, (screen_pos[0] - layer_radius, screen_pos[1] - layer_radius), 
                        special_flags=pygame.BLEND_ALPHA_SDL2)


def create_molecule_particles(molecules: list, camera):
    """Create particles from organic molecules"""
    for molecule in molecules:
        # More frequent particle emission
        if random.random() < 0.05:  # 5% chance per frame (5x more frequent)
            world_pos = (molecule.pos.x, molecule.pos.y)
            particle_system.add_particle(
                pos=world_pos,
                color=(255, 255, 255),
                size=random.uniform(1.0, 3.0),
                lifetime=random.uniform(4.0, 8.0),  # Longer lifetime
                velocity=(random.uniform(-20, 20), random.uniform(-20, 20))  # Faster/further velocity
            )
