import os
import yaml
from typing import Dict, Any


class TemplateSelector:
    """Selects the appropriate template based on vendor and file name."""

    def __init__(self, templates_dir: str) -> None:
        self.templates_dir = templates_dir

    def select_template(self, vendor: str, file_name: str) -> Dict[str, Any]:
        """
        Select a template for a given vendor and PDF file name.

        Args:
            vendor: Name of the asesoría or client (maps to subfolder in templates).
            file_name: Name of the PDF file being processed.

        Returns:
            A dictionary representing the selected template loaded from YAML.
        """
        # Look for vendor-specific templates
        vendor_dir = os.path.join(self.templates_dir, vendor)
        if os.path.isdir(vendor_dir):
            for fname in os.listdir(vendor_dir):
                if fname.lower().endswith(('.yml', '.yaml')):
                    # Match template based on file name prefix
                    base_name = os.path.splitext(fname)[0].lower()
                    if file_name.lower().startswith(base_name):
                        path = os.path.join(vendor_dir, fname)
                        with open(path, 'r', encoding='utf-8') as f:
                            return yaml.safe_load(f)

        # Fallback to default template
        default_path = os.path.join(self.templates_dir, "default", "default.yml")
        with open(default_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
