import matplotlib

matplotlib.use('qt5agg')
import matplotlib.pyplot as plt
from PIL import Image


class Cursor(object):
    def __init__(self, ax):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.ly = ax.axvline(color='k')  # the vert line
        self.xs, self.ys = [], []
        self.line = None

    def on_press(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        self.xs = [x]
        self.ys = [y]
        self.ax.plot(self.xs, self.ys, marker='o')

    def on_release(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        self.xs.append(x)
        self.ys.append(y)

        self.line = self.ax.plot(self.xs, self.ys, color='red')[0]
        self.ax.figure.canvas.draw()

    def mouse_move(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata
        # update the line positions
        self.lx.set_ydata(y)
        self.ly.set_xdata(x)
        if len(self.xs) == 1:
            if self.line:
                self.line.remove()
            self.line = self.ax.plot(self.xs + [x], self.ys + [y])[0]

        self.ax.figure.canvas.draw()


def get_line_coords(x, y, image_path):
    fig, ax = plt.subplots()
    img = Image.open(image_path)
    img = img.resize((512, 512))
    ax.hist2d(x, y, bins=40, range=[[0, 512], [0, 512]], alpha=0.4, zorder=2, cmin=0.01)
    ax.invert_yaxis()
    ax.imshow(img, zorder=1)
    cursor = Cursor(ax)
    fig.canvas.mpl_connect('button_press_event', cursor.on_press)
    fig.canvas.mpl_connect('button_release_event', cursor.on_release)
    fig.canvas.mpl_connect('motion_notify_event', cursor.mouse_move)

    plt.show()
    while True:
        if plt.waitforbuttonpress(10):
            break
    return list(zip(cursor.xs, cursor.ys))
