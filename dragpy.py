import numpy as np
import matplotlib.pyplot as plt

class DraggableLine:
    def __init__(self, orientation, ax, position):
        if orientation.lower() == 'horizontal':
            self.myline, = ax.plot(ax.get_xlim(), np.array([1, 1])*position)
            self.orientation = orientation.lower()
        elif orientation.lower() == 'vertical':
            self.myline, = ax.plot(np.array([1, 1])*position, ax.get_ylim())
            self.orientation = orientation.lower()
        else:
            # throw an error
            pass

        self.parentfig = self.myline.figure.canvas
        self.parentax = ax
        self.myline._label = 'dragobj'

        self.clickpress = self.parentfig.mpl_connect('button_press_event', self.on_click)  # Execute on mouse click
        self.clicked = False

    def on_click(self, event):
        # Executed on mouse click
        if event.inaxes != self.parentax: return  # See if the mouse is over the parent axes object

        # Check for overlaps, make sure we only fire for one object per click
        timetomove = self.shouldthismove(event)
        if not timetomove: return

        self.mousemotion = self.parentfig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.clickrelease = self.parentfig.canvas.mpl_connect('button_release_event', self.on_release)
        self.clicked = True

    def shouldthismove(self, event):
        # Check to see if this object has been clicked on
        contains, attrs = self.myline.contains(event)
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
            if firingobjs[-1] == self.myline:
                timetomove = True
            else:
                timetomove = False

        return timetomove

    def on_motion(self, event):
        # Executed on mouse motion
        if not self.clicked: return  # See if we've clicked yet
        if event.inaxes != self.parentax: return # See if we're moving over the parent axes object

        if self.orientation == 'vertical':
            self.myline.set_xdata(np.array([1, 1])*event.xdata)
            self.myline.set_ydata(self.parentax.get_ylim())
        elif self.orientation == 'horizontal':
            self.myline.set_xdata(self.parentax.get_xlim())
            self.myline.set_ydata(np.array([1, 1])*event.ydata)

        self.parentfig.draw()

    def on_release(self, event):
        self.clicked = False

        self.parentfig.mpl_disconnect(self.mousemotion)
        self.parentfig.mpl_disconnect(self.clickrelease)
        self.parentfig.draw()