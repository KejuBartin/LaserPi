import colorsys
import pygame

pygame.init()

# --------------------------------
# Config
# --------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60

SQUARE_SIZE = 300
LINE_WIDTH = 8

ROTATION_SPEED = 90  # degrees/sec

# --------------------------------
# Window
# --------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# --------------------------------
# Create gradient square surface
# --------------------------------
square_surface_size = SQUARE_SIZE + LINE_WIDTH * 2

square_surface = pygame.Surface(
    (square_surface_size, square_surface_size),
    pygame.SRCALPHA
)

half = SQUARE_SIZE // 2
offset = LINE_WIDTH

# Square corner positions
corners = [
    (offset, offset),
    (offset + SQUARE_SIZE, offset),
    (offset + SQUARE_SIZE, offset + SQUARE_SIZE),
    (offset, offset + SQUARE_SIZE),
]

# --------------------------------
# Draw gradient outline
# --------------------------------
segments_per_edge = 200

for edge in range(4):
    start = pygame.Vector2(corners[edge])
    end = pygame.Vector2(corners[(edge + 1) % 4])

    for i in range(segments_per_edge):
        t1 = i / segments_per_edge
        t2 = (i + 1) / segments_per_edge

        p1 = start.lerp(end, t1)
        p2 = start.lerp(end, t2)

        # Global gradient position around square
        gradient_pos = (edge + t1) / 4

        r, g, b = colorsys.hsv_to_rgb(
            gradient_pos,
            1.0,
            1.0
        )

        color = (
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )

        pygame.draw.line(
            square_surface,
            color,
            p1,
            p2,
            LINE_WIDTH
        )

# --------------------------------
# Main loop
# --------------------------------
angle = 0
running = True

while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    angle += ROTATION_SPEED * dt

    # Black background
    screen.fill((0, 0, 0))

    # Rotate full gradient square
    rotated = pygame.transform.rotozoom(
        square_surface,
        -angle,
        1
    )

    rect = rotated.get_rect(
        center=(WIDTH // 2, HEIGHT // 2)
    )

    screen.blit(rotated, rect)

    pygame.display.flip()

pygame.quit()