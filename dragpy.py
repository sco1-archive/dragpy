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

        self.clickpress = self.parentfig.mpl_connect('button_press_event', self.on_click)  # Execute on mouse click
        self.clicked = False

    def on_click(self, event):
        # Executed on mouse click
        if event.inaxes != self.parentax: return  # See if the mouse is over the parent axes object

        # See if the click is on top of this line object
        contains, attrs = self.myline.contains(event)
        if not contains: return

        self.mousemotion = self.parentfig.mpl_connect('motion_notify_event', self.on_motion)
        self.clickrelease = self.parentfig.mpl_connect('button_release_event', self.on_release)
        self.clicked = True

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