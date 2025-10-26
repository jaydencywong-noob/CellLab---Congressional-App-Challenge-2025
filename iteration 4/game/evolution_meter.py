import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class EvolutionMeter:
    """Tracks and displays evolution progress as a percentage meter"""
    
    def __init__(self):
        self.progress = 0.0  # 0.0 to 100.0
        self.max_progress = 100.0
        
        # Evolution tracking stats
        self.stats = {
            "molecules_collected": 0,
            "proteins_created": 0,
            "organelles_created": 0,
            "enemies_defeated": 0,
            "cells_split": 0,
            "discoveries_made": 0
        }
        
        # Point values for different evolutionary milestones
        self.point_values = {
            "molecule_collected": 0.1,      # Small but frequent
            "protein_created": 2.0,         # Moderate advancement
            "organelle_created": 3.0,       # Significant advancement
            "enemy_defeated": 1.5,          # Combat progress
            "cell_split": 1.0,              # Biological milestone
            "discovery_made": 2.5           # Scientific progress
        }
        
        # UI properties
        self.meter_width = 300
        self.meter_height = 20
        self.meter_x = (SCREEN_WIDTH - self.meter_width) // 2
        self.meter_y = SCREEN_HEIGHT - 50
        
        # Visual properties
        self.bg_color = (40, 40, 60)
        self.border_color = (100, 150, 200)
        self.fill_color = (50, 200, 100)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont("calibri", 16)
        
        # Animation properties for visual effects
        self.glow_intensity = 0.0
        self.glow_direction = 1
        
    def add_progress(self, event_type, amount=1):
        """Add evolution progress for a specific event type"""
        if event_type in self.point_values:
            points = self.point_values[event_type] * amount
            self.progress = min(self.max_progress, self.progress + points)
            
            # Update stats
            if event_type == "molecule_collected":
                self.stats["molecules_collected"] += amount
            elif event_type == "protein_created":
                self.stats["proteins_created"] += amount
            elif event_type == "organelle_created":
                self.stats["organelles_created"] += amount
            elif event_type == "enemy_defeated":
                self.stats["enemies_defeated"] += amount
            elif event_type == "cell_split":
                self.stats["cells_split"] += amount
            elif event_type == "discovery_made":
                self.stats["discoveries_made"] += amount
                
            # Trigger visual effect when progress is added
            self.glow_intensity = min(1.0, self.glow_intensity + 0.3)
            
            return points
        return 0
    
    def get_progress_percentage(self):
        """Get current progress as a percentage (0-100)"""
        return self.progress
    
    def is_evolution_complete(self):
        """Check if evolution meter has reached 100%"""
        return self.progress >= self.max_progress
    
    def get_evolution_stage(self):
        """Get current evolution stage based on progress"""
        if self.progress < 10:
            return "Primitive"
        elif self.progress < 25:
            return "Basic"
        elif self.progress < 50:
            return "Developing"
        elif self.progress < 75:
            return "Advanced"
        elif self.progress < 95:
            return "Complex"
        else:
            return "Evolved"
    
    def update(self, delta_time):
        """Update animation effects"""
        # Update glow animation
        self.glow_intensity -= delta_time * 1.5
        self.glow_intensity = max(0.0, self.glow_intensity)
    
    def draw(self, screen):
        """Draw the evolution meter on screen"""
        if not screen:
            return
            
        # Calculate fill width
        fill_width = int((self.progress / self.max_progress) * self.meter_width)
        
        # Draw background
        bg_rect = pygame.Rect(self.meter_x, self.meter_y, self.meter_width, self.meter_height)
        pygame.draw.rect(screen, self.bg_color, bg_rect)
        
        # Draw progress fill
        if fill_width > 0:
            fill_rect = pygame.Rect(self.meter_x, self.meter_y, fill_width, self.meter_height)
            
            # Add glow effect if recently updated
            if self.glow_intensity > 0:
                glow_color = (
                    min(255, int(self.fill_color[0] + self.glow_intensity * 100)),
                    min(255, int(self.fill_color[1] + self.glow_intensity * 50)),
                    min(255, int(self.fill_color[2] + self.glow_intensity * 50))
                )
                pygame.draw.rect(screen, glow_color, fill_rect)
            else:
                pygame.draw.rect(screen, self.fill_color, fill_rect)
        
        # Draw border
        pygame.draw.rect(screen, self.border_color, bg_rect, 2)
        
        # Draw progress text
        progress_text = f"Evolution: {self.progress:.1f}% - {self.get_evolution_stage()}"
        text_surface = self.font.render(progress_text, True, self.text_color)
        text_rect = text_surface.get_rect()
        text_rect.centerx = self.meter_x + self.meter_width // 2
        text_rect.bottom = self.meter_y - 5
        screen.blit(text_surface, text_rect)
        
        # Draw milestone indicators (every 25%)
        for i in range(1, 4):  # 25%, 50%, 75%
            milestone_x = self.meter_x + int((i * 0.25) * self.meter_width)
            milestone_color = self.border_color if self.progress >= i * 25 else (80, 80, 80)
            pygame.draw.line(screen, milestone_color, 
                           (milestone_x, self.meter_y), 
                           (milestone_x, self.meter_y + self.meter_height), 2)
    
    def reset(self):
        """Reset evolution progress"""
        self.progress = 0.0
        self.stats = {key: 0 for key in self.stats.keys()}
        self.glow_intensity = 0.0
    
    def save_state(self):
        """Return current state for saving"""
        return {
            "progress": self.progress,
            "stats": self.stats.copy()
        }
    
    def load_state(self, state_data):
        """Load evolution state from saved data"""
        if state_data:
            self.progress = state_data.get("progress", 0.0)
            self.stats = state_data.get("stats", {key: 0 for key in self.stats.keys()})