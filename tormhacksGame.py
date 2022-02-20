from operator import truediv
from unittest.mock import AsyncMockMixin
import pygame
import os
import random
import csv

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Stormhacks Game')

#set frame rate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 12
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 45
screen_scroll = 0
bg_scroll = 0
Level = 1


#define player action variables
moving_left = False
moving_right = False
shoot = False

#load images
background0_img = pygame.image.load('backgrounds/0.png').convert_alpha()
background0_img = pygame.transform.scale(background0_img, (800, 640))

background1_img = pygame.image.load('backgrounds/1.png').convert_alpha()
background1_img = pygame.transform.scale(background1_img, (800, 640))

background2_img = pygame.image.load('backgrounds/2.png').convert_alpha()
background2_img = pygame.transform.scale(background2_img, (800, 640))

background3_img = pygame.image.load('backgrounds/3.png').convert_alpha()
background3_img = pygame.transform.scale(background3_img, (800, 640))

background4_img = pygame.image.load('backgrounds/4.png').convert_alpha()
background4_img = pygame.transform.scale(background4_img, (800, 640))
#Tiles
img_list = []
for x in range (TILE_TYPES):
    img = pygame.image.load(f'tiles/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
    
#arrow
arrow_scale = 0.15
arrow_img = pygame.image.load('sprites/icons/0.png').convert_alpha()
arrow_img = pygame.transform.scale(arrow_img, (arrow_img.get_width()*arrow_scale, arrow_img.get_height()*arrow_scale))

arrow_scale = 0.15
arrow_ammo_img = pygame.image.load('sprites/icons/5.png').convert_alpha()
arrow_ammo_img = pygame.transform.scale(arrow_ammo_img, (arrow_ammo_img.get_width()*arrow_scale, arrow_ammo_img.get_height()*arrow_scale))

#pickup item
item_box_img = pygame.image.load('sprites/icons/1.png').convert_alpha()
health_box_img = pygame.image.load('sprites/icons/2.png').convert_alpha()
item_boxes = {
    'Health'    : health_box_img,
    'Item'      : item_box_img
}

heart_red_scale = 1
heart_red_img = pygame.image.load('sprites/icons/3.png').convert_alpha()
heart_red_img = pygame.transform.scale(heart_red_img, (heart_red_img.get_width()*heart_red_scale, heart_red_img.get_height()*heart_red_scale))

heart_black_scale = 1
heart_black_img = pygame.image.load('sprites/icons/4.png').convert_alpha()
heart_black_img = pygame.transform.scale(heart_black_img, (heart_black_img.get_width()*heart_black_scale, heart_black_img.get_height()*heart_black_scale))


#define colours
BG = (144, 201, 120)
RED = (255,0,0)
WHITE = (255, 255, 255)

#define font
font = pygame.font.SysFont('Futura', 20)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    width = background0_img.get_width()
    for x in range(8):
        screen.blit(background0_img, ((x * width) - bg_scroll * 0.3 , 0))
        screen.blit(background1_img, ((x * width) - bg_scroll * 0.5 , 0))
        screen.blit(background2_img, ((x * width) - bg_scroll * 0.6 , 0))
        screen.blit(background3_img, ((x * width) - bg_scroll * 0.7 , 0))
        screen.blit(background4_img, ((x * width) - bg_scroll * 0.8 , 0))
    #screen.blit(sky_img, (0,0))

class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.health = 5
        self.max_health = self.health
        self.direction = 1 #right
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0 #0=idle 1=walking
        self.update_time = pygame.time.get_ticks()
        #create ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0,0, 150, 20)
        self.idling = False
        self_idling_counter = 0

        #load all images for the players
        animation_types = ['Idle', 'Walking', 'Jump', 'Death', 'Attack', 'Hurt']
        for animation in animation_types:
            #reset temporary list of images
            temp_list = []
            #count number of files in the folder
            num_of_frames = len(os.listdir(f'sprites/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'sprites/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
                temp_list.append(img)
            self.animation_list.append(temp_list)

            #temp_list = []
            #for i in range(2):
                #img = pygame.image.load(f'sprites/{self.char_type}/Walking/{i}.png')
                #img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
                #temp_list.append(img)
            #self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        #reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0

        #assign movement variables left/right
        if moving_left:
            dx = -self.speed
            self.flip = False
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = True
            self.direction = 1

        #jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -16
            self.jump = False
            self.in_air = True

        #apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        #check collision with floor
        for tile in world.obstacle_list:
            #check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai has hit a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #check collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below ground, ie jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above ground, ie falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0
                
        #if self.rect.bottom + dy > 300:
            #dy = 300 - self.rect.bottom
            #self.in_air = False

        #update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - (SCROLL_THRESH + 200) and bg_scroll < (world.level_length * TILE_SIZE) - (SCREEN_WIDTH + 200))\
                 or (self.rect.left < SCREEN_WIDTH - SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll


    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            #player.update_action(4)
            arrow = Arrow(self.rect.centerx + (self.direction * self.rect.size[0]), self.rect.centery, self.direction)
            arrow_group.add(arrow)
            #reduce ammo
            self.ammo -= 1

    #def shoot_enemy(self): #TESTING ENEMY SWORD PROJECTILE
        #sword = Arrow(self.rect.centerx + (self.direction * self.rect.size[0]), self.rect.centery, self.direction)
        #arrow_group.add(sword)


    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0) #0: Idle
                self.idling = True
                self.idling_counter = 50
            #check if the ai is near the player
            if self.vision.colliderect(player.rect):
                #stop running and face the player
                self.update_action(0)#0: idle
                #shoot
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) #1: run
                    self.move_counter += 1
                    #update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #pygame.draw.rect(screen, RED, self.vision)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else: 
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        #scroll
        self.rect.x += screen_scroll


    def update_animation(self):
        #update animation
        ANIMATION_COOLDOWN = 100
        #update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        #check if enough time has passed since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if animation has run out reset to start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self,new_action):
        #check if new action is diff than previous
        if new_action != self.action:
            self.action = new_action
            #update animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)






class HealthBar():
    def __init__(self, health, max_health):
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #update with new health
        #print(health)
        #self.kill()
        self.health = health
        for y in range(player.max_health):
            screen.blit(heart_black_img, (90 + (y*20), 10))
        for y in range(self.health):
            screen.blit(heart_red_img, (90 + (y*20), 10))

        #for y in range(player.max_health):
            #screen.blit(heart_black_img, (90 + (y*20), 10))
        
        #pygame.draw.rect(screen, RED (self.x, self.y, 150, 20))

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if player has picked up box
        if pygame.sprite.collide_rect(self, player):
            #check type of box
            if self.item_type == 'Health':
                #print(player.health) #DELETE LATER
                player.health += 1
                #print(player.health) #DELETE LATER
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Item':
                player.ammo += 2
            #delete item box
            self.kill()
    def update(self):
        #scroll
        self.rect.x += screen_scroll

class Friend(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('sprites/friend/idle/0.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #scroll
        self.rect.x += screen_scroll

class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self) 
        self.speed = 5
        self.image = arrow_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move arrow
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        #check collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #check collision w/ characters
        if pygame.sprite.spritecollide(player, arrow_group, False):
            if player.alive:
                player.health -= 1
                player.update_action(5)
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, arrow_group, False):
                if enemy.alive:
                    enemy.health -= 3
                    player.update_action(5)
                    self.kill()





class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)

                    #obstacles
                    if ( tile >= 0 and tile <= 28 ) or ( tile >= 32 and tile <=38):
                        self.obstacle_list.append(tile_data)
                    elif tile == 40:
                        void = Void(img,x * TILE_SIZE, y * TILE_SIZE)
                        void_group.add(void)
                        self.obstacle_list.append(tile_data)
                    elif tile == 44: #player
                        player = Soldier('player',x * TILE_SIZE, y * TILE_SIZE,1.5,5,5)
                        health_bar = HealthBar(player.health, player.max_health)
                    elif tile == 39: #friend
                        friend = Friend('friend',x * TILE_SIZE, y * TILE_SIZE) 
                        friend_group.add(friend)
                    elif tile == 43: #enemy
                        enemy = Soldier('enemy',x * TILE_SIZE, y * TILE_SIZE, 2,2,100)
                        enemy_group.add(enemy)
                    elif tile == 42: #ammo box
                        item_box = ItemBox('Item', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)  
                    elif tile == 41: #health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif (tile >= 29 and tile <= 31): #exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
                        self.obstacle_list.append(tile_data)
                    
        return player, health_bar
    
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0],tile[1])
            

            
class Exit(pygame.sprite.Sprite):
    def __init__(self,img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

class Void(pygame.sprite.Sprite):
    def __init__(self,img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y+ (TILE_SIZE - self.image.get_height()))


#create sprite groups
enemy_group = pygame.sprite.Group()
arrow_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
void_group = pygame.sprite.Group()
friend_group = pygame.sprite.Group()
        
#create empty tile list 
world_data = []
for row in range (ROWS):
    r = [-1] * COLS
    world_data.append(r) 
#load in level data and create world 
with open(f'level{Level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile,delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)





def menu():
    image = pygame.image.load('menu.png')
    image = pygame.transform.scale(image, (800,640))

    #menu loop
    MenuScreen = True
    while MenuScreen:
        screen.blit(image,(0,0))

        pygame.display.update()
        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                pygame.display.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] in range(310,490) and event.pos[1] in range(310,440):
                    MenuScreen = False

def instructions():
    image = pygame.image.load('instructions.png')
    image = pygame.transform.scale(image, (800,640))

    instructionsScreen = True
    while instructionsScreen:
        screen.blit(image,(0,0))

        pygame.display.update()
        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                pygame.display.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] in range(0,800) and event.pos[1] in range(0,640):
                    instructionsScreen = False
                    
