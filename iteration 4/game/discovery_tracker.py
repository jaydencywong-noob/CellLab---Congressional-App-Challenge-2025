"""
Scientific Discovery Tracking System
Monitors player actions and triggers discoveries when conditions are met.
"""

import time
from config import DISCOVERIES

class DiscoveryTracker:
    """Tracks and manages scientific discoveries"""
    
    def __init__(self, notebook_ui=None):
        self.notebook_ui = notebook_ui
        self.discovered = set()
        self.stats = {
            "molecules_collected": {"protein": 0, "lipid": 0, "nucleic_acid": 0, "carbohydrate": 0},
            "cells_split": 0,
            "viruses_defeated": 0,
            "enemies_defeated": 0,
            "pois_discovered": 0,
            "organelles_created": 0,
            "biomes_explored": set(),
            "max_cell_size": 0,
            "max_speed": 0,
            "survival_start_time": time.time(),
            "upgrades_purchased": 0,
            "symbiosis_formed": 0
        }
    
    def set_notebook_ui(self, notebook_ui):
        """Set the notebook UI reference"""
        self.notebook_ui = notebook_ui
    
    def trigger_discovery(self, discovery_id):
        """Manually trigger a specific discovery"""
        if discovery_id not in self.discovered and self.notebook_ui:
            if self.notebook_ui.add_discovery(discovery_id):
                self.discovered.add(discovery_id)
                print(f"🔬 New Discovery: {DISCOVERIES[discovery_id]['title']}")
                
                # Add evolution progress for discovery
                from main import evolution_meter
                if evolution_meter:
                    evolution_meter.add_progress("discovery_made")
                
                return True
        return False
    
    def check_molecule_discoveries(self):
        """Check for molecule collection milestones"""
        for molecule_type, count in self.stats["molecules_collected"].items():
            discovery_id = f"100_{molecule_type}"
            if count >= 100 and discovery_id not in self.discovered:
                self.trigger_discovery(discovery_id)
    
    def check_size_discoveries(self, cell_radius):
        """Check for cell size milestones"""
        if cell_radius > self.stats["max_cell_size"]:
            self.stats["max_cell_size"] = cell_radius
            
            if cell_radius >= 200 and "large_cell" not in self.discovered:
                self.trigger_discovery("large_cell")
    
    def check_speed_discoveries(self, current_speed):
        """Check for speed milestones"""
        if current_speed > self.stats["max_speed"]:
            self.stats["max_speed"] = current_speed
            
            if current_speed >= 500 and "speed_demon" not in self.discovered:
                self.trigger_discovery("speed_demon")
    
    def check_survival_discoveries(self):
        """Check for survival time milestones"""
        survival_time = time.time() - self.stats["survival_start_time"]
        if survival_time >= 300 and "survivor" not in self.discovered:  # 5 minutes
            self.trigger_discovery("survivor")
    
    def check_exploration_discoveries(self):
        """Check for exploration milestones"""
        if len(self.stats["biomes_explored"]) >= 5 and "ecosystem_explorer" not in self.discovered:
            self.trigger_discovery("ecosystem_explorer")
    
    # Event handlers for specific actions
    def on_cell_split(self):
        """Called when a cell splits"""
        self.stats["cells_split"] += 1
        if "first_split" not in self.discovered:
            self.trigger_discovery("first_split")
            
        # Add evolution progress for cell division
        from main import evolution_meter
        if evolution_meter:
            evolution_meter.add_progress("cell_split")
    
    def on_molecule_collected(self, molecule_type, amount=1):
        """Called when molecules are collected"""
        if molecule_type in self.stats["molecules_collected"]:
            self.stats["molecules_collected"][molecule_type] += amount
            self.check_molecule_discoveries()
            
            # Add evolution progress for molecule collection
            from main import evolution_meter
            if evolution_meter:
                evolution_meter.add_progress("molecule_collected", amount)
    
    def on_virus_defeated(self):
        """Called when a virus is defeated"""
        self.stats["viruses_defeated"] += 1
        if "first_virus_defeat" not in self.discovered:
            self.trigger_discovery("first_virus_defeat")
            
        # Add evolution progress for combat
        from main import evolution_meter
        if evolution_meter:
            evolution_meter.add_progress("enemy_defeated")
    
    def on_enemy_defeated(self):
        """Called when an enemy cell is defeated"""
        self.stats["enemies_defeated"] += 1
        if "first_enemy_defeat" not in self.discovered:
            self.trigger_discovery("first_enemy_defeat")
            
        # Add evolution progress for combat
        from main import evolution_meter
        if evolution_meter:
            evolution_meter.add_progress("enemy_defeated")
    
    def on_poi_discovered(self):
        """Called when a POI is discovered"""
        self.stats["pois_discovered"] += 1
        if "poi_discovery" not in self.discovered:
            self.trigger_discovery("poi_discovery")
    
    def on_organelle_created(self):
        """Called when an organelle is created"""
        self.stats["organelles_created"] += 1
        if "organelle_creation" not in self.discovered:
            self.trigger_discovery("organelle_creation")
    
    def on_membrane_upgraded(self):
        """Called when membrane is upgraded"""
        if "membrane_upgrade" not in self.discovered:
            self.trigger_discovery("membrane_upgrade")
    
    def on_biome_explored(self, biome_name):
        """Called when a new biome is explored"""
        if biome_name not in self.stats["biomes_explored"]:
            self.stats["biomes_explored"].add(biome_name)
            self.check_exploration_discoveries()
    
    def on_symbiosis_formed(self):
        """Called when symbiosis is formed"""
        self.stats["symbiosis_formed"] += 1
        if "symbiosis" not in self.discovered:
            self.trigger_discovery("symbiosis")
    
    def on_cell_update(self, cell):
        """Called during cell updates to check various stats"""
        if hasattr(cell, 'radius'):
            self.check_size_discoveries(cell.radius)
        
        if hasattr(cell, 'velocity'):
            speed = cell.velocity.length() if hasattr(cell.velocity, 'length') else 0
            self.check_speed_discoveries(speed)
        
        self.check_survival_discoveries()
    
    def get_discovery_count(self):
        """Get total number of discoveries made"""
        return len(self.discovered)
    
    def get_discovery_percentage(self):
        """Get percentage of total discoveries completed"""
        total_discoveries = len(DISCOVERIES)
        return (len(self.discovered) / total_discoveries) * 100 if total_discoveries > 0 else 0
    
    def on_organelle_purchased(self, organelle_name):
        """Called when an organelle is purchased/created"""
        self.stats["organelles_created"] = self.stats.get("organelles_created", 0) + 1
        
        # Add evolution progress for organelle creation
        from main import evolution_meter
        if evolution_meter:
            evolution_meter.add_progress("organelle_created")
        
        # Trigger general organelle creation
        if "organelle_creation" not in self.discovered:
            self.trigger_discovery("organelle_creation")
        
        # Trigger specific organelle discoveries
        organelle_discoveries = {
            "Cell Membrane+": "membrane_upgrade",
            "Lysosome Pack": "lysosome_discovery",
            "Mitochondria": "mitochondria_discovery",
            "Nucleus": "nucleus_formation", 
            "Endoplasmic Reticulum": "er_creation",
            "Golgi Apparatus": "golgi_formation"
        }
        
        if organelle_name in organelle_discoveries:
            discovery_id = organelle_discoveries[organelle_name]
            if discovery_id not in self.discovered:
                self.trigger_discovery(discovery_id)
    
    def on_protein_purchased(self, protein_name):
        """Called when a protein is purchased/created"""
        # Add evolution progress for protein creation
        from main import evolution_meter
        if evolution_meter:
            evolution_meter.add_progress("protein_created")
            
        # Map protein names to discovery IDs
        protein_discoveries = {
            "Protein Core": "protein_core_discovery",
            "Elastin Protein": "elastin_protein_discovery", 
            "Collagen Protein": "collagen_protein_discovery",
            "Enzymes": "enzyme_discovery",
            "Receptors": "receptor_discovery",
            "Protein Cannon": "protein_cannon_discovery",
            "Protein Bomb": "protein_bomb_discovery",
            "Protein Burst": "protein_burst_discovery",
            "Molecular Drill": "molecular_drill_discovery",
            "Enzyme Strike": "enzyme_strike_discovery",
            "Spikes": "spike_discovery",
            "Barrier Matrix": "barrier_matrix_discovery",
            "Adhesion Web": "adhesion_web_discovery", 
            "Resonance Shield": "resonance_shield_discovery",
            "Chitin Armor": "chitin_armor_discovery"
        }
        
        if protein_name in protein_discoveries:
            discovery_id = protein_discoveries[protein_name]
            if discovery_id not in self.discovered:
                self.trigger_discovery(discovery_id)
    
    def on_symbiosis_formed(self):
        """Called when cells are connected via springs"""
        self.stats["symbiosis_formed"] = self.stats.get("symbiosis_formed", 0) + 1
        if "symbiosis" not in self.discovered:
            self.trigger_discovery("symbiosis")