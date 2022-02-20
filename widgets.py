import numpy as np
import PyQt6.QtWidgets as qtw
import pyqtgraph as pg
from matplotlib import cm


class LabelDial(qtw.QVBoxLayout):

    def __init__(self, text, range_min, range_max, value_changed):
        super(qtw.QVBoxLayout, self).__init__()
        self.label = qtw.QLabel(text)
        self.dial = qtw.QDial()
        self.dial.setRange(range_min, range_max)
        self.dial.valueChanged.connect(value_changed)
        self.addWidget(self.label)
        self.addWidget(self.dial)


class WaveWidget(pg.PlotWidget):

    def __init__(self):
        super(WaveWidget, self).__init__()
        self.curve = self.plot(pen='y')
        self.setYRange(-1.1, 1.1, padding=0)
        self.hideAxis('bottom')
        self.hideAxis('left')


class SpectrogramWidget(pg.PlotWidget):
    # https://gist.github.com/boylea/1a0b5442171f9afbf372

    def __init__(self, sample_rate, buf_size):
        super(SpectrogramWidget, self).__init__()
        self.buf_size = buf_size
        self.win = np.hanning(buf_size)
        self.top_db = 1e-5
        draw_secs = 3  # drawing seconds

        self.img_array = np.zeros(
            (sample_rate * draw_secs // buf_size, buf_size // 2 + 1))
        self.img_array -= 20 * np.log10(self.top_db)

        # set colormap
        colormap = cm.get_cmap('jet')
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)
        self.img = pg.ImageItem()
        self.addItem(self.img)
        self.img.setLookupTable(lut)
        self.img.setLevels([-100, 100])

        yticks = {}
        n_grids = 10
        nyq = sample_rate // 2 + 1
        for i in range(n_grids):
            bin = (i) * buf_size // n_grids
            freq = int(nyq * bin / buf_size)
            yticks[bin] = str(freq)
        ay = self.getAxis('left')
        ay.setTicks([yticks.items()])
        self.setYRange(0, buf_size // 2 + 1)
        self.setLabel('left', 'Frequency', units='Hz')

        xticks = {}
        n_grids = 5
        for i in range(n_grids + 1):
            bin = int(i * self.img_array.shape[0] / n_grids)
            ms = draw_secs * i / n_grids
            xticks[bin] = f'{ms:.1f}'
        ax = self.getAxis('bottom')
        ax.setTicks([xticks.items()])
        self.setLabel('bottom', 'Time', units='ms')

        # prepare window for later use
        self.img.setImage(self.img_array, autoLevels=False)
        # self.show()

    def update(self, chunk):
        # normalized, windowed frequencies in data chunk
        spec = np.fft.rfft(chunk * self.win) / self.buf_size
        # get magnitude
        psd = abs(spec)
        # convert to dB scale
        psd = 20 * np.log10(psd + self.top_db)

        # roll down one and replace leading edge with new data
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = psd

        self.img.setImage(self.img_array, autoLevels=False)


class ADSRWidget(pg.PlotWidget):

    def __init__(self, sample_rate, buf_size):
        super(ADSRWidget, self).__init__()
        self.sample_rate = sample_rate
        self.buf_size = buf_size

        self.curve = self.plot()
        xticks = {}
        n_grids = 15
        draw_secs = 3
        for i in range(n_grids + 1):
            bin = int(i * draw_secs * sample_rate / n_grids)
            ms = bin / sample_rate
            xticks[bin] = f'{ms:.1f}'
        ax = self.getAxis('bottom')
        ax.setTicks([xticks.items()])
        self.setLabel('bottom', 'Time', units='ms')