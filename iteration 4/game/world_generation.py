import pygame
import math
import random
from enum import Enum
from config import (CHUNK_SIZE, MAP_SIZE, WORLD_BOUNDS, CELL_VIEW_RANGE, RENDER_DISTANCE,
                   BIOMES, MAP_UNDISCOVERED_COLOR, MAP_DISCOVERED_COLOR, MAP_VIEWED_COLOR, MAP_RED_ZONE_COLOR)

class ChunkState(Enum):
    UNDISCOVERED = 0
    DISCOVERED = 1
    CELL_VIEWED = 2

class NoiseGenerator:
    """Simple noise generator for procedural world generation"""
    
    def __init__(self, seed=None):
        if seed is None:
            seed = random.randint(0, 1000000)
        self.seed = seed
        random.seed(seed)
        
    def noise2d(self, x, y, scale=1.0):
        """Generate 2D noise value between 0 and 1"""
        # Simple deterministic noise function
        x *= scale
        y *= scale
        n = int(x * 57 + y * 131 + self.seed * 37) % 2147483647
        n = (n << 13) ^ n
        return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)
    
    def fractal_noise2d(self, x, y, octaves=4, persistence=0.5, scale=1.0):
        """Generate fractal noise for more natural-looking terrain"""
        value = 0.0
        amplitude = 1.0
        frequency = scale
        
        for _ in range(octaves):
            value += self.noise2d(x * frequency, y * frequency) * amplitude
            amplitude *= persistence
            frequency *= 2.0
            
        # Normalize to 0-1 range
        return max(0.0, min(1.0, (value + 1.0) / 2.0))

