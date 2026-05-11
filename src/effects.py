import math
from collections.abc import Callable

import pygame

from colors import get_color_function
from state import LaserState


EffectRenderer = Callable[[pygame.Surface, LaserState], pygame.Surface]

EFFECTS: dict[str, EffectRenderer] = {}
MOTION_EFFECTS: dict[str, EffectRenderer] = {}


def register_effect(name):
    def decorator(effect_fn):
        EFFECTS[name] = effect_fn
        return effect_fn

    return decorator


def register_motion_effect(name):
    def decorator(effect_fn):
        MOTION_EFFECTS[name] = effect_fn
        return effect_fn

    return decorator


def list_effect_names():
    return sorted(EFFECTS)


def list_motion_names():
    return sorted(MOTION_EFFECTS)


def get_effect_renderer(name):
    try:
        return EFFECTS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown effect: {name}") from exc


def get_motion_renderer(name):
    try:
        return MOTION_EFFECTS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown motion effect: {name}") from exc


def apply_effect_chain(surface, state, effect_names):
    result = surface
    for name in effect_names:
        renderer = get_effect_renderer(name)
        result = renderer(result, state)
    return result


def _clamp_scale(scale, maximum=4.0):
    return min(maximum, max(0.01, float(scale)))


def _translate_surface(source_surface, offset_x=0, offset_y=0):
    width, height = source_surface.get_size()
    translated_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    if width <= 0 or height <= 0:
        return translated_surface

    shift_x = int(round(offset_x)) % width
    shift_y = int(round(offset_y)) % height

    if shift_x and shift_y:
        positions = (
            (shift_x - width, shift_y - height),
            (shift_x - width, shift_y),
            (shift_x, shift_y - height),
            (shift_x, shift_y),
        )
    elif shift_x:
        positions = ((shift_x - width, 0), (shift_x, 0))
    elif shift_y:
        positions = ((0, shift_y - height), (0, shift_y))
    else:
        positions = ((0, 0),)

    for x, y in positions:
        translated_surface.blit(source_surface, (x, y))

    return translated_surface


@register_effect("static")
def render_static(source_surface, state):
    del state
    return source_surface


@register_effect("rotate")
def render_rotating(source_surface, state):
    rotated_surface = pygame.transform.rotozoom(source_surface, -state.angle, _clamp_scale(state.scale))
    return rotated_surface


@register_effect("pulse")
def render_pulsing(source_surface, state):
    pulse = 0.90 + 0.10 * (0.5 - 0.5 * math.cos(math.tau * state.beat_phase))
    scaled_surface = pygame.transform.rotozoom(source_surface, 0.0, state.scale * pulse)
    return scaled_surface


@register_effect("beat_flash")
def render_beat_flash(source_surface, state):
    flash_width = 0.08
    if state.beat_phase < flash_width:
        return source_surface

    return pygame.Surface(source_surface.get_size(), pygame.SRCALPHA)


@register_effect("grow")
def render_grow(source_surface, state):
    # Sawtooth envelope: grow continuously, then snap back to small at wrap.
    phase = state.beat_phase % 1.0
    min_scale = 0.12
    max_scale = 3.2
    scale = min_scale + (max_scale - min_scale) * phase
    grown_surface = pygame.transform.rotozoom(source_surface, 0.0, _clamp_scale(state.scale * scale))
    return grown_surface


@register_effect("bounce")
def render_bounce(source_surface, state):
    phase = state.lines_offset % 1.0
    # Oscillate between -1.0 and 1.0 using triangle wave
    if phase < 0.5:
        t = phase * 2.0  # 0 to 1
    else:
        t = (1.0 - phase) * 2.0  # 1 to 0

    oscillation = t * 2.0 - 1.0  # -1 to 1

    direction = getattr(state, "bounce_direction", "horizontal")
    bounce_range = max(0.0, min(1.0, float(getattr(state, "bounce_range", 1.0))))
    src_width, src_height = source_surface.get_size()

    viewport_width = max(src_width, int(getattr(state, "viewport_width", src_width) or src_width))
    viewport_height = max(src_height, int(getattr(state, "viewport_height", src_height) or src_height))

    max_dx = max(0.0, (viewport_width - src_width) / 2.0) * bounce_range
    max_dy = max(0.0, (viewport_height - src_height) / 2.0) * bounce_range

    if direction == "vertical":
        bounce_height = src_height + int(math.ceil(max_dy * 2.0))
        bounce_width = src_width
        bounced = pygame.Surface((bounce_width, bounce_height), pygame.SRCALPHA)
        center_y = bounce_height / 2.0
        src_y = int(round(center_y - src_height / 2.0 + oscillation * max_dy))
        bounced.blit(source_surface, (0, src_y))
    else:  # horizontal
        bounce_width = src_width + int(math.ceil(max_dx * 2.0))
        bounce_height = src_height
        bounced = pygame.Surface((bounce_width, bounce_height), pygame.SRCALPHA)
        center_x = bounce_width / 2.0
        src_x = int(round(center_x - src_width / 2.0 + oscillation * max_dx))
        bounced.blit(source_surface, (src_x, 0))

    return bounced


@register_motion_effect("left-to-right")
def render_left_to_right(source_surface, state):
    return _translate_surface(source_surface, offset_x=state.lines_offset * source_surface.get_width())


@register_motion_effect("right-to-left")
def render_right_to_left(source_surface, state):
    return _translate_surface(source_surface, offset_x=state.lines_offset * source_surface.get_width())


@register_motion_effect("top-to-bottom")
def render_top_to_bottom(source_surface, state):
    return _translate_surface(source_surface, offset_y=state.lines_offset * source_surface.get_height())


@register_motion_effect("bottom-to-top")
def render_bottom_to_top(source_surface, state):
    return _translate_surface(source_surface, offset_y=state.lines_offset * source_surface.get_height())
