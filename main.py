#! /usr/bin/env python3
import random
import math
import collections

import os
import sys

libdir = os.path.join(sys.path[0], 'deps')
for inc in os.listdir(libdir):
  sys.path.append(os.path.join(libdir, inc))

import pyglet
pyglet.options['search_local_libs'] = True
#pyglet.options['debug_trace'] = True
#import pyglet.lib
#n = 0
#def tmp(self, *a, **kw):
#  k = n
#  global n
#  n += 1
#  print k, self._func.__name__, a, kw,
#  sys.stdout.flush()
#  r = self._func(*a, **kw)
#  print k, "->", r
#  return r
#pyglet.lib._TraceFunction.__call__ = tmp
import pyglet.window.key as key
from pyglet.gl import *
import squirtle
import togepy.draw
import togepy.gfx
import cocos
from cocos.actions.interval_actions import *
from cocos.actions.instant_actions import *
from cocos.director import director

def clip(val, vmin, vmax): return min(max(val, vmin), vmax)
def format_number(n):
  x = str(n)
  from itertools import chain, cycle
  # <evil laugh>
  return ''.join(','.join(''.join(y) for y in zip(x[-1::-3], chain(x[-2::-3], cycle(' ')), chain(x[-3::-3], cycle(' '))))[::-1]).strip()

class SVGNode(cocos.cocosnode.CocosNode):
  def __init__(self, image, *args, **kw):
    super(SVGNode, self).__init__(*args, **kw)
    self.image = image

  def draw(self):
    glPushMatrix()
    self.transform()
    self.image.draw(0, 0)
    glPopMatrix()

  def min_x(self): return -0.5
  def max_x(self): return 0.5
  def min_y(self): return -0.5
  def max_y(self): return 0.5
  def width(self): return self.max_x() - self.min_x()
  def height(self): return self.max_y() - self.min_y()

class TileNode(SVGNode):
  images = {}

  @staticmethod
  def get_colored_image(color):
    # outerLight: 9d 9d ff c7
    # outerDark:  00 00 7f c7
    # inner    :  41 41 ff 64
    if color not in TileNode.images:
      (r,g,b) = color
      color_overrides = dict(innerColor=[65+r*190,65+g*190,65+b*190],
                             outerLight=[155+r*100,155+g*100,155+b*100],
                             outerDark=[127*r,127*g,127*b])
      TileNode.images[color] = squirtle.SVG("data/images/tile.svg", anchor_x='center', anchor_y='center',
                                            color_overrides=color_overrides)
    return TileNode.images[color]

  def __init__(self, color = (1,0,1)):
    super(TileNode, self).__init__(image = TileNode.get_colored_image(color))
    self.scale = 1/32.

class BulletNode(cocos.cocosnode.CocosNode):
  def draw(self) :
    glPushMatrix()
    self.transform()
    togepy.draw.line((0.8, 0.8, 0.2, 0.8), (0, 0), (0, 0.7), width=0.4, endcolor=(1.0, 0.2, 0.2, 0.8))
    glPopMatrix()

  def min_x(self): return -0.2
  def max_x(self): return 0.2
  def min_y(self): return 0.0
  def max_y(self): return 0.7
  def width(self): return self.max_x() - self.min_x()
  def height(self): return self.max_y() - self.min_y()

