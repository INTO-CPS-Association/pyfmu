import sys
from threading import Thread
from math import sin

from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import time
import numpy as np
import pyqtgraph as pg


from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes, Fmi2Status


class LivePlotting(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "LivePlotting"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        self.x0 = 0
        self.y0 = 0
        self.interval = -1
        self.n_samples = -1
        self.title = 'Robot position'
        self.register_variable('x0', 'real', 'input',
                               start=0, description='first variable')
        self.register_variable('y0', 'real', 'input',
                               start=0, description='second variable')

        self.register_variable('title', 'string', 'parameter', 'fixed',
                               start='Robot position', description='title of the plot')

        self.ts = -1
        self.register_variable('ts','real','parameter','fixed',start=-1, description='simulation time between refresh.')
        


        self._nsamples = 0
        self._measurements = np.empty((1,2))
        self._ptr = 0

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        app = QtGui.QApplication(["Robot live plotting"])

        win = pg.GraphicsWindow(title="Basic plotting examples")
        win.resize(1000, 1000)
        win.setWindowTitle(self.title)

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=False)

        #scatter_item = pg.ScatterPlotItem(x =1,2,3)
        p1 = win.addPlot(title="Parametric Plot",
                         x=[self.x0], y=[self.y0],symbolPen='w',autoDownsample=True)

        
        app.processEvents()

        self.app = app
        self.win = win
        self.p1 = p1
        self.curve = p1.plot()

    def exit_initialization_mode(self):
        self._measurements[0,:] = [self.x0,self.y0]
        self._lastTime = time()
        self._lastSimTime = 0

    def do_step(self, current_time: float, step_size: float) -> bool:

        
        time_downsampling = (self.ts != -1)
        if(time_downsampling):
            diff = (current_time+step_size) - self._lastSimTime
            if(diff < self.ts):
                return


        self._lastSimTime = current_time

        self._measurements = np.vstack([self._measurements,[self.x0,self.y0]])

        self.curve.setData(self._measurements, pen='w')

        self.app.processEvents()

        # measure performance
        
        fps=None
        now = time()
        dt = now - self._lastTime
        self._lastTime = now
        if fps is None:
            fps = 1.0/dt
        else:
            s = np.clip(dt*3., 0, 1)
            fps = fps * (1-s) + (1.0/dt) * s

        self.p1.setTitle('%0.2f fps' % fps)

    

if __name__ == "__main__":

    fmu = LivePlotting()

    fmu.enter_initialization_mode()
    fmu.ts = 0.2
    fmu.exit_initialization_mode()

    n = 10000
    ts = 0.01
    for i in range(n):
        fmu.x0 = i
        fmu.y0 = sin(i*ts)
        fmu.do_step(i*ts, ts)
    
    a = 10
