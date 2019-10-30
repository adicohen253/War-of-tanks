import pygame
import random
import time


# general constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# war of tanks
IMG_PLY = 'tank_player.png'
BULLET = 'bullet.png'
SURPRISE = 'surprise.png'
MOVES = [(2, 0, 0), (1, 1, -45), (0, 2, -90), (-1, 1, -135),
         (-2, 0, 180), (-1, -1, 135), (0, -2, 90), (1, -1, 45)]

NUM_BULLETS = 10
START_HEALTH = 30


class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, direct=0, demo_tank=None):
        super(Tank, self).__init__()
        self.__image = pygame.image.load(IMG_PLY).convert()
        self.__image.set_colorkey(WHITE)
        self.rect = self.__image.get_rect()  # the location of the player
        self.__tank_direct = direct  # uses as direct of the tank
        self.__original_image = self.__image  # original image (uses to rotate the tank with every direct)
        self.__image = pygame.transform.rotate(self.__original_image, MOVES[self.__tank_direct][2])
        self.rect.x = x
        self.rect.y = y
        self.__num_bullet = NUM_BULLETS  # the current number of bullets
        self.__health = START_HEALTH  # health of the player
        self.__color = None
        self.__need_pointing = True
        self.__last_time_of_shot = time.time()
        if type(demo_tank) == Tank:
            self.change_player_color(demo_tank.get_color())
        else:
            self.__color = [255, 0, 0]  # the default color of the player
        self.reload_time = time.time()  # time passes from the last reload
        self.__eternal_ammo_mode = False  # flag is tank has infinite ammo now, lasts for 6 seconds
        self.__eternal_ammo_time = None  # the moment it became to be with endless ammo
        # (when eternal ammo mode is of the time is none)
        self.__ghost_mode = False  # flag is tank in ghost mode, lasts for 5 seconds
        self.__is_stuck_in_ghost = False  # turn to true when ghost mode turn of and tank still in wall
        self.__ghost_time = None  # the moment it became to be ghost
        # (when ghost mode is of the time is none)

    def change_player_color(self, new_color):
        """change the image of the player to the new color
        argument:
                player - type: tank, the player that changing his color
                new_color = type: list, the new color for the player (rgb format)
        """
        for element in range(len(new_color)):
            new_color[element] = int(new_color[element])
        # if color is totally white, set_colorkey make to color disappear
        if new_color == list(WHITE):
            new_color[0] -= 1
        if new_color == list(BLACK):
            new_color[0] += 1
        for x in range(self.__image.get_size()[0]):
            for y in range(self.__image.get_size()[1]):
                if self.__image.get_at((x, y)) != BLACK and self.__image.get_at((x, y)) != WHITE:
                    self.__image.set_at((x, y), new_color)
        for x in range(self.__original_image.get_size()[0]):
            for y in range(self.__original_image.get_size()[1]):
                if self.__original_image.get_at((x, y)) != BLACK and self.__original_image.get_at((x, y)) != WHITE:
                    self.__original_image.set_at((x, y), new_color)
        self.update_color(new_color)

    def is_done_ghost(self):
        """"Checks if it's time to turn off ghost mode"""
        if self.__ghost_time is not None:
            if time.time() - self.__ghost_time >= 5:
                # print "ghost mode over"
                self.__ghost_time = None
                self.__ghost_mode = False
                self.__is_stuck_in_ghost = True

    def is_done_eternal_ammo(self):
        """Checks if it's time to turn off eternal mode"""
        if self.__eternal_ammo_time is not None:
            if time.time() - self.__eternal_ammo_time >= 6:
                self.__num_bullet = NUM_BULLETS
                self.__eternal_ammo_time = None
                self.__eternal_ammo_mode = False

    def reload_ammo(self):
        """taking care about load the ammo of the tank"""
        if time.time() - self.reload_time >= 10:
            flag = False
            if self.__num_bullet == 0:
                self.__num_bullet = NUM_BULLETS
                if self.__eternal_ammo_mode is False:
                    flag = True
            self.reload_time = time.time()
            return flag
        return False

    def active_ghost_mode(self):
        self.__ghost_mode = True
        self.__ghost_time = time.time()  # start be ghost

    def active_eternal_ammo_mode(self):
        self.__eternal_ammo_mode = True
        self.__eternal_ammo_time = time.time()  # start use eternal ammo

    def set_enemy_pointer(self, point):
        """update enemy point
        argument:
            point: type - int, the new enemy direct
        """
        self.__tank_direct = point
        self.__image = pygame.transform.rotate(self.__original_image, MOVES[self.__tank_direct][2])

    def absolute_pointer(self):
        """consider the pointer for always point to legal index on MOVES"""
        while not (0 <= self.__tank_direct < 8):
            if self.__tank_direct >= 8:
                self.__tank_direct -= len(MOVES)
            elif self.__tank_direct <= -1:
                self.__tank_direct += len(MOVES)

    def update_enemy_loc(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def update_direct(self, walls, event):
        """update the current direct of the tank in step to the input
        argument:
            walls: type - list, the list of all walls in the battlefield
            event: type - pygame.event, the input from the user
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.__need_pointing = False
                self.__tank_direct += 1
            if event.key == pygame.K_LEFT:
                self.__need_pointing = False
                self.__tank_direct -= 1
        self.absolute_pointer()
        self.__image = pygame.transform.rotate(self.__original_image, MOVES[self.__tank_direct][2])
        if pygame.sprite.spritecollide(self, walls, None):
            self.get_out_wall(walls)

    def get_out_wall(self, walls):
        """check if the tank stuck in some wall when it changed his direct
        argument:
            walls: type - list, the list of all walls in the battlefield
        """
        x, y = self.get_loc()
        for i in range(0, 8, 1):
            self.rect.x -= MOVES[i][0]
            self.rect.y -= MOVES[i][1]
            if not pygame.sprite.spritecollide(self, walls, False):
                break
            else:
                self.rect.x, self.rect.y = x, y

    def move_tank(self, walls, enemy_tank):
        """moves the tank in step the player input, helped with hit_wall to avoid stuck in walls
        :argument:
            walls: type- list of walls, every wall in the game
        """
        if self.__ghost_mode:
            walls = walls[0:4]
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.__need_pointing = False
            if not pygame.sprite.spritecollide(self, walls, False):
                self.__is_stuck_in_ghost = False
                self.update_loc()
                is_get_into_wall = False
            else:
                if self.__is_stuck_in_ghost:
                    self.update_loc()
                    is_get_into_wall = False
                else:
                    self.hit_wall()
                    is_get_into_wall = True

            if not pygame.sprite.spritecollide(self, [enemy_tank], False):
                is_get_into_enemy = False
            else:
                self.lost_health(2)
                enemy_tank.lost_health(2)
                self.hit_wall()
                is_get_into_enemy = True
            return is_get_into_wall, is_get_into_enemy
        return False, False

    def hit_wall(self):
        """Reflects the tank when in the wall"""
        self.rect.x -= MOVES[self.__tank_direct][0]
        self.rect.y -= MOVES[self.__tank_direct][1]
        self.__tank_direct += 4
        self.absolute_pointer()
        self.__image = pygame.transform.rotate(self.__original_image, MOVES[self.__tank_direct][2])

    def shoot_bullet(self, event, bullets, lunch_direct_of_bullet):
        """add new bullets to the bullets in the battlefield, if there option to shoot
        argument:
            event: type- event (pygame class)
            bullets: type - list of bullet, all the bullets in the battlefield
        """
        if time.time() - self.__last_time_of_shot >= 0.5:
            if event == pygame.K_f:
                if self.__eternal_ammo_mode is False:
                    self.update_num_bullet()
                bullet = Bullet(self, lunch_direct_of_bullet)
                bullets.append(bullet)
                self.__last_time_of_shot = time.time()
                return True, bullet
            elif (event.key == pygame.K_SPACE) and (self.__num_bullet > 0):
                if self.__eternal_ammo_mode is False:
                    self.update_num_bullet()
                bullet = Bullet(self, lunch_direct_of_bullet)
                bullets.append(bullet)
                self.__last_time_of_shot = time.time()
                return True, bullet
            else:
                return False, None
        return False, None

    def get_is_ghost_mode(self):
        return self.__ghost_mode

    def get_is_eternal_ammo_mode(self):
        return self.__eternal_ammo_mode

    def is_need_pointing(self):
        return self.__need_pointing

    def set_demo_tank_image(self, img):
        self.__image = img

    def get_color(self):
        return self.__color

    def update_color(self, new_color):
        self.__color = new_color

    def get_health(self):
        return self.__health

    def heal_health(self):
        self.__health += 1

    def lost_health(self, injury):
        self.__health -= injury

    def get_num_bullet(self):
        return self.__num_bullet

    def update_num_bullet(self):
        self.__num_bullet -= 1

    def get_loc(self):
        return self.rect.x, self.rect.y

    def update_loc(self):
        """move the tank in the current direct"""
        self.rect.x += MOVES[self.__tank_direct][0]
        self.rect.y += MOVES[self.__tank_direct][1]

    def get_image(self):
        return self.__image

    def get_pointer(self):
        return self.__tank_direct


class Wall(pygame.sprite.Sprite):
    def __init__(self, screen, start_pos, end_pose):
        super(Wall, self).__init__()
        self.__surface = screen
        self.__start_pos = start_pos
        self.__end_pos = end_pose
        self.width = 7  # constant width
        self.rect = self.draw_line()

    def get_start_pos(self):
        return self.__start_pos

    def get_end_pos(self):
        return self.__end_pos

    def draw_line(self):
        return pygame.draw.line(self.__surface, BLACK, self.__start_pos, self.__end_pos, self.width)


class Bullet(pygame.sprite.Sprite):
    RIGHT = 1
    LEFT = -1
    BULLET_MOVES = [(4, 0, 30, 13), (3, 3, 27, 24), (0, 4, 12, 30), (-3, 3, 2, 27),
                    (-4, 0, -11, 12), (-3, -3, -10, -9), (0, -4, 12, -11), (3, -3, 33, -7)]
    MAX_BULLET_HOPS = 6

    def __init__(self, shooter, lunch_direct_of_enemy_bullet):  # get the tank's as shooter
        super(Bullet, self).__init__()
        self.__image = pygame.image.load(BULLET).convert()
        self.__image.set_colorkey(WHITE)
        self.__bullet_direct = shooter.get_pointer()  # the direct of thr bullet
        if self.__bullet_direct % 2 == 0:
            if lunch_direct_of_enemy_bullet == 0:
                self.__first_lunch_direct = [self.RIGHT, self.LEFT][random.randint(0, 1)]
            elif lunch_direct_of_enemy_bullet == 2:
                self.__first_lunch_direct = 0
            else:
                self.__first_lunch_direct = lunch_direct_of_enemy_bullet
        else:
            self.__first_lunch_direct = 0  # doesn't needed
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = shooter.get_loc()
        self.place_bullet()  # place the bullet in position in front of tank's canon
        self.ttl = self.MAX_BULLET_HOPS  # number of times that bullet can hit the walls

    def update_loc(self):
        """update the location of the bullet"""
        self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
        self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]

    def place_bullet(self):
        """place the bullet in order to direct of the shooter tank"""
        self.rect.x += self.BULLET_MOVES[self.__bullet_direct][2]
        self.rect.y += self.BULLET_MOVES[self.__bullet_direct][3]

    def hit_wall(self, walls):
        """get the bullet avoid of stuck in the walls
        argument:
            walls: type - list, all the walls in the battlefield
        """
        if self.__bullet_direct % 2 == 1:
            self.rect.x -= self.BULLET_MOVES[self.__bullet_direct][0]
            self.rect.y -= self.BULLET_MOVES[self.__bullet_direct][1]
            self.__bullet_direct += 2
            self.absolute_pointer()
            self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
            self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]
            if not pygame.sprite.spritecollide(self, walls, False):
                pass
            else:
                self.rect.x -= self.BULLET_MOVES[self.__bullet_direct][0] * 2
                self.rect.y -= self.BULLET_MOVES[self.__bullet_direct][1] * 2
                self.__bullet_direct -= 4
                self.absolute_pointer()
                self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
                self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]
        else:
            self.rect.x -= self.BULLET_MOVES[self.__bullet_direct][0]
            self.rect.y -= self.BULLET_MOVES[self.__bullet_direct][1]
            self.__bullet_direct += 3 * self.__first_lunch_direct
            self.absolute_pointer()
            self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
            self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]
        self.ttl -= 1

    def get_ttl(self):
        return self.ttl

    def absolute_pointer(self):
        """consider the pointer for always point to legal index on BULLET MOVE"""
        if self.__bullet_direct >= len(MOVES):
            self.__bullet_direct -= len(MOVES)
        elif self.__bullet_direct <= len(MOVES) * -1:
            self.__bullet_direct += len(MOVES)

    def get_first_lunch_direct(self):
        return self.__first_lunch_direct

    def get_loc(self):
        return self.rect.x, self.rect.y

    def get_image(self):
        return self.__image


class Surprise(pygame.sprite.Sprite):
    def __init__(self, x, y, attr=None):
        super(Surprise, self).__init__()
        self.__image = pygame.image.load(SURPRISE).convert()
        self.__image.set_colorkey(WHITE)
        self.rect = self.__image.get_rect()
        self.rect.x, self.rect.y = x, y
        if attr is None:
            #  create the surprise
            self.attribute = random.randint(1, 4)
        else:
            # get info about surprise from the main player
            self.attribute = attr

    def get_attribute(self):
        return self.attribute

    def get_loc(self):
        return self.rect.x, self.rect.y

    def get_image(self):
        return self.__image


def main():
    pass


if __name__ == '__main__':
    main()
