import pygame
import math

pygame.init()

screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

pygame.display.set_caption("Showlaser")

clock = pygame.time.Clock()

def generateCornerShape(center, size, sides, angleOffset=0):
    shape = []
    angleStep = 360 / sides
    for i in range(sides):
        angle = math.radians(i * angleStep + angleOffset)
        x = center[0] + size * math.cos(angle)
        y = center[1] + size * math.sin(angle)
        shape.append((x, y))
    return shape


circleCenter = (500, 500)


trianle = generateCornerShape((300, 300), 100, 3, -90)
sqare = generateCornerShape((500, 300), 100, 4, 45)

hexagon = generateCornerShape((700, 300), 100, 6)
octagon = generateCornerShape((300, 500), 100, 8, 22.5)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    screen.fill((0, 0, 0))

    pygame.draw.polygon(screen, (255, 0, 0), trianle, width=3)
    
    pygame.draw.polygon(screen, (0, 255, 0), sqare, width=3)

    pygame.draw.circle(screen, (0, 0, 255), circleCenter, 100, width=3)

    pygame.draw.polygon(screen, (255, 255, 0), hexagon, width=3)

    pygame.draw.polygon(screen, (255, 0, 255), octagon, width=3)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()