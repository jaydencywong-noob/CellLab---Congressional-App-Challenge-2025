import pygame
from entity import Point
import random

class Protein(Point):
    def __init__(self, pos, parent=None):
        super().__init__(pos, parent)
        self.radius = 15
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 180, 255), (15, 15), self.radius)
        self.pos = pygame.Vector2(pos)
        self.type = "protein"
        self.value = random.randint(1, 3)
        self.parent = parent

    def draw(self, surface, camera):
        screen_pos = camera.world_to_screen(self.pos)
        img = camera.apply_zoom(self.image)
        surface.blit(img, img.get_rect(center=screen_pos))

class Lipid(Point):
    def __init__(self, pos, parent=None):
        super().__init__(pos, parent)
        self.radius = 15
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180, 255, 100), (15, 15), self.radius)
        self.pos = pygame.Vector2(pos)
        self.type = "lipid"
        self.value = random.randint(1, 3)
        self.parent = parent


class NucleicAcid(Point):
    def __init__(self, pos, parent=None):
        super().__init__(pos, parent)
        self.radius = 15
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 100, 180), (15, 15), self.radius)
        self.pos = pygame.Vector2(pos)
        self.type = "nucleic_acid"
        self.value = random.randint(1, 3)
        self.parent = parent

    def draw(self, surface, camera):
        screen_pos = camera.world_to_screen(self.pos)
        img = camera.apply_zoom(self.image)
        surface.blit(img, img.get_rect(center=screen_pos))

class Carbohydrate(Point):
    def __init__(self, pos, parent=None):
        super().__init__(pos, parent)
        self.radius = 15
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 200, 100), (15, 15), self.radius)
        self.pos = pygame.Vector2(pos)
        self.type = "carbohydrate"
        self.value = random.randint(1, 3)
        self.parent = parent

    def draw(self, surface, camera):
        screen_pos = camera.world_to_screen(self.pos)
        img = camera.apply_zoom(self.image)
        surface.blit(img, img.get_rect(center=screen_pos))