import pygame
from ui.host_interface import interface
pygame.init()
w = pygame.display.set_mode((800,600))

running = True
interface = interface(w)
while running:
    w.fill((0,0,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        interface.event(event)
    interface.tick()
    data = interface.returns()
    interface.draw()
    pygame.display.flip()
        

