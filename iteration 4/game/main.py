from turtle import mode
import pygame
import random
import math
import time
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, SILVER, LIGHT_BLUE, DARK_BLUE, BROWN, GRAY

from player import PlayerCell
from virus import CapsidVirus, FilamentousVirus, PhageVirus 
from ui import GameUI, UpgradeUI, Button, SettingsMenuUI, MainMenuUI, ImageButton
from ui import MapUI
from molecule import Protein, Lipid, NucleicAcid, Carbohydrate
from camera import Camera
from entity import Cell, ExternalSpring
from upgrade import OrganelleUpgrade, buy_organelle, buy_protein
from game_state import GameStateManager, GameState
from discovery_tracker import DiscoveryTracker
from evolution_meter import EvolutionMeter

class ConnectionManager:
    """Manages chains of connected cells for snake-like movement"""
    def __init__(self):
        self.chains = []  # List of cell chains
        
    def update_chains(self, external_springs, all_cells):
        """Rebuild chains based on current connections"""
        self.chains.clear()
        processed_cells = set()
        
        # Build adjacency graph of connected cells
        connections = {}
        for spring in external_springs:
            if spring.active:
                cell1 = spring.point1.parent
                cell2 = spring.point2.parent
                if cell1 not in connections:
                    connections[cell1] = []
                if cell2 not in connections:
                    connections[cell2] = []
                connections[cell1].append(cell2)
                connections[cell2].append(cell1)
        
        # Find chains (connected components)
        for cell in all_cells:
            if cell not in processed_cells and cell in connections:
                chain = self._build_chain(cell, connections, processed_cells)
                if len(chain) > 1:  # Only chains with multiple cells
                    self.chains.append(chain)
    
    def _build_chain(self, start_cell, connections, processed_cells):
        """Build a chain starting from a cell using BFS"""
        chain = []
        queue = [start_cell]
        processed_cells.add(start_cell)
        
        while queue:
            current = queue.pop(0)
            chain.append(current)
            
            for neighbor in connections.get(current, []):
                if neighbor not in processed_cells:
                    processed_cells.add(neighbor)
                    queue.append(neighbor)
        
        return chain
    
    def apply_snake_movement(self, delta_time):
        """Apply snake-like following behavior to chains"""
        for chain in self.chains:
            if len(chain) < 2:
                continue
                
            # The first cell in the chain is the "head" - it moves freely
            # Other cells try to follow their predecessor with some delay
            
            for i in range(1, len(chain)):
                follower = chain[i]
                leader = chain[i-1]
                
                # Only apply snake movement if follower is not player-controlled
                if not (hasattr(follower, 'is_player') and follower.is_player):
                    # Calculate desired position (behind the leader)
                    leader_pos = leader.center
                    follower_pos = follower.center
                    
                    # Desired distance between cells (slightly less than connection length)
                    desired_distance = 80
                    
                    # Direction from leader to follower
                    direction = follower_pos - leader_pos
                    current_distance = direction.length()
                    
                    if current_distance > desired_distance:
                        # Pull follower towards leader
                        direction_normalized = direction.normalize() if current_distance > 0 else pygame.Vector2(0, 0)
                        target_pos = leader_pos + direction_normalized * desired_distance
                        
                        # Apply gentle following force
                        follow_force = (target_pos - follower_pos) * 150.0  # Adjust strength as needed
                        follower.apply_global_force(follow_force)

connection_manager = ConnectionManager()
from world_generation import WorldMap
import visuals

pygame.init()
pygame.key.set_repeat(400, 40)

# Initialize game state manager
game_state_manager = GameStateManager()
current_game_mode = None

# Central systems for upgrades and resources
player_upgrades = {
    "Proteins": [],
    "Crafted Proteins": [],
    "Organelles": []
}

# Central molecule/resource storage
player_molecules = {
    "protein": 1000,
    "lipid": 1000,
    "nucleic_acid": 1000,
    "carbohydrate": 1000
}

# External springs system for inter-cell connections
external_springs = []
selected_connection_points = []  # For tracking points selected for connection

# Combat systems
pending_virus_spawns = []  # Queue for virus spawning after cell deaths

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cell Evolution Game")
clock = pygame.time.Clock()
delta_time = 1.0/FPS  # Initialize as seconds

current_menu = None

""""FUNCTIONS"""
def open_menu(menu_name):
    global current_menu
    current_menu = menu_name
    
    # Special handling for notebook
    if menu_name == "notebook" and notebook_ui:
        notebook_ui.open()

def close_menu():
    global current_menu
    current_menu = None
    
    # Close notebook if it's open
    if notebook_ui:
        notebook_ui.close()

def return_to_main_menu():
    """Return to main menu and save current game"""
    global game_state_manager, current_game_mode, player_cells, player_molecules, player_upgrades
    
    # Save current game if in a game mode and we have valid data
    if current_game_mode and current_game_mode != "multiplayer" and player_cells:
        try:
            world_seed = getattr(world_map, 'seed', None) if 'world_map' in globals() and world_map else None
            game_state_manager.save_current_game(current_game_mode, player_cells, player_molecules, player_upgrades, world_seed)
        except Exception as e:
            print(f"Warning: Failed to save game state: {e}")
    
    # Set state to main menu
    game_state_manager.set_state(GameState.MAIN_MENU)
    current_game_mode = None

def initialize_new_game(mode: str):
    """Initialize a new game with the specified mode"""
    global current_game_mode, player_cells, player_molecules, player_upgrades, origin
    global selected_entities, camera, world_map, map_ui, cell_groups, group_colors
    global camera_follow_group_key, sprites, viruses, enemy_cells, external_springs
    
    current_game_mode = mode
    
    # Get mode-specific defaults
    defaults = game_state_manager.get_new_game_defaults(mode)
    
    # Reset game state
    player_upgrades = {
        "Proteins": [],
        "Crafted Proteins": [],
        "Organelles": []
    }
    player_molecules = defaults["player_molecules"].copy()
    
    # Create new player cell with mode-specific settings
    origin = PlayerCell((500, 500), defaults["starting_size"], defaults["starting_health"])
    player_cells = [origin]
    selected_entities = []
    
    # Reset world and camera
    camera = Camera(origin.pos, zoom=1.0)
    world_map = WorldMap(seed=random.randint(1, 1000000))
    map_ui = MapUI(world_map)


    
    # Reset groups and other game state
    cell_groups.clear()
    group_colors.clear()
    camera_follow_group_key = None
    sprites.clear()
    viruses.clear()
    enemy_cells.clear()
    external_springs.clear()
    
    # Initialize UI components for the game
    initialize_game_ui()
    
    # Reset evolution meter for new game
    if evolution_meter:
        evolution_meter.reset()
    
    # Add some initial content for lab mode
    if mode == "lab":
        # Spawn some test enemies and resources nearby for lab mode
        spawn_virus((200, 200))
        spawn_enemy_cell((300, -200))
        # Spawn some test enemies and resources nearby
        spawn_virus((200, 200))
        spawn_enemy_cell((300, -200))

