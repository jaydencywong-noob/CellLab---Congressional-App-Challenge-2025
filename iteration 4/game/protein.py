from game.entity import Entity

class Protein(Entity):
    def __init__(self, pos, name, boosts):
        super().__init__(pos)
        self.name = name
        self.boosts = boosts  # Dict of stat boosts
        # Ensure icon attribute exists for UI and Point drawing
        self.icon = self.get_image()

    def use(self, target):
        # Apply effect to target (e.g., attack, heal)
        pass

    def get_image(self):
        # Placeholder: return a colored surface or icon
        import pygame
        surf = pygame.Surface((40, 40))
        surf.fill((100, 180, 255))
        return surf