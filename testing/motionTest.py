import pygame
from shapeLib import generateCornerShape

pygame.init()

screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

sizeX, sizeY = pygame.display.get_surface().get_size()
print(f"Screen size: {sizeX}x{sizeY}")

pygame.display.set_caption("Showlaser")

clock = pygame.time.Clock()


dot = (1000, 1000)
dot2 = (1920, 1080)
circleCenter = (500, 500)

triangle = generateCornerShape((300, 300), 100, 3, "bbox", -90)
square = generateCornerShape((500, 300), 100, 4, "bbox", 45)

hexagon = generateCornerShape((700, 300), 100, 6, "diameter")
octagon = generateCornerShape((300, 500), 100, 8, "bbox", 22.5)

# Autonomous octagon motion: position and velocity (pixels per frame)
octagon_pos = [300.0, 500.0]
octagon_vel = [2.0, 1.5]

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    screen.fill((0, 0, 0))

    # update octagon position and regenerate shape each frame
    octagon_pos[0] += octagon_vel[0]
    octagon_pos[1] += octagon_vel[1]
    margin = 100
    if octagon_pos[0] < margin or octagon_pos[0] > sizeX - margin:
        octagon_vel[0] = -octagon_vel[0]
    if octagon_pos[1] < margin or octagon_pos[1] > sizeY - margin:
        octagon_vel[1] = -octagon_vel[1]
    octagon = generateCornerShape((int(octagon_pos[0]), int(octagon_pos[1])), 100, 8, "bbox", 22.5)

    pygame.draw.circle(screen, (255, 255, 255), dot, 5)
    pygame.draw.circle(screen, (255, 255, 255), dot2, 5)

    pygame.draw.polygon(screen, (255, 0, 0), triangle, width=3)
    
    pygame.draw.polygon(screen, (0, 255, 0), square, width=3)

    pygame.draw.circle(screen, (0, 0, 255), circleCenter, 50, width=3)

    pygame.draw.polygon(screen, (255, 255, 0), hexagon, width=3)

    pygame.draw.polygon(screen, (255, 0, 255), octagon, width=3)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()