import pygame
import sys
import time


class Spritesheet(object):
	def __init__(self, filename, rect, cols, rows, colorkey=None):
		self.sheet = pygame.image.load(filename).convert()
		self.images = self.load_strip(rect, cols, rows, colorkey)
		self.i = 0

	def image_at(self, rectangle, colorkey=None):
		"""Loads image from x,y,x+offset,y+offset"""
		rect = pygame.Rect(rectangle)
		image = pygame.Surface(rect.size).convert()
		image.blit(self.sheet, (0, 0), rect)
		if colorkey is not None:
			if colorkey is -1:
				colorkey = image.get_at((0, 0))
			image.set_colorkey(colorkey, pygame.RLEACCEL)
		return image

	# Load a whole bunch of images and return them as a list
	def images_at(self, rects, colorkey=None):
		return [self.image_at(rect, colorkey) for rect in rects]

	# Load a whole strip of images
	def load_strip(self, rect, cols, rows, colorkey=None):
		"""Loads a strip of images and returns them as a list"""
		tups = []
		for y in range(cols):
			for x in range(rows):
				tups.append((rect[0] + rect[2] * x, rect[1] + rect[3] * y, rect[2], rect[3]))
		# tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3]) for x in range(count)]
		return self.images_at(tups, colorkey)

	def next(self):
		if self.i >= len(self.images):
			return False
		image = self.images[self.i]
		self.i += 1
		return image


def main():
	surface = pygame.display.set_mode((300, 300))
	surface.fill((255, 255, 255))

	strips = Spritesheet('1.png', (0, 0, 50, 50), 5, 5, (0, 0, 0))
	image = strips.next()
	while image is not False:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
		surface.blit(image, (0, 0))
		pygame.display.flip()
		image = strips.next()
		surface.fill((255, 255, 255))
		time.sleep(0.07)
	pygame.quit()



if __name__ == '__main__':
	main()
