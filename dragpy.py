import matplotlib.patches as patches
import matplotlib.lines as lines
import warnings

class _DragObj:
    def __init__(self, ax):
        self.parentcanvas = ax.figure.canvas
        self.parentax = ax

        self.myobj.set_url('dragobj')
        self.clickpress = self.parentcanvas.mpl_connect('button_press_event', self.on_click)  # Execute on mouse click
        self.clicked = False

    def on_click(self, event):
        # Executed on mouse click
        if event.inaxes != self.parentax: return  # See if the mouse is over the parent axes object

        # Check for overlaps, make sure we only fire for one object per click
        timetomove = self.shouldthismove(event)
        if not timetomove: return

        self.mousemotion = self.parentcanvas.mpl_connect('motion_notify_event', self.on_motion)
        self.clickrelease = self.parentcanvas.mpl_connect('button_release_event', self.on_release)
        
        # Add extra event data for patches to prevent jumping on drag
        self.clickx = event.xdata  
        self.clicky = event.ydata
        
        self.clicked = True
    
    def shouldthismove(self, event):
        # Check to see if this object has been clicked on
        contains, attrs = self.myobj.contains(event)
        if not contains:
            # We haven't been clicked
            timetomove = False
        else:
            # See how many draggable objects contain this event
            firingobjs = []
            for child in self.parentax.get_children():
                if child.get_url() == 'dragobj':
                    contains, attrs = child.contains(event)
                    if contains:
                        firingobjs.append(child)
            
            # Assume the last child object is the topmost rendered object, only move if we're it
            if firingobjs[-1] is self.myobj:
                timetomove = True
            else:
                timetomove = False

        return timetomove

    def on_release(self, event):
        self.clicked = False
        self.disconnect()

    def disconnect(self):
        self.parentcanvas.mpl_disconnect(self.mousemotion)
        self.parentcanvas.mpl_disconnect(self.clickrelease)
        self.parentcanvas.draw()

    def stopdrag(self):
        self.myobj.set_url('')
        self.parentcanvas.mpl_disconnect(self.clickpress)


class _DragLine(_DragObj):
    def __init__(self, ax):
        super().__init__(ax)

    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked:
            # See if we've clicked yet
            return
        if event.inaxes != self.parentax:
            # See if we're moving over the parent axes object
            return

        if self.orientation == 'vertical':
            if self.snapto:
                xcoord = draglimiter(self.snapto.get_xdata(), event.xdata)
            else:
                xcoord = event.xdata
            self.myobj.set_xdata(listmult([1, 1], xcoord))
            self.myobj.set_ydata(self.parentax.get_ylim())
        elif self.orientation == 'horizontal':
            if self.snapto:
                ycoord = draglimiter(self.snapto.get_ydata(), event.ydata)
            else:
                ycoord = event.ydata
            self.myobj.set_xdata(self.parentax.get_xlim())
            self.myobj.set_ydata(listmult([1, 1], ycoord))

        self.parentcanvas.draw()


class _DragPatch(_DragObj):
    def __init__(self, ax, xy):
        super().__init__(ax)
    
        self.oldxy = xy  # Store for motion callback

    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked:
             # See if we've clicked yet
            return
        if event.inaxes != self.parentax: 
             # See if we're moving over the parent axes object
            return

        oldx, oldy = self.oldxy
        dx = event.xdata - self.clickx
        dy = event.ydata - self.clicky
        newxy = [oldx + dx, oldy + dy]

        # LBYL for patches with centers (e.g. ellipse) vs. xy location (e.g. rectangle)
        try:
            # Wedge has to be a special snowflake and update doesn't work for basically everything else
            self.myobj.update({'center': newxy})
        except AttributeError:
            if hasattr(self.myobj, 'center'):
                self.myobj.center = newxy
            else:
                self.myobj.xy = newxy

        self.parentcanvas.draw()

    def on_release(self, event):
        self.clicked = False
        
        # LBYL for patches with centers (e.g. ellipse) vs. xy location (e.g. rectangle)
        if hasattr(self.myobj, 'center'):
            self.oldxy = self.myobj.center
        else:
            self.oldxy = self.myobj.xy

        self.disconnect()
    

class DragLine2D(_DragLine):
    def __init__(self, ax, position, orientation='vertical', snapto=None, **kwargs):
        self.orientation = orientation.lower()
        if self.orientation == 'horizontal':
            self.myobj = lines.Line2D(ax.get_xlim(), listmult([1, 1], position), **kwargs)
        elif self.orientation == 'vertical':
            self.myobj = lines.Line2D(listmult([1, 1], position), ax.get_ylim(), **kwargs)
        else:
            raise ValueError(f"Unsupported orientation string: '{orientation}'")

        ax.add_artist(self.myobj)
        super().__init__(ax)

        # Check to make sure snapto is a valid lineseries (or None) by checking 
        # to see if it has valid x data
        try:
            snapto.get_xdata()
        except AttributeError:
            if snapto is not None:
                warnings.warn(f"Unknown snapto lineseries: '{snapto}'\nIgnoring...")
                snapto = None

        self.snapto = snapto

    def get_xydata(self):
        """Return the xy data as a Nx2 numpy array."""
        return self.myobj.get_xydata()
    
    def get_xdata(self, orig=True):
        """Return the xdata.

        If orig is True, return the original data, else the processed data.
        """
        return self.myobj.get_xdata(orig)
    
    def get_ydata(self, orig=True):
        """Return the ydata.

        If orig is True, return the original data, else the processed data.
        """
        return self.myobj.get_ydata(orig)


