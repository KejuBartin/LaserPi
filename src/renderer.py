import math
import random

import pygame

from colors import rainbow


def create_gradient_outline_surface(
    points,
    line_width=6,
    segments_per_edge=100,
    closed=True,
    color_fn=rainbow
):
    if len(points) < 2:
        raise ValueError("At least two points are required to render an outline")

    line_width = max(1, int(line_width))
    segments_per_edge = max(1, int(segments_per_edge))

    # --------------------------------
    # Center points on their centroid and compute bounds
    # --------------------------------
    n = len(points)
    cx = sum(p.x for p in points) / n
    cy = sum(p.y for p in points) / n

    rel_points = [pygame.Vector2(p.x - cx, p.y - cy) for p in points]

    max_distance = max(p.length() for p in rel_points)
    canvas_size = max(1, math.ceil(max_distance * 2 + line_width * 6))

    # --------------------------------
    # Create transparent surface
    # --------------------------------
    surface = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

    # place centroid at the center of the surface
    center_shift = pygame.Vector2(canvas_size / 2.0, canvas_size / 2.0)

    offset_points = [r + center_shift for r in rel_points]

    edge_count = len(offset_points)

    max_edges = edge_count if closed else edge_count - 1

    # --------------------------------
    # Draw gradient outline
    # --------------------------------
    for edge in range(max_edges):
        start = offset_points[edge]
        end = offset_points[(edge + 1) % edge_count]

        for i in range(segments_per_edge):
            t1 = i / segments_per_edge
            t2 = (i + 1) / segments_per_edge

            p1 = start.lerp(end, t1)
            p2 = start.lerp(end, t2)

            gradient_pos = (edge + t1) / edge_count

            color = color_fn(gradient_pos)

            pygame.draw.line(
                surface,
                color,
                p1,
                p2,
                line_width
            )

    return surface


def create_gradient_outline_viewport_surface(
    points,
    size,
    line_width=6,
    segments_per_edge=100,
    closed=True,
    color_fn=rainbow,
):
    if len(points) < 2:
        raise ValueError("At least two points are required to render an outline")

    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))
    line_width = max(1, int(line_width))
    segments_per_edge = max(1, int(segments_per_edge))

    n = len(points)
    cx = sum(p.x for p in points) / n
    cy = sum(p.y for p in points) / n
    center_shift = pygame.Vector2(width / 2.0, height / 2.0)
    offset_points = [pygame.Vector2(p.x - cx, p.y - cy) + center_shift for p in points]

    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    edge_count = len(offset_points)
    max_edges = edge_count if closed else edge_count - 1

    for edge in range(max_edges):
        start = offset_points[edge]
        end = offset_points[(edge + 1) % edge_count]

        for i in range(segments_per_edge):
            t1 = i / segments_per_edge
            t2 = (i + 1) / segments_per_edge
            color = color_fn((edge + t1) / edge_count)
            pygame.draw.line(surface, color, start.lerp(end, t1), start.lerp(end, t2), line_width)

    return surface


def create_circle_outline_viewport_surface(
    size,
    radius,
    line_width=6,
    segments=384,
    color_fn=rainbow,
    angle_offset_deg=0.0,
):
    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))
    radius = max(1.0, float(radius))
    line_width = max(1, int(line_width))
    segments = max(24, int(segments))

    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    center_x = width / 2.0
    center_y = height / 2.0
    angle_offset = math.radians(float(angle_offset_deg) % 360.0)

    previous_x = center_x + math.cos(angle_offset) * radius
    previous_y = center_y + math.sin(angle_offset) * radius

    for i in range(1, segments + 1):
        t = i / segments
        angle = angle_offset + t * math.tau
        x = center_x + math.cos(angle) * radius
        y = center_y + math.sin(angle) * radius
        pygame.draw.line(surface, color_fn((i - 1) / segments), (previous_x, previous_y), (x, y), line_width)
        previous_x = x
        previous_y = y

    return surface