class Chunk:
    """Represents a single chunk of the world"""
    
    def __init__(self, x, y, world_generator):
        self.chunk_x = x
        self.chunk_y = y
        self.state = ChunkState.UNDISCOVERED
        self.biome = None
        self.entities = []  # Entities within this chunk
        self.molecules = []  # Molecules generated for this chunk
        self.world_generator = world_generator
        self.poi_type = None  # Point of Interest type
        self.poi_data = None  # Additional POI data
        self._generate_biome()
        self._generate_poi()  # Generate POI before molecules
        self._generate_molecules()
        
    def _generate_biome(self):
        """Generate biome for this chunk based on noise"""
        # Use chunk coordinates for biome generation with medium frequency for medium-sized biomes
        noise_value = self.world_generator.noise_gen.fractal_noise2d(
            self.chunk_x * 0.05, self.chunk_y * 0.05, octaves=3, scale=0.02
        )
        
        # Assign biome based on noise value
        if noise_value < 0.33:
            self.biome = "cold"
        elif noise_value < 0.66:
            self.biome = "warm"
        else:
            self.biome = "hot"
    
    def _generate_poi(self):
        """Generate Points of Interest with semi-rare chance"""
        import random
        
    # Increase POI chance (about 8% of chunks)
        if random.random() < 0.08:
            poi_types = ["molecule_abundance", "virus_cluster", "giant_enemy"]
            self.poi_type = random.choice(poi_types)
            
            if self.poi_type == "molecule_abundance":
                from molecule import Protein, Lipid, NucleicAcid, Carbohydrate
                molecule_types = [Protein, Lipid, NucleicAcid, Carbohydrate]
                self.poi_data = {
                    "molecule_type": random.choice(molecule_types),
                    "abundance_multiplier": random.randint(3, 8)
                }
            elif self.poi_type == "virus_cluster":
                from virus import CapsidVirus, FilamentousVirus, PhageVirus
                virus_types = [CapsidVirus, FilamentousVirus, PhageVirus]
                self.poi_data = {
                    "virus_type": random.choice(virus_types),
                    "cluster_count": random.randint(8, 20)
                }
            elif self.poi_type == "giant_enemy":
                self.poi_data = {
                    "points": 50,
                    "radius": 500
                }

    def _generate_molecules(self):
        """Generate molecules for this chunk"""
        import random
        from molecule import Protein, Lipid, NucleicAcid, Carbohydrate
        
        # Base number of molecules per chunk
        molecules_per_chunk = 15
        
        # If this is a molecule abundance POI, multiply by the abundance factor
        if self.poi_type == "molecule_abundance":
            molecules_per_chunk *= self.poi_data["abundance_multiplier"]
        
        world_rect = self.world_rect
        
        for _ in range(molecules_per_chunk):
            # Random position within the chunk
            x = random.randint(world_rect.left + 10, world_rect.right - 10)
            y = random.randint(world_rect.top + 10, world_rect.bottom - 10)
            pos = (x, y)
            
            # If molecule abundance POI, use specific type, otherwise random
            if self.poi_type == "molecule_abundance":
                molecule_type = self.poi_data["molecule_type"]
            else:
                molecule_type = random.choice([Protein, Lipid, NucleicAcid, Carbohydrate])
            
            molecule = molecule_type(pos)
            self.molecules.append(molecule)
    
    def spawn_poi_entities(self):
        """Spawn POI-specific entities when chunk is discovered"""
        if self.poi_type == "virus_cluster" and not hasattr(self, '_poi_spawned'):
            import random
            from virus import CapsidVirus, FilamentousVirus, PhageVirus
            
            virus_type = self.poi_data["virus_type"]
            cluster_count = self.poi_data["cluster_count"]
            world_rect = self.world_rect
            
            # Store virus data to be spawned by main.py
            if not hasattr(self, 'pending_virus_spawns'):
                self.pending_virus_spawns = []
            
            for _ in range(cluster_count):
                x = random.randint(world_rect.left + 50, world_rect.right - 50)
                y = random.randint(world_rect.top + 50, world_rect.bottom - 50)
                pos = (x, y)
                
                spawn_data = {
                    'virus_type': virus_type,
                    'position': pos,
                    'size': random.randint(100, 150)
                }
                self.pending_virus_spawns.append(spawn_data)
            
            self._poi_spawned = True
            
        elif self.poi_type == "giant_enemy" and not hasattr(self, '_poi_spawned'):
            world_rect = self.world_rect
            
            # Spawn giant enemy cell in center of chunk
            center_x = (world_rect.left + world_rect.right) // 2
            center_y = (world_rect.top + world_rect.bottom) // 2
            pos = (center_x, center_y)
            
            # Store spawn data to be handled by main.py
            if not hasattr(self, 'pending_enemy_spawn'):
                self.pending_enemy_spawn = {
                    'position': pos,
                    'points': self.poi_data["points"],
                    'radius': self.poi_data["radius"]
                }
            
            self._poi_spawned = True
    
    @property
    def world_pos(self):
        """Get world position of chunk's top-left corner"""
        return (self.chunk_x * CHUNK_SIZE[0], self.chunk_y * CHUNK_SIZE[1])
    
    @property
    def world_rect(self):
        """Get world rectangle of this chunk"""
        x, y = self.world_pos
        return pygame.Rect(x, y, CHUNK_SIZE[0], CHUNK_SIZE[1])
    
    def contains_world_pos(self, world_pos):
        """Check if world position is within this chunk"""
        return self.world_rect.collidepoint(world_pos)
    
    def update_entities(self, all_entities):
        """Update list of entities within this chunk"""
        self.entities.clear()
        chunk_rect = self.world_rect
        
        for entity in all_entities:
            if hasattr(entity, 'center'):
                if chunk_rect.collidepoint(entity.center):
                    self.entities.append(entity)
            elif hasattr(entity, 'pos'):
                if chunk_rect.collidepoint(entity.pos):
                    self.entities.append(entity)

