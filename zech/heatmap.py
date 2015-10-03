from __future__ import print_function


class HeatmapInteractor(object):
    '''A heatmap editor

    http://matplotlib.org/examples/event_handling/poly_editor.html
    '''
    def __init__(self, fig):
        canvas = fig.canvas
        canvas.mpl_connect('scroll_event', self.scroll_callback)
        canvas.mpl_connect('key_press_event', self.key_press_callback)

    def key_press_callback(self, event, base_scale=2.):
        ax = event.inaxes
        ylim_lower, ylim_upper = ax.get_ylim()
        if event.key == '[':
            ax.set_ylim(top=ylim_lower + (ylim_upper - ylim_lower) / base_scale)
        elif event.key == ']':
            ax.set_ylim(top=ylim_lower + (ylim_upper - ylim_lower) * base_scale)
        plt.tight_layout()
        plt.draw()

    def scroll_callback(self, event, base_scale=2.):
        print(event)
        ax = event.inaxes
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0]) * .5
        cur_yrange = (cur_ylim[1] - cur_ylim[0]) * .5
        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            print(event.button)
        # set new limits
        ax.set_xlim([xdata - cur_xrange * scale_factor,
                     xdata + cur_xrange * scale_factor])
        ax.set_ylim([ydata - cur_yrange * scale_factor,
                     ydata + cur_yrange * scale_factor])
        plt.draw()  # force re-draw


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    im = ax.imshow([[1, 2], [3, 4]])
    p = HeatmapInteractor(fig)

    plt.show()
