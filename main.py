import pygame

from shapes import create_polygon, create_line, create_circle
from renderer import create_gradient_outline_surface

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

# --------------------------------
# Shape
# --------------------------------
square = create_polygon(
    sides=4,
    radius=350
)

square_surface = create_gradient_outline_surface(
    square,
    closed=True
)

line = create_line(1000)

line_surface = create_gradient_outline_surface(
    line,
    closed=False
)

circle = create_circle(200)

circle_surface = create_gradient_outline_surface(
    circle,
    closed=True
)

# --------------------------------
# Animation
# --------------------------------
angle = 0
rotation_speed = 90

running = True

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
    angle += rotation_speed * dt

    # --------------------------------
    # Render
    # --------------------------------
    screen.fill((0, 0, 0))

    rotated_surface = pygame.transform.rotozoom(
        square_surface,
        -angle,
        1
    )

    rect = rotated_surface.get_rect(
        center=CENTER
    )

    screen.blit(rotated_surface, rect)

    pygame.display.flip()

pygame.quit()