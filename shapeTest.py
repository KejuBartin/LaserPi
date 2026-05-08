import pygame
import math

pygame.init()

screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

sizeX, sizeY = pygame.display.get_surface().get_size()
print(f"Screen size: {sizeX}x{sizeY}")

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


dot = (450, 200)
dot2 = (550, 200)
circleCenter = (500, 500)


triangle = generateCornerShape((300, 300), 100, 3, -90)
square = generateCornerShape((500, 300), 100, 4, 45)

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

    pygame.draw.circle(screen, (255, 255, 255), dot, 5)
    pygame.draw.circle(screen, (255, 255, 255), dot2, 5)

    pygame.draw.polygon(screen, (255, 0, 0), triangle, width=3)
    
    pygame.draw.polygon(screen, (0, 255, 0), square, width=3)

    pygame.draw.circle(screen, (0, 0, 255), circleCenter, 100, width=3)

    pygame.draw.polygon(screen, (255, 255, 0), hexagon, width=3)

    pygame.draw.polygon(screen, (255, 0, 255), octagon, width=3)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()