class Gestalt(cocos.cocosnode.CocosNode):
  def __init__(self, color):
    super(Gestalt, self).__init__()
    dd = collections.defaultdict
    self.tiles = dd(lambda: dd(lambda: None))
    self.color = color
    #self.addAt(0, 0)

  def centreOfGravity(self):
    mx, my = 0, 0
    m = 0
    for x, col in self.tiles.items():
      for y, t in col.items():
        if not t: continue
        mx += x
        my += y
        m += 1
    if m:
      return self.x + mx / m, self.y + my / m
    else:
      return self.x, self.y

  def addAt(self, x, y):
    t = self.tiles[x][y]
    if t: self.remove(t)
    t = TileNode(self.color)
    t.x = x
    t.y = y
    self.tiles[x][y] = t
    self.add(t)

  def destroyAt(self, x, y, time=0.5):
    #print "destroyAt", x, y
    t = self.tiles[x][y]
    if t:
      del self.tiles[x][y]
      t.do(FadeOut(time) | ScaleBy(3, time) | (Delay(time) + CallFunc(self.remove, t)))

  def moveCell(self, x0, y0, x1, y1, delay=0, time=0.5):
    if x0 == x1 and y0 == y1: return
    if self.tiles[x1][y1]:
      print("moveCell: destination already occupied")
      self.remove(self.tiles[x1][y1])
    #print "moveCell", x0, y0, x1, y1
    t = self.tiles[x0][y0]
    self.tiles[x1][y1] = t
    del self.tiles[x0][y0]
    if t:
      t.do(Delay(delay) + MoveTo((x1, y1), time))

  def area(self):
    return sum(1 for d in self.tiles.values() for c in d.values() if c)

  def at(self, x, y):
    return self.tiles.get(x, {}).get(y, None)

  def canCombine(self, o, dx, dy):
    adjacent = False
    for z, c in o.children:
      x, y = c.x + dx, c.y + dy
      # Check for overlap with existing tiles.
      if self.tiles[x][y]:
        adjacent = False
        break
      # Check for adjacency to existing tiles.
      for check_x, check_y in (x-1,y), (x+1,y), (x,y-1), (x,y+1):
        if self.tiles[check_x][check_y]:
          adjacent = True
    return adjacent

  def combine(self, o, off, force=False):
    sx, sy = self.position
    ox, oy = o.position
    dx, dy = round(ox - sx - off[0]), round(oy - sy - off[1])
    if self.canCombine(o, dx, dy) or force:
      for z, c in o.children:
        o.remove(c)
        c.x += dx
        c.y += dy
        if self.tiles[c.x][c.y]:
          self.remove(self.tiles[c.x][c.y])
        self.tiles[c.x][c.y] = c
        self.add(c)
      return True
    else:
      return False

  def remove_intersection(self, o):
    for _, sc in self.children:
      for _, oc in o.children:
        if collide(sc, oc, self.position, o.position):
          del self.tiles[sc.x][sc.y]
          self.remove(sc)
          del o.tiles[oc.x][oc.y]
          o.remove(oc)
          break

  def rotate(self, dir, time=0.1):
    dd = collections.defaultdict
    tiles = dd(lambda: dd(lambda: None))
    for x, col in self.tiles.items():
      for y, t in col.items():
        if not t: continue
        t.stop()
        if dir:
          newX, newY = y, -x
        else:
          newX, newY = -y, x
        tiles[newX][newY] = t
        if time:
          t.do(MoveTo((newX, newY), time))
        else:
          t.x, t.y = newX, newY
    self.tiles = tiles

  def min_x(self): return min(self.tiles.keys()) - 0.5
  def max_x(self): return max(self.tiles.keys()) + 0.5
  def min_y(self): return min(sum((list(col.keys()) for col in self.tiles.values()), [])) - 0.5
  def max_y(self): return max(sum((list(col.keys()) for col in self.tiles.values()), [])) + 0.5
  def width(self): return self.max_x() - self.min_x()
  def height(self): return self.max_y() - self.min_y()

def dotLine(x0, y0, x1, y1, scale, color, every=1, parent=None):
  if not parent:
    parent = cocos.cocosnode.CocosNode()
  parent.scale = scale
  v = abs(x1 - x0 + y1 - y0)
  for d in range(0, v + 1, every):
    t = TileNode(color=color)
    t.x = x0 + (x1 - x0) * d / float(v)
    t.y = y0 + (y1 - y0) * d / float(v)
    parent.add(t)
  return parent

