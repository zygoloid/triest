"""Various graphical odds and ends, including particle systems and 
post-processing effects"""

from pyglet import image, gl

__all__ = ["ViewObjectBag", "GLViewObject2D", "Particle", "Particle2D", 
           "ParticleSystem", "SlowParticleSystem", "DisplayList", 
           "gl_compiled_function", "gl_compiled_method", "vector_glow", 
           "motion_blur"]

class ViewObjectBag(object):
    """A managed collection of view objects."""
    def __init__(self, targets, viewerclass):
        """Initialise a ViewObjectBag, with a given collection of model objects
        and a class of view object.
        
        :Parameters:
            `targets` : iterable
                An iterable of model objects which are to be handled.
            `viewerclass` : class
                The class of view object with which to handle the model objects.
        """
        
        self.targets = targets
        self.viewers = dict() 
        self.viewerclass = viewerclass
    
    def report(self):
        """Return a string describing the contents of a ViewObjectBag"""
        return "%s: %d" % (self.viewerclass.__name__, len(self.viewers))
        
    def tick(self):
        """Update the list of view objects, creating and destroying objects as
        necessary. Tick each of the view objects within the bag."""
        
        for target in self.targets:
            if target not in self.viewers:
                self.viewers[target] = self.viewerclass(target)
        for target, viewer in self.viewers.items():
            viewer.tick()
            if viewer.dead:
                del self.viewers[target]

    def draw(self):
        """Render each of the included view items"""
        for viewer in self.viewers.values():
            viewer.draw()   
                         
class GLViewObject2D(object):
    """A view object representing a 2d object with possibly dynamic position and
    angle"""
    axis = (0, 0, 1)

    def __init__(self, target):
        """Initialise a new GLViewObject2D for a given model object."""
        self.target = target
        self.dead = False
    
    def __getattr__(self, name):
        return getattr(self.target, name)

    def report(self):
        """Return a text description of a GLViewObject2D"""
        return "%s: (%f, %f, %f)" % (self.__name__, self.x, self.y, self.angle)
        
    def tick(self):
        """Update the view object"""
        if self.target.dead:
            #self.target = None
            self.dead = True

    def draw(self):
        """Render the view object"""
        gl.glPushMatrix()
        gl.glTranslatef(self.x,self.y,0)
        gl.glRotatef(self.angle, *self.axis)
        self.draw_aligned()
        gl.glPopMatrix()

    def draw_aligned(self):
        """Draw the object at the origin, facing along the positive x-axis. To
        be overridden by subclasses."""
        pass

class Particle(object):
    """A point particle, as handled by a particle system. Should never be 
    instantiated directly."""
    
    defaultcolor = (1, 1, 1, 1)
    """The default color for particles of this class. Defaults to white."""
    
    size = 1
    """The default point size for particles of this class. Defaults to one."""
    
    def __init__(self, particle_system, slot, **kwargs):
        """Instantiates a particle. Any keyword arguments are set as attributes 
        on the particle. For internal use only."""
        self.particle_system = particle_system
        self.slot = slot
        self.color = self.defaultcolor
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.dead = False

    def _get_color(self):
        return tuple(self.particle_system.data[self.slot * 10:self.slot * 10+4])

    def _set_color(self, value):
        self.particle_system.data[self.slot * 10:self.slot * 10+4] = value

    color = property(_get_color, _set_color)

    def _get_x(self):
        return self.particle_system.data[self.slot * 10 + 7]

    def _set_x(self, value):
        self.particle_system.data[self.slot * 10 + 7] = value

    x = property(_get_x, _set_x)

    def _get_y(self):
        return self.particle_system.data[self.slot * 10 + 8]

    def _set_y(self, value):
        self.particle_system.data[self.slot * 10 + 8] = value

    y = property(_get_y, _set_y)

    def _get_z(self):
        return self.particle_system.data[self.slot * 10 + 9]

    def _set_z(self, value):
        self.particle_system.data[self.slot * 10 + 9] = value

    z = property(_get_z, _set_z)

    def tick(self):
        """Update this particle. To be overridden by subclasses. Should set
        self.dead to indicate the particle is no longer in use."""
        pass


