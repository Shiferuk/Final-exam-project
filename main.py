import pygame
import config
from game_logic import Game

def main():
    game = Game()
    running = True
    while running:
        try:
            running = game.handle_events()
        except SystemExit:
            break
        game.update()
        game.draw()
        config.clock.tick(config.fps)
    pygame.quit()

if __name__ == "__main__":
    main()
