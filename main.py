
from os import read
import socket
from numpy.lib.arraysetops import isin
import pygame
import select
import pygame
from macros import *
from entities import *
import pickle
import traceback
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((SERVER_IP, SERVER_PORT))


pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hysteresis")
clock = pygame.time.Clock()


id = None
all_sprites = None
main_player = None

running = True
while running:
    ready_sockets, _, _ = select.select([server], [], [],
                                        CLIENT_TIMEOUT)
    try:
        if ready_sockets:
            try:
                data = pickle.loads(server.recv(1024))
            except:
                continue

            print('curr id:', id, 'received:', data)

            if id is None and not isinstance(data, str):
                print('still needs id')
                continue

            elif id is None and isinstance(data, str):
                id = data
                print('new id', id)
                continue

            elif id is not None and not isinstance(data, dict):
                print('not dict')
                continue

            elif id is not None and isinstance(data, dict):
                enemies = pygame.sprite.Group()
                players = pygame.sprite.Group()
                ui = pygame.sprite.Group()
                all_sprites = pygame.sprite.Group()

                for player in data['players']:
                    sprite = Player(entity=player,
                                    color=BLUE)
                    ui.add(HealthBar(sprite))
                    players.add(sprite)

                    if player['id'] == id:
                        main_player = sprite

                for enemy in data['enemies']:
                    sprite = Enemy(entity=enemy,
                                   color=YELLOW)
                    ui.add(HealthBar(sprite))
                    enemies.add(sprite)

                all_sprites.add(players)
                all_sprites.add(enemies)
                all_sprites.add(ui)
            else:
                print(data)
                exit('strange result:')

        print(id, 'all sprites', all_sprites)
        if all_sprites is None:
            continue
        else:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            all_sprites.update()

            hits = pygame.sprite.groupcollide(players, enemies, False, False)

            if hits:
                for hitting in hits:
                    print(hits[hitting])
                    if hitting.stats['attacking']:
                        for hitted in hits[hitting]:
                            damage = CALCULATE_DAMAGE(hitting.stats,
                                                      hitted.stats,
                                                      NORMAL_ATTACK)
                            new_hp = hitted.stats['hp']
                            hitted.receive_damage(damage)
                            message = bytes(
                                f'{hitting.name} attacked {hitted.name}, damage: {damage} {new_hp}', "utf-8")
                            print(message)

                            damage_response = {'command': 'damage: player-to-enemy',
                                               'hitting': hitting.entity,
                                               'hitted': hitted.entity}
                            server.send(pickle.dumps(damage_response))

            movement_response = {'command': 'movement'}
            movement_response.update(main_player.entity)

            server.send(pickle.dumps(movement_response))
            
            screen.fill(BLACK)
            all_sprites.draw(screen)
            pygame.display.flip()

    except Exception as e:
        print('global error:', e)
        server.send(pickle.dumps(e))
        traceback.print_exc()
        exit()
        
pygame.quit()
