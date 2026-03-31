from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartCanvas(FigureCanvas):
    def __init__(self, width=5, height=3, dpi=100):
        self.fig = Figure(
            figsize=(width, height),
            dpi=dpi,
            facecolor="white"
        )
        self.ax = self.fig.add_subplot(111)

        # ---- STYLE ----
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.grid(axis="y", linestyle="--", alpha=0.3)

        self.ax.tick_params(axis="x", labelrotation=0)
        self.ax.tick_params(axis="y")

        super().__init__(self.fig)

    def clear(self):
        self.ax.clear()
        self.draw()
