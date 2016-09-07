import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class DragObj:
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
            # See how many draggable objects contains this event
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
        self.disconnect

    def disconnect(self):
        self.parentcanvas.mpl_disconnect(self.mousemotion)
        self.parentcanvas.mpl_disconnect(self.clickrelease)
        self.parentcanvas.draw()

    def stopdrag(self):
        self.myobj.set_url('')
        self.parentcanvas.mpl_disconnect(self.clickpress)


class DragLine(DragObj):
    def __init__(self, orientation, ax, position, **kwargs):
        if orientation.lower() == 'horizontal':
            self.myobj, = ax.plot(ax.get_xlim(), np.array([1, 1])*position, **kwargs)
            self.orientation = orientation.lower()
        elif orientation.lower() == 'vertical':
            self.myobj, = ax.plot(np.array([1, 1])*position, ax.get_ylim(), **kwargs)
            self.orientation = orientation.lower()
        else:
            # throw an error
            pass
        
        DragObj.__init__(self, ax)

    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked: return  # See if we've clicked yet
        if event.inaxes != self.parentax: return # See if we're moving over the parent axes object

        if self.orientation == 'vertical':
            self.myobj.set_xdata(np.array([1, 1])*event.xdata)
            self.myobj.set_ydata(self.parentax.get_ylim())
        elif self.orientation == 'horizontal':
            self.myobj.set_xdata(self.parentax.get_xlim())
            self.myobj.set_ydata(np.array([1, 1])*event.ydata)

        self.parentcanvas.draw()


class DragEllipse(DragObj):
    def __init__(self, ax, xy, width, height, angle=0.0, **kwargs):
        self.myobj = patches.Ellipse(xy, width, height, angle, **kwargs)
        ax.add_artist(self.myobj)

        DragObj.__init__(self, ax)
        self.oldcenter = xy  # Store for motion callback

    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked: return  # See if we've clicked yet
        if event.inaxes != self.parentax: return # See if we're moving over the parent axes object

        oldx, oldy = self.oldcenter
        dx = event.xdata - self.clickx
        dy = event.ydata - self.clicky
        self.myobj.center = [oldx + dx, oldy + dy]

        self.parentcanvas.draw()

    def on_release(self, event):
        self.clicked = False
        self.oldcenter = self.myobj.center

        self.disconnect


class DragCircle(DragEllipse):
    def __init__(self, ax, xy, radius, **kwargs):
        width = radius*2
        height = radius*2

        DragEllipse.__init__(self, ax, xy, width, height, **kwargs)