#!/usr/bin/env python
"""Executable script to run game, "Escape from Wikipedia".

See "README.txt" for instructions.
"""
# Copyright 2013 Aaron Graham-Horowitz
# 
# This file is part of Escape from Wikipedia.
# 
# Escape from Wikipedia is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or any later version.
# 
# Escape from Wikipedia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
# 
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

# TODO: Add some kind of score keeping.
# TODO: Create some sort of reward for reaching the top of a page.

import sys, os, pygame, rabbyt
from pygame.locals import *
from constants import *
import glutils
from sprites import Player
from scrapewiki import Page, Word

# Make sure we can use our .png and other images
assert(pygame.image.get_extended() > 0)

LEFT_KEYS = (K_LEFT, K_a)
RIGHT_KEYS = (K_RIGHT, K_d)
UP_KEYS = (K_UP, K_w)
DOWN_KEYS = (K_DOWN, K_s)
QUIT_KEYS = (K_ESCAPE, )
RESTART_KEYS = (K_r, )

FPS = 90
TIME_FACTOR = 1000.0   # Helps rabbyt read pygame ticks


def terminate():
    """Quit and clean up."""
    pygame.quit()
    sys.exit()

def main():
    """Initialize environment, then start game instance."""
    pygame.init()
    pygame.display.set_mode( (WINWIDTH, WINHEIGHT),
                             pygame.OPENGL | pygame.DOUBLEBUF )
    # (0,0) is center point of screen
    rabbyt.set_viewport( (WINWIDTH, WINHEIGHT) )
    rabbyt.set_default_attribs()
    pygame.display.set_icon(pygame.image.load(os.path.join('images',
        'gameicon.png')).convert_alpha())
    pygame.display.set_caption('Escape from Wikipedia')

    while True:
        runGame()       # Allows restarts

def runGame():
    """Initialize new game."""
    pygame.display.set_caption('Escape from Wikipedia - Loading')
    fpsclock = pygame.time.Clock()
    camx = 0
    camy = 0
    section = 0
    player = Player(PLAYER_START)
    loading = Word("LOADING", (camx - 205, camy - 55),
            attr=BOLD, size=2, color=PURPLE)
    rabbyt.clear(WHITE)
    loading.render()     # Loading screen
    pygame.display.flip()
    # Short, simple page
    #page = Page("http://en.wikipedia.org/wiki/Solariellidae")
    # Longest page in Wikipedia
    #page = Page("http://en.wikipedia.org/wiki/Character_mask")
    # Random page
    page = Page("http://en.wikipedia.org/wiki/Special:Random")
    pygame.display.set_caption('Escape from...   ' + page.title)
    # xkcd
    #page = Page("http://en.wikipedia.org/wiki/Xkcd")
    #print len(page.words)

    # Main loop
    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key in QUIT_KEYS:
                    terminate()
                elif event.key in RESTART_KEYS:
                    glutils.scroll(-camx, -camy) # Reset glMatrix
                    return
                elif event.key in LEFT_KEYS:
                    player.goingleft = True
                    player.goingright = False
                    player.image.tex_shape = (1, 1, 0, 0)
                elif event.key in RIGHT_KEYS:
                    player.goingright = True
                    player.goingleft = False
                    player.image.tex_shape = (0, 1, 1, 0)
                elif event.key in UP_KEYS:
                    player.jump()
                elif event.key in DOWN_KEYS and player.plat is not None:
                    # Enter hyperlink
                    if not player.plat.hyperlink == "":
                        pygame.display.set_caption(
                                'Escape from Wikipedia - Loading')
                        loading = Word("LOADING", (camx - 205, camy - 55),
                                attr=BOLD, size=2, color=PURPLE)
                        rabbyt.clear(WHITE)
                        loading.render()   # Display load screen
                        pygame.display.flip()
                        page = Page(player.plat.hyperlink)
                        pygame.display.set_caption(page.title)
                        pygame.display.set_caption('Escape from...   '
                                + page.title)
                        #print len(page.words)
                        player.reset(page)
            elif event.type == KEYUP:
                if event.key in LEFT_KEYS:
                    player.goingleft = False
                elif event.key in RIGHT_KEYS:
                    player.goingright = False
                elif event.key in UP_KEYS and player.velocity[1] > 0:
                    player.velocity[1] *= 0.5   # Control jump height

        # Update position
        player.update()

        # Check for player-platform collisions
        collisions = rabbyt.collisions.aabb_collide_single(player,
                page.visible_words)
        # Player forced out of platforms by most direct route, more or less;
        for plat in collisions:
            if (player.right / 3 + 2 * player.left / 3 < plat.left
            and player.velocity[0] > 0):
                player.right = plat.left - 1
            elif (player.left / 3 + 2 * player.right / 3 > plat.right
            and player.velocity[0] < 0):
                player.left = plat.right + 1
            # More sensitive about the top, to compensate for high fall veloc
            elif player.top > plat.top and player.velocity[1] < 0:
                player.bottom = plat.top + 1
                player.plat = plat
                player.velocity[1] = 0   # Stop falling
                player.jumps = 0         # Reset jumps
                if plat.hyperlink != "":
                    player.hl_landed(TIMEOUT)
            elif (2 * player.top / 3 + player.bottom / 3 < plat.bottom
            and player.velocity[1] > 0):
                player.top = plat.bottom - 1
                player.velocity[1] = 0   # Jump stops

        prev_section = section
        prev_y = camy
        # adjust camera if beyond the "camera slack"
        if camx - player.x > CAMERASLACK:
            glutils.scroll(player.x + CAMERASLACK - camx, 0)
            camx = player.x + CAMERASLACK
        elif player.x - camx > CAMERASLACK:
            glutils.scroll(player.x - CAMERASLACK - camx, 0)
            camx = player.x - CAMERASLACK
        if camy - player.y > CAMERASLACK:
            glutils.scroll(0, player.y + CAMERASLACK - camy)
            camy = player.y + CAMERASLACK
        elif player.y - camy > CAMERASLACK:
            glutils.scroll(0, player.y - CAMERASLACK - camy)
            camy = player.y - CAMERASLACK

        # Keep track of viewing section
        section += int(prev_y / WINHEIGHT) - int(camy / WINHEIGHT)
        if not section == prev_section:
            if section > len(page.sections) + 1:
                glutils.scroll(-camx, -camy) # Reset glMatrix
                return
            page.visible_words = page.words[
                    page.sections[min(len(page.sections) - 1, max(0, section - 1))]:
                    page.sections[max(0, min(len(page.sections) - 1, section + 1))]]

        # Slow to FPS
        fpsclock.tick(FPS)
        # Need to tell Rabbyt what time it is every frame
        rabbyt.set_time(pygame.time.get_ticks() / TIME_FACTOR)

        # Draw screen
        rabbyt.clear(WHITE)
        rabbyt.render_unsorted(page.visible_words)
        rabbyt.render_unsorted(page.lines)
        player.render()
        pygame.display.flip()


if __name__ == '__main__':
    main()

