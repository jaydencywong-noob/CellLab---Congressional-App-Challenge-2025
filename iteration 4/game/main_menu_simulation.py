import pygame
import random
import math
from entity import Cell
from molecule import Lipid

class MainMenuSimulation:
    """Manages softbody simulation for main menu background"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Simulation area (left side of screen)
        self.sim_width = screen_width // 2  # Left half of screen
        self.sim_height = screen_height
        self.sim_x = 0
        self.sim_y = 0
        
        # Softbody list
        self.softbodies = []
        
        # Simulation parameters
        self.gravity = pygame.Vector2(0, 50)  # Gentle downward pull
        self.air_resistance = 0.98  # Slow down movement over time
        self.boundary_bounce = 0.7  # Energy retained on boundary collision
        
        # Splitting parameters
        self.split_timer = 0
        self.split_interval_min = 5.0  # Minimum seconds between splits
        self.split_interval_max = 15.0  # Maximum seconds between splits
        self.next_split_time = random.uniform(self.split_interval_min, self.split_interval_max)
        self.min_points_before_removal = 3
        
        # Spawn parameters
        self.spawn_timer = 0
        self.spawn_delay = 2.0  # Seconds after last softbody is removed
        
        # Initialize with first softbody
        self.spawn_new_softbody()
    
    def spawn_new_softbody(self):
        """Spawn a new softbody with random position and velocity"""
        # Random position within simulation area
        margin = 100
        pos_x = random.randint(margin, self.sim_width - margin)
        pos_y = random.randint(margin, self.sim_height - margin)
        
        # Create softbody cell with specified parameters
        softbody = Cell(
            pos=(pos_x, pos_y),
            points=25,  # As requested
            radius=50,  # As requested
            membrane_molecule=Lipid
        )
        
        # Add random initial velocity for floating effect
        velocity_magnitude = random.uniform(20, 50)
        angle = random.uniform(0, 2 * math.pi)
        softbody.velocity = pygame.Vector2(
            velocity_magnitude * math.cos(angle),
            velocity_magnitude * math.sin(angle)
        )
        
        # Add random angular velocity for spinning
        softbody.angular_velocity = random.uniform(-2.0, 2.0)  # Radians per second
        softbody.rotation_angle = 0
        
        self.softbodies.append(softbody)
        
        # Reset spawn timer
        self.spawn_timer = 0
    
    def update(self, delta_time):
        """Update simulation physics and logic"""
        # Update split timer
        self.split_timer += delta_time
        
        # Update each softbody
        for softbody in self.softbodies[:]:  # Use slice to allow safe removal
            self.update_softbody(softbody, delta_time)
        
        # Check for splitting
        if self.split_timer >= self.next_split_time and self.softbodies:
            self.try_split_random_softbody()
            self.split_timer = 0
            self.next_split_time = random.uniform(self.split_interval_min, self.split_interval_max)
        
        # Check if we need to spawn new softbodies
        if not self.softbodies:
            self.spawn_timer += delta_time
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_new_softbody()
        
        # Remove softbodies that are too small or off-screen
        self.cleanup_softbodies()
    
    def update_softbody(self, softbody, delta_time):
        """Update individual softbody physics"""
        # Apply gravity
        softbody.velocity += self.gravity * delta_time
        
        # Apply air resistance
        softbody.velocity *= self.air_resistance
        
        # Update position
        softbody.center += softbody.velocity * delta_time
        softbody.pos = softbody.center  # Keep pos in sync
        
        # Update rotation
        if hasattr(softbody, 'angular_velocity'):
            softbody.rotation_angle += softbody.angular_velocity * delta_time
            
            # Apply rotation to points (visual spinning effect)
            if hasattr(softbody, 'points'):
                for point in softbody.points:
                    # Rotate point around center
                    relative_pos = point.pos - softbody.center
                    angle = softbody.angular_velocity * delta_time
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)
                    
                    new_x = relative_pos.x * cos_a - relative_pos.y * sin_a
                    new_y = relative_pos.x * sin_a + relative_pos.y * cos_a
                    
                    point.pos = softbody.center + pygame.Vector2(new_x, new_y)
        
        # Boundary collision
        self.handle_boundary_collision(softbody)
        
        # Update softbody internal physics if it has an update method
        if hasattr(softbody, 'update'):
            try:
                # Call with minimal parameters to avoid errors
                softbody.update(None, [], delta_time, None)
            except:
                pass  # Ignore errors from softbody update
    
    def handle_boundary_collision(self, softbody):
        """Handle collisions with simulation boundaries"""
        radius = getattr(softbody, 'radius', 50)
        
        # Left boundary
        if softbody.center.x - radius < self.sim_x:
            softbody.center.x = self.sim_x + radius
            softbody.velocity.x = abs(softbody.velocity.x) * self.boundary_bounce
            
        # Right boundary
        if softbody.center.x + radius > self.sim_x + self.sim_width:
            softbody.center.x = self.sim_x + self.sim_width - radius
            softbody.velocity.x = -abs(softbody.velocity.x) * self.boundary_bounce
            
        # Top boundary
        if softbody.center.y - radius < self.sim_y:
            softbody.center.y = self.sim_y + radius
            softbody.velocity.y = abs(softbody.velocity.y) * self.boundary_bounce
            
        # Bottom boundary
        if softbody.center.y + radius > self.sim_y + self.sim_height:
            softbody.center.y = self.sim_y + self.sim_height - radius
            softbody.velocity.y = -abs(softbody.velocity.y) * self.boundary_bounce
    
    def try_split_random_softbody(self):
        """Attempt to split a random softbody"""
        if not self.softbodies:
            return
            
        # Filter softbodies that can be split (more than min_points_before_removal)
        splittable = [sb for sb in self.softbodies 
                     if hasattr(sb, 'points') and len(sb.points) > self.min_points_before_removal]
        
        if not splittable:
            return
            
        # Choose random softbody to split
        target = random.choice(splittable)
        
        # Attempt to split it
        if hasattr(target, 'split_body') and callable(target.split_body):
            try:
                result = target.split_body()
                if result:  # If split was successful
                    sb1, sb2, old_body = result
                    
                    # Remove old body
                    if old_body in self.softbodies:
                        self.softbodies.remove(old_body)
                    
                    # Add new bodies with inherited properties
                    for new_body in [sb1, sb2]:
                        # Inherit velocity with some randomization
                        base_velocity = getattr(old_body, 'velocity', pygame.Vector2(0, 0))
                        random_factor = pygame.Vector2(
                            random.uniform(-20, 20),
                            random.uniform(-20, 20)
                        )
                        new_body.velocity = base_velocity * 0.5 + random_factor
                        
                        # Inherit angular velocity with randomization
                        base_angular = getattr(old_body, 'angular_velocity', 0)
                        new_body.angular_velocity = base_angular + random.uniform(-1, 1)
                        new_body.rotation_angle = 0
                        
                        self.softbodies.append(new_body)
            except Exception as e:
                print(f"Split failed: {e}")
    
    def cleanup_softbodies(self):
        """Remove softbodies that are too small or should be removed"""
        to_remove = []
        
        for softbody in self.softbodies:
            should_remove = False
            
            # Remove if too few points
            if hasattr(softbody, 'points') and len(softbody.points) <= self.min_points_before_removal:
                should_remove = True
            
            # Remove if too far off screen (add exit animation)
            margin = 200
            if (softbody.center.x < -margin or 
                softbody.center.x > self.sim_width + margin or
                softbody.center.y < -margin or 
                softbody.center.y > self.sim_height + margin):
                should_remove = True
            
            if should_remove:
                to_remove.append(softbody)
        
        # Remove marked softbodies
        for softbody in to_remove:
            if softbody in self.softbodies:
                self.softbodies.remove(softbody)
    
    def draw(self, screen, camera=None):
        """Draw all softbodies in the simulation"""
        # Create a simple camera-like object for drawing if none provided
        class SimpleCamera:
            zoom = 0.5  # Smaller scale for main menu
            def world_to_screen(self, pos):
                return (int(pos.x * self.zoom), int(pos.y * self.zoom))
        
        if camera is None:
            camera = SimpleCamera()
        
        # Draw simulation boundary (optional debug)
        # pygame.draw.rect(screen, (50, 50, 100), 
        #                 (self.sim_x, self.sim_y, self.sim_width, self.sim_height), 2)
        
        # Draw all softbodies
        for softbody in self.softbodies:
            if hasattr(softbody, 'draw'):
                try:
                    softbody.draw(screen, camera)
                except:
                    # Fallback drawing
                    screen_pos = camera.world_to_screen(softbody.center)
                    radius = int(softbody.radius * camera.zoom)
                    pygame.draw.circle(screen, (100, 150, 200), screen_pos, radius, 2)
            else:
                # Fallback drawing
                screen_pos = camera.world_to_screen(softbody.center)
                radius = int(getattr(softbody, 'radius', 50) * camera.zoom)
                pygame.draw.circle(screen, (100, 150, 200), screen_pos, radius, 2)
    
    def reset(self):
        """Reset simulation to initial state"""
        self.softbodies.clear()
        self.split_timer = 0
        self.spawn_timer = 0
        self.next_split_time = random.uniform(self.split_interval_min, self.split_interval_max)
        self.spawn_new_softbody()