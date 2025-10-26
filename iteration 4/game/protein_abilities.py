"""
Protein Ability System - Attack and Defense Proteins
Handles special protein behaviors, projectiles, and effects
"""

import pygame
import math
import random
from config import *

class Projectile:
    """Base class for all projectiles"""
    def __init__(self, pos, target, damage, speed, owner, color=(255, 100, 100)):
        self.pos = pygame.Vector2(pos)
        self.target = target
        self.damage = damage
        self.speed = speed
        self.owner = owner
        self.color = color
        self.radius = 5
        self.lifetime = 5.0  # Seconds before auto-despawn
        self.active = True
        
        # Calculate initial direction
        if target:
            target_pos = target.center if hasattr(target, 'center') else target.pos
            direction = target_pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
            self.velocity = direction * speed
        else:
            self.velocity = pygame.Vector2(0, 0)
    
    def update(self, delta_time, all_entities):
        """Update projectile position and check for hits"""
        if not self.active:
            return False
        
        # Update position
        self.pos += self.velocity * delta_time
        self.lifetime -= delta_time
        
        # Check if lifetime expired
        if self.lifetime <= 0:
            self.active = False
            return False
        
        # Check for collisions with entities
        for entity in all_entities:
            if entity == self.owner:
                continue  # Don't hit the owner
            
            entity_pos = entity.center if hasattr(entity, 'center') else entity.pos
            distance = self.pos.distance_to(entity_pos)
            entity_radius = getattr(entity, 'radius', 20)
            
            if distance < (self.radius + entity_radius):
                # Hit!
                self.on_hit(entity)
                self.active = False
                return False
        
        return True  # Still active
    
    def on_hit(self, target):
        """Called when projectile hits a target"""
        from entity import calculate_incoming_damage
        import time
        
        current_time = time.time()
        final_damage, combat_info = calculate_incoming_damage(
            self.damage, self.owner, target
        )
        target.take_damage(final_damage, current_time, attacker=self.owner)
        
        # Visual feedback
        feedback = f"Projectile hit for {final_damage:.1f} damage"
        if combat_info['dodged']:
            feedback += " (DODGED)"
        elif combat_info['critical']:
            feedback += " (CRITICAL!)"
        print(feedback)
    
    def draw(self, surface, camera):
        """Draw the projectile"""
        screen_pos = camera.world_to_screen(self.pos)
        pygame.draw.circle(surface, self.color, screen_pos, int(self.radius * camera.zoom))
        # Add glow effect
        glow_color = tuple(min(255, c + 50) for c in self.color[:3])
        pygame.draw.circle(surface, glow_color, screen_pos, int((self.radius + 2) * camera.zoom), 1)


