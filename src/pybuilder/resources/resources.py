from pathlib import Path


_resources = None

_wrapper_name = 'pyfmu'

class Resources:
    """Singleton object representing static resources.


    For example to get path to pyfmu directory:
    ```
    pyfmu_dir = Resources.get().pyfmu_dir
    ```

    Do not move the file as the resources must are located relative to this file
    """

    @staticmethod
    def get():

        global _resources

        if(_resources is None):
            _resources = Resources()

        return _resources

    def __init__(self):
        self.root = Path(__file__).parent
        self.pyfmu_dir = self.root / 'pyfmu'
        self.templates_dir = self.root / 'templates'
        self.scriptTemplate_path = self.templates_dir / 'fmu.py.j2'

        # binaries
        self.binaries_dir: Path = self.root / 'wrapper' / 'binaries'
        self.wrapper_win64 = self.binaries_dir / 'win64' / (_wrapper_name + '.dll')
        self.wrapper_linux64 = self.binaries_dir / 'linux64' / (_wrapper_name + '.so')


        self.VDMCheck2_jar = self.root / 'validation' / 'vdmcheck-0.0.2' / 'fmi2vdm-0.0.2.jar'
        self.VDMCheck3_jar = self.root / 'validation' / 'vdmcheck-0.0.3' / 'fmi2vdm-0.0.3.jar'