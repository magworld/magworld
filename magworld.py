#
# Blind, two-dimensional, rotationless agent simulation
#
# You are the red square.
#
# Instructions
#
#    i, j, k, l  =  move
#    m           =  toggle magnetism on/off (so we can pull, not just push)
#    b           =  toggle blind mode
#    q           =  quit
#
# When you collide with an object, you will be stopped.  But you can
# push on the object by simply pressing the motion key again.
#
#





from pygame.time import Clock

import pygame
import sys
from math import sqrt, pi, sin, cos, atan2


red = (255,0,0)
magenta = (255,0,255)
green = (0,255,0)
orange = (255,128,0)
yellow = (255,255,0)
blue = (0,0,255)
darkBlue = (0,0,128)
white = (255,255,255)
black = (0,0,0)
pink = (255,200,200)
gray = (220, 220, 220)


cardinal_directions = ((-1,0),
                       (1,0),
                       (0,-1),
                       (0,1))

class Body:
    def __init__(self, points, x, y, color=black, name="?", fixed=False):
        self.x = x
        self.y = y
        self.points = set(points)
        self.color = color
        self.name = name
        self.fixed = fixed

    # if i go from this body in the direction (dx,dy), do I touch body?
    def contacts(self, dx, dy, body):
        if body == self: return False

        # offset
        ox = self.x + dx - body.x
        oy = self.y + dy - body.y
        
        for x, y in self.points:
            if (x+ox, y+oy) in body.points:
                return True
        return False

    def neighbors(self, dx, dy):
        return [body for body in bodies if self.contacts(dx, dy, body)]

    def self_and_all_magnetic_neighbors(self):
        ret = set([self])
        for dx, dy in cardinal_directions:
            for n in self.neighbors(dx,dy):
                if not n == arena:
                    ret.add(n)
        return ret

    def build_contact_subtree(self, dx, dy, accum):
        if not self in accum:
            accum.add(self)
            for neighbor in self.neighbors(dx, dy):
                neighbor.build_contact_subtree(dx, dy, accum)
        
    def contact_subtree(self, dx, dy):
        ret = set()
        self.build_contact_subtree(dx, dy, ret)
        return ret

    def __repr__(self):
        return self.name


def hline(x, y, w):
    return [(i,y) for i in xrange(x,x+w)]

def vline(x, y, h):
    return [(x,j) for j in xrange(y,y+h)]

def rect(w,h):
    return [(i,0) for i in xrange(w)] \
        + [(i,h-1) for i in xrange(w)] \
        + [(0,j) for j in xrange(1,h-1)] \
        + [(w-1,j) for j in xrange(1,h-1)]


class Rect(Body):
    def __init__(self, w, h, x, y, **kwargs):
        points = rect(w,h)
        Body.__init__(self, points, x, y, **kwargs)

agentbody = Rect(13, 13, 30, 50, color=red, name='agent')
arena = Body(rect(190,190)+
             hline(12, 110, 170)+
             vline(100,5,20)+
             vline(100,50,130)+
             vline(102,5,20)+
             vline(102,50,130)
             ,
             4, 4,
             color=gray, name='arena', fixed=True)
bodies = [agentbody, arena,
          Rect(10, 10, 30, 30, color=blue, name='blue'),
          Rect(1, 50, 105, 20, color=blue, name='door'),
          Rect(10, 10, 60, 30, color=green, name='green'),
          Rect(5, 10, 60, 20, color=orange, name='orange'),
          Rect(2, 2, 13, 125, color=orange, name='reward'),
          Body(hline(0,0,4)+
               vline(4,0,15)+
               hline(4,15,3)+
               vline(7,15,4)+
               hline(0,19,8)+
               vline(0,0,19),
               70,20,
               name='L')
          ]
               
            



M = N = 200
cellsize = 5

captured = []

pygame.init()

screen = pygame.display.set_mode((M*cellsize,N*cellsize))


screen.fill(white)






