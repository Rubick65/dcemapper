import sys

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QApplication, QDialogButtonBox, QVBoxLayout, QLabel, \
    QHBoxLayout
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import RectangleSelector

RETRY_CODE = 2


class PreprocessingCanvas(FigureCanvas):
    MIN_WIDTH = 500
    MIN_HEIGHT = 300

    MAX_WIDTH = 800
    MAX_HEIGHT = 500

    def __init__(self, figure, parent=None):
        super().__init__(figure)
        self.setParent(parent)

        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.fig = figure


class PreprocessingVisual(QDialog):

    def __init__(self, figure, data, retry=True, parent=None, question_label_text="Are you happy with the results?"):
        super().__init__(parent)
        self.question_label_text = question_label_text
        self.figure = figure
        self.toolbar = None
        self.retry = retry
        self.RS = None
        self.data = data
        self.roi_coords = None  # Para guardar las coordenadas del ROI

        self.initUI()

    def initUI(self):
        self.show_options()

    def show_options(self):
        v_layout = QVBoxLayout()
        v_layout.setSpacing(25)

        h_layout = QHBoxLayout()

        sc = PreprocessingCanvas(self.figure, self)

        self.toolbar = NavigationToolbar(sc, self)

        question_label = QLabel(self.question_label_text)
        question_label.setStyleSheet("font-size: 20px; font-weight: plain")
        button_box = self.create_buttonBox()

        h_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)

        v_layout.addStretch()
        v_layout.addWidget(self.toolbar, alignment=Qt.AlignmentFlag.AlignLeft)
        v_layout.addWidget(sc, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(question_label, alignment=Qt.AlignmentFlag.AlignCenter)
        v_layout.addLayout(h_layout)

        v_layout.addStretch()

        self.setLayout(v_layout)

        ax = self.figure.gca()
        self.RS = RectangleSelector(ax, self.on_select,
                                    useblit=False,
                                    button=[1],
                                    minspanx=5, minspany=5,
                                    spancoords='data',
                                    interactive=True)

    def create_buttonBox(self):

        QBtn = self.create_buttons()
        button_box = QDialogButtonBox(QBtn)
        button_box.layout().setSpacing(20)

        if self.retry:
            retry_btn = button_box.button(QDialogButtonBox.StandardButton.Retry)
            retry_btn.clicked.connect(lambda: self.done(2))
        else:
            button_box = QDialogButtonBox(QBtn)

        button_box.accepted.connect(self.create_roi)
        button_box.rejected.connect(self.reject)

        return button_box

    def create_buttons(self):
        if self.retry:
            return (
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Retry
            )
        else:
            return (
                QDialogButtonBox.StandardButton.Ok
            )

    def on_select(self, eclick, erelease):
        self.roi_coords = (eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata)
        print(f"ROI seleccionado: {self.roi_coords}")

    def create_roi(self):
        if self.roi_coords is None:
            print("No se seleccionó ningún ROI")
            return

            # Convertir a enteros y asegurarse de que estén en orden correcto
        x1, y1, x2, y2 = map(int, map(np.floor, self.roi_coords))

        self.create_mask(x1, y1, x2, y2)
        #self.accept()

    def create_mask(self, x1, y1, x2, y2):
        try:
            # Seleccionamos el slice (ajusta el índice 2 si es necesario)
            data_slice = self.data[:, :, 2, 0]
            mask = np.zeros_like(data_slice, dtype=bool)

            # IMPORTANTE: Mapeo de coordenadas
            # x1, x2 del selector -> corresponden a la primera dimensión de data_slice
            # y1, y2 del selector -> corresponden a la segunda dimensión de data_slice
            ix1, ix2 = sorted([int(x1), int(x2)])
            iy1, iy2 = sorted([int(y1), int(y2)])

            # Clip para no salirnos del array
            ix1, ix2 = np.clip([ix1, ix2], 0, data_slice.shape[0])
            iy1, iy2 = np.clip([iy1, iy2], 0, data_slice.shape[1])

            mask[ix1:ix2, iy1:iy2] = True

            # Llamamos a la función que refresca el canvas
            self.update_canvas_with_roi(mask, data_slice)

        except Exception as e:
            print(f"Error procesando el ROI: {e}")

    def update_canvas_with_roi(self, mask, data_slice):
        # Aplicamos la máscara
        roi_result = data_slice * mask.astype(float)
        # En lugar de plt.show(), usamos la figura que ya tenemos en el diálogo
        ax = self.figure.gca()
        ax.clear()  # Limpiamos la imagen original

        # Dibujamos el ROI
        ax.imshow(roi_result, cmap='turbo', origin='lower')
        ax.set_title("ROI Seleccionado (Previsualización)")
        ax.axis('off')

        # ESTO es lo que actualiza la ventana de PyQt6 sin que explote
        self.figure.canvas.draw()
        print("Canvas actualizado con éxito.")




def init_view(figure, retry, data):
    app = QApplication.instance() or QApplication(sys.argv)
    window = PreprocessingVisual(figure, data, retry)

    response_code = window.exec()

    if response_code == QDialog.DialogCode.Accepted:
        result = False
    elif response_code == RETRY_CODE:
        result = True
    else:
        result = False

    return result


def main():
    app = QApplication(sys.argv)
    window = PreprocessingVisual()
    window.exec()


if __name__ == "__main__":
    main()