def create_parallel_lines_surface(
    size,
    line_count,
    angle_deg,
    line_width,
    color_fn,
    offset=0.0,
    segments_per_line=100,
    gradient_zoom=1.0,
):
    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))
    line_count = max(1, int(line_count))
    line_width = max(1, int(line_width))
    segments_per_line = max(1, int(segments_per_line))
    gradient_zoom = float(gradient_zoom)
    gradient_zoom = max(0.01, gradient_zoom)

    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    angle_rad = math.radians(float(angle_deg) % 360.0)
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    px = -dy
    py = dx

    perpendicular_extent = (abs(px) * width + abs(py) * height) / 2.0
    line_extent = (abs(dx) * width + abs(dy) * height) / 2.0
    spacing = max(1.0, (perpendicular_extent * 2.0) / line_count)
    center_x = width / 2.0
    center_y = height / 2.0

    offset = (float(offset) % 1.0) * spacing
    half_range = int(math.ceil((perpendicular_extent + line_width * 2.0) / spacing)) + 3
    segment = line_extent * 2.0 + line_width * 4.0
    sample_segments = max(segments_per_line, int(math.ceil(segments_per_line / gradient_zoom)))
    colors = [color_fn(((s / sample_segments) / gradient_zoom) % 1.0) for s in range(sample_segments)]

    for i in range(-half_range, half_range + 1):
        distance = i * spacing + offset
        line_center_x = center_x + px * distance
        line_center_y = center_y + py * distance

        start_x = line_center_x - dx * segment
        start_y = line_center_y - dy * segment
        end_x = line_center_x + dx * segment
        end_y = line_center_y + dy * segment

        for s in range(sample_segments):
            t1 = s / sample_segments
            t2 = (s + 1) / sample_segments

            x1 = start_x + (end_x - start_x) * t1
            y1 = start_y + (end_y - start_y) * t1
            x2 = start_x + (end_x - start_x) * t2
            y2 = start_y + (end_y - start_y) * t2

            color = colors[s]
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), line_width)

    return surface


def create_wrapped_shifted_surface(source_surface, offset_x=0, offset_y=0):
    width, height = source_surface.get_size()
    shift_x = int(round(offset_x)) % width if width else 0
    shift_y = int(round(offset_y)) % height if height else 0

    if not shift_x and not shift_y:
        return source_surface

    shifted_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    if shift_x and shift_y:
        positions = (
            (shift_x - width, shift_y - height),
            (shift_x - width, shift_y),
            (shift_x, shift_y - height),
            (shift_x, shift_y),
        )
    elif shift_x:
        positions = ((shift_x - width, 0), (shift_x, 0))
    else:
        positions = ((0, shift_y - height), (0, shift_y))

    for x, y in positions:
        shifted_surface.blit(source_surface, (x, y))

    return shifted_surface


def create_dots_surface(
    size,
    dot_count,
    line_width,
    color_fn,
):
    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))
    dot_count = max(1, int(dot_count))
    line_width = max(1, int(line_width))
    
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    center_x = width / 2.0
    center_y = height / 2.0
    
    # Draw center dot
    color = color_fn(0.0)
    pygame.draw.circle(surface, color, (int(center_x), int(center_y)), line_width)
    
    # Draw random dots (dot_count includes the center, so draw dot_count - 1 random)
    for i in range(max(0, dot_count - 1)):
        # Random position across screen
        rand_x = random.randint(0, width - 1)
        rand_y = random.randint(0, height - 1)
        
        # Color based on dot index for variety
        color_phase = (i + 2) / (dot_count + 1)
        color = color_fn(color_phase)
        
        # Draw dot
        pygame.draw.circle(surface, color, (rand_x, rand_y), line_width)
    
    return surface


def _triangle_01(value):
    return 1.0 - abs(2.0 * (float(value) % 1.0) - 1.0)


def create_dvd_dots_surface(
    size,
    dot_count,
    line_width,
    color_fn,
    time_phase,
    travel=1.0,
):
    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))
    dot_count = max(1, int(dot_count))
    line_width = max(1, int(line_width))
    travel = max(0.0, min(1.0, float(travel)))

    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    max_x = max(0.0, (width - line_width * 2) * travel)
    max_y = max(0.0, (height - line_width * 2) * travel)

    for i in range(dot_count):
        if i == 0:
            phase_x = 0.25
            phase_y = 0.25
            speed_x = 1.0
            speed_y = 1.37
        else:
            phase_x = (0.173 * i + 0.31) % 1.0
            phase_y = (0.271 * i + 0.57) % 1.0
            speed_x = 0.7 + ((i * 37) % 70) / 100.0
            speed_y = 0.9 + ((i * 53) % 90) / 100.0

        tx = _triangle_01(time_phase * speed_x + phase_x)
        ty = _triangle_01(time_phase * speed_y + phase_y)

        x = int(round(line_width + tx * max_x))
        y = int(round(line_width + ty * max_y))

        color_phase = (i + 1) / (dot_count + 1)
        color = color_fn(color_phase)
        pygame.draw.circle(surface, color, (x, y), line_width)

    return surface
