import pygame
from gameObjects import *
from library.contants import Values


def update():
    mainWindow.blit(drawBoard.window, Values.POINT_DB)


if __name__ == '__main__':
    clock = pygame.time.Clock()
    drawing = False
    last_position = None

    while True:
        clock.tick(Values.FRAMERATE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)

            if drawing and event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                drawBoard.draw(last_position, pos)
                last_position = pos

            if event.type == pygame.MOUSEBUTTONDOWN:
                buttons = pygame.mouse.get_pressed(3)
                if buttons[0]:
                    drawBoard.setModeToInk()
                    if last_position is None:
                        last_position = pygame.mouse.get_pos()
                    drawing = True
                elif buttons[1]:
                    drawBoard.setModeToEraser()
                    if last_position is None:
                        last_position = pygame.mouse.get_pos()
                    drawing = True

            if event.type == pygame.MOUSEBUTTONUP:
                last_position = None
                drawing = False

        update()
        pygame.display.update()