class Player(cocos.cocosnode.CocosNode):
  def __init__(self):
    super(Player, self).__init__()
    self.alive = True
    self.body = Gestalt(color=(0.2,0.2,0.2))
    self.body.addAt(0,0)
    self.add(self.body)
    p = [-17, 17]
    c = list(map(lambda xy: (p[xy[0]],p[xy[1]]), [(0,0),(0,1),(1,1),(1,0),(0,0)]))
    self.dots = cocos.cocosnode.CocosNode()
    for (x0,y0),(x1,y1) in zip(c, c[1:]):
      dotLine(x0, y0, x1, y1, scale = 1/3., color=(0.2,0.2,0.2), every=2, parent=self.dots)
    for _, dot in self.dots.children:
      dot.target_x, dot.target_y = dot.x, dot.y
    self.add(self.dots)
  def min_x(self): return -5.5
  def max_x(self): return 5.5
  def min_y(self): return -5.5
  def max_y(self): return 5.5
  def width(self): return 11
  def height(self): return 11
  def combine(self, o, **kw):
    if not self.body.combine(o, off=self.position, **kw):
      return 0
    fullRow = collections.defaultdict(lambda: True)
    fullCol = collections.defaultdict(lambda: True)
    cells = []
    lines = 0
    outside = 0
    for x in range(-9, 10):
      for y in range(-9, 10):
        cell = self.body.at(x, y)
        if cell:
          cell.__target = [x, y]
          cells.append((cell, x, y))
        if abs(x) > 5 or abs(y) > 5:
          if cell:
            self.alive = False
            self.body.destroyAt(x, y, time=0.5)
            outside += 1
        else:
          if not cell:
            fullRow[y] = False
            fullCol[x] = False
    for a in list(range(-5, 1)) + list(range(5,0,-1)):
      if a > 0:
        dir = -1
      else:
        dir = 1
      collapse = range(dir * -5, a, dir)
      if fullRow[a]:
        lines += 1
        #print "Full row y =", a
        for x in range(-5, 6):
          self.body.destroyAt(x, a, time=1)
          for y in collapse:
            cell = self.body.at(x, y)
            if cell:
              cell.__target[1] += dir
      if fullCol[a]:
        lines += 1
        #print "Full col x =", a
        for y in range(-5, 6):
          self.body.destroyAt(a, y, time=1)
          for x in collapse:
            cell = self.body.at(x, y)
            if cell:
              cell.__target[0] += dir
    cells.sort(key=lambda cxy: abs(cxy[1]) + abs(cxy[2]))
    for cell, x, y in cells:
      assert not self.body.at(x, y) or cell == self.body.at(x, y)
      self.body.moveCell(x, y, cell.__target[0], cell.__target[1], delay=1)
      del cell.__target
    return outside, lines

  def rotate(self, dir, time=0.1):
    self.body.rotate(dir, time=time)
    for _, t in self.dots.children:
      t.stop()
      x, y = t.target_x, t.target_y
      if dir:
        newX, newY = y, -x
      else:
        newX, newY = -y, x
      t.target_x, t.target_y = newX, newY
      if time:
        t.do(MoveTo((newX, newY), time))
      else:
        t.x, t.y = newX, newY

def collide(a, b, ap = (0,0), bp = (0,0)):
  if not getattr(a, 'min_x', None) or not getattr(b, 'min_x', None):
    return False
  ax, ay = a.position
  bx, by = b.position
  ax += ap[0]
  ay += ap[1]
  bx += bp[0]
  by += bp[1]
  cx1 = max(ax + a.min_x(), bx + b.min_x())
  cx2 = min(ax + a.max_x(), bx + b.max_x())
  cy1 = max(ay + a.min_y(), by + b.min_y())
  cy2 = min(ay + a.max_y(), by + b.max_y())
  if cx1 < cx2 and cy1 < cy2:
    if a.children or b.children:
      aas, bs = [a], [b]
      if a.children: aas, ap = [c for (z,c) in a.children], (ax,ay)
      if b.children: bs, bp = [c for (z,c) in b.children], (bx,by)
      return any(collide(ac, bc, ap, bp) for ac in aas for bc in bs)
    else:
      return True
  else:
    return False

class StarsLayer(cocos.layer.Layer):
  def __init__(self, tracked):
    super(StarsLayer, self).__init__()
    self.tracked = tracked
    
    class StarParticle(togepy.gfx.Particle):
      def __init__(self, *a, **kw):
        super(StarParticle, self).__init__(*a, **kw)
        self.init_x = self.x
        self.init_y = self.y
        
      def tick(inner):
        inner.x = (inner.init_x + inner.z * self.trackedx) % director.window.width
        inner.y = (inner.init_y + inner.z * self.trackedy) % director.window.height

    self.stars = togepy.gfx.ParticleSystem(StarParticle)
    maxsize = max(director.window.height / 400.0, 1.0)
    StarParticle.size = maxsize
    for i in range(100):
      x = random.uniform(0, director.window.width)
      y = random.uniform(0, director.window.height)
      # Size
      s = random.uniform(0.25, 1.0)
      # Brightness
      b = random.uniform(0.3, 5) ** 0.3
      self.stars.new_particle(x=x, y=y, z=maxsize * s, color=(2-b,0.8,b,s*b))
    self.schedule(self.tick)

  def draw(self):
    super(StarsLayer, self).draw()
    self.stars.draw()

  def tick(self, dt):
    self.trackedx, self.trackedy = self.tracked(dt)
    self.stars.tick()