def keyinstructions():
    image = pygame.image.load('keybinds.png')
    image = pygame.transform.scale(image, (800,640))

    KeyScreen = True
    while KeyScreen:
        screen.blit(image,(0,0))

        pygame.display.update()
        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                pygame.display.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] in range(0,800) and event.pos[1] in range(0,640):
                    KeyScreen = False
                    
                    
menu()
instructions()
keyinstructions()

#game loop
run = True
while run:

    clock.tick(FPS)
    
    #background update
    draw_bg()

    #draw world map
    world.draw()
    
    #show player health
    draw_text('HEALTH: ', font, WHITE, 10, 10)
    health_bar.draw(player.health)
    
        
    #show ammo
    draw_text('ARROWS: ', font, WHITE, 10, 35)
    for x in range(player.ammo):
        screen.blit(arrow_ammo_img, (90 + (x*10), 30))

    player.update()
    player.draw()
    
    #for friend in friend_group:
        #friend.update()
        #friend.draw()

    for enemy in enemy_group:
        enemy.ai()
        enemy.update()
        enemy.draw()

    #update and draw groups
    arrow_group.update()
    item_box_group.update()
    void_group.update()
    exit_group.update()
    friend_group.update()

    arrow_group.draw(screen)
    item_box_group.draw(screen)
    void_group.draw(screen)
    exit_group.draw(screen)
    friend_group.draw(screen)

    #update player actions
    if player.alive:
        #shoot arrows
        if shoot:
            player.update_action(4) #4=attack ADDED FOR SHOOT ANIMATION CHECK LATER
            player.shoot()
        if player.in_air:
            player.update_action(2) #2=jump
        elif moving_left or moving_right:
            player.update_action(1) #1=walking
        else:
            player.update_action(0) #0=idle
        screen_scroll = player.move(moving_left, moving_right)
        bg_scroll -= screen_scroll



    for event in pygame.event.get():
        #quit game
        if event.type == pygame.QUIT:
            run = False

        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False

        #keyboard button release
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False

    pygame.display.update()



pygame.quit()