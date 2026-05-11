import pygame
import math

def rotate_point(point, angle_deg):
    rad = math.radians(angle_deg)

    x = point.x * math.cos(rad) - point.y * math.sin(rad)
    y = point.x * math.sin(rad) + point.y * math.cos(rad)

    return pygame.Vector2(x, y)


def rotate_points(points, angle_deg):
    return [
        rotate_point(p, angle_deg)
        for p in points
    ]


def translate_points(points, offset):
    return [
        p + offset
        for p in points
    ]