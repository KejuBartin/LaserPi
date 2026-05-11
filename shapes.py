import pygame
import math


def create_polygon(sides, radius):
    points = []

    angle_step = 360 / sides

    for i in range(sides):
        angle = math.radians(i * angle_step)

        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        points.append(pygame.Vector2(x, y))

    return points

def create_line(length):
    half = length / 2

    return [
        pygame.Vector2(-half, 0),
        pygame.Vector2(half, 0),
    ]

def create_circle(radius, segments=128):
    return create_polygon(segments, radius)