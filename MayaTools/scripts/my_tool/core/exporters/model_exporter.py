from .base_exporter import ExporterBase
from ..checks import geometry_checks
from ..checks import naming_checks

class ModelExporter(ExporterBase):
    def _process_logic(self):
        if not self.run_preflight_checks("Model"):
            return False

        self.add_log("Checks passed. Exporting...")

        return True