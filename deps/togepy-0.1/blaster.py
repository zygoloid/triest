import math
import random

from pyglet import clock, window, event, font
from pyglet.window import key
from pyglet.gl import *

from togepy import gfx, draw


def wrap(obj):
    obj.x = (512 + obj.x) % 512
    obj.y = (512 + obj.y) % 512


class BlasterModel(event.EventDispatcher):
    event_types = ["on_asteroid_destroyed", "on_ship_destroyed"]

    def __init__(self):
        self.ship = Ship(self)
        self.bullets = []
        self.asteroids = []
        self.score = 0

    def new_random_asteroid(self):
        if random.random() > 0.5:
            x, y = random.uniform(0, 512), 0
        else:
            x, y = 0, random.uniform(0, 512)
        angle = random.uniform(0, 360)
        self.new_asteroid(x, y, angle)
        
    def new_asteroid(self, x, y, angle, radius=20):
        self.asteroids.append(Asteroid(self, x, y, angle, radius))

    def tick(self):
        if not self.asteroids:
            for i in xrange(5):
                self.new_random_asteroid()
        self.ship.tick()
        for b in self.bullets[:]:
            b.tick()
            if b.dead:
                self.bullets.remove(b)
        for a in self.asteroids[:]:
            a.tick()
            if a.dead:
                self.asteroids.remove(a)

class BlasterController(object):

    def __init__(self, model):
        self.model = model
        self.model.push_handlers(self)

        self.window = window.Window(512, 512)
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)

        self.fps = clock.ClockDisplay(color=(1, 0, 0, 1))
        self.font = font.load(None, 24, bold=True)
        self.bigfont = font.load(None, 48, bold=True)
        self.score_view = font.Text(self.font,
                                    "Score: 0",
                                    x=16,
                                    y=496,
                                    halign='left',
                                    valign='top',
                                    color=(1,0,0,.8))
        self.game_over = font.Text(self.bigfont, 
                                   "GAME OVER", 
                                   x=256, 
                                   y=256, 
                                   halign='center', 
                                   valign='center',
                                   color=(1,0,0,.8))
        # View objects
        self.ship_view = ShipView(self.model.ship)
        self.bullet_views = gfx.ViewObjectBag(self.model.bullets, BulletView)
        self.asteroid_views = gfx.ViewObjectBag(self.model.asteroids,
                AsteroidView)
        self.dust = gfx.ParticleSystem(DustParticle)
        self.exhaust = gfx.ParticleSystem(ExhaustParticle)
        self.stars = gfx.SlowParticleSystem(Star)
        
        # Generate stars
        for i in range(20):
            dist = random.uniform(5, 20)
            x = random.uniform(0, 512)
            y = random.uniform(0, 512)
            angle = random.uniform(0, 72)
            self.stars.new_particle(x=x, y=y, vx=-dist * 0.05, vy=0,
                    radius=dist, angle=angle)
        
        # Setup GL
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glClearColor(0, 0, 0, 0)

    
    def run(self):
        while not self.window.has_exit:
            self.window.dispatch_events()
            clock.tick()
            self.handle_keys()
            self.model.tick()
            
            #Visual effects
            self.dust.tick()
            self.exhaust.tick()
            self.stars.tick()
            self.ship_view.tick()
            self.bullet_views.tick()
            self.asteroid_views.tick()

            self.window.clear()
            self.render()
            self.window.flip()

    def on_ship_destroyed(self, ship):
        for i in range(100):
            ox = random.gauss(0, .5)
            oy = random.gauss(0, .5)
            self.dust.new_particle(x=ship.x + ox * ship.radius,
                                   y=ship.y + oy * ship.radius,
                                   vx=ship.vx + 5 * ox,
                                   vy=ship.vy + 5 * oy,
                                   color=(1, random.uniform(0, 1), 0, 1))
            
    def on_asteroid_destroyed(self, asteroid):
        for i in range(2*asteroid.radius):
            ox = random.gauss(0, .5)
            oy = random.gauss(0, .5)
            self.dust.new_particle(x=asteroid.x + ox * asteroid.radius,
                                   y=asteroid.y + oy * asteroid.radius,
                                   vx=asteroid.vx + ox,
                                   vy=asteroid.vy + oy,
                                   color=(1, random.uniform(0, 1), 0, 1))
        self.score_view.text = "Score: %d" % (self.model.score,)                                   
    def handle_keys(self):
        self.set_firing(self.keys[key.SPACE])
        self.set_engine(self.keys[key.UP])

        if self.keys[key.LEFT]:
            self.model.ship.angle += 3
        if self.keys[key.RIGHT]:
            self.model.ship.angle -= 3

    def set_engine(self, engine_on):
        if self.model.ship.dead:
            return
        self.model.ship.engine_on = engine_on
        ship = self.model.ship
        if engine_on:
            evx = ship.vx - 10 * math.cos(math.radians(ship.angle))
            evy = ship.vy - 10 * math.sin(math.radians(ship.angle))
            for i in range(5):
                color = (1, random.uniform(0, 1), 0, 1)
                self.exhaust.new_particle(x=ship.x,
                                          y=ship.y,
                                          vx=evx + random.gauss(0, 1),
                                          vy=evy + random.gauss(0, 1),
                                          color=color)

    def set_firing(self, firing):
        self.model.ship.firing = firing

    @gfx.motion_blur
    def render(self):
        self.stars.draw()
        self.bullet_views.draw()
        self.asteroid_views.draw()
        self.dust.draw()
        self.exhaust.draw()
        if self.model.ship.dead:
            self.game_over.draw()
        else:
            self.ship_view.draw()
        self.score_view.draw()
        self.fps.draw()


