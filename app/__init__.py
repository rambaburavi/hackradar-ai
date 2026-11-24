from importlib import import_module

# Load the actual backend package located at apps/api/app
_backend = import_module('apps.api.app')
# Export its public attributes
globals().update(_backend.__dict__)
