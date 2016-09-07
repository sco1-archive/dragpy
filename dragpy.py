import numpy as np
import matplotlib.pyplot as plt

class DragObj:
    def __init__(self, ax):
        self.parentcanvas = ax.figure.canvas
        self.parentax = ax

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
                if child._label == 'dragobj':
                    contains, attrs = child.contains(event)
                    if contains:
                        firingobjs.append(child)

            # Assume the last child object is the topmost rendered object, only move if we're it
            if firingobjs[-1] == self.myobj:
                timetomove = True
            else:
                timetomove = False

        return timetomove

    def on_release(self, event):
        self.clicked = False

        self.parentcanvas.mpl_disconnect(self.mousemotion)
        self.parentcanvas.mpl_disconnect(self.clickrelease)
        self.parentcanvas.draw()

class DragLine(DragObj):
    def __init__(self, orientation, ax, position):
        DragObj.__init__(self, ax)

        if orientation.lower() == 'horizontal':
            self.myobj, = ax.plot(ax.get_xlim(), np.array([1, 1])*position)
            self.orientation = orientation.lower()
        elif orientation.lower() == 'vertical':
            self.myobj, = ax.plot(np.array([1, 1])*position, ax.get_ylim())
            self.orientation = orientation.lower()
        else:
            # throw an error
            pass

        self.myobj._label = 'dragobj'

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

fig = plt.figure()
ax = fig.add_subplot(111)

vl1 = DragLine('vertical', ax, 3)
vl2 = DragLine('vertical', ax, 6)

ax.set_xlim([0, 10])
plt.show()