class ExhaustParticle(gfx.Particle):
    defaultcolor = (1, .5, 0, 1)
    size=2

    def tick(self):
        self.vx *= .95
        self.vy *= .95
        if self.vx ** 2 + self.vy ** 2 < 4:
            self.dead = True
        self.x += self.vx
        self.y += self.vy
        wrap(self)


class DustParticle(gfx.Particle):
    defaultcolor = (1, 1, 1, 1)
    size=2

    def tick(self):
        self.vx *= .99
        self.vy *= .99
        if self.vx ** 2 + self.vy ** 2 < 4:
            self.dead = True
        self.x += self.vx
        self.y += self.vy
        wrap(self)
        
class Asteroid(object):

    def __init__(self, model, x, y, angle, radius=20, speed=2):
        self.model = model
        self.x = x
        self.y = y
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))
        self.radius = radius
        self.angle = angle
        self.dead = False
    
    def tick(self):
        self.x += self.vx
        self.y += self.vy
        for b in self.model.bullets:
            if not b.dead and (b.x - self.x) ** 2 + (b.y - self.y) ** 2 <= self.radius ** 2:
                self.model.score += 10 * self.radius
                b.dead = True
                self.dead = True
                self.model.dispatch_event("on_asteroid_destroyed", self)
                if self.radius > 5:
                    self.model.new_asteroid(self.x, self.y, self.angle + 60,
                        self.radius/2)
                    self.model.new_asteroid(self.x, self.y, self.angle - 60,
                        self.radius/2)
        wrap(self)


class AsteroidView(gfx.GLViewObject2D):
    color = (1, 1, 1, 1)
    @gfx.gl_compiled_method
    def draw_aligned(self):
        angles = [math.pi * .25 * n for n in range(8)]
        points = [(self.radius * math.cos(theta) + random.gauss(0,2), 
                   self.radius * math.sin(theta) + random.gauss(0,2)) for theta in angles]
        draw.polygon(self.color, points, width=1)


class Bullet(object):

    def __init__(self, x, y, angle, speed=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))
        self.age = 0
        self.dead = False
        
    def tick(self):
        self.x += self.vx
        self.y += self.vy
        if self.age >= 40:
            self.dead = True
        self.age +=1
        wrap(self)


class BulletView(gfx.GLViewObject2D):
    color=(0, 1, 0, 1)

    @gfx.gl_compiled_method
    def draw_aligned(self):
        draw.line(self.color, (0, 0), (10, 0), width=2)


class Ship(object):

    def __init__(self, model, x=256, y=256):
        self.model = model
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.angle = 0
        self.engine_on = False
        self.firing = False
        self.firetimer = 0
        self.dead = False
        self.radius = 10

    def tick(self):
        if self.dead:
            return
        self.vx *= .97
        self.vy *= .97
        if self.engine_on:
            self.vx += math.cos(math.radians(self.angle)) * .2
            self.vy += math.sin(math.radians(self.angle)) * .2
            self.engine_on = False
        self.x += self.vx
        self.y += self.vy
        wrap(self)
        
        if self.firing and self.firetimer <= 0:
            self.model.bullets.append(Bullet(self.x, self.y, self.angle))
            self.firetimer = 5
        self.firetimer -= 1    
        
        for a in self.model.asteroids:
            if not a.dead and (self.x - a.x) ** 2 + (self.y - a.y) ** 2 <= (a.radius + self.radius) ** 2:
                self.dead = True
                self.model.dispatch_event("on_ship_destroyed", self)

class ShipView(gfx.GLViewObject2D):
    points = [[(10, 0), (-10, 5), (-10, -5)],
              [(5, 5), (0, 10), (-10, 5)],
              [(5, -5), (0, -10), (-10, -5)]]
    color = (0, .5, 1, 1)

    @gfx.gl_compiled_method
    def draw_aligned(self):
        for loop in self.points:
            draw.polygon(self.color, loop, width=1)


class Star(gfx.Particle2D):
    defaultcolor=(1, 1, 0, 1)

    def tick(self):
        self.x += self.vx
        self.y += self.vy
        wrap(self)

    @gfx.gl_compiled_method
    def draw_aligned(self):
        draw.regular_polygon(self.color, (0,0), self.radius, 5, 2, width=1)


#import cProfile
#cProfile.run("""
BlasterController(BlasterModel()).run()
#""")
