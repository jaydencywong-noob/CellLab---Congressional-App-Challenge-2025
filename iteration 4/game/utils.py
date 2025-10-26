import pygame

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def lerp(a, b, t):
    return a + (b - a) * t

def load_image(path):
    return pygame.image.load(path).convert_alpha()

def distance(a, b):
    return (a - b).length()