from pathlib import Path


_resources = None

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
        self.binaries_dir = self.root / 'wrapper' / 'binaries'

        # VDMCheck
        self.vdmcheck_fmi2_ps = self.root / 'validation' / 'vdmcheck-0.0.2' / 'VDMCheck2.ps1'
        self.vdmcheck_fmi2_sh = self.root / 'validation' / 'vdmcheck-0.0.2' / 'VDMCheck2.sh'
        self.vdmcheck_fmi3_ps = self.root / 'validation' / 'vdmcheck-0.0.3' / 'VDMCheck3.ps1'
        self.vdmcheck_fmi3_sh = self.root / 'validation' / 'vdmcheck-0.0.3' / 'VDMCheck2.sh'

