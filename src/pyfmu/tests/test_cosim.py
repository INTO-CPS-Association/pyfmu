from fmpy.ssp.simulation import simulate_ssp

from pyfmu.tests import ExampleSystem


def disable_test_sumOfSines():
    """Sum of two sine waves
    """
    with ExampleSystem('SumOfSines') as s:

        s_str = str(s)

        try:
            res = simulate_ssp(
                s_str,
                start_time=0,
                stop_time=1,
                step_size=0.01)

        except Exception as e:
            print(e)

        _ = 10
        print(res)


if __name__ == "__main__":
    with ExampleSystem('SumOfSines') as s:

        s_str = str(s)

        try:
            res = simulate_ssp(
                s_str,
                start_time=0,
                stop_time=1,
                step_size=0.01)

        except Exception as e:
            print(e)

        print(res)