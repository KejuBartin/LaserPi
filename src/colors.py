import colorsys
import math
from collections.abc import Callable


Color = tuple[int, int, int]
ColorFunction = Callable[[float], Color]

COLOR_SCHEMES: dict[str, ColorFunction] = {}


def register_color(name):
    def decorator(color_fn):
        COLOR_SCHEMES[name] = color_fn
        return color_fn

    return decorator


def list_color_names():
    return sorted(COLOR_SCHEMES)


def get_color_function(name, solid_color="#ffffff"):
    if name == "solid":
        return solid_color_function(solid_color)

    try:
        return COLOR_SCHEMES[name]
    except KeyError as exc:
        raise KeyError(f"Unknown color scheme: {name}") from exc


def parse_hex_color(hex_color):
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError("Hex color must be in #RRGGBB format")

    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return (red, green, blue)


def solid_color_function(hex_color):
    rgb = parse_hex_color(hex_color)
    return lambda t: rgb


@register_color("solid")
def solid(t):
    return (255, 255, 255)


@register_color("rainbow")
def rainbow(t):
    r, g, b = colorsys.hsv_to_rgb(t % 1.0, 1.0, 1.0)

    return (
        int(r * 255),
        int(g * 255),
        int(b * 255),
    )


@register_color("ice")
def ice(t):
    phase = t % 1.0
    wave = 0.5 + 0.5 * math.sin(phase * math.tau)

    return (
        40,
        int(120 + 80 * wave),
        int(180 + 60 * wave),
    )


@register_color("fire")
def fire(t):
    phase = t % 1.0
    ember = 0.5 + 0.5 * math.sin(phase * math.tau)
    glow = 0.5 + 0.5 * math.sin(phase * math.tau + math.pi / 3)
    r = int(180 + 60 * ember)
    g = int(35 + 150 * glow)
    b = int(8 + 28 * (1.0 - glow))
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


@register_color("pastel")
def pastel(t):
    phase = (t * 0.7) % 1.0
    r = int(205 + 35 * math.sin(phase * math.tau))
    g = int(195 + 35 * math.sin(phase * math.tau + 2.1))
    b = int(225 + 25 * math.sin(phase * math.tau + 4.2))
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


@register_color("mono")
def mono(t):
    phase = t % 1.0
    v = int(100 + 110 * (0.5 + 0.5 * math.sin(phase * math.tau)))
    return (v, v, v)


@register_color("ocean")
def ocean(t):
    phase = t % 1.0
    red = int(20 + 20 * (0.5 + 0.5 * math.sin(phase * math.tau + 1.2)))
    green = int(90 + 120 * (0.5 + 0.5 * math.sin(phase * math.tau + 2.3)))
    blue = int(150 + 100 * (0.5 + 0.5 * math.sin(phase * math.tau + 3.4)))
    return (
        max(0, min(255, red)),
        max(0, min(255, green)),
        max(0, min(255, blue)),
    )


@register_color("neon")
def neon(t):
    phase = t % 1.0
    red = int(180 + 70 * (0.5 + 0.5 * math.sin(phase * math.tau)))
    green = int(120 + 120 * (0.5 + 0.5 * math.sin(phase * math.tau + 2.1)))
    blue = int(180 + 70 * (0.5 + 0.5 * math.sin(phase * math.tau + 4.2)))
    return (
        max(0, min(255, red)),
        max(0, min(255, green)),
        max(0, min(255, blue)),
    )