pieces = [
  ((0,0,1),[[1,1],[1,1]]),
  ((0,1,0),[[0,1,1],[1,1,0]]),
  ((0,1,1),[[1,1,0],[0,1,1]]),
  ((1,0,0),[[1,1,1,1]]),
  ((1,0,1),[[1,1,1],[1,0,0]]),
  ((1,1,0),[[1,1,1],[0,1,0]]),
  ((1,1,1),[[1,1,1],[0,0,1]]),
]

class Piece(Gestalt):
  def __init__(self):
    color, piece = random.choice(pieces)
    self.vx, self.vy = 0, 0
    Gestalt.__init__(self, color=color)
    for y, line in enumerate(piece):
      for x, val in enumerate(line):
        if val:
          self.addAt(x-1, y)
    #location = player.x + 4, player.y + 20
    self.ticksSettled = 0
  # rotate about (0,0)

class GameLayer(cocos.cocosnode.CocosNode):
  def __init__(self, scale):
    super(GameLayer, self).__init__()
    self.game = GameNode()
    self.scale = scale
    self.add(self.game)

class GameNode(cocos.layer.Layer):
  is_event_handler = True

  def __init__(self):
    super(GameNode, self).__init__()

    self.schedule(self.tick)

    self.player = Player()
    self.player.position = (0, 0)
    self.add(self.player)
    self.timeSinceBullet = 10

    self.bullets = []
    self.objects = []

    self.addRandomEnemy()

    self.anchor = (0,0)

    self.keyboard = key.KeyStateHandler()

    self.soundLine = pyglet.resource.media('line.wav', streaming=False)
    self.soundDestroy = pyglet.resource.media('destroy.wav', streaming=False)
    self.soundDrop = pyglet.resource.media('drop.wav', streaming=False)

    self.overflow = 0

    self.lives = 10
    self.lines = 0
    self.score = 0
    self.speed = 1

  def addRandomEnemy(self):
    piece = Piece()
    for i in range(random.randrange(4)):
      piece.rotate(1, time=0)
    px, py = self.player.x, self.player.y
    piece.x, piece.y = random.choice([(px, py+28), (px, py-28), (px+28, py), (px-28, py)])
    self.do(MoveTo((32 - (self.player.x + piece.x) / 2, 24 - (self.player.y + piece.y) / 2), 0.2))
    self.objects.append(piece)
    self.add(piece)

  def on_key_press(self, k, mod):
    self.keyboard.on_key_press(k, mod)
    if k == key.Z:
      ok = True
      self.player.rotate(False, time=0)
      for o in self.objects:
        if collide(self.player, o):
          ok = False
          break
      self.player.rotate(True, time=0)
      if ok:
        self.player.rotate(False)
    if k == key.X:
      ok = True
      self.player.rotate(True, time=0)
      for o in self.objects:
        if collide(self.player, o):
          ok = False
          break
      self.player.rotate(False, time=0)
      if ok:
        self.player.rotate(True)
  def on_key_release(self, key, mod):
    self.keyboard.on_key_release(key, mod)

  def tick(self, dt):
    self.overflow += dt
    while self.overflow > 0.01:
      self.go(0.01)
      self.overflow -= 0.01

  def go(self, dt):
    self.player.vy = 0
    if self.keyboard[ key.UP ]:
      self.player.vy = 20
    elif self.keyboard[ key.DOWN ]:
      self.player.vy = -20

    self.player.vx = 0
    if self.keyboard[ key.RIGHT ]:
      self.player.vx = 20
    elif self.keyboard[ key.LEFT ]:
      self.player.vx = -20

    px, py = self.player.body.centreOfGravity()
    px += self.player.x
    py += self.player.y
    for o in self.objects:
      o.lastX, o.lastY = o.x, o.y
      cx, cy = o.centreOfGravity()
      nx, ny = px - cx, py - cy
      n = (nx*nx + ny*ny) ** 0.5
      s = self.speed #20
      if n:
        o.vx += s * nx / n * dt
        o.vy += s * ny / n * dt
      o.vx *= 4 ** -dt
      o.vy *= 4 ** -dt
      o.x += o.vx * dt
      o.y += o.vy * dt

    self.player.lastX, self.player.lastY = self.player.x, self.player.y
    self.player.x = clip(self.player.x + self.player.vx * dt,
                         -self.x - self.player.min_x(),
                         -self.x + 64 - self.player.max_x())
    self.player.y = clip(self.player.y + self.player.vy * dt,
                         -self.y - self.player.min_y(),
                         -self.y + 48 - self.player.max_y())

    self.timeSinceBullet += dt
    #if self.keyboard[ key.SPACE ] and self.timeSinceBullet > 0.2:
    #  b = BulletNode()
    #  b.position = self.player.position
    #  b.do(MoveBy((0, 50), 2) + CallFuncS(self.removeBullet))
    #  self.bullets.append(b)
    #  self.add(b)
    #  self.timeSinceBullet = 0

    for o in self.objects[:]:
      for b in self.bullets:
        if collide(b, o):
          self.removeBullet(b)
          self.removeObject(o)
          break
      else:
        settled = False
        if collide(self.player, o):
          #if self.player.area() > o.area():
          #else:
          #  Gestalt.remove_intersection(o, self.player)
          vx, vy = o.vx - self.player.vx, o.vy - self.player.vy
          oldx, oldy = o.x, o.y
          oldvx, oldvy = o.vx, o.vy
          relx = round(o.x - self.player.x)
          rely = round(o.y - self.player.y)
          clipx = relx + self.player.x
          clipy = rely + self.player.y
          #vx, vy = self.player.vx, self.player.vy
          #if abs(vx) == abs(vy):
          #  cx, cy = o.centreOfGravity()
          #  vx, vy = cx - px, cy - py
          if abs(vx) > abs(vy):
            o.y, o.vy = clipy, 0
          else:
            o.x, o.vx = clipx, 0
          #if collide(self.player, o):
          #  if abs(vx) > abs(vy):
          #    o.x, o.vx = clipx, 0
          #    o.y, o.vy = oldy, oldvy
          #  else:
          #    o.x, o.vx = oldx, oldvx
          #    o.y, o.vy = clipy, 0
          if collide(self.player, o):
            o.x, o.vx = clipx, 0
            o.y, o.vy = clipy, 0
          #if getattr(o, 'relx', None) == relx and \
          #   getattr(o, 'rely', None) == rely and \
          #   self.player.vx == self.player.vy == 0:
          if (o.x == o.lastX and o.y == o.lastY) or \
             (o.x - self.player.x == o.lastX - self.player.lastX and
              o.y - self.player.y == o.lastY - self.player.lastY):
            if not o.ticksSettled or \
               (o.relx == relx and o.rely == rely):
              settled = True
          o.relx, o.rely = relx, rely
        if not settled:
          o.ticksSettled = 0
        else:
          o.ticksSettled += dt
          if o.ticksSettled > 0.2:
            out, lines = self.player.combine(o, force=True)
            if lines:
              self.soundLine.play()
            else:
              self.soundDrop.play()
            self.lives -= out
            self.lives += max(lines * 2 - 1, 0)
            self.lines += lines
            # Score for squares placed
            self.score += (4-out) * self.speed * 10
            # Score for lines achieved
            self.score += lines * lines * self.speed * 100
            # Score for emptying the grid
            if self.player.body.area() == 0:
              self.score += self.speed * 5000
              self.player.body.addAt(0,0)
            if self.lines > self.speed * 2:
              self.speed = int(self.lines / 2)
            if self.lives > 10:
              self.lives = 10
            if self.lives <= 0:
              # Game over
              self.unschedule(self.tick)
              self.overflow = 0
              director.scene.add(GameOverMenu(self.score), z=2000)
            else:
              self.removeObject(o)
              self.addRandomEnemy()

  def removeBullet(self, bullet):
    self.bullets.remove(bullet)
    self.remove(bullet)

  def removeObject(self, object):
    self.objects.remove(object)
    self.remove(object)

