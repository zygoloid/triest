"""Simple 2d graphical primitives, modeled after pygame.draw"""

__docformat__ = 'restructuredtext'

import math
from pyglet import gl

__all__ = ["rect", "polygon", "circle", "ellipse", "arc", "line", "lines",
           "aaline", "aalines"]


def _set_gl_color(color):
    """Convenience function for setting the GL color to a 3- or 4-tuple."""
    if len(color) == 3:
        gl.glColor3f(*color)
    if len(color) == 4:
        gl.glColor4f(*color)


def rect(color, corner, size, width=0):
    """Draw a rectangle

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `corner` : tuple
            The co-ordinates of the top-left corner of the rectangle
        `size` : tuple
            A tuple of (width, height) for the rectangle
        `width` : float
            The line width for the rectangle. If zero, rectangle is filled.
            Defaults to zero.

    """
    _set_gl_color(color)
    if width:
        gl.glLineWidth(width)
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(*corner)
    gl.glVertex2f(corner[0], corner[1] + size[1])
    gl.glVertex2f(corner[0] + size[0], corner[1] + size[1])
    gl.glVertex2f(corner[0] + size[0], corner[1])
    gl.glEnd()


def polygon(color, pointlist, width=0):
    """Draw a closed polygon

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `pointlist` : list
            An list of (x,y) tuples for vertices of the polygon
        `width` : float
            The line width for the polygon. If zero, polygon is filled.
            Defaults to zero.

    """
    _set_gl_color(color)
    if width:
        gl.glLineWidth(width)
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_POLYGON)
    for p in pointlist:
        gl.glVertex2f(*p)
    gl.glEnd()

def regular_polygon(color, center, radius, points, orbits=1, width=0):
    """Draw a regular polygon
    
    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `center` : tuple
            The co-ordinates of the center of the polygon
        `radius` : float
            The circumradius of the polygon
        `points` : int
            The number of vertices of the polygon
        `orbits` : int
            The number of times the polygon repeats back on itself. Values
            greater than one yield star shapes. Defaults to one.
        `width` : float
            The line width for the polygon. If zero, polygon is filled.
            Defaults to zero.
    """
    theta = (2 * math.pi * orbits)/points
    pointlist = [(center[0] + radius * math.cos(n * theta), 
                  center[1] + radius * math.sin(n * theta)) 
                  for n in range(points)]
    polygon(color, pointlist, width)

def circle(color, center, radius, width=0, npoints=24):
    """Draw a circle

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `center` : tuple
            The co-ordinates of the center of the circle
        `radius` : float
            The radius of the circle
        `width` : float
            The line width for the circle. If zero, circle is filled.
            Defaults to zero.
        `npoints` : int
            The number of vertices on the circumference of the circle.
            Defaults to 24.

    """
    _set_gl_color(color)
    if width:
        gl.glLineWidth(width)
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_POLYGON)
    for i in xrange(npoints):
        theta = i * math.pi * 2 / npoints
        gl.glVertex2f(center[0] + radius * math.cos(theta),
                   center[1] + radius * math.sin(theta))
    gl.glEnd()


def ellipse(color, corner, size, width=0, npoints=24):
    """Draw an axis-aligned ellipse

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `corner` : tuple
            The co-ordinates of the top-left corner of the ellipse's
            enclosing rectangle
        `size` : tuple
            A tuple of (width, height) for the ellipse
        `width` : float
            The line width for the ellipse. If zero, ellipse is filled.
            Defaults to zero.
        `npoints` : int
            The number of vertices on the circumference of the ellipse.
            Defaults to 24.

    """
    _set_gl_color(color)
    center = (corner[0] + .5 * size[0], corner[1] + .5 * size[1])
    if width:
        gl.glLineWidth(width)
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_POLYGON)
    for i in xrange(npoints):
        theta = i * math.pi * 2 / npoints
        gl.glVertex2f(center[0] + .5 * size[0] * math.cos(theta),
                   center[1] + .5 * size[1] * math.sin(theta))
    gl.glEnd()


def arc(color, corner, size, start_angle, stop_angle, width=1, npoints=24):
    """Draw an arc of an axis-aligned ellipse

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `corner` : tuple
            The co-ordinates of the top-left corner of the ellipse's
            enclosing rectangle
        `size` : tuple
            A tuple of (width, height) for the ellipse
        `start_angle` : float
            The start angle of the arc, in radians, counterclockwise from the
            positive x-axis
        `stop_angle` : float
            The start angle of the arc, in radians, counterclockwise from the
            positive x-axis
        `width` : float
            The line width for the ellipse. Defaults to 1.0
        `npoints` : int
            The number of vertices on the circumference of the ellipse.
            Defaults to 24.

    """
    _set_gl_color(color)
    center = (corner[0] + .5 * size[0], corner[1] + .5 * size[1])
    gl.glLineWidth(width)
    gl.glBegin(gl.GL_LINE_STRIP)
    for i in range(npoints + 1):
        theta = start_angle + (float(i * (stop_angle - start_angle)) / npoints)
        gl.glVertex2f(center[0] + .5 * size[0] * math.cos(theta),
                   center[1] + .5 * size[1] * math.sin(theta))
    gl.glEnd()


def line(color, start, end, width=1, endcolor=None):
    """Draw a line segment

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `start` : tuple
            The co-ordinates of the start point of the line segment
        `end` : tuple
            The co-ordinates of the end point of the line segment
        `width` : float
            The line width. Defaults to 1.0

    """
    _set_gl_color(color)
    gl.glLineWidth(width)
    gl.glBegin(gl.GL_LINES)
    gl.glVertex2f(*start)
    if endcolor: _set_gl_color(endcolor)
    gl.glVertex2f(*end)
    gl.glEnd()

def lines(color, closed, pointlist, width=1):
    """Draw a sequence of linked line segments

    :Parameters:
        `color` : tuple
            The colour to use, as a 3- or 4-tuple of floats
        `closed` : bool
            If true, the start and end points are joined by an extra segment.
        `pointlist` : list
            A list of (x,y) tuples for the endpoints of the segments.
        `width` : float
            The line width. Defaults to 1.0

    """
    _set_gl_color(color)
    gl.glLineWidth(width)
    if closed:
        gl.glBegin(gl.GL_LINE_LOOP)
    else:
        gl.glBegin(gl.GL_LINE_STRIP)
    for p in pointlist:
        gl.glVertex2f(*p)
    gl.glEnd()


aaline = line
aalines = lines