class Particle2D(Particle):
    """A 2D non-point particle, as handled by a SlowParticleSystem. Should never
    be instantiated directly."""
    
    angle = 0
    axis = (0, 0, 1)

    def draw(self):
        """Render the particle."""
        gl.glPushMatrix()
        gl.glTranslatef(self.x, self.y, self.z)
        gl.glRotatef(self.angle, *self.axis)
        self.draw_aligned()
        gl.glPopMatrix()

    def draw_aligned(self):
        """Draw the particle at the origin, facing along the positive x-axis. To
        be overridden by subclasses."""
        pass

class ParticleSystem(object):
    """A system of point particles."""
    
    def __init__(self, particle_class=Particle, slots=64):
        """Initialise a particle system.
        
        :Parameters:
            `particle_class` : class
                The subclass of Particle to use for this system.
            `slots` : int
                The initial number of slots to allocate for particles. Defaults
                to 64.
        """
        
        self.num_slots = slots
        self.data = (gl.GLfloat * (slots * 10))()
        self.available_slots = list(range(slots))
        self.dirty_indices = True
        self.live_particles = []
        self.particle_class = particle_class

    def new_particle(self, *args, **kwargs):
        """Add a new particle to the system. Any arguments are passed to the 
        particle constructor."""
        
        if not self.available_slots:
            self._expand()
        p = self.particle_class(self, self.available_slots.pop(), *args, **kwargs)
        self.live_particles.append(p)
        self.dirty_indices = True

    def delete_particle(self, particle):
        """Remove a particle from the system.
        
            :Parameters:
                `particle` : Particle
                    The particle to be removed.
        """
        self.live_particles.remove(particle)
        self.available_slots.append(particle.slot)
        self.dirty_indices = True

    def _expand(self):
        self.available_slots.extend(list(range(self.num_slots, self.num_slots*2)))
        self.num_slots *= 2
        self.data = (gl.GLfloat * (self.num_slots * 10))(*self.data)

    def draw(self):
        """Render the particle system."""
        
        if not self.live_particles:
            return
        if self.dirty_indices:
            indices = [p.slot for p in self.live_particles if not p.dead]
            self.indices = (gl.GLuint * len(indices))(*indices)
            self.dirty_indices = False
        gl.glPointSize(self.particle_class.size)
        gl.glInterleavedArrays(gl.GL_C4F_N3F_V3F, 0, self.data)
        gl.glDrawElements(gl.GL_POINTS, len(self.indices), gl.GL_UNSIGNED_INT, self.indices)

    def tick(self):
        """Update the particle system."""
        deadlist = []
        for p in self.live_particles[:]:
            p.tick()
            if p.dead:
                self.delete_particle(p)

class SlowParticleSystem(ParticleSystem):
    """A particle system with individually drawn particles."""
    
    def draw(self):
        """Render the particle system."""
        for p in self.live_particles:
            p.draw()

class DisplayList(object):
    """A wrapper class for GL display lists. When called, renders its contents.
    """
    
    def __init__(self):
        """Create a new display list"""
        self.id = gl.glGenLists(1)
    
    def begin(self):
        """Begin compilation of a display list."""
        gl.glNewList(self.id, gl.GL_COMPILE)
    
    def end(self):
        """End compilation of a display list."""
        gl.glEndList()
    
    def __call__(self):
        gl.glCallList(self.id)
        
    def __del__(self):
        if gl.gl_info.have_context():
            try:
                gl.glDeleteLists(self.id, 1)
            except:
                pass

#Decorators, etc.

def gl_compiled_function(func):
    """Function decorator which thunks function calls as GL display lists. Be
    warned that these are never freed."""
    disp_lists = dict()
    def compiled_func(*args, **kwargs):
        argtuple = (args, tuple(kwargs.items()))
        if argtuple not in disp_lists:
            lst = DisplayList()
            lst.begin()
            func(*args, **kwargs)
            lst.end()
            disp_lists[argtuple] = lst
        disp_lists[argtuple]()
        if len(disp_lists) > 1000:
            print("Warning, %s recompiled too often [%s, %s]" % (func, args, kwargs))

    return compiled_func