class GameOverMenu(cocos.menu.Menu):
  def __init__(self, score):
    super(GameOverMenu, self).__init__()
    from cocos.menu import MenuItem
    items = [
        MenuItem("Game over!", lambda: director.scene.end()),
        MenuItem("Your score: %s" % format_number(score), None),
    ]
    self.create_menu(items)

  def _select_item(self, new_idx):
    pass

  def on_quit(self):
    director.scene.end()

class OverlayLayer(cocos.layer.ColorLayer):
  def __init__(self, game, scale):
    cocos.layer.ColorLayer.__init__(self, 255,0,0,0)

    self.game = game
    self.status = cocos.text.Label(position=(director.window.width-5,5), font_size=12, anchor_x='right')
    self.add(self.status)

    self.schedule(self.tick)
    self.lives = -1
    self.lifeMeter = None
    self.lm_scale = scale / 2

    self.alarmPos = 0

  def tick(self, dt):
    self.status.element.text = 'score: %s' % format_number(self.game.score)
    if self.lives != self.game.lives:
      self.lives = self.game.lives
      if self.lifeMeter:
        self.remove(self.lifeMeter)
      self.lifeMeter = cocos.cocosnode.CocosNode()
      self.lifeMeter.scale = self.lm_scale
      self.lifeMeter.x = 5
      self.lifeMeter.y = 5
      bright = (min(2 - self.lives / 5, 1), min(self.lives / 5, 1), 0)
      dim = (bright[0] / 2, bright[1] / 2, bright[0] / 4 + bright[1] / 4)
      for i in range(10):
        rgb = (i < self.lives) and bright or dim
        n = TileNode(color=rgb)
        n.x = i * 1.2
        self.lifeMeter.add(n)
      self.add(self.lifeMeter)
    if self.lives > 0:
      if self.lives < 5:
        self.alarmPos += 2 * dt * (5 - self.lives)
      elif self.alarmPos > math.pi:
        self.alarmPos = min(self.alarmPos + 10*dt, 2 * math.pi)
      else:
        self.alarmPos = max(self.alarmPos - 10*dt, 0)
      self.alarmPos %= 2 * math.pi
      self.opacity = 32 * (1 - math.cos(self.alarmPos))
    else:
      self.color = (0,0,0)
      self.opacity = 64

