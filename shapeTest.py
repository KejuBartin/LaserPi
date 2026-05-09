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

def generateCornerShape(center, size, sides, sizeMode, angleOffset=0, pixelSnap=True):
    # 1) Build unit polygon
    angle_step = 360 / sides
    points = []
    for i in range(sides):
        a = math.radians(i * angle_step + angleOffset)
        points.append((math.cos(a), math.sin(a)))

    unit_center_x = 0.0
    unit_center_y = 0.0

    if sizeMode == "radius":
        sx = sy = size
    elif sizeMode == "diameter":
        sx = sy = size / 2
    elif sizeMode == "bbox":
        # size can be number (square box) or (width, height)
        if isinstance(size, (tuple, list)):
            target_w, target_h = size
        else:
            target_w = target_h = size

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        # Keep the resulting bbox centered on the provided center point.
        unit_center_x = (min_x + max_x) / 2
        unit_center_y = (min_y + max_y) / 2

        sx = target_w / (max_x - min_x)
        sy = target_h / (max_y - min_y)
    else:
        raise ValueError("sizeMode must be 'radius', 'diameter', or 'bbox'")

    # 2) Scale + translate
    shape = [
        (
            center[0] + (x - unit_center_x) * sx,
            center[1] + (y - unit_center_y) * sy,
        )
        for x, y in points
    ]

    # Snap to integer pixel positions to reduce subtle rasterization bias.
    if pixelSnap:
        shape = [(round(x), round(y)) for x, y in shape]

    return shape


def shape_bbox(shape): # debug function to check the bounding box of a shape
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    return max(xs) - min(xs), max(ys) - min(ys)


dot = (1000, 1000)
dot2 = (1920, 1080)
circleCenter = (500, 500)


triangle = generateCornerShape((300, 300), 100, 3, "bbox", -90)
square = generateCornerShape((500, 300), 100, 4, "bbox", 45)

hexagon = generateCornerShape((700, 300), 100, 6, "diameter")
octagon = generateCornerShape((300, 500), 100, 8, "bbox", 22.5)

#print("Triangle bbox:", shape_bbox(triangle))
#print("Hexagon bbox:", shape_bbox(hexagon))

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

    pygame.draw.circle(screen, (0, 0, 255), circleCenter, 50, width=3)

    pygame.draw.polygon(screen, (255, 255, 0), hexagon, width=3)

    pygame.draw.polygon(screen, (255, 0, 255), octagon, width=3)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()