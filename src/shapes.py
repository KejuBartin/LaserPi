import math
from collections.abc import Callable
from dataclasses import dataclass

import pygame


ShapeFactory = Callable[[], list[pygame.Vector2]]


@dataclass(frozen=True)
class ShapePreset:
    name: str
    factory: ShapeFactory
    closed: bool = True


SHAPE_PRESETS: dict[str, ShapePreset] = {}


def register_shape(name, closed=True):
    def decorator(factory):
        SHAPE_PRESETS[name] = ShapePreset(name=name, factory=factory, closed=closed)
        return factory

    return decorator


def list_shape_names():
    return sorted(SHAPE_PRESETS)


def get_shape_preset(name):
    try:
        return SHAPE_PRESETS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown shape preset: {name}") from exc


def create_polygon(sides, radius):
    if sides < 3:
        raise ValueError("Polygon needs at least 3 sides")
    if radius <= 0:
        raise ValueError("Polygon radius must be positive")

    points = []
    angle_step = 360 / sides

    for i in range(sides):
        angle = math.radians(i * angle_step)

        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        points.append(pygame.Vector2(x, y))

    return points


def create_line(length):
    if length <= 0:
        raise ValueError("Line length must be positive")

    half = length / 2

    return [
        pygame.Vector2(-half, 0),
        pygame.Vector2(half, 0),
    ]


def create_circle(radius, segments=128):
    if radius <= 0:
        raise ValueError("Circle radius must be positive")
    if segments < 3:
        raise ValueError("Circle needs at least 3 segments")

    return create_polygon(segments, radius)


@register_shape("square")
def create_square_shape():
    return create_polygon(4, 350)


@register_shape("triangle")
def create_triangle_shape():
    return create_polygon(3, 300)


@register_shape("line", closed=False)
def create_line_shape():
    return create_line(1000)


@register_shape("circle")
def create_circle_shape():
    return create_circle(200)


@register_shape("multilines", closed=False)
def create_multilines_shape():
    # placeholder: actual rendering for multiple parallel lines is handled by the 'lines' effect
    return []


@register_shape("dots", closed=False)
def create_dots_shape():
    return []