# world to pixel
def wtop(world):
    wx, wy = world
    return (wx * cellsize, wy * cellsize)



blind_mode = True

# center of window
cx, cy = M/2,N/2

def draw():

    # hide objects, show sensor values
    if blind_mode:

        for dx, dy in agentbody.points:
            pygame.draw.rect(screen, agentbody.color,
                             wtop((cx + dx,
                                   cy + dy))
                             + (cellsize, cellsize))

        offsets = ((-1,6),
                   (13,6),
                   (6,-1),
                   (6,13),
                   )
        for (dx, dy), (ox, oy) in zip(cardinal_directions, offsets):
            if agentbody.neighbors(dx, dy):
                pygame.draw.rect(screen, blue,
                                 wtop((ox + cx, oy + cy))
                                 + (cellsize, cellsize))

        motion_indicators = {(1,0): (10,6),
                             (-1,0): (2,6),
                             (0,1): (6,10),
                             (0,-1): (6,2)}

        if adx or ady:
            ix, iy = motion_indicators[adx,ady]
            pygame.draw.rect(screen, green,
                             wtop((cx + ix, cy + iy))
                             + (cellsize, cellsize))
            
            
        if magnetism:
            pygame.draw.rect(screen, magenta,
                             wtop((cx+6, cy+6))
                             + (cellsize, cellsize))
            
            
            
    
    else:
        for body in bodies:
            for dx,dy in body.points:
                pygame.draw.rect(screen, body.color,
                                 wtop((body.x + dx,
                                       body.y + dy))
                                 + (cellsize, cellsize))
            

# motion    
mdx = mdy = 0

clock = Clock()

comovers = None
magnetism = False
temp_stop = False

t = 0

while True:

    adx = ady = 0

    # are we trying to move?
    if mdx or mdy:
        
        # test for impacts
        oldcomovers = comovers

        comovers = set()

        # determine comovers
        if magnetism:
            for b in agentbody.self_and_all_magnetic_neighbors():
                b.build_contact_subtree(mdx, mdy, comovers)
        else:
            agentbody.build_contact_subtree(mdx, mdy, comovers)

            
        #comovers = agentbody.contact_subtree(dx, dy)

        if oldcomovers != None and comovers != oldcomovers:
            # we've hit a new object; stop temporarily
            temp_stop = True

        # are we stuck?
        if not any([body.fixed for body in comovers]) and not temp_stop:
            adx = mdx
            ady = mdy

        for body in comovers:
            body.x += adx
            body.y += ady

    format = "Timestep: %4s     Input: %2s %2s %s     Output: %2s %2s %s"
    print format  % (t,
                     mdx, mdy,
                     1 if magnetism else 0,
                     adx, ady,
                     " ".join([('1' if agentbody.neighbors(dx2,dy2) else '0')
                               for dx2, dy2 in cardinal_directions]))



    # check for quit events
    for event in pygame.event.get():
         if event.type == pygame.QUIT:
              pygame.quit(); sys.exit();
         elif event.type is pygame.MOUSEBUTTONDOWN:
             mdown = pygame.mouse.get_pos()
         elif event.type is pygame.MOUSEBUTTONUP:
             pass
         elif event.type is pygame.KEYDOWN and mdx == mdy == 0:
             if event.unicode == 'b':
                 blind_mode = not blind_mode
             if event.unicode == 'i':
                 mdy = -1
             if event.unicode == 'k':
                 mdy = 1
             if event.unicode == 'j':
                 mdx = -1
             if event.unicode == 'l':
                 mdx = 1
             if event.unicode == 'm':
                 magnetism = not magnetism
             if event.unicode == 'q':
                 pygame.quit(); sys.exit();
         elif event.type is pygame.KEYUP:
             mdx = mdy = 0
             comovers = None
             temp_stop = False

    # erase the screen
    screen.fill(white)

    draw()


    # update the screen
    pygame.display.update()

    clock.tick(60)

    #print agentbody.contact_subtree(0,-1)

    t += 1
