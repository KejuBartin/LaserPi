import math
import pygame
from collections import OrderedDict

from colors import get_color_function
from effects import apply_effect_chain
from renderer import create_gradient_outline_surface, create_parallel_lines_surface, create_dots_surface
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


def build_shape_surface(snapshot):
    preset = get_shape_preset(snapshot.shape_name)
    color_fn = get_color_function(snapshot.color_name, snapshot.solid_color)

    if snapshot.shape_name == "multilines":
        # Use a diagonal-sized canvas so rotate/angle combinations still cover screen corners.
        multiline_canvas = int(math.ceil(math.hypot(WIDTH, HEIGHT))) + snapshot.line_width * 8
        return create_parallel_lines_surface(
            (multiline_canvas, multiline_canvas),
            line_count=snapshot.lines_count,
            angle_deg=snapshot.lines_angle,
            line_width=snapshot.line_width,
            color_fn=color_fn,
            offset=snapshot.lines_offset,
            segments_per_line=snapshot.segments_per_edge,
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

    shape_points = preset.factory()

    if snapshot.shape_name == "line":
        angle_rad = math.radians(float(snapshot.line_angle) % 360.0)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        shape_points = [
            pygame.Vector2(
                p.x * cos_a - p.y * sin_a,
                p.x * sin_a + p.y * cos_a,
            )
            for p in shape_points
        ]

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
        dt = clock.tick(60) / 1000

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

        if snapshot.shape_name == "multilines":
            shape_surface = build_shape_surface(snapshot)
        else:
            cache_key = (
                snapshot.shape_name,
                snapshot.color_name,
                snapshot.solid_color,
                snapshot.line_width,
                snapshot.segments_per_edge,
                snapshot.line_angle,
                snapshot.dot_count if snapshot.shape_name == "dots" else 0,
            )

            if cache_key in surface_cache:
                shape_surface = surface_cache.pop(cache_key)
                surface_cache[cache_key] = shape_surface
            else:
                shape_surface = build_shape_surface(snapshot)
                surface_cache[cache_key] = shape_surface
                while len(surface_cache) > CACHE_LIMIT:
                    surface_cache.popitem(last=False)

        effect_names = snapshot.effect_names or ([snapshot.effect_name] if snapshot.effect_name else ["static"])

        # --------------------------------
        # Render
        # --------------------------------
        screen.fill((0, 0, 0))

        if not snapshot.output_enabled:
            pygame.display.flip()
            continue

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

        effected_surface = apply_effect_chain(shape_surface, snapshot, effect_names)

        if snapshot.motion_name and snapshot.motion_name != "none":
            blit_motion_wrapped(screen, effected_surface, snapshot.motion_name, snapshot.lines_offset)
        else:
            screen.blit(effected_surface, effected_surface.get_rect(center=CENTER))

        screen.set_clip(None)

        pygame.display.flip()
finally:
    if web_server is not None:
        web_server.shutdown()
        web_server.server_close()

    pygame.quit()