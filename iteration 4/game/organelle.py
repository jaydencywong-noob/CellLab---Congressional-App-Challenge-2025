from game.entity import Entity

class Organelle(Entity):
    def __init__(self, pos, name, boosts):
        super().__init__(pos)
        self.name = name
        self.boosts = boosts  # Dict of stat boosts

    def activate(self, player):
        # Apply boosts to player
        for stat, amount in self.boosts.items():
            setattr(player, stat, getattr(player, stat, 0) + amount)

    def get_image(self):
        # Placeholder: return a colored surface or icon
        import pygame
        surf = pygame.Surface((40, 40))
        surf.fill((180, 255, 100))
        return surf