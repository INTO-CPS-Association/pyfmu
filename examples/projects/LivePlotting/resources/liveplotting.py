import multiprocessing as mp
import multiprocessing
from math import sin

from pyqtgraph.Qt import QtGui
from pyqtgraph import time
import numpy as np
import pyqtgraph as pg


from pyfmu.fmi2 import Fmi2Slave


class LivePlotting(Fmi2Slave):

    def __init__(self, *args, **kwargs):

        author = ""
        modelName = "LivePlotting"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
        )

        self.x0 = 0.0
        self.y0 = 0.0
        self.interval = -1.0
        self.n_samples = -1.0
        self.title = 'Robot position'
        self.register_variable('x0', 'real', 'input',
                               start=0.0, description='first variable')
        self.register_variable('y0', 'real', 'input',
                               start=0.0, description='second variable')

        self.register_variable('title', 'string', 'parameter', 'fixed',
                               start='Robot position', description='title of the plot')

        self.ts = -1.0
        self.register_variable('ts', 'real', 'parameter', 'fixed',
                               start=-1.0, description='simulation time between refresh.')

        # Qt application must run on main thread.
        # We start a new process to ensure this.
        # Samples are shared through a buffer
        ctx = mp.get_context('spawn')
        self.q = ctx.Queue()
        self.plot_process = ctx.Process(
            target=LivePlotting._draw_process_func, args=(self.q,))
        self._lastSimTime = 0.0
        self._running = False

    def terminate(self):

        if(not self.plot_process.is_alive()):
            return

        # put sentinel object to indicate end of data
        self._terminated = True
        self.q.put(None)
        try:
            self.plot_process.join()
        except Exception:
            pass

    def __del__(self):
        self.terminate()

    def exit_initialization_mode(self):

        self._running = True
        self.plot_process.start()

    def do_step(self, current_time: float, step_size: float, no_prior_step: bool):

        time_downsampling = (self.ts != -1)
        if(time_downsampling):
            diff = (current_time+step_size) - self._lastSimTime
            if(diff < self.ts):
                return

        self._lastSimTime = current_time

        self.q.put(np.array([self.x0, self.y0]))

    @staticmethod
    def _draw_process_func(q: multiprocessing.Queue):

        app = QtGui.QApplication(["Robot live plotting"])

        win = pg.GraphicsWindow(title="Basic plotting examples")
        win.resize(1000, 1000)
        win.setWindowTitle('Robot plotting')

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=False)

        # scatter_item = pg.ScatterPlotItem(x =1,2,3)
        p1 = win.addPlot(title="Parametric Plot",
                         symbolPen='w', autoDownsample=True)

        curve = p1.plot()
        lastTime = time()
        samples = None

        samples = q.get()

        while(True):

            new_sample = q.get()

            if(new_sample is None):
                return 0

            samples = np.vstack([samples, new_sample])

            curve.setData(samples, pen='w')

            # performance metrics
            fps = None
            now = time()
            dt = now - lastTime
            lastTime = now
            if fps is None:
                fps = 1.0/dt
            else:
                s = np.clip(dt*3., 0, 1)
                fps = fps * (1-s) + (1.0/dt) * s

            fps_str = f'fps: {int(fps)}, samples : {len(samples)}'
            p1.setTitle(fps_str)

            app.processEvents()


if __name__ == "__main__":

    fmu = LivePlotting()

    fmu.enter_initialization_mode()
    fmu.ts = 0.1
    fmu.exit_initialization_mode()

    n = 10000
    ts = 0.01
    for i in range(n):
        fmu.x0 = float(i)
        fmu.y0 = sin(i*ts)
        fmu.do_step(i*ts, ts, True)

    fmu.terminate()

    # fmu.plot_process.join()
