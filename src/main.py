import math
import traceback
import pygame
from collections import OrderedDict

from colors import get_color_function
from effects import apply_effect_chain
from renderer import (
    create_gradient_outline_surface,
    create_gradient_outline_viewport_surface,
    create_parallel_lines_surface,
    create_dots_surface,
    create_dvd_dots_surface,
)
from shapes import get_shape_preset
from state import SharedLaserState
from web_control import start_web_server
from aalink_adapter import start_ableton_link

pygame.init()

# --------------------------------
# Window
# --------------------------------
screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

WIDTH, HEIGHT = screen.get_size()

CENTER = (WIDTH // 2, HEIGHT // 2)

pygame.display.set_caption("Showlaser")
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()

control_state = SharedLaserState()
control_state.update(viewport_width=WIDTH, viewport_height=HEIGHT)

try:
    web_server = start_web_server(control_state)
    print(f"LaserPi web control running on http://{web_server.server_address[0]}:{web_server.server_address[1]}")
except OSError as exc:
    web_server = None
    print(f"Could not start web control server: {exc}")

# start Ableton Link if available
aalink_stop = None
try:
    aalink_stop = start_ableton_link(control_state)
    if aalink_stop is not None:
        print("Ableton Link adapter started")
except Exception as exc:
    print(f"Ableton Link adapter failed to start: {exc}")

surface_cache = OrderedDict()
CACHE_LIMIT = 16
BASIC_OUTLINE_SHAPES = {"circle", "line", "square", "triangle"}


def blit_motion_wrapped(target_surface, source_surface, motion_name, offset_fraction):
    base_rect = source_surface.get_rect(center=CENTER)
    offset_fraction = float(offset_fraction) % 1.0

    if motion_name in ("left-to-right", "right-to-left"):
        offset_x = int(round(offset_fraction * WIDTH))
        for screen_shift in (-WIDTH, 0, WIDTH):
            target_surface.blit(source_surface, base_rect.move(offset_x + screen_shift, 0))
        return

    if motion_name in ("top-to-bottom", "bottom-to-top"):
        offset_y = int(round(offset_fraction * HEIGHT))
        for screen_shift in (-HEIGHT, 0, HEIGHT):
            target_surface.blit(source_surface, base_rect.move(0, offset_y + screen_shift))
        return

    target_surface.blit(source_surface, base_rect)


def blit_positioned(target_surface, source_surface, snapshot, effect_name):
    src_width, src_height = source_surface.get_size()
    bounce_range = max(0.0, min(1.0, float(getattr(snapshot, "bounce_range", 1.0))))
    max_dx = max(0.0, (WIDTH - src_width) / 2.0) * bounce_range
    max_dy = max(0.0, (HEIGHT - src_height) / 2.0) * bounce_range

    if effect_name == "dvd":
        bx = float(getattr(snapshot, "dvd_pos_x", 0.5))
        by = float(getattr(snapshot, "dvd_pos_y", 0.5))
        x = int(round((WIDTH - src_width) / 2.0 + (bx - 0.5) * 2.0 * max_dx))
        y = int(round((HEIGHT - src_height) / 2.0 + (by - 0.5) * 2.0 * max_dy))
        target_surface.blit(source_surface, (x, y))
        return

    phase = float(getattr(snapshot, "lines_offset", 0.0)) % 1.0
    t = phase * 2.0 if phase < 0.5 else (1.0 - phase) * 2.0
    oscillation = t * 2.0 - 1.0

    if getattr(snapshot, "bounce_direction", "horizontal") == "vertical":
        x = int(round((WIDTH - src_width) / 2.0))
        y = int(round((HEIGHT - src_height) / 2.0 + oscillation * max_dy))
    else:
        x = int(round((WIDTH - src_width) / 2.0 + oscillation * max_dx))
        y = int(round((HEIGHT - src_height) / 2.0))

    target_surface.blit(source_surface, (x, y))


def get_cached_surface(cache_key, build_fn):
    if cache_key in surface_cache:
        cached_surface = surface_cache.pop(cache_key)
        surface_cache[cache_key] = cached_surface
        return cached_surface

    cached_surface = build_fn()
    surface_cache[cache_key] = cached_surface
    while len(surface_cache) > CACHE_LIMIT:
        surface_cache.popitem(last=False)
    return cached_surface


def get_multiline_motion_offset(snapshot, angle_deg):
    width, height = WIDTH, HEIGHT
    angle_rad = math.radians(float(angle_deg) % 360.0)
    px = -math.sin(angle_rad)
    py = math.cos(angle_rad)
    perpendicular_extent = (abs(px) * width + abs(py) * height) / 2.0
    spacing = max(1.0, (perpendicular_extent * 2.0) / max(1, int(snapshot.lines_count)))
    offset_fraction = float(snapshot.lines_offset) % 1.0

    if snapshot.motion_name in ("left-to-right", "right-to-left"):
        return (px * offset_fraction * WIDTH) / spacing
    if snapshot.motion_name in ("top-to-bottom", "bottom-to-top"):
        return (py * offset_fraction * HEIGHT) / spacing

    return 0.0


def get_grow_scale(snapshot, points):
    phase = float(snapshot.beat_phase) % 1.0
    min_scale = 0.12
    max_scale = 3.2
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    shape_size = max(0.1, float(getattr(snapshot, "shape_size", 1.0)))
    base_extent = max((max(xs) - min(xs)) / shape_size, (max(ys) - min(ys)) / shape_size, 1.0)
    viewport_extent = math.hypot(WIDTH, HEIGHT)
    max_scale = max(max_scale, (viewport_extent / base_extent) * 1.15)
    return min_scale + (max_scale - min_scale) * phase


def rotate_points(points, angle_deg):
    if not angle_deg:
        return points

    angle_rad = math.radians(float(angle_deg) % 360.0)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return [
        pygame.Vector2(
            p.x * cos_a - p.y * sin_a,
            p.x * sin_a + p.y * cos_a,
        )
        for p in points
    ]


def build_outline_points(snapshot, effect_names=()):
    preset = get_shape_preset(snapshot.shape_name)
    shape_points = preset.factory()

    shape_size = max(0.1, float(getattr(snapshot, "shape_size", 1.0)))
    if shape_size != 1.0:
        shape_points = [pygame.Vector2(p.x * shape_size, p.y * shape_size) for p in shape_points]

    angle = 0.0
    if snapshot.shape_name == "line":
        angle += float(snapshot.line_angle) % 360.0
    if "rotate" in effect_names:
        angle -= float(snapshot.angle) % 360.0

    shape_points = rotate_points(shape_points, angle)

    if "grow" in effect_names:
        grow_scale = get_grow_scale(snapshot, shape_points)
        shape_size = max(0.1, float(getattr(snapshot, "shape_size", 1.0)))
        grow_scale = float(snapshot.scale) * grow_scale / shape_size
        shape_points = [pygame.Vector2(p.x * grow_scale, p.y * grow_scale) for p in shape_points]

    return preset, shape_points


def build_shape_surface(snapshot, effect_names=(), viewport=False, multiline_angle=None, multiline_offset=0.0):
    preset = get_shape_preset(snapshot.shape_name)
    color_fn = get_color_function(snapshot.color_name, snapshot.solid_color)

    if snapshot.shape_name == "multilines":
        line_count = max(1, int(snapshot.lines_count))
        gradient_zoom = max(0.01, float(snapshot.lines_gradient_zoom))
        segment_budget = max(8, int((1536 * gradient_zoom) / line_count))
        segments_per_line = max(8, min(int(snapshot.segments_per_edge), segment_budget))
        return create_parallel_lines_surface(
            (WIDTH, HEIGHT),
            line_count=snapshot.lines_count,
            angle_deg=snapshot.lines_angle if multiline_angle is None else multiline_angle,
            line_width=snapshot.line_width,
            color_fn=color_fn,
            offset=multiline_offset,
            segments_per_line=segments_per_line,
            gradient_zoom=snapshot.lines_gradient_zoom,
        )

    if snapshot.shape_name == "dots":
        # Keep a single dot compact so bounce can move it across the screen.
        dot_canvas = (WIDTH, HEIGHT)
        if int(snapshot.dot_count) <= 1:
            single_size = max(16, int(snapshot.line_width) * 6)
            dot_canvas = (single_size, single_size)
        return create_dots_surface(
            dot_canvas,
            dot_count=snapshot.dot_count,
            line_width=snapshot.line_width,
            color_fn=color_fn,
        )

    preset, shape_points = build_outline_points(snapshot, effect_names)

    if viewport:
        return create_gradient_outline_viewport_surface(
            shape_points,
            (WIDTH, HEIGHT),
            line_width=snapshot.line_width,
            segments_per_edge=snapshot.segments_per_edge,
            closed=preset.closed,
            color_fn=color_fn,
        )

    return create_gradient_outline_surface(
        shape_points,
        line_width=snapshot.line_width,
        segments_per_edge=snapshot.segments_per_edge,
        closed=preset.closed,
        color_fn=color_fn,
    )

# --------------------------------
# Animation
# --------------------------------
angle = 0
rotation_speed = 90

running = True

try:
    while running:
        dt = min(clock.tick(60) / 1000, 0.05)

        # --------------------------------
        # Events
        # --------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --------------------------------
        # Update
        # --------------------------------
        snapshot = control_state.advance_timing(dt)
        effect_names = snapshot.effect_names or ([snapshot.effect_name] if snapshot.effect_name else ["static"])
        has_dvd = "dvd" in effect_names

        if not snapshot.output_enabled:
            screen.fill((0, 0, 0))
            pygame.display.flip()
            continue

        dots_dvd = snapshot.shape_name == "dots" and has_dvd
        direct_outline_effects = [
            name
            for name in effect_names
            if name in ("rotate", "grow") and snapshot.shape_name in BASIC_OUTLINE_SHAPES
        ]
        direct_viewport_surface = (
            "grow" in direct_outline_effects
            and snapshot.motion_name == "none"
            and "bounce" not in effect_names
            and "dvd" not in effect_names
        )

        if dots_dvd:
            shape_surface = None
        elif snapshot.shape_name == "multilines":
            multiline_angle = float(snapshot.lines_angle)
            if "rotate" in effect_names:
                multiline_angle -= float(snapshot.angle)
            multiline_offset = get_multiline_motion_offset(snapshot, multiline_angle)
            if "rotate" in effect_names or snapshot.motion_name != "none":
                shape_surface = build_shape_surface(
                    snapshot,
                    multiline_angle=multiline_angle,
                    multiline_offset=multiline_offset,
                )
            else:
                cache_key = (
                    "multilines-base",
                    snapshot.color_name,
                    snapshot.solid_color,
                    snapshot.line_width,
                    snapshot.segments_per_edge,
                    snapshot.lines_count,
                    round(float(multiline_angle), 1),
                    round(float(multiline_offset), 3),
                    round(float(snapshot.lines_gradient_zoom), 3),
                )
                shape_surface = get_cached_surface(
                    cache_key,
                    lambda: build_shape_surface(
                        snapshot,
                        multiline_angle=multiline_angle,
                        multiline_offset=multiline_offset,
                    ),
                )
        elif direct_outline_effects:
            shape_surface = build_shape_surface(
                snapshot,
                effect_names=direct_outline_effects,
                viewport=direct_viewport_surface,
            )
        else:
            cache_key = (
                snapshot.shape_name,
                snapshot.color_name,
                snapshot.solid_color,
                snapshot.line_width,
                round(float(getattr(snapshot, "shape_size", 1.0)), 3),
                snapshot.segments_per_edge,
                snapshot.line_angle,
                snapshot.dot_count if snapshot.shape_name == "dots" else 0,
            )

            shape_surface = get_cached_surface(cache_key, lambda: build_shape_surface(snapshot))

        # --------------------------------
        # Render
        # --------------------------------
        screen.fill((0, 0, 0))

        left = max(0.0, min(1.0, float(snapshot.crop_left)))
        right = max(0.0, min(1.0, float(snapshot.crop_right)))
        top = max(0.0, min(1.0, float(snapshot.crop_top)))
        bottom = max(0.0, min(1.0, float(snapshot.crop_bottom)))

        if right <= left:
            right = min(1.0, left + 0.01)
        if bottom <= top:
            bottom = min(1.0, top + 0.01)

        left_px = int(left * WIDTH)
        right_px = int(right * WIDTH)
        top_px = int(top * HEIGHT)
        bottom_px = int(bottom * HEIGHT)

        crop_rect = pygame.Rect(left_px, top_px, max(1, right_px - left_px), max(1, bottom_px - top_px))

        screen.set_clip(crop_rect)

        position_effect = None
        if not dots_dvd:
            if "dvd" in effect_names:
                position_effect = "dvd"
            elif "bounce" in effect_names:
                position_effect = "bounce"

        filtered_effect_names = [
            name
            for name in effect_names
            if name != "static"
            and not (snapshot.shape_name == "multilines" and name == "rotate")
            and name not in direct_outline_effects
            and name != position_effect
        ]

        if dots_dvd:
            color_fn = get_color_function(snapshot.color_name, snapshot.solid_color)
            effected_surface = create_dvd_dots_surface(
                (WIDTH, HEIGHT),
                dot_count=snapshot.dot_count,
                line_width=snapshot.line_width,
                color_fn=color_fn,
                time_phase=snapshot.dvd_time,
                travel=snapshot.bounce_range,
            )
            remaining_effects = [name for name in filtered_effect_names if name != "dvd"]
            if remaining_effects:
                effected_surface = apply_effect_chain(effected_surface, snapshot, remaining_effects)
        else:
            effected_surface = shape_surface
            if filtered_effect_names:
                effected_surface = apply_effect_chain(shape_surface, snapshot, filtered_effect_names)

        if position_effect is not None:
            blit_positioned(screen, effected_surface, snapshot, position_effect)
        elif snapshot.motion_name and snapshot.motion_name != "none" and snapshot.shape_name != "multilines":
            blit_motion_wrapped(screen, effected_surface, snapshot.motion_name, snapshot.lines_offset)
        elif direct_viewport_surface or dots_dvd or snapshot.shape_name == "multilines":
            screen.blit(effected_surface, (0, 0))
        else:
            screen.blit(effected_surface, effected_surface.get_rect(center=CENTER))

        screen.set_clip(None)

        pygame.display.flip()
except Exception:
    traceback.print_exc()
    screen.set_clip(None)
    screen.fill((0, 0, 0))
    pygame.display.flip()
finally:
    screen.set_clip(None)
    screen.fill((0, 0, 0))
    pygame.display.flip()

    if aalink_stop is not None:
        aalink_stop()

    if web_server is not None:
        web_server.shutdown()
        web_server.server_close()

    pygame.quit()