class Menu(cocos.menu.Menu):
  def __init__(self):
    super(Menu, self).__init__('Triest')
    from cocos.menu import MenuItem, zoom_in, zoom_out, shake
    items = [
        MenuItem("New game", lambda: self.new_game()),
        MenuItem("Quit", lambda: director.scene.end())
    ]
    self.create_menu(items)

  def new_game(self):
    scale_x = director.window.width / 64.0
    scale_y = director.window.height / 48.0
    scale = min(scale_x, scale_y)

    game = GameLayer(scale=scale)
    overlay = OverlayLayer(game.game, scale=scale)
    stars = StarsLayer(lambda _: (game.game.x, game.game.y))
    scene = cocos.scene.Scene(stars, game, overlay)
    director.push(scene)

  def on_quit(self):
    director.scene.end()

def main():
  pyglet.resource.path = ['data/sounds']
  pyglet.resource.reindex()

  sys.stdout.write("Loading music... ")
  sys.stdout.flush()
  music = pyglet.resource.media('music.ogg')
  sys.stdout.write("done\n")
  sys.stdout.flush()

  director.init(fullscreen=True)

  # Sets up blending so we get anti-aliased edges. Allegedly.
  squirtle.setup_gl()

  musicPlayer = pyglet.media.Player()
  musicPlayer.queue(music)
  #musicPlayer.eos_action = pyglet.media.Player.EOS_LOOP
  musicPlayer.loop = True
  musicPlayer.play()

  menu = Menu()
  def starsAnim():
    t = [0]
    from math import sin, cos
    def result(dt):
      t[0] += dt
      tt = t[0]
      return (5 * sin(tt) + 20 * cos(tt / 4),
              7 * sin(tt / 3) + 18 * cos(tt / 5))
    return result
  stars = StarsLayer(starsAnim())
  scene = cocos.scene.Scene(stars, menu)
  director.run(scene)

if __name__ == '__main__':
  main()
