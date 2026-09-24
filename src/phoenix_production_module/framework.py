"""Phoenix Production Framework registration contract."""

from phoenix_framework.contracts import (
    ModuleContract,
    ModuleIntegrationContract,
)
from phoenix_framework.registration import ModuleRegistrationBundle

from . import __module_code__, __module_name__, __version__


PRODUCTION_MODULE_CONTRACT = ModuleContract(
    code=__module_code__,
    name=__module_name__,
    version=__version__,
    description="Phoenix Production 360 manufacturing module.",
    required_permissions=(
        "production.view",
        "production.order.create",
        "production.order.edit",
        "production.order.release",
        "production.order.execute",
        "production.quantity.record",
        "production.quantity.adjust",
        "production.bom.view",
        "production.bom.manage",
        "production.spc.view",
        "production.spc.manage",
        "production.eta.view",
        "production.eta.recalculate",
        "production.ai.use",
        "production.admin",
    ),
    required_entitlements=("production",),
    capabilities=(
        "production.orders",
        "production.execution",
        "production.quantity",
        "production.bom",
        "production.spc",
        "production.eta",
    ),
)


PRODUCTION_INTEGRATION_CONTRACT = ModuleIntegrationContract(
    module_code=__module_code__,
    version=__version__,
    provided_contracts=(
        "production.order.lifecycle",
        "production.quantity.recording",
        "production.eta.snapshot",
    ),
    provided_capabilities=(
        "production.orders",
        "production.execution",
        "production.quantity",
        "production.eta",
    ),
    provided_events=(
        "production.order.released",
        "production.order.started",
        "production.order.stage_started",
        "production.order.held",
        "production.order.resumed",
        "production.order.completed",
        "production.quantity.recorded",
    ),
)


PRODUCTION_REGISTRATION_BUNDLE = ModuleRegistrationBundle(
    module=PRODUCTION_MODULE_CONTRACT,
    integration=PRODUCTION_INTEGRATION_CONTRACT,
)
