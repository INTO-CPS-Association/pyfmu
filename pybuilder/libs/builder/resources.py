from pathlib import Path


_resources = None

class Resources:
    """Singleton object representing static resources.
    

    For example to get path to pyfmu directory:
    ```
    pyfmu_dir = Resources.get().pyfmu_dir
    ```
    """

    @staticmethod
    def get():

        global _resources

        if(_resources is None):
            _resources = Resources()

        return _resources


    def __init__(self):
        self.root = Path(__file__).parent.parent.parent / 'resources'
        self.pyfmu_dir = self.root / 'pyfmu'
        self.templates_dir = self.root / 'templates'
        self.scriptTemplate_path = self.templates_dir / 'fmu.py.j2'
