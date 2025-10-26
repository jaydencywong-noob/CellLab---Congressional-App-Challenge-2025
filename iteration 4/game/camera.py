import pygame

class Camera:
    def __init__(self, pos, zoom=1.0):
        self.pos = pygame.Vector2(pos)
        self.zoom = zoom

    def world_to_screen(self, world_pos):
        return (world_pos - self.pos) * self.zoom + pygame.Vector2(self.get_screen_center())

    def screen_to_world(self, screen_pos):
        return (pygame.Vector2(screen_pos) - pygame.Vector2(self.get_screen_center())) / self.zoom + self.pos

    def get_screen_center(self):
        surface = pygame.display.get_surface()
        return (surface.get_width() // 2, surface.get_height() // 2)

    def apply_zoom(self, surface):
        size = surface.get_size()
        return pygame.transform.smoothscale(surface, (int(size[0] * self.zoom), int(size[1] * self.zoom)))