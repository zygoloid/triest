"""Basic AI routines, such as path-finding, etc"""

__docformat__ = 'restructuredtext'

import heapq

constant_one = lambda x,y: 1 
constant_zero = lambda x,y: 0

def find_path(start, end, neighbourhood, dist=constant_one, 
              heuristic=constant_zero):
    """Simple A-* implementation, with configurable heuristic and distance 
       functions.
    
    :Parameters:
        `start` : node
            An opaque object representing the start node.
        `end` : node
            An opaque object representing the end node.
        `neighbourhood` : function
            A function which, given a node, returns an iterable of nodes which 
            are directly connected to it.
        `dist` : function
            A function which, given two directly connected nodes, returns the
            distance between them. Defaults to a constant 1.
        `heuristic` : function
            A function which, given two nodes, estimates the distance between
            them. This should be an admissible heuristic, i.e. it should never
            over-estimate. Defaults to a constant 0.
    """ 
    initialpath = [start]
    solutions = [(heuristic(start, end), 0, initialpath)]
    ignore = set()
    while solutions:
        nothing, olddist, route = heapq.heappop(solutions)
        last = route[-1]
        if last not in ignore:
            if last == end:
                return route
            ignore.add(last)
            new = neighbourhood(last)
            for node in new:
                if node in ignore:
                    continue
                path = route + [node]
                newdist = olddist + dist(last, node)
                heapq.heappush(solutions, (heuristic(node, end) + newdist, 
                                           newdist, path))
    return None