def load_saved_game(mode: str):
    """Load a saved game for the specified mode"""
    global current_game_mode, player_cells, player_molecules, player_upgrades
    global camera, world_map, map_ui, selected_entities
    
    instance = game_state_manager.load_game_instance(mode)
    if instance:
        current_game_mode = mode
        
        # Reconstruct player cells from serialized data
        player_cells = []
        from player import PlayerCell
        from molecule import Lipid
        
        for cell_data in instance.player_cells:
            pos = pygame.Vector2(cell_data['pos'])
            radius = cell_data['radius']
            health = cell_data.get('health', 100)
            max_health = cell_data.get('max_health', 100)
            
            # Create new player cell with saved data
            cell = PlayerCell(pos, points=12, radius=radius)
            cell.health = health
            cell.max_health = max_health
            player_cells.append(cell)
            sprites.append(cell)
        
        player_molecules = instance.player_molecules
        player_upgrades = instance.player_upgrades
        
        # Restore camera and world if available
        if player_cells:
            camera = Camera(player_cells[0].pos, zoom=1.0)
        
        seed = instance.world_seed or random.randint(1, 1000000)
        world_map = WorldMap(seed=seed)
        map_ui = MapUI(world_map)
        selected_entities = []
        
        # Initialize UI components for the loaded game
        initialize_game_ui()
        
        return True
    return False

def start_game_mode(mode: str):
    """Start a game in the specified mode (load if available, otherwise create new)"""
    if mode == "multiplayer":
        # Placeholder for multiplayer
        print("Multiplayer not yet implemented!")
        return
    
    # Try to load saved game first
    if game_state_manager.has_saved_game(mode):
        if load_saved_game(mode):
            game_state_manager.set_state(GameState.SINGLEPLAYER if mode == "singleplayer" else GameState.LAB_MODE)
            return
    
    # If no saved game or loading failed, create new game
    initialize_new_game(mode)
    if mode == "singleplayer":
        game_state_manager.set_state(GameState.SINGLEPLAYER)
    elif mode == "lab":
        game_state_manager.set_state(GameState.LAB_MODE)

