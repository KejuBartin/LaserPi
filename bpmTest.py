import pygame
import asyncio
import aalink

pygame.init()

screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

sizeX, sizeY = pygame.display.get_surface().get_size()
print(f"Screen size: {sizeX}x{sizeY}")

pygame.display.set_caption("Showlaser")

clock = pygame.time.Clock()

# Create and set event loop for aalink
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialize Ableton Link inside async context
async def init_link():
    link = aalink.Link(120)
    link.enabled = True
    return link

link = loop.run_until_complete(init_link())

circleCenter = [500, 500]
last_beat = -1
circle_radius = 50
max_radius = 100

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Sync with Ableton Link
    loop.run_until_complete(link.sync(0.016))  # ~60fps

    screen.fill((0, 0, 0))

    # Get current beat info from Ableton Link
    beat = link.beat  # Current beat position
    phase = link.phase  # Position within current beat (0.0 to 1.0)
    bpm = link.tempo
    
    # Animate circle radius based on beat phase
    # Expands when beat starts, shrinks as beat progresses
    radius = circle_radius + (max_radius - circle_radius) * (1 - phase)
    
    pygame.draw.circle(screen, (0, 0, 255), circleCenter, int(radius), width=3)

    pygame.display.flip()

    clock.tick(60)

loop.close()
pygame.quit()