class ProteinBomb:
    """Mine that explodes when enemies approach"""
    def __init__(self, pos, owner):
        self.pos = pygame.Vector2(pos)
        self.owner = owner
        self.radius = 10
        self.trigger_radius = PROTEIN_BOMB_TRIGGER_RADIUS
        self.explosion_radius = PROTEIN_BOMB_EXPLOSION_RADIUS
        self.damage = PROTEIN_BOMB_DAMAGE
        self.active = True
        self.triggered = False
        self.explosion_timer = 0
        self.explosion_duration = 0.3  # Visual explosion duration
        self.color = (200, 50, 50)
    
    def update(self, delta_time, all_entities):
        """Check for nearby enemies and explode"""
        if not self.active:
            return False
        
        if self.triggered:
            self.explosion_timer += delta_time
            if self.explosion_timer >= self.explosion_duration:
                self.active = False
                return False
            return True
        
        # Check for enemies within trigger radius
        for entity in all_entities:
            if entity == self.owner or getattr(entity, 'is_player', False):
                continue  # Don't trigger on owner or other player cells
            
            entity_pos = entity.center if hasattr(entity, 'center') else entity.pos
            distance = self.pos.distance_to(entity_pos)
            
            if distance < self.trigger_radius:
                self.explode(all_entities)
                return True
        
        return True
    
    def explode(self, all_entities):
        """Trigger explosion and damage nearby entities"""
        from entity import calculate_incoming_damage
        import time
        
        self.triggered = True
        current_time = time.time()
        print(f"Protein Bomb exploded at {self.pos}!")
        
        # Damage all entities in explosion radius
        for entity in all_entities:
            if entity == self.owner:
                continue
            
            entity_pos = entity.center if hasattr(entity, 'center') else entity.pos
            distance = self.pos.distance_to(entity_pos)
            
            if distance < self.explosion_radius:
                # Scale damage by distance (full damage at center, less at edges)
                damage_multiplier = 1.0 - (distance / self.explosion_radius)
                scaled_damage = self.damage * damage_multiplier
                
                final_damage, combat_info = calculate_incoming_damage(
                    scaled_damage, self.owner, entity
                )
                entity.take_damage(final_damage, current_time, attacker=self.owner)
                print(f"  Bomb damaged enemy for {final_damage:.1f}")
    
    def draw(self, surface, camera):
        """Draw the mine or explosion"""
        screen_pos = camera.world_to_screen(self.pos)
        
        if self.triggered:
            # Draw explosion
            explosion_progress = self.explosion_timer / self.explosion_duration
            explosion_size = int(self.explosion_radius * explosion_progress * camera.zoom)
            alpha = int(255 * (1.0 - explosion_progress))
            
            # Draw expanding circle
            color = (255, 100, 50)
            pygame.draw.circle(surface, color, screen_pos, explosion_size, 3)
            pygame.draw.circle(surface, (255, 200, 100), screen_pos, explosion_size // 2, 2)
        else:
            # Draw mine
            pygame.draw.circle(surface, self.color, screen_pos, int(self.radius * camera.zoom))
            # Pulsing trigger radius indicator
            pulse = abs(math.sin(pygame.time.get_ticks() / 500))
            trigger_alpha = int(100 * pulse)
            pygame.draw.circle(surface, (*self.color, trigger_alpha), screen_pos, 
                             int(self.trigger_radius * camera.zoom), 1)


class BarrierShield:
    """Orbiting shield that blocks damage"""
    def __init__(self, owner, index, total_shields):
        self.owner = owner
        self.index = index
        self.total_shields = total_shields
        self.angle_offset = (2 * math.pi / total_shields) * index
        self.orbit_radius = 50  # Distance from cell center
        self.rotation_speed = 1.0  # Radians per second
        self.current_angle = self.angle_offset
        self.active = True
        self.health = 30  # Shield has its own health
        self.max_health = 30
        self.radius = 15
        self.color = (80, 180, 255)
    
    def update(self, delta_time):
        """Update shield position around owner"""
        if not self.active:
            return False
        
        # Rotate around owner
        self.current_angle += self.rotation_speed * delta_time
        
        # Check if owner is still alive
        if not hasattr(self.owner, 'health') or self.owner.health <= 0:
            self.active = False
            return False
        
        return True
    
    def get_position(self):
        """Get current shield position"""
        owner_pos = self.owner.center if hasattr(self.owner, 'center') else self.owner.pos
        offset_x = self.orbit_radius * math.cos(self.current_angle)
        offset_y = self.orbit_radius * math.sin(self.current_angle)
        return owner_pos + pygame.Vector2(offset_x, offset_y)
    
    def absorb_damage(self, damage):
        """Shield takes damage, returns remaining damage that passes through"""
        self.health -= damage
        if self.health <= 0:
            remaining = abs(self.health)
            self.active = False
            print(f"Barrier Shield destroyed!")
            return remaining
        else:
            print(f"Barrier Shield absorbed {damage:.1f} damage ({self.health:.1f}/{self.max_health} remaining)")
            return 0  # All damage absorbed
    
    def draw(self, surface, camera):
        """Draw the shield"""
        if not self.active:
            return
        
        screen_pos = camera.world_to_screen(self.get_position())
        
        # Health-based color
        health_percent = self.health / self.max_health
        color = (
            int(80 + (175 * (1 - health_percent))),
            int(180 * health_percent),
            255
        )
        
        # Draw shield
        pygame.draw.circle(surface, color, screen_pos, int(self.radius * camera.zoom))
        pygame.draw.circle(surface, (200, 220, 255), screen_pos, int(self.radius * camera.zoom), 2)
        
        # Draw connection line to owner
        owner_screen_pos = camera.world_to_screen(
            self.owner.center if hasattr(self.owner, 'center') else self.owner.pos
        )
        pygame.draw.line(surface, (150, 200, 255, 128), owner_screen_pos, screen_pos, 1)


class AdhesionWeb:
    """Sticky web that slows enemies"""
    def __init__(self, pos, owner):
        self.pos = pygame.Vector2(pos)
        self.owner = owner
        self.radius = ADHESION_WEB_RADIUS
        self.slow_multiplier = ADHESION_WEB_SLOW
        self.duration = 5.0  # Seconds web lasts
        self.active = True
        self.color = (180, 140, 255)
    
    def update(self, delta_time, all_entities):
        """Apply slow effect to entities in range"""
        if not self.active:
            return False
        
        self.duration -= delta_time
        if self.duration <= 0:
            self.active = False
            return False
        
        # Apply slow to enemies
        for entity in all_entities:
            if entity == self.owner or getattr(entity, 'is_player', False):
                continue
            
            entity_pos = entity.center if hasattr(entity, 'center') else entity.pos
            distance = self.pos.distance_to(entity_pos)
            
            if distance < self.radius:
                # Apply slow effect (implemented as velocity reduction)
                if hasattr(entity, 'velocity'):
                    entity.velocity *= (1.0 - (self.slow_multiplier * 0.1))  # Gradual slow
        
        return True
    
    def draw(self, surface, camera):
        """Draw the web"""
        if not self.active:
            return
        
        screen_pos = camera.world_to_screen(self.pos)
        alpha = int(150 * (self.duration / 5.0))  # Fade out over time
        
        # Draw web circle
        pygame.draw.circle(surface, (*self.color, alpha), screen_pos, 
                         int(self.radius * camera.zoom), 2)
        
        # Draw web pattern
        num_lines = 8
        for i in range(num_lines):
            angle = (2 * math.pi / num_lines) * i
            end_x = screen_pos[0] + int(self.radius * camera.zoom * math.cos(angle))
            end_y = screen_pos[1] + int(self.radius * camera.zoom * math.sin(angle))
            pygame.draw.line(surface, (*self.color, alpha), screen_pos, (end_x, end_y), 1)