def handle_game_logic(events, delta_time):
    """Handle all game logic when in a game state - restored from iteration 3"""
    global current_menu, player_cells, enemy_cells, viruses, external_springs, camera_follow_group_key
    global selected_entities, is_selecting, selection_box, cell_groups, mouse_pos
    global player_molecules, player_upgrades, all_entities, evolution_meter, notebook_ui
    
    # Get current time for invincibility and other time-based features
    current_time = time.time()
    
    # Create all_entities list for hotkey spawning
    all_entities = player_cells + enemy_cells + viruses
    
    # Handle button events first (but disable while in upgrade menu)
    if upgrade_button and settings_button and map_button and notebook_button:
        for event in events:
            if current_menu != "upgrade":
                upgrade_button.handle_event(event)
                settings_button.handle_event(event)
                map_button.handle_event(event)
                notebook_button.handle_event(event)
    
    # Handle notebook events first if notebook is open (regardless of current_menu)
    if notebook_ui and notebook_ui.is_open:
        for event in events:
            notebook_ui.handle_event(event)
        # If notebook consumed events, skip other event handling
        if notebook_ui.is_open:  # Still open after handling events
            pass  # Continue to other event handling but notebook takes priority
    
    # Handle UI events based on current state
    if current_menu == "upgrade" and upgrade_ui:
        for event in events:
            upgrade_ui.handle_event(event)
    elif current_menu == "settings" and settings_ui:
        for event in events:
            settings_ui.handle_event(event)
    elif map_ui and map_ui.is_open:
        map_result = map_ui.handle_event(events)
        if map_result and map_result.get('move_to'):
            # Handle cell movement from map click
            world_pos = map_result['move_to']
            # Enforce selection requirement: only selected cells move
            if selected_entities:
                for entity in selected_entities:
                    if hasattr(entity, 'target_pos'):
                        entity.target_pos = pygame.Vector2(world_pos)
    else:
        # Handle game events only when no menus are open - RESTORED ORIGINAL LOGIC
        for event in events:
            # Let Cell Manager consume its own input first
            if cell_manager_ui and cell_manager_ui.handle_event(event):
                continue
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                # Create a group from selected player cells
                from player import PlayerCell
                grouped = [e for e in selected_entities if isinstance(e, PlayerCell)]
                if grouped:
                    # Find the lowest available group number starting at 1
                    used_nums = set()
                    for key in cell_groups.keys():
                        if key.startswith("Group "):
                            try:
                                n = int(key.split(" ", 1)[1])
                                used_nums.add(n)
                            except Exception:
                                continue
                    next_num = 1
                    while next_num in used_nums:
                        next_num += 1
                    name = f"Group {next_num}"

                    # Enforce single-group membership: remove selected cells from any existing groups
                    for gname, members in list(cell_groups.items()):
                        for c in grouped:
                            if c in members:
                                members.remove(c)
                        if not members:
                            del cell_groups[gname]
                            group_colors.pop(gname, None)

                    # Add to new group
                    cell_groups[name] = list(dict.fromkeys(grouped))
                    # Assign a random color for this group
                    import random
                    group_colors[name] = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    # Left click - selection logic (RESTORED ORIGINAL)
                    world_pos = camera.screen_to_world(pygame.mouse.get_pos())
                    clicked_entity = None
                    
                    # Check for cell clicks first
                    for cell in player_cells + enemy_cells:
                        if cell.center.distance_to(world_pos) < cell.radius:
                            clicked_entity = cell
                            break
                    
                    # Selection logic
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # Control+click: toggle selection
                        if clicked_entity:
                            if clicked_entity in selected_entities:
                                selected_entities.remove(clicked_entity)
                            else:
                                selected_entities.append(clicked_entity)
                    else:
                        # Regular click behavior
                        if clicked_entity:
                            # Clicked on an entity - select it
                            selected_entities.clear()
                            selected_entities.append(clicked_entity)
                        elif selected_entities:
                            # Clicked on empty space with selected entities - set target position
                            for entity in selected_entities:
                                if hasattr(entity, 'target_pos'):
                                    entity.target_pos = pygame.Vector2(world_pos)
                        else:
                            # No entities selected and clicked on empty space - start selection box
                            is_selecting = True
                            selection_box = (pygame.mouse.get_pos(), pygame.mouse.get_pos())

                elif event.button == pygame.BUTTON_RIGHT and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # RESTORED: Right+Shift click for selection box (from iteration 3)
                    is_selecting = True
                    selection_box = (pygame.mouse.get_pos(), pygame.mouse.get_pos())
                    
            elif event.type == pygame.MOUSEMOTION and is_selecting:
                # Update selection box
                if selection_box:
                    selection_box = (selection_box[0], pygame.mouse.get_pos())
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if (event.button == pygame.BUTTON_LEFT or event.button == pygame.BUTTON_RIGHT) and is_selecting:
                    # End selection box (works with both left and right button)
                    if selection_box:
                        start_pos = camera.screen_to_world(selection_box[0])
                        end_pos = camera.screen_to_world(selection_box[1])
                        
                        # Create selection rectangle
                        min_x = min(start_pos.x, end_pos.x)
                        max_x = max(start_pos.x, end_pos.x)
                        min_y = min(start_pos.y, end_pos.y)
                        max_y = max(start_pos.y, end_pos.y)
                        
                        # Select all entities in rectangle
                        if not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            selected_entities.clear()
                        
                        for cell in player_cells + enemy_cells:
                            if (min_x <= cell.center.x <= max_x and 
                                min_y <= cell.center.y <= max_y):
                                if cell not in selected_entities:
                                    selected_entities.append(cell)
                    
                    is_selecting = False
                    selection_box = None

            elif event.type == pygame.KEYDOWN:
                # FIXED: ESC only closes menus, doesn't return to main menu
                if event.key == pygame.K_ESCAPE:
                    if current_menu:
                        close_menu()
                elif event.key == pygame.K_SPACE:
                    # Toggle between selecting all and deselecting all player cells
                    if len(selected_entities) == len(player_cells) and all(cell in selected_entities for cell in player_cells):
                        # All cells are selected, deselect all
                        selected_entities.clear()
                        print("Deselected all player cells")
                    else:
                        # Not all cells are selected, select all
                        selected_entities.clear()
                        selected_entities.extend(player_cells)
                        print("Selected all player cells")
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    # RESTORED: Left/Right arrow for group navigation
                    keys = _group_keys_sorted()
                    if keys:
                        if camera_follow_group_key in keys:
                            idx = keys.index(camera_follow_group_key)
                        else:
                            idx = -1
                        if event.key == pygame.K_RIGHT:
                            idx = (idx + 1) % len(keys)
                        else:
                            idx = (idx - 1) % len(keys)
                        camera_follow_group_key = keys[idx]
                elif event.key == pygame.K_m:
                    # Toggle map (always allow this)
                    if map_ui:
                        map_ui.toggle_map()
                
                # Check if we should ignore demo hotkeys (when typing notes)
                elif not (notebook_ui and notebook_ui.is_open and notebook_ui.is_typing_note):
                    # Demo hotkeys are only active when NOT typing notes
                    if event.key == pygame.K_p:
                        # Demo Hotkey: Spawn virus cluster near first selected player cell
                        if selected_entities and player_cells:
                            first_cell = selected_entities[0] if selected_entities[0] in player_cells else None
                            if first_cell:
                                spawn_x = first_cell.center.x + 250
                                spawn_y = first_cell.center.y
                                # Spawn 5 random viruses in a cluster
                                for i in range(5):
                                    offset_x = random.randint(-50, 50)
                                    offset_y = random.randint(-50, 50)
                                    virus_pos = (spawn_x + offset_x, spawn_y + offset_y)
                                    virus_type = random.choice([CapsidVirus, FilamentousVirus, PhageVirus])
                                    new_virus = virus_type(virus_pos)
                                    viruses.append(new_virus)
                                    all_entities.append(new_virus)
                                print(f"Demo: Spawned 5 viruses near selected cell at ({spawn_x}, {spawn_y})")
                    elif event.key == pygame.K_t:
                        # Demo Hotkey: Give +10000 of all organic molecules
                        player_molecules["lipid"] += 10000
                        player_molecules["protein"] += 10000
                        player_molecules["nucleic_acid"] += 10000
                        player_molecules["carbohydrate"] += 10000
                        print("Demo: Added 10000 of all organic molecules to inventory")
                    elif event.key == pygame.K_s:
                        # Demo Hotkey: Add all organelles and proteins to inventory (former debug button)

                        # Add all proteins
                        from config import PROTEIN_DATA, ORGANELLE_DATA
                        for category, items in PROTEIN_DATA.items():
                            for item in items:
                                buy_protein(player_cells[0], item, free=True)

                        # Add all organelles
                        for category, items in ORGANELLE_DATA.items():
                            for item in items:
                                buy_organelle(player_cells[0], item, free=True)

                        print("Demo: Added all organelles and proteins to inventory")
                    elif event.key == pygame.K_l:
                        # Demo Hotkey: Skip to next evolution level
                        if evolution_meter:
                            current_progress = evolution_meter.get_progress_percentage()
                            if current_progress < 25:
                                evolution_meter.progress = 25
                            elif current_progress < 50:
                                evolution_meter.progress = 50
                            elif current_progress < 75:
                                evolution_meter.progress = 75
                            elif current_progress < 100:
                                evolution_meter.progress = 100
                            else:
                                evolution_meter.progress = 0  # Reset if already at max
                            print(f"Demo: Evolution progress set to {evolution_meter.progress}% - {evolution_meter.get_evolution_stage()}")
                    elif event.key == pygame.K_k:
                        # Demo Hotkey: Make all player cells invincible for 1 minute
                        invincibility_duration = 60.0  # 60 seconds
                        for cell in player_cells:
                            cell.invincible_until = current_time + invincibility_duration
                        print(f"Demo: All player cells are now invincible for {invincibility_duration} seconds")
                    elif event.key == pygame.K_j:
                        # Demo Hotkey: Unlock all discoveries
                        if discovery_tracker:
                            from config import DISCOVERIES
                            discovery_count = 0
                            for discovery_id in DISCOVERIES.keys():
                                if discovery_tracker.trigger_discovery(discovery_id):
                                    discovery_count += 1
                            print(f"Demo: Unlocked {discovery_count} new discoveries! Check your notebook.")
                        else:
                            print("Demo: Discovery tracker not available")
                    elif event.key == pygame.K_BACKQUOTE:  # Backtick key (`)
                        # Demo Hotkey: Reset all saves and progress
                        import os
                        import shutil
                        
                        # Reset player molecules to default
                        player_molecules["lipid"] = 1000
                        player_molecules["protein"] = 1000
                        player_molecules["nucleic_acid"] = 1000
                        player_molecules["carbohydrate"] = 1000
                        
                        # Clear player upgrades
                        player_upgrades["Proteins"].clear()
                        player_upgrades["Crafted Proteins"].clear()
                        player_upgrades["Organelles"].clear()
                        
                        # Reset evolution meter
                        if evolution_meter:
                            evolution_meter.reset()
                        
                        # Clear discoveries
                        if discovery_tracker:
                            discovery_tracker.discovered.clear()
                            discovery_tracker.stats = {
                                "molecules_collected": {"protein": 0, "lipid": 0, "nucleic_acid": 0, "carbohydrate": 0},
                                "cells_split": 0,
                                "viruses_defeated": 0,
                                "enemies_defeated": 0,
                                "pois_discovered": 0,
                                "organelles_created": 0,
                                "biomes_explored": set(),
                                "max_cell_size": 0,
                                "max_speed": 0,
                                "survival_start_time": current_time,
                                "upgrades_purchased": 0,
                                "symbiosis_formed": 0
                            }
                        
                        # Reset notebook discoveries and custom notes
                        if notebook_ui:
                            notebook_ui.discoveries.clear()
                            notebook_ui.discovered_ids.clear()
                            notebook_ui.custom_notes.clear()
                            notebook_ui._add_initial_entry()  # Re-add welcome message
                        
                        # Delete save files
                        try:
                            saves_dir = "saves"
                            if os.path.exists(saves_dir):
                                for filename in os.listdir(saves_dir):
                                    file_path = os.path.join(saves_dir, filename)
                                    if os.path.isfile(file_path):
                                        os.remove(file_path)
                                        print(f"Deleted save file: {filename}")
                        except Exception as e:
                            print(f"Error deleting save files: {e}")
                        
                        print("Demo: All saves and progress have been reset to default!")
                    
            # Disable manual zoom: ignore mouse wheel in main view (map handles its own zoom)
            elif event.type == pygame.MOUSEWHEEL:
                pass
    
    # RESTORED: Add the original game update logic from iteration 3
    # Cleanup groups: remove cells that no longer exist; delete empty groups
    existing_set = set(player_cells)
    to_delete = []
    for gname, members in cell_groups.items():
        kept = []
        for c in members:
            if c in existing_set:
                kept.append(c)
            else:
                try:
                    selected_entities.remove(c)
                except Exception:
                    pass
        cell_groups[gname] = kept
        if not kept:
            to_delete.append(gname)
    for gname in to_delete:
        del cell_groups[gname]
        group_colors.pop(gname, None)
        if camera_follow_group_key == gname:
            camera_follow_group_key = None
    
    # Update game systems only if we have initialized components
    if player_cells and camera and world_map:
        update_game_systems(delta_time)
        
    # Render the game
    render_game(delta_time)