class WorldGenerator:
    """Manages procedural world generation and chunk system"""
    
    def __init__(self, seed=None):
        self.noise_gen = NoiseGenerator(seed)
        self.chunks = {}  # Dict of (chunk_x, chunk_y) -> Chunk
        self.loaded_chunks = set()  # Currently loaded chunks
        
    def get_chunk_coords(self, world_pos):
        """Convert world position to chunk coordinates"""
        x, y = world_pos
        return (int(x // CHUNK_SIZE[0]), int(y // CHUNK_SIZE[1]))
    
    def get_chunk(self, chunk_x, chunk_y):
        """Get or create chunk at given coordinates"""
        key = (chunk_x, chunk_y)
        if key not in self.chunks:
            self.chunks[key] = Chunk(chunk_x, chunk_y, self)
        return self.chunks[key]
    
    def get_chunks_in_range(self, center_world_pos, radius):
        """Get all chunks within radius of center position"""
        center_chunk_x, center_chunk_y = self.get_chunk_coords(center_world_pos)
        chunks = []
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                chunk_x = center_chunk_x + dx
                chunk_y = center_chunk_y + dy
                chunks.append(self.get_chunk(chunk_x, chunk_y))
        
        return chunks
    
    def update_chunk_discovery(self, player_cells):
        """Update chunk discovery states based on player cell positions"""
        
        # First, reset all previously viewed chunks to discovered state
        # (they maintain discovery but lose cell-viewed status)
        for chunk in self.chunks.values():
            if chunk.state == ChunkState.CELL_VIEWED:
                chunk.state = ChunkState.DISCOVERED
        
        # Now process each player cell
        for cell in player_cells:
            center_pos = cell.center
            
            # Get chunks in view range
            nearby_chunks = self.get_chunks_in_range(center_pos, CELL_VIEW_RANGE)
            for chunk in nearby_chunks:
                # If undiscovered, mark as discovered first and spawn POI entities
                if chunk.state == ChunkState.UNDISCOVERED:
                    chunk.state = ChunkState.DISCOVERED
                    # Spawn POI entities when chunk is first discovered
                    if hasattr(chunk, 'poi_type') and chunk.poi_type:
                        chunk.spawn_poi_entities()
                # Then mark as currently cell-viewed (highest priority)
                chunk.state = ChunkState.CELL_VIEWED
    
    def get_chunks_around_camera(self, camera_pos, radius):
        """Get chunks around camera position for rendering"""
        return self.get_chunks_in_range(camera_pos, radius)
    
    def is_within_world_bounds(self, world_pos):
        """Check if position is within the playable world bounds"""
        x, y = world_pos
        return (-WORLD_BOUNDS[0]/2 <= x <= WORLD_BOUNDS[0]/2 and 
                -WORLD_BOUNDS[1]/2 <= y <= WORLD_BOUNDS[1]/2)
    
    def get_biome_at_position(self, world_pos):
        """Get biome at given world position"""
        chunk_x, chunk_y = self.get_chunk_coords(world_pos)
        chunk = self.get_chunk(chunk_x, chunk_y)
        return chunk.biome

class WorldMap:
    """Manages the overall world state and chunk tracking"""
    
    def __init__(self, seed=None):
        self.world_generator = WorldGenerator(seed)
        self.discovered_chunks = set()  # (chunk_x, chunk_y) tuples
        self.viewed_chunks = set()  # (chunk_x, chunk_y) tuples
        
    def update(self, player_cells, all_entities):
        """Update world state based on player positions"""
        # Update chunk discovery
        self.world_generator.update_chunk_discovery(player_cells)
        
        # Update entity positions in chunks
        for chunk in self.world_generator.chunks.values():
            chunk.update_entities(all_entities)
        
        # Track discovered and viewed chunks
        for chunk in self.world_generator.chunks.values():
            key = (chunk.chunk_x, chunk.chunk_y)
            if chunk.state == ChunkState.DISCOVERED:
                self.discovered_chunks.add(key)
            elif chunk.state == ChunkState.CELL_VIEWED:
                self.viewed_chunks.add(key)
                self.discovered_chunks.add(key)  # Viewed chunks are also discovered
    
    def get_chunk_at_world_pos(self, world_pos):
        """Get chunk at given world position"""
        chunk_x, chunk_y = self.world_generator.get_chunk_coords(world_pos)
        return self.world_generator.get_chunk(chunk_x, chunk_y)
    
    def get_molecules_in_discovered_chunks(self):
        """Get all molecules from discovered chunks"""
        from world_generation import ChunkState
        molecules = []
        for chunk in self.world_generator.chunks.values():
            if chunk.state != ChunkState.UNDISCOVERED:
                molecules.extend(chunk.molecules)
        return molecules
    
    def get_biome_overlay_color(self, world_pos):
        """Get the biome overlay color for a world position"""
        biome_name = self.world_generator.get_biome_at_position(world_pos)
        return BIOMES[biome_name]["color"]
    
    def render_world_boundaries(self, surface, camera):
        """Render red zone outside world boundaries"""
        # Get screen boundaries
        screen_rect = surface.get_rect()
        
        # Convert world bounds to screen coordinates
        world_bounds_rect = pygame.Rect(
            -WORLD_BOUNDS[0]//2, -WORLD_BOUNDS[1]//2, 
            WORLD_BOUNDS[0], WORLD_BOUNDS[1]
        )
        
        # Convert to screen coordinates
        top_left = camera.world_to_screen((world_bounds_rect.left, world_bounds_rect.top))
        bottom_right = camera.world_to_screen((world_bounds_rect.right, world_bounds_rect.bottom))
        
        bounds_screen_rect = pygame.Rect(
            top_left[0], top_left[1],
            bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]
        )
        
        # Create red zone overlay surface
        red_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        red_overlay.fill(MAP_RED_ZONE_COLOR)
        
        # Cut out the world bounds area (make it transparent)
        if bounds_screen_rect.colliderect(screen_rect):
            # Clip the bounds rect to screen
            clipped_bounds = bounds_screen_rect.clip(screen_rect)
            pygame.draw.rect(red_overlay, (0, 0, 0, 0), clipped_bounds)
        
        surface.blit(red_overlay, (0, 0))
    
    def render_chunk_backgrounds(self, surface, camera):
        """Render chunk backgrounds based on discovery state"""
        chunks_to_render = self.world_generator.get_chunks_around_camera(
            camera.pos, RENDER_DISTANCE
        )
        
        for chunk in chunks_to_render:
            # Get chunk screen rect
            world_rect = chunk.world_rect
            top_left = camera.world_to_screen((world_rect.left, world_rect.top))
            bottom_right = camera.world_to_screen((world_rect.right, world_rect.bottom))
            
            # Add 1 pixel to width and height to prevent floating point gaps
            screen_rect = pygame.Rect(
                int(top_left[0]), int(top_left[1]),
                int(bottom_right[0] - top_left[0]) + 1, int(bottom_right[1] - top_left[1]) + 1
            )
            
            # Only render if on screen
            if screen_rect.colliderect(surface.get_rect()):
                # Choose background color based on chunk state
                if chunk.state == ChunkState.UNDISCOVERED:
                    bg_color = MAP_UNDISCOVERED_COLOR  # Black
                elif chunk.state == ChunkState.DISCOVERED:
                    bg_color = MAP_DISCOVERED_COLOR    # Dark gray
                else:  # ChunkState.CELL_VIEWED
                    continue  # No background overlay for cell-viewed (use normal background)
                
                # Fill the chunk area with the appropriate color
                chunk_surface = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
                chunk_surface.fill(bg_color + (200,))  # Add alpha for overlay effect
                surface.blit(chunk_surface, screen_rect.topleft)

    def render_biome_overlay(self, surface, camera):
        """Render biome overlays for visible chunks"""
        chunks_to_render = self.world_generator.get_chunks_around_camera(
            camera.pos, RENDER_DISTANCE
        )
        
        for chunk in chunks_to_render:
            if chunk.state != ChunkState.UNDISCOVERED:
                # Get chunk screen rect
                world_rect = chunk.world_rect
                top_left = camera.world_to_screen((world_rect.left, world_rect.top))
                bottom_right = camera.world_to_screen((world_rect.right, world_rect.bottom))
                
                screen_rect = pygame.Rect(
                    top_left[0], top_left[1],
                    bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]
                )
                
                # Only render if on screen
                if screen_rect.colliderect(surface.get_rect()):
                    biome_color = BIOMES[chunk.biome]["color"]
                    overlay = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
                    overlay.fill(biome_color)
                    surface.blit(overlay, screen_rect.topleft)