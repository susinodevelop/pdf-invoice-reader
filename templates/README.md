# Templates for invoice extraction

This directory contains optional JSON templates that can be used to improve extraction for specific invoice formats.

Templates should be organised in subdirectories named after the advisor or client, for example:

```
templates/my_client/template1.json
templates/my_client/template2.json
```

Each JSON file should map field names (e.g. `invoice_number`, `issue_date`, `total`) to regular expressions or other extraction rules tailored for that invoice layout.

During processing, if the filename of an uploaded invoice matches a template pattern, the corresponding rules will be applied in addition to the generic heuristics. If no template applies, the service will fall back to generic extraction logic.