# Maintain ordering of group navigation (restored from iteration 3)
def _group_keys_sorted():
    # sort by numeric suffix if name like "Group N", else lexicographic
    def key_fn(k):
        if k.startswith("Group "):
            try:
                return (0, int(k.split(" ", 1)[1]))
            except Exception:
                return (1, k)
        return (1, k)
    return sorted(cell_groups.keys(), key=key_fn)

def process_poi_spawns():
    """Process pending POI spawns from discovered chunks"""
    if not world_map or not hasattr(world_map, 'world_generator'):
        return
        
    for chunk in world_map.world_generator.chunks.values():
        # Process virus cluster spawns
        if hasattr(chunk, 'pending_virus_spawns') and chunk.pending_virus_spawns:
            # Trigger POI discovery (only once per chunk)
            if discovery_tracker and not hasattr(chunk, 'poi_discovery_triggered'):
                discovery_tracker.on_poi_discovered()
                chunk.poi_discovery_triggered = True
                
            for spawn_data in chunk.pending_virus_spawns:
                virus_type = spawn_data['virus_type']
                pos = spawn_data['position']
                size = spawn_data['size']
                
                # Create the virus based on type
                if virus_type.__name__ == 'CapsidVirus':
                    virus = virus_type(pos, size, size//2)
                elif virus_type.__name__ == 'FilamentousVirus':
                    virus = virus_type(pos, length=size*4, spacing=size//2, radius=size)
                elif virus_type.__name__ == 'PhageVirus':
                    virus = virus_type(pos, radius=size, points=size//2)
                else:
                    continue  # Unknown virus type
                    
                viruses.append(virus)
                sprites.append(virus)
            
            # Clear the pending spawns
            chunk.pending_virus_spawns.clear()
        
        # Process giant enemy spawns
        if hasattr(chunk, 'pending_enemy_spawn') and chunk.pending_enemy_spawn:
            # Trigger POI discovery (only once per chunk)
            if discovery_tracker and not hasattr(chunk, 'poi_discovery_triggered'):
                discovery_tracker.on_poi_discovered()
                chunk.poi_discovery_triggered = True
                
            spawn_data = chunk.pending_enemy_spawn
            pos = spawn_data['position']
            points = spawn_data['points']
            radius = spawn_data['radius']
            
            # Create giant enemy cell
            from entity import EnemyCell
            from molecule import Lipid
            giant_enemy = EnemyCell(pos, points=points, radius=radius, membrane_molecule=Lipid)
            enemy_cells.append(giant_enemy)
            sprites.append(giant_enemy)
            
            # Clear the pending spawn
            chunk.pending_enemy_spawn = None

def update_game_systems(delta_time):
    """Update all game systems - entities, physics, AI, etc."""
    global player_cells, enemy_cells, viruses, external_springs, pending_virus_spawns
    
    # Update all player cells with events like in iteration 3
    for cell in player_cells:
        if hasattr(cell, 'update'):
            cell.update(screen, events, delta_time, camera)  # Pass events like in original
            
            for u in cell.organelle_slots:
                if u and u.name == "Cell Membrane Extender":
                    # Add new membrane points
                    cell.extend_membrane(10)
                    # Increase radius
                    cell.radius += 10
                    # Redistribute all points and springs into a larger circle
                    cell.redistribute_points_to_circle(cell.radius)
                    # Update shape and area calculations
                    cell.initial_shape = cell.calculate_shape()
                    cell.rest_area = cell.calculate_area()
                    # Remove the extender after use
                    cell.organelle_slots[cell.organelle_slots.index(u)] = None

            # # RESTORED: Handle organelle updates
            # for u in cell.organelle_slots:
            #     if u and u.name == "Cell Membrane Extender":
            #         # Add new membrane points
            #         cell.extend_membrane(10)
            #         # Increase radius
            #         cell.radius += 10
            #         # Redistribute all points and springs into a larger circle
            #         cell.redistribute_points_to_circle(cell.radius)
        
        # RESTORED: Update targeting system for all player cells
        import time
        current_time = time.time()
        all_enemies = viruses + enemy_cells  # Combine all potential targets
        all_entities = player_cells + enemy_cells + viruses  # All entities for abilities
        
        cell.update_targeting(current_time, all_enemies)
        cell.maintain_target_distance(delta_time)
        cell.update_protein_abilities(delta_time, all_entities, current_time)
        
        # Handle cell splitting
        if hasattr(cell, 'split_body') and cell.split_body():
            random_vector = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            sb1, sb2, old_body = cell.split_body()
            player_cells.append(sb1)
            sb1.pos += random_vector * sb1.points[0].pos.distance_to(sb1.points[1].pos)*2
            sb1.is_player = True
            sb1.atp = old_body.atp // 2
            player_cells.append(sb2)
            sb2.pos += random_vector * -sb2.points[0].pos.distance_to(sb2.points[1].pos)*2
            sb2.is_player = True
            sb2.atp = old_body.atp // 2
            sb1.target_pos = sb1.pos
            sb2.target_pos = sb2.pos
            player_cells.remove(old_body)
            sb1.radius = max(10, sb1.radius * 0.75) 
            sb2.radius = max(10, sb2.radius * 0.75)
            
            # Update selected entities if the split cell was selected
            if old_body in selected_entities:
                selected_entities.remove(old_body)
                selected_entities.extend([sb1, sb2])
            
            # Trigger discovery for first cell split
            if discovery_tracker:
                discovery_tracker.on_cell_split()
            break

    # Update viruses
    for virus in viruses:
        all_cells = player_cells + enemy_cells
        if hasattr(virus, 'update'):
            virus.update(all_cells, delta_time)
            
        # Check for virus-cell collisions
        for cell in all_cells:
            distance = virus.pos.distance_to(cell.center)
            if distance < (virus.radius + cell.radius):
                # Virus attacks cell
                if hasattr(cell, 'take_damage'):
                    cell.take_damage(10, current_time, virus)

    # Update enemy cells
    for cell in enemy_cells:
        if hasattr(cell, 'update'):
            cell.update(screen, [], delta_time, camera)
    
    # Handle cell deaths and cleanup
    dying_player_cells = [cell for cell in player_cells if hasattr(cell, 'health') and cell.health <= 0]
    dying_enemy_cells = [cell for cell in enemy_cells if hasattr(cell, 'health') and cell.health <= 0]
    dying_viruses = [virus for virus in viruses if hasattr(virus, 'health') and virus.health <= 0]
    
    # Trigger discoveries for defeated enemies and viruses
    if discovery_tracker:
        for _ in dying_enemy_cells:
            discovery_tracker.on_enemy_defeated()
        for _ in dying_viruses:
            discovery_tracker.on_virus_defeated()
    
    # Remove dead cells
    player_cells[:] = [cell for cell in player_cells if not hasattr(cell, 'health') or cell.health > 0]
    enemy_cells[:] = [cell for cell in enemy_cells if not hasattr(cell, 'health') or cell.health > 0]
    
    # Remove dead viruses
    viruses[:] = [virus for virus in viruses if not hasattr(virus, 'health') or virus.health > 0]
    
    # Update external springs (inter-cell connections)
    for spring in external_springs[:]:
        if hasattr(spring, 'update'):
            spring.update(delta_time)
            if hasattr(spring, 'active') and not spring.active:
                external_springs.remove(spring)
    
    # Update connection chains and apply snake-like movement
    connection_manager.update_chains(external_springs, player_cells + enemy_cells)
    connection_manager.apply_snake_movement(delta_time)
    
    # Handle molecule collection by player cells (RESTORED from iteration 3)
    if world_map and hasattr(world_map, 'world_generator'):
        for cell in player_cells:
            for chunk in world_map.world_generator.chunks.values():
                from world_generation import ChunkState
                if chunk.state != ChunkState.UNDISCOVERED:
                    molecules_to_remove = []
                    for mol in chunk.molecules:
                        # Check collision between cell and molecule
                        distance = cell.center.distance_to(mol.pos)
                        if distance < cell.radius + getattr(mol, 'radius', 15):  # Molecule collection radius
                            # Add to central inventory
                            mol_type_name = type(mol).__name__.lower()
                            # Handle nucleicacid -> nucleic_acid mapping
                            if mol_type_name == "nucleicacid":
                                mol_type_name = "nucleic_acid"
                            if mol_type_name in player_molecules:
                                mol_value = getattr(mol, 'value', 1)  # Use molecule's value, default to 1
                                player_molecules[mol_type_name] += mol_value
                                molecules_to_remove.append(mol)
                                # Trigger discovery for molecule collection
                                if discovery_tracker:
                                    discovery_tracker.on_molecule_collected(mol_type_name)
                    
                    # Remove collected molecules from chunk
                    for mol in molecules_to_remove:
                        chunk.molecules.remove(mol)
    
    # Handle collisions between cells
    all_cells = player_cells + enemy_cells
    if len(all_cells) > 1:
        collision_system.detect_and_resolve_collisions(all_cells)
    
    # Update camera to follow selected entities or all player cells
    focus_cells = selected_entities if selected_entities else player_cells
    if focus_cells:
        # Filter to only player cells for camera
        from player import PlayerCell
        player_focus = [e for e in focus_cells if isinstance(e, PlayerCell)]
        if player_focus:
            # Center camera on average position
            total_pos = pygame.Vector2(0, 0)
            for cell in player_focus:
                total_pos += cell.center
            camera.pos = total_pos / len(player_focus)
            
            # Adjust zoom based on spread
            if len(player_focus) > 1:
                distances = []
                center = camera.pos
                for cell in player_focus:
                    distances.append(cell.center.distance_to(center))
                max_distance = max(distances) if distances else 100
                
                # Calculate zoom to fit all cells
                screen_size = min(SCREEN_WIDTH, SCREEN_HEIGHT)
                desired_zoom = (screen_size * 0.3) / max(max_distance, 100)

                for cell in player_focus:
                    for organelle in cell.organelle_slots:
                        if organelle and organelle.name == "Zoom Enhancer":
                            desired_zoom *= 1.2  # Increase zoom by 20%

                if selected_mode == "lab":
                    camera.zoom = max(0.1, min(0.75, desired_zoom))
                else:
                    camera.zoom = max(0.1, min(0.75, desired_zoom))
            else:
                camera.zoom = 1.0
    
    # Update world generation and chunk discovery
    if world_map and hasattr(world_map, 'update'):
        all_entities = player_cells + enemy_cells + viruses
        world_map.update(player_cells, all_entities)
        
        # Process POI spawns from discovered chunks
        process_poi_spawns()
    
    # Update discovery tracking
    if discovery_tracker:
        # Track player cell stats
        for cell in player_cells:
            discovery_tracker.on_cell_update(cell)
        
        # Check biome exploration based on world map
        if world_map and hasattr(world_map, 'world_generator') and player_cells:
            for cell in player_cells:
                try:
                    biome = world_map.world_generator.get_biome_at_position(cell.center)
                    if biome:
                        discovery_tracker.on_biome_explored(biome.get("name", "unknown"))
                except:
                    pass  # Handle any biome lookup errors
    
    # Update evolution meter
    if evolution_meter:
        evolution_meter.update(delta_time)
    
    # Update visual systems
    if 'visuals' in globals():
        visuals.update_visual_systems(delta_time)

def render_game(delta_time):
    """Render the game world and UI"""
    global background_tile, screen, camera
    
    if not camera or not background_tile:
        # Not ready to render yet
        screen.fill((20, 25, 35))  # Dark background
        return
    
    # Draw scrolling background
    camera_offset = camera.pos - pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_scrolling_background(screen, background_tile, camera_offset, camera)
    
    # Render world boundaries and chunk backgrounds
    if world_map and hasattr(world_map, 'render_world_boundaries'):
        world_map.render_world_boundaries(screen, camera)
        if hasattr(world_map, 'render_chunk_backgrounds'):
            world_map.render_chunk_backgrounds(screen, camera)
        if hasattr(world_map, 'render_biome_overlay'):
            world_map.render_biome_overlay(screen, camera)
    
    # Handle menu rendering
    if current_menu == "upgrade" and upgrade_ui:
        upgrade_ui.draw(delta_time)
        return
    elif current_menu == "settings" and settings_ui:
        settings_ui.draw(delta_time)
        return
    
    # Draw selection box if active
    if is_selecting and selection_box:
        start, end = selection_box
        rect = pygame.Rect(*start, *(pygame.Vector2(end) - pygame.Vector2(start)))
        rect.normalize()
        pygame.draw.rect(screen, (100, 200, 255, 80), rect, 2)
    
    # Draw targeting lines for selected entities
    for entity in selected_entities:
        if hasattr(entity, 'target_pos') and entity.target_pos:
            pygame.draw.line(screen, (150, 150, 255), 
                           camera.world_to_screen(entity.center), 
                           camera.world_to_screen(entity.target_pos), 3)
            pygame.draw.circle(screen, (150, 100, 255), 
                             camera.world_to_screen(entity.target_pos), 8, 2)
    
    # Draw player cells
    for cell in player_cells:
        if 'visuals' in globals() and hasattr(visuals, 'draw_cell_with_effects'):
            visuals.draw_cell_with_effects(screen, cell, camera, delta_time, enable_effects=True)
        else:
            # Fallback drawing
            screen_pos = camera.world_to_screen(cell.center)
            pygame.draw.circle(screen, (100, 150, 255), screen_pos, int(cell.radius * camera.zoom))
            
        # Draw protein abilities if available
        if hasattr(cell, 'draw_protein_abilities'):
            cell.draw_protein_abilities(screen, camera)
    
    # Draw enemy cells
    for cell in enemy_cells:
        if 'visuals' in globals() and hasattr(visuals, 'draw_cell_with_effects'):
            visuals.draw_cell_with_effects(screen, cell, camera, delta_time, enable_effects=True)
        else:
            # Fallback drawing
            screen_pos = camera.world_to_screen(cell.center)
            pygame.draw.circle(screen, (255, 100, 100), screen_pos, int(cell.radius * camera.zoom))
    
    # Draw viruses
    for virus in viruses:
        if hasattr(virus, 'draw'):
            virus.draw(screen, camera)
        else:
            # Fallback drawing
            screen_pos = camera.world_to_screen(virus.pos)
            pygame.draw.circle(screen, (255, 255, 100), screen_pos, int(virus.radius * camera.zoom))
    
    # Draw molecules if available
    if world_map and hasattr(world_map, 'get_molecules_in_discovered_chunks'):
        molecules = world_map.get_molecules_in_discovered_chunks()
        for mol in molecules:
            if 'visuals' in globals() and hasattr(visuals, 'draw_molecule_with_effects'):
                visuals.draw_molecule_with_effects(screen, mol, camera, delta_time, enable_effects=True)
            else:
                # Fallback drawing
                screen_pos = camera.world_to_screen(mol.pos)
                pygame.draw.circle(screen, (100, 255, 100), screen_pos, 5)
    
    # Draw external spring connections
    for spring in external_springs:
        if hasattr(spring, 'draw'):
            spring.draw(screen, camera)
    
    # Draw visual effects
    if 'visuals' in globals() and hasattr(visuals, 'draw_visual_systems'):
        visuals.draw_visual_systems(screen, camera)
    
    # Draw UI components
    if game_ui:
        game_ui.draw(delta_time)
    
    if cell_manager_ui:
        try:
            cell_manager_ui.draw(screen)
        except:
            pass  # Handle any UI drawing errors gracefully
    
    # Draw header buttons only when not in menus
    if current_menu != "upgrade" and upgrade_button and settings_button and map_button and notebook_button:
        upgrade_button.draw(screen)
        settings_button.draw(screen)
        map_button.draw(screen)
        notebook_button.draw(screen)
    
    # Draw evolution meter
    if evolution_meter:
        evolution_meter.draw(screen)
    
    # Draw notebook UI if open
    if notebook_ui and notebook_ui.is_open:
        notebook_ui.draw()
    
    # Draw map UI if open (always on top)
    if map_ui and map_ui.is_open:
        molecules = world_map.get_molecules_in_discovered_chunks() if world_map else []
        all_entities = player_cells + enemy_cells + viruses + molecules
        map_ui.draw(screen, player_cells, all_entities)

def draw_scrolling_background(screen, texture, player_pos, camera):
    # Scale the texture according to camera zoom
    texture_size = int(texture.get_width() * camera.zoom)
    scaled_texture = pygame.transform.smoothscale(texture, (texture_size, texture_size))
    screen_rect = screen.get_rect()

    # Calculate offset to scroll based on player position
    offset_x = -player_pos.x * camera.zoom % texture_size
    offset_y = -player_pos.y * camera.zoom % texture_size

    # Draw enough tiles to fill the screen
    for x in range(-texture_size, screen_rect.width + texture_size, texture_size):
        for y in range(-texture_size, screen_rect.height + texture_size, texture_size):
            screen.blit(scaled_texture, (x + offset_x, y + offset_y))

def spawn_main_menu_softbody():
    """Spawn a new softbody for main menu simulation"""
    global main_menu_softbodies
    from entity import Cell
    from molecule import Lipid
    
    # Random position within left half of screen
    margin = 100
    sim_width = SCREEN_WIDTH // 2
    pos_x = random.randint(margin, sim_width - margin) 
    pos_y = random.randint(margin, SCREEN_HEIGHT - margin)
    
    # Create softbody with specified parameters
    softbody = Cell(
        pos=(pos_x, pos_y),
        points=25,  # As requested
        radius=50,  # As requested  
        membrane_molecule=Lipid
    )
    
    # Add random velocity and angular velocity
    velocity_magnitude = random.uniform(20, 50)
    angle = random.uniform(0, 2 * math.pi)
    softbody.velocity = pygame.Vector2(
        velocity_magnitude * math.cos(angle),
        velocity_magnitude * math.sin(angle)
    )
    softbody.angular_velocity = random.uniform(-2.0, 2.0)
    softbody.rotation_angle = 0
    
    main_menu_softbodies.append(softbody)

def update_main_menu_simulation(delta_time):
    """Update main menu softbody simulation"""
    global menu_split_timer, menu_next_split_time, menu_spawn_timer, main_menu_softbodies
    
    if not main_menu_softbodies:
        menu_spawn_timer += delta_time
        if menu_spawn_timer >= 2.0:  # 2 second delay before spawning
            spawn_main_menu_softbody()
            menu_spawn_timer = 0
        return
    
    # Update split timer
    menu_split_timer += delta_time
    
    # Update softbody physics
    for softbody in main_menu_softbodies[:]:
        # Apply gravity and air resistance
        softbody.velocity += pygame.Vector2(0, 50) * delta_time  # Gentle gravity
        softbody.velocity *= 0.98  # Air resistance
        
        # Update position
        softbody.center += softbody.velocity * delta_time
        softbody.pos = softbody.center
        
        # Update rotation
        if hasattr(softbody, 'angular_velocity'):
            softbody.rotation_angle += softbody.angular_velocity * delta_time
            
            # Apply rotation to points
            if hasattr(softbody, 'points'):
                for point in softbody.points:
                    relative_pos = point.pos - softbody.center
                    angle = softbody.angular_velocity * delta_time
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)
                    
                    new_x = relative_pos.x * cos_a - relative_pos.y * sin_a
                    new_y = relative_pos.x * sin_a + relative_pos.y * cos_a
                    
                    point.pos = softbody.center + pygame.Vector2(new_x, new_y)
        
        # Boundary collision (left half of screen)
        radius = softbody.radius
        sim_width = SCREEN_WIDTH // 2
        
        if softbody.center.x - radius < 0:
            softbody.center.x = radius
            softbody.velocity.x = abs(softbody.velocity.x) * 0.7
        elif softbody.center.x + radius > sim_width:
            softbody.center.x = sim_width - radius
            softbody.velocity.x = -abs(softbody.velocity.x) * 0.7
            
        if softbody.center.y - radius < 0:
            softbody.center.y = radius
            softbody.velocity.y = abs(softbody.velocity.y) * 0.7
        elif softbody.center.y + radius > SCREEN_HEIGHT:
            softbody.center.y = SCREEN_HEIGHT - radius
            softbody.velocity.y = -abs(softbody.velocity.y) * 0.7
        
        # Update softbody internal physics
        try:
            softbody.update(None, [], delta_time, None)
        except:
            pass
    
    # Handle splitting
    if menu_split_timer >= menu_next_split_time and main_menu_softbodies:
        # Find splittable softbodies (more than 3 points)
        splittable = [sb for sb in main_menu_softbodies 
                     if hasattr(sb, 'points') and len(sb.points) > 3]
        
        if splittable:
            target = random.choice(splittable)
            
            # Try to split
            if hasattr(target, 'split_body') and callable(target.split_body):
                try:
                    result = target.split_body()
                    if result:
                        sb1, sb2, old_body = result
                        
                        # Remove old body
                        if old_body in main_menu_softbodies:
                            main_menu_softbodies.remove(old_body)
                        
                        # Add new bodies with inherited properties
                        for new_body in [sb1, sb2]:
                            base_velocity = getattr(old_body, 'velocity', pygame.Vector2(0, 0))
                            random_factor = pygame.Vector2(
                                random.uniform(-20, 20),
                                random.uniform(-20, 20)
                            )
                            new_body.velocity = base_velocity * 0.5 + random_factor
                            new_body.angular_velocity = getattr(old_body, 'angular_velocity', 0) + random.uniform(-1, 1)
                            new_body.rotation_angle = 0
                            
                            main_menu_softbodies.append(new_body)
                except:
                    pass
        
        menu_split_timer = 0
        menu_next_split_time = random.uniform(5.0, 15.0)
    
    # Cleanup softbodies that are too small
    to_remove = []
    for softbody in main_menu_softbodies:
        if hasattr(softbody, 'points') and len(softbody.points) <= 3:
            to_remove.append(softbody)
    
    for softbody in to_remove:
        main_menu_softbodies.remove(softbody)

def draw_main_menu_simulation(screen):
    """Draw main menu softbody simulation"""
    # Simple camera for drawing
    class SimpleCamera:
        zoom = 0.5
        def world_to_screen(self, pos):
            return (int(pos.x * self.zoom), int(pos.y * self.zoom))
    
    simple_camera = SimpleCamera()
    
    for softbody in main_menu_softbodies:
        try:
            softbody.draw(screen, simple_camera)
        except:
            # Fallback drawing
            screen_pos = simple_camera.world_to_screen(softbody.center)
            radius = int(softbody.radius * simple_camera.zoom)
            pygame.draw.circle(screen, (100, 150, 200), screen_pos, radius, 2)

""""Initialize player and UI - will be set when game starts"""
# These will be initialized when a game mode is selected
background_tile = None
origin = None
player_cells = []
selected_entities = []
camera = None
world_map = None
map_ui = None

# Game state variables that need to exist
cell_groups = {}
group_counter = 1
group_colors = {}
camera_follow_group_key = None
sprites = []
viruses = []
enemy_cells = []
virustypes = [CapsidVirus, FilamentousVirus, PhageVirus]
selection_box = None
is_selecting = False

# Main menu simulation variables
main_menu_softbodies = []
menu_split_timer = 0
menu_next_split_time = random.uniform(5.0, 15.0)
menu_spawn_timer = 0

# Initialize collision system
from entity import CollisionSystem
collision_system = CollisionSystem(cell_size=50)

# UI components that don't depend on game state
game_ui = None
cell_manager_ui = None
upgrade_ui = None
settings_ui = None
notebook_ui = None
discovery_tracker = None
evolution_meter = None
upgrade_button = None
settings_button = None
map_button = None
notebook_button = None

def initialize_game_ui():
    """Initialize UI components when starting a game"""
    global background_tile, game_ui, cell_manager_ui, upgrade_ui, settings_ui
    global upgrade_button, settings_button, map_button, notebook_button, notebook_ui, discovery_tracker, evolution_meter
    
    # Load background
    background_tile = pygame.image.load("assets\\scrolling_pattern.jpg").convert()
    background_tile = pygame.transform.scale(background_tile, (SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Initialize UI components
    game_ui = GameUI(screen, player_cells[0] if player_cells else None)
    
    from ui import CellManagerUI, NotebookUI
    from discovery_tracker import DiscoveryTracker
    
    cell_manager_ui = CellManagerUI(
        rect=pygame.Rect(10, 34 + 24*4 + 10, 240, 320),
        font=pygame.font.SysFont("calibri", 18),
        groups_ref=cell_groups,
        selected_entities_ref=selected_entities
    )
    
    upgrade_ui = UpgradeUI(screen, player_cells[0] if player_cells else None, close_menu, selected_entities)
    settings_ui = SettingsMenuUI(screen, close_menu, return_to_main_menu)
    
    # Initialize notebook and discovery tracker
    notebook_ui = NotebookUI(screen, lambda: None)  # Close callback handled in open_menu
    discovery_tracker = DiscoveryTracker(notebook_ui)
    
    # Initialize evolution meter
    evolution_meter = EvolutionMeter()
    
    upgrade_button = Button((SCREEN_WIDTH - 120, 20, 100, 40), "Upgrade", lambda: open_menu("upgrade"), pygame.font.SysFont("calibri", 20))
    settings_button = Button((SCREEN_WIDTH - 120, 70, 100, 40), "Settings", lambda: open_menu("settings"), pygame.font.SysFont("calibri", 20))
    map_button = Button((SCREEN_WIDTH - 120, 120, 100, 40), "Map (M)", lambda: map_ui.toggle_map() if map_ui else None, pygame.font.SysFont("calibri", 20))
    
    # Create notebook button with image
    try:
        notebook_icon = pygame.image.load("assets\\Notebook.png").convert_alpha()
        notebook_icon = pygame.transform.scale(notebook_icon, (40, 40))
        notebook_button = ImageButton((SCREEN_WIDTH - 120, 170, 100, 40), notebook_icon, lambda: open_menu("notebook"), "Notebook")
    except:
        # Fallback to text button if image not found
        notebook_button = Button((SCREEN_WIDTH - 120, 170, 100, 40), "Notebook", lambda: open_menu("notebook"), pygame.font.SysFont("calibri", 20))

def spawn_virus(pos):
    """Spawn a virus at the given position"""
    global virustypes, viruses
    virus_type = random.choice(virustypes)
    rr1 = random.randint(15, 25)  # Much smaller virus sizes
    if virus_type == CapsidVirus:
        viruses.append(CapsidVirus(pos, rr1, rr1//2))
    elif virus_type == FilamentousVirus:
        viruses.append(FilamentousVirus(pos, length=rr1*4, spacing=rr1//2, radius=rr1))
    elif virus_type == PhageVirus:
        viruses.append(PhageVirus(pos, radius=rr1, points=rr1//2))
    sprites.append(viruses[-1])

def spawn_enemy_cell(pos):
    """Spawn an enemy cell at the given position"""
    from entity import EnemyCell
    cell = EnemyCell(pos, points=12, radius=150, membrane_molecule=Lipid)
    enemy_cells.append(cell)
    sprites.append(cell)

game_ui = GameUI(screen, origin)
from ui import CellManagerUI
# Cell groups: dict name -> list of cells
cell_groups = {}
group_counter = 1
# Per-group color mapping: name -> (r,g,b)
group_colors = {}
# Camera follows this group name when available
camera_follow_group_key = None
# Maintain ordering of group navigation (function defined earlier)
cell_manager_ui = CellManagerUI(
    rect=pygame.Rect(10, 34 + 24*4 + 10, 240, 320),
    font=pygame.font.SysFont("calibri", 18),
    groups_ref=cell_groups,
    selected_entities_ref=selected_entities
)
# Initialize main menu UI (always available)
main_menu_ui = MainMenuUI(screen)

# Game-specific UI will be initialized when a game starts
upgrade_ui = None
settings_ui = SettingsMenuUI(screen, close_menu, return_to_main_menu)

# Game UI buttons - will be initialized when game starts
upgrade_button = None
settings_button = None
map_button = None

sprites = []
viruses = []
enemy_cells = []

virustypes = [CapsidVirus, FilamentousVirus, PhageVirus]

selection_box = None
is_selecting = False

# Initialize the improved collision system
from entity import CollisionSystem
collision_system = CollisionSystem(cell_size=50)

# Initialize main menu simulation
spawn_main_menu_softbody()

#spawn_enemy_cell((100, 100))

"""Main game loop"""

running = True
while running:
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    
    # Handle basic events that should always work
    for event in events:
        if event.type == pygame.QUIT:
            running = False
    
    # Handle events based on current game state
    current_state = game_state_manager.get_state()
    
    if current_state == GameState.MAIN_MENU:
        # Handle main menu events
        for event in events:
            selected_mode = main_menu_ui.handle_event(event)
            if selected_mode:
                start_game_mode(selected_mode)
        
        # Draw main menu
        main_menu_ui.draw(delta_time)
    
    else:
        # In game state - handle all game logic
        # RESTORED: Add procedural enemy spawning from iteration 3
        if player_cells and world_map:
            # Derive a view size based on current camera zoom (avoid division by zero)
            effective_zoom = max(0, camera.zoom)
            size_h = int(SCREEN_HEIGHT / effective_zoom)
            size_w = int(SCREEN_WIDTH / effective_zoom)
            half_size_h = size_h//2
            half_size_w = size_w//2

            bounding_box = pygame.Rect(camera.pos.x-half_size_w, camera.pos.y-half_size_h, size_w, size_h)
            min_spawn_distance = 1000  # Minimum distance from any player cell

            # Procedural enemy generation near groups (simplified from iteration 3)
            def _random_point_near(center: pygame.Vector2, min_d: float, max_d: float) -> pygame.Vector2:
                ang = random.uniform(0, 3.14159 * 2)
                dist = random.uniform(min_d, max_d)
                return pygame.Vector2(center.x + dist * math.cos(ang), center.y + dist * math.sin(ang))

            def _get_chunk_for_pos(pos):
                return world_map.get_chunk_at_world_pos(pos)

            def _chunk_has_enemy(chunk):
                # Check if chunk contains any enemy cells or viruses
                for cell in enemy_cells:
                    if _get_chunk_for_pos(cell.center) == chunk:
                        return True
                for virus in viruses:
                    if _get_chunk_for_pos(virus.pos) == chunk:
                        return True
                return False

            def _spawn_enemy_at(pos: pygame.Vector2, enemy_kind: str):
                chunk = _get_chunk_for_pos(pos)
                if chunk and _chunk_has_enemy(chunk):
                    return  # Mob cap reached, do not spawn
                if enemy_kind == 'rogue-virus':
                    spawn_virus(pos)
                elif enemy_kind == 'rogue-cell':
                    spawn_enemy_cell(pos)

            # Choose a group center as focus for spawns
            group_keys = [k for k, v in cell_groups.items() if v]
            group_centers = []
            for k in group_keys:
                members = cell_groups[k]
                if not members:
                    continue
                c = pygame.Vector2(0, 0)
                for m in members:
                    c += m.center
                group_centers.append(c / len(members))

            # Low probability each frame; scale with delta_time
            if group_centers and random.random() < 0.02 * (delta_time * 60.0):
                center = random.choice(group_centers)
                spawn_type = random.choice(['rogue-virus', 'rogue-cell'])
                # pick a valid spawn pos not too close to player cells
                for _ in range(8):
                    pos = _random_point_near(center, 400, 900)
                    chunk = _get_chunk_for_pos(pos)
                    if chunk and not _chunk_has_enemy(chunk) and all(pos.distance_to(cell.center) > min_spawn_distance for cell in player_cells):
                        _spawn_enemy_at(pos, spawn_type)
                        break
        
        handle_game_logic(events, delta_time)

    pygame.display.flip()
    delta_time = clock.tick(FPS) / 1000.0  # Convert milliseconds to seconds

pygame.quit()
                    