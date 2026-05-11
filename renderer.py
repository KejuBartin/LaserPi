import pygame

from colors import rainbow


def create_gradient_outline_surface(
    points,
    line_width=6,
    segments_per_edge=100,
    closed=True
):
    # --------------------------------
    # Find bounds
    # --------------------------------
    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)

    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)

    width = int(max_x - min_x + line_width * 4)
    height = int(max_y - min_y + line_width * 4)

    # --------------------------------
    # Create transparent surface
    # --------------------------------
    surface = pygame.Surface(
        (width, height),
        pygame.SRCALPHA
    )

    # Offset points into surface space
    offset_points = [
        pygame.Vector2(
            p.x - min_x + line_width * 2,
            p.y - min_y + line_width * 2
        )
        for p in points
    ]

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

            color = rainbow(gradient_pos)

            pygame.draw.line(
                surface,
                color,
                p1,
                p2,
                line_width
            )

    return surface