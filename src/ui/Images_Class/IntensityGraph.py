import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class IntensityGraph(FigureCanvas):
    def __init__(self,parent = None):
        self.fig, self.axes = plt.subplots()
        super().__init__(self.fig)
        self.axes.set_title('Intensity graph')
        self.axes.set_xlabel("Time point (T)")
        self.axes.set_ylabel("Intensity")
        self.axes.yaxis.set_label_coords(-0.15, 0.5)
        self.axes.xaxis.set_label_coords(0.5, -0.10)
        self.line, = self.axes.plot([], [], marker='o', color='b', markersize=4)
        self.fig.tight_layout() #We prepare the graphic

    def close_graph(self):
        plt.close(self.fig)

    def update_graph(self, intensities_t, x, y):
        """
        Upload of the graphic
        :param intensities_t: Current values of the intensitie in the x and y axes given
        :param x: coorX of the pixel
        :param y: coorY of the pixel
        """
        #We upload the line changes
        self.line.set_data(range(len(intensities_t)), intensities_t)

        #We adapt the limits to the new line data
        self.axes.relim()
        self.axes.autoscale_view()

        #We upload the title to know where we are on the axes
        self.axes.set_title(f"Intensity in Pixel: ({x}, {y})")
        self.draw()