def gl_compiled_method(func):
    """Method decorator which thunks method calls as GL display lists. These are
    freed upon garbage collection of the relevant object instance."""
    def compiled_method(self, *args, **kwargs):
        if not hasattr(self, "compiled_disp_lists"):
            self.compiled_disp_lists = dict()
        argtuple = (args, tuple(kwargs.items()))
        if argtuple not in self.compiled_disp_lists:
            lst = DisplayList()
            lst.begin()
            func(self, *args, **kwargs)
            lst.end()
            self.compiled_disp_lists[argtuple] = lst
        self.compiled_disp_lists[argtuple]()
        if len(self.compiled_disp_lists) > 1000:
            print("Warning, %s recompiled too often [%s, %s]" % (func, args, kwargs))
    return compiled_method
    
def motion_blur(func):
    """Function decorator implementing a motion blur post-processing effect. To
    be applied to the main rendering function."""
    texes = []
    num_texes = 10
    buffers = []
    def multi_draw(*args, **kwargs):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glClearColor(0, 0, 0, 0)
        gl.glColor4f(1,1,1,1)
    
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        if not buffers:
            buffers.append(image.get_buffer_manager())
        x, y, w, h = buffers[0].get_viewport()

        #Draw lowres version
        gl.glViewport(0,0,256,256)
        func(*args, **kwargs)
        texes.append(buffers[0].get_color_buffer().texture)
        if len(texes) > num_texes:
            texes.pop(0)
            
        #Lay down copies of lowres version
        gl.glViewport(x,y,w,h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if texes:
            alphas = range(1,len(texes)+1)
            alphas = [float(f)/sum(alphas) for f in alphas]
            for tex, alpha in zip(texes, alphas):
                gl.glBindTexture(tex.target, tex.id)
            
                gl.glEnable(gl.GL_TEXTURE_2D)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                
                gl.glColor4f(1,1,1,alpha)
                gl.glBegin(gl.GL_QUADS)
                gl.glTexCoord2f(0,0)
                gl.glVertex3f(0,0,-.5)
                gl.glTexCoord2f(1,0)
                gl.glVertex3f(w,0,-.5)
                gl.glTexCoord2f(1,1)
                gl.glVertex3f(w,h,-.5)
                gl.glTexCoord2f(0,1)
                gl.glVertex3f(0,h,-.5)
                gl.glEnd()
                gl.glDisable(gl.GL_TEXTURE_2D)
            
        #Draw real thing
        gl.glColor4f(1,1,1,1)
        func(*args, **kwargs)
    return multi_draw
   
def vector_glow(func):
    """Function decorator implementing a 'vector glow' post-processing effect.
    To be applied to the main rendering function."""
    
    disp_list = []
    buffers = []
    ctex = [None]

    def multi_draw(*args, **kwargs):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glClearColor(0, 0, 0, 0)
        gl.glColor4f(1,1,1,1)
    
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        if not buffers:
            buffers.append(image.get_buffer_manager())
        x, y, w, h = buffers[0].get_viewport()

        #Draw lowres version
        gl.glViewport(0,0,256,256)
        func(*args, **kwargs)
        ctex[0] = buffers[0].get_color_buffer().texture

        #Lay down copies of lowres version
        gl.glViewport(x,y,w,h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindTexture(ctex[0].target, ctex[0].id)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        if not disp_list:
            disp_list.append(gl.glGenLists(1))
            gl.glNewList(disp_list[0], gl.GL_COMPILE)
            for u in range(-3,4,3):
                for v in range(-3,4,3):
                    gl.glColor4f(1,1,1,(20.0 - u **2 - v ** 2) / 72)
                    gl.glBegin(gl.GL_QUADS)
                    gl.glTexCoord2f(0,0)
                    gl.glVertex3f(u,v,-.5)
                    gl.glTexCoord2f(1,0)
                    gl.glVertex3f(u+w,v,-.5)
                    gl.glTexCoord2f(1,1)
                    gl.glVertex3f(u+w,v+h,-.5)
                    gl.glTexCoord2f(0,1)
                    gl.glVertex3f(u,v+h,-.5)
                    gl.glEnd()
            gl.glEndList()
        gl.glCallList(disp_list[0])
        gl.glDisable(gl.GL_TEXTURE_2D)

        #Draw real thing
        gl.glColor4f(1,1,1,1)
        func(*args, **kwargs)

    return multi_draw
