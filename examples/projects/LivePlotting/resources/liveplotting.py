import multiprocessing as mp
import multiprocessing
from math import sin

from pyqtgraph.Qt import QtGui
from pyqtgraph import time
import numpy as np
import pyqtgraph as pg


from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T


class LivePlotting(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):

        author = ""
        modelName = "LivePlotting"
        description = ""

        super().__init__(
            model_name=modelName,
            author=author,
            description=description,
            *args,
            **kwargs,
        )

        self.log_ok(f"My file attribute is: {__file__}")

        # Qt application must run on main thread.
        # We start a new process to ensure this.
        # Samples are shared through a buffer
        ctx = mp.get_context("spawn")

        self.q = ctx.Queue()
        self.plot_process = ctx.Process(
            target=LivePlotting._draw_process_func,
            args=(self.q,),
            name="pyfmu_livelogging",
            daemon=False,
        )

        self._reset_variables()
        self.register_input("x0", "real", "continuous", description="first variable")
        self.register_input("y0", "real", "continuous", description="second variable")

        self.register_parameter(
            "title", "string", "fixed", description="title of the plot",
        )

        self.ts = -1.0
        self.register_parameter(
            "ts", "real", "fixed", description="simulation time between refresh.",
        )

    def reset(self) -> Fmi2Status_T:

        self.terminate()
        self._reset_variables()
        return Fmi2Status.ok

    def _reset_variables(self):
        self.x0 = 0.0
        self.y0 = 0.0
        self.interval = -1.0
        self.n_samples = -1.0
        self.title = "Robot position"
        self._lastSimTime = 0.0
        self._running = False

    # def __del__(self):

    #     if not self._terminated:
    #         self.terminate()

    def exit_initialization_mode(self):

        assert self._running is False

        self.log_ok("Starting GUI process")
        self._running = True

        self.plot_process.start()

        assert self.plot_process.is_alive()

        return Fmi2Status.ok

    def do_step(self, current_time: float, step_size: float, no_prior_step: bool):

        time_downsampling = self.ts != -1
        if time_downsampling:
            diff = (current_time + step_size) - self._lastSimTime
            if diff < self.ts:
                return

        assert self.plot_process.is_alive()
        self._lastSimTime = current_time

        self.q.put(np.array([self.x0, self.y0]))

        return Fmi2Status.ok

    @staticmethod
    def _draw_process_func(q: multiprocessing.Queue):
        try:

            app = QtGui.QApplication(["Robot live plotting"])

            win = pg.GraphicsWindow(title="Basic plotting examples")
            win.resize(1000, 1000)
            win.setWindowTitle("Robot plotting")

            # Enable antialiasing for prettier plots
            pg.setConfigOptions(antialias=False)

            # scatter_item = pg.ScatterPlotItem(x =1,2,3)
            p1 = win.addPlot(
                title="Parametric Plot", symbolPen="w", autoDownsample=True
            )

            curve = p1.plot()
            lastTime = time()
            samples = None

            while True:

                new_sample = q.get()

                if new_sample is None:  # sentinel object read
                    win.close()
                    return 0

                if samples is None:
                    samples = np.array(new_sample)
                else:
                    samples = np.vstack([samples, new_sample])

                curve.setData(samples, pen="w")

                # performance metrics
                fps = None
                now = time()
                dt = now - lastTime
                lastTime = now
                if fps is None:
                    fps = 1.0 / dt
                else:
                    s = np.clip(dt * 3.0, 0, 1)
                    fps = fps * (1 - s) + (1.0 / dt) * s

                fps_str = f"fps: {int(fps)}, samples : {len(samples)}"
                p1.setTitle(fps_str)

                app.processEvents()
        except Exception as e:
            print(f"An exception was raised in the drawing thread: {e}")

    def terminate(self):

        self.log_ok("Terminating GUI process")

        if self.plot_process.is_alive():
            self.log_ok("Waiting for GUI process to finish")
            self.q.put(None)
            self.plot_process.join()
            assert not self.plot_process.is_alive()
            self.log_ok("Process has successfully terminated")
        return Fmi2Status.ok


if __name__ == "__main__":
    c = LivePlotting()

    assert c.setup_experiment(start_time=0, stop_time=10) == Fmi2Status.ok
    assert c.enter_initialization_mode() == Fmi2Status.ok
    assert c.exit_initialization_mode() == Fmi2Status.ok

    for i in range(0, 100):
        c.x0 = i
        c.y0 = i
        assert c.do_step(i, i + 1, False) == Fmi2Status.ok

    assert c.terminate() == Fmi2Status.ok
    assert c.reset() == Fmi2Status.ok
