import pygame

IMAGE = "project images/Sound on.png"
SIZE = (1200, 600)

def main():
	pygame.init()
	image = pygame.image.load(IMAGE)
	x = image.get_at((16, 46))
	for x in range(image.get_size()[0]):
		for y in range(image.get_size()[1]):
			if image.get_at((x, y))[0] < 50:
				image.set_at((x,y), (0, 0, 0))
			else:
				image.set_at((x,y), (255, 255, 255))
	pygame.image.save(image, "Sound1.png")



if __name__ == '__main__':
	main()
