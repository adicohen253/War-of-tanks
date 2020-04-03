import game_objects
import pygame
from time import sleep
from sys import exit


# consider if clean up bullets from the map and keep the traps
SIZE = (800, 600)
BACKGROUND = pygame.image.load("game images/zone.jpg")


def flickering(screen, tank):
	for i in range(6):
		screen.blit(BACKGROUND, [0, 0])
		if i % 2 == 0:
			screen.blit(tank.get_image(), tank.get_loc())
		pygame.display.flip()
		sleep(0.5)


def main():
	pygame.init()
	screen = pygame.display.set_mode(SIZE)
	pygame.display.set_caption("War Of Tanks")
	tank = game_objects.Tank((100, 200), 0)
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					exit()
				elif event.key == pygame.K_f:
					flickering(screen, tank)
		screen.blit(BACKGROUND, [0, 0])
		screen.blit(tank.get_image(), tank.get_loc())
		pygame.display.flip()
	

if __name__ == '__main__':
	main()
