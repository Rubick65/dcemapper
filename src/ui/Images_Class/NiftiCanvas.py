import matplotlib.pyplot as plt
from PyQt6.QtCore import pyqtSignal, Qt
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class NiftiCanvas(FigureCanvas):
    """
    Class to create a matpplotlib figure in a PyQT6 interface
    """
    z_changed = pyqtSignal(int)
    def __init__(self, np_array):
        self.fig, self.axes = plt.subplots()
        self.axes.axis('off') #Remove the axis numbers
        super().__init__(self.fig)

        self.data = np_array
        self.cmap = 'gray' #Color map, by default in black and white colors
        self.current_z = 0 #Current slide
        self.current_t = 0 #Current time

        self.slice_text = self.fig.text(0.5, 1.25,
                                        f"Slice: {self.current_z}",
                                         transform=self.axes.transAxes,
                                         color='white',
                                         fontsize=15,
                                         family = "Georgia",
                                         ha='center',
                                         va='top'
                                         )

        #self.cmap_text = self.fig.text(0.5, -0.25,
        #                                f"Colormap: {self.cmap}",
        #                                transform=self.axes.transAxes,
        #                                color='white',
        #                                fontsize=15,
        #                                family = "Georgia",
        #                                ha='center',
        #                                va='bottom'
        #                                )

        self.max_z = self.data.shape[2] - 1 #Max number of slides in np array
        self.max_t = self.data.shape[3] - 1 #Max number of seconds in np array

        self.current_slice = self.data[:, :,self.current_z,self.current_t].T

        #Image of the np array
        self.img_slice = self.axes.imshow(self.current_slice, cmap = self.cmap)

        #Event click in the matplotlib image
        self.mpl_connect('button_press_event', self._on_click)

        #Change background color
        self.fig.patch.set_facecolor('black')
        self.fig.subplots_adjust(top=0.9, bottom=0.1)

        #parameter to save and external function
        self.pixel_callback = None

    #To change the current time and reload the image
    def set_t(self,t_index):
        """
        Function to change the current time (T) and reload the image
        :param t_index: new time (T)
        :return: Reload of the image with the new T
        """
        if t_index < 0 or t_index > self.max_t:
            raise IndexError(f"Error: T={t_index} Out of range (0-{self.max_t})")
        self.current_t = t_index
        self.load_image()

    def set_z(self,z_index):
        """
        Function to change the current z (Z) and reload the image
        :param z_index: new z/slice (Z)
        :return: Reload of the image with the new Z
        """
        if z_index < 0 or z_index > self.max_z:
            raise IndexError(f"Error: Z={z_index} Out of range (0-{self.max_z})")
        self.current_z = z_index
        self.load_image()
        self.z_changed.emit(self.current_z)

    def load_image(self):
        """
        Function to load/reload the image
        """
        self.current_slice = self.data[:, :, self.current_z, self.current_t].T #We update de slice with the changes
        self.slice_text.set_text(f"Slice: {self.current_z}")
        self.img_slice.set_data(self.current_slice)
        self.draw()

    def _on_click(self, event):
        #If the click are not in the image axes we ignored
        if event.inaxes != self.axes:
            return

        #If the click have valid coordinates
        if event.xdata is not None and event.ydata is not None:
            x = int(round(event.xdata))
            y = int(round(event.ydata))

            #Current numbers of the rows and columns
            rows, columns = self.current_slice.shape[:2]

            #We checked that the coordinate rounding
            #did not go beyond the limits of the image
            if 0 <= y < rows and 0 <= x < columns:
                value = self.current_slice[y, x]

                #If the image have and external function, we execute
                if self.pixel_callback:
                    self.pixel_callback(x, y, value)

    #Allows to the main window to hear the clicks
    def set_pixel_observer(self, callback_func):
        self.pixel_callback = callback_func
