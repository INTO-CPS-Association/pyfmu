from fmpy.ssp.simulation import simulate_ssp

from pyfmu.tests import ExampleSystem


def test_sumOfSines():
    """Sum of two sine waves
    """
    with ExampleSystem('SumOfSines') as s:

        s_str = str(s)

        try:
            simulate_ssp(
                s_str,
                start_time=0,
                stop_time=1,
                step_size=0.01)

        except Exception as e:
            print(e)

