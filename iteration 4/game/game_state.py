import pickle
import os
from enum import Enum
from typing import Optional, Dict, Any

class GameState(Enum):
    """Enumeration of possible game states"""
    MAIN_MENU = "main_menu"
    SINGLEPLAYER = "singleplayer"
    MULTIPLAYER = "multiplayer"
    LAB_MODE = "lab"

class GameInstance:
    """Represents a saved game instance"""
    def __init__(self, mode: str):
        self.mode = mode
        self.player_cells = []
        self.player_molecules = {}
        self.player_upgrades = {}
        self.world_seed = None
        self.timestamp = None
        
    def save_state(self, player_cells, player_molecules, player_upgrades, world_seed=None):
        """Save the current game state - only serializable data, not pygame objects"""
        # Save serializable cell data instead of pygame objects
        self.player_cells = []
        for cell in player_cells:
            cell_data = {
                'pos': (cell.pos.x, cell.pos.y) if hasattr(cell.pos, 'x') else cell.pos,
                'radius': cell.radius,
                'health': getattr(cell, 'health', 100),
                'max_health': getattr(cell, 'max_health', 100),
                # Add other serializable properties as needed
            }
            self.player_cells.append(cell_data)
            
        self.player_molecules = player_molecules.copy()
        self.player_upgrades = {k: v.copy() for k, v in player_upgrades.items()}
        self.world_seed = world_seed
        import time
        self.timestamp = time.time()

class GameStateManager:
    """Manages game states and saves/loads game instances"""
    
    def __init__(self):
        self.current_state = GameState.MAIN_MENU
        self.singleplayer_instance: Optional[GameInstance] = None
        self.lab_instance: Optional[GameInstance] = None
        self.save_directory = "saves"
        
        # Create saves directory if it doesn't exist
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
    
    def set_state(self, new_state: GameState):
        """Change the current game state"""
        self.current_state = new_state
    
    def get_state(self) -> GameState:
        """Get the current game state"""
        return self.current_state
    
    def save_current_game(self, mode: str, player_cells, player_molecules, player_upgrades, world_seed=None):
        """Save the current game state to the appropriate instance"""
        if mode == "singleplayer":
            if self.singleplayer_instance is None:
                self.singleplayer_instance = GameInstance("singleplayer")
            self.singleplayer_instance.save_state(player_cells, player_molecules, player_upgrades, world_seed)
            self._save_to_file("singleplayer", self.singleplayer_instance)
            
        elif mode == "lab":
            if self.lab_instance is None:
                self.lab_instance = GameInstance("lab")
            self.lab_instance.save_state(player_cells, player_molecules, player_upgrades, world_seed)
            self._save_to_file("lab", self.lab_instance)
    
    def load_game_instance(self, mode: str) -> Optional[GameInstance]:
        """Load a game instance for the specified mode"""
        instance = self._load_from_file(mode)
        
        if mode == "singleplayer":
            self.singleplayer_instance = instance
        elif mode == "lab":
            self.lab_instance = instance
            
        return instance
    
    def has_saved_game(self, mode: str) -> bool:
        """Check if there's a saved game for the specified mode"""
        return os.path.exists(os.path.join(self.save_directory, f"{mode}_save.pkl"))
    
    def _save_to_file(self, mode: str, instance: GameInstance):
        """Save game instance to file"""
        try:
            filepath = os.path.join(self.save_directory, f"{mode}_save.pkl")
            with open(filepath, 'wb') as f:
                pickle.dump(instance, f)
        except Exception as e:
            print(f"Failed to save {mode} game: {e}")
    
    def _load_from_file(self, mode: str) -> Optional[GameInstance]:
        """Load game instance from file"""
        try:
            filepath = os.path.join(self.save_directory, f"{mode}_save.pkl")
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
            else:
                if os.path.exists(filepath):
                    print(f"Warning: Save file {filepath} is empty, removing it")
                    os.remove(filepath)
        except (pickle.UnpicklingError, EOFError) as e:
            print(f"Corrupted save file for {mode}, removing it: {e}")
            filepath = os.path.join(self.save_directory, f"{mode}_save.pkl")
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Failed to load {mode} game: {e}")
        return None
    
    def get_new_game_defaults(self, mode: str) -> Dict[str, Any]:
        """Get default values for starting a new game in the specified mode"""
        if mode == "lab":
            # Lab mode starts with more resources and upgrades
            return {
                "player_molecules": {
                    "protein": 10000,
                    "lipid": 10000,
                    "nucleic_acid": 10000,
                    "carbohydrate": 10000
                },
                "starting_size": 15,  # Larger starting cell
                "starting_health": 300,
                "debug_mode": True
            }
        else:
            # Normal singleplayer defaults
            return {
                "player_molecules": {
                    "protein": 1000,
                    "lipid": 1000,
                    "nucleic_acid": 1000,
                    "carbohydrate": 1000
                },
                "starting_size": 10,
                "starting_health": 200,
                "debug_mode": False
            }