class DragEllipse(_DragPatch):
    def __init__(self, ax, xy, width, height, angle=0.0, **kwargs):
        self.myobj = patches.Ellipse(xy, width, height, angle, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, xy)


class DragCircle(DragEllipse):
    def __init__(self, ax, xy, radius=5, **kwargs):
        self.myobj = patches.Circle(xy, radius, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, xy)


class DragRectangle(_DragPatch):
    def __init__(self, ax, xy, width, height, angle=0.0, **kwargs):
        self.myobj = patches.Rectangle(xy, width, height, angle, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, xy)


class FixedWindow(_DragPatch):
    def __init__(self, ax, primaryedge, windowsize, orientation='vertical', snapto=None,
                 alpha=0.25, facecolor='limegreen', edgecolor='green', **kwargs):
        self.orientation = orientation.lower()
        if self.orientation == 'vertical':
            axesdimension = get_axesextent(ax)[1]  # Axes height
            xy = (primaryedge, ax.get_ylim()[0])
        elif self.orientation == 'horizontal':
            axesdimension = get_axesextent(ax)[0]  # Axes width
            xy = (ax.get_xlim()[0], primaryedge)
        else:
            raise ValueError(f"Unsupported orientation string: '{orientation}'")

        self.myobj = patches.Rectangle(xy, windowsize, axesdimension, alpha=alpha,
                                       facecolor=facecolor, edgecolor=edgecolor, **kwargs)
        ax.add_artist(self.myobj)
        
        super().__init__(ax, xy)

        # Check to make sure snapto is a valid lineseries (or None) by checking 
        # to see if it has valid x data
        try:
            snapto.get_xdata()
        except AttributeError:
            if snapto is not None:
                warnings.warn(f"Unknown snapto lineseries: '{snapto}'\nIgnoring...")
                snapto = None

        self.snapto = snapto
    
    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked:
             # See if we've clicked yet
            return
        if event.inaxes != self.parentax: 
             # See if we're moving over the parent axes object
            return
        
        oldx, oldy = self.oldxy
        if self.orientation == 'horizontal':
            dy = event.ydata - self.clicky
            newxy = (oldx, oldy + dy)
        elif self.orientation == 'vertical':
            dx = event.xdata - self.clickx
            newxy = (oldx + dx, oldy)

        self.myobj.xy = newxy

        self.parentcanvas.draw()


class Window:
    def __init__(self, ax, primaryedge, windowstartsize, orientation='vertical', snapto=None, 
                 alpha=0.25, facecolor='limegreen', edgecolor='green'):
        # Initialize window edges
        # DragLine2D call will take care of orientation validation
        self.edges = []
        self.edges.append(DragLine2D(ax, primaryedge, orientation, snapto, color=edgecolor))
        self.edges.append(DragLine2D(ax, (primaryedge+windowstartsize), orientation, snapto, color=edgecolor))

        # Add spanning rectangle
        xy, width, height = self.spanpatchdims(*self.edges)
        self.spanpatch = patches.Rectangle(xy, width, height, color=facecolor, alpha=alpha)
        ax.add_artist(self.spanpatch)

    @staticmethod
    def spanpatchdims(edge1, edge2):
        # Find leftmost, rightmost points
        minx = min(edge1.get_xdata() + edge2.get_xdata())  # Joining the two lists, not adding them
        maxx = max(edge1.get_xdata() + edge2.get_xdata())  # Joining the two lists, not adding them

        # Find bottommostm, topmost points
        miny = min(edge1.get_ydata() + edge2.get_ydata())  # Joining the two lists, not adding them
        maxy = max(edge1.get_ydata() + edge2.get_ydata())  # Joining the two lists, not adding them

        xy = (minx, miny)
        width = abs(maxx - minx)
        height = abs(maxy - miny)

        return xy, width, height


class DragArc(_DragPatch):
    def __init__(self, ax, xy, width, height, angle=0, theta1=0, theta2=360.00, **kwargs):
        self.myobj = patches.Arc(xy, width, height, angle, theta1, theta2, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, xy)


class DragWedge(_DragPatch):
    def __init__(self, ax, center, r, theta1, theta2, width=None, **kwargs):
        self.myobj = patches.Wedge(center, r, theta1, theta2, width, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, center)


class DragRegularPolygon(_DragPatch):
    def __init__(self, ax, xy, numVertices, radius=5, orientation=0, **kwargs):
        self.myobj = patches.RegularPolygon(xy, numVertices, radius, orientation, **kwargs)
        ax.add_artist(self.myobj)

        super().__init__(ax, xy)

def get_axesextent(ax):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    xextent = xlim[1] - xlim[0]
    yextent = ylim[1] - ylim[0]

    return (xextent, yextent)


def listmult(A, c):
    return [i * c for i in A]


def draglimiter(dataseries, querypoint):
    minvalue = min(dataseries)
    maxvalue = max(dataseries)
    if querypoint > maxvalue:
        return maxvalue
    elif querypoint < minvalue:
        return minvalue
    else:
        return querypoint
