"""Runtime registry for Phoenix module integration handlers and metadata."""

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from phoenix_framework.contracts.integration import ModuleIntegrationContract


IntegrationHandler = Callable[..., object]


@dataclass(frozen=True)
class PublishedIntegration:
    """Runtime registration of a contract published by a module."""

    module_code: str
    contract: str
    handler: IntegrationHandler
    integration_contract: Optional[ModuleIntegrationContract] = None


class IntegrationRegistry:
    """
    Runtime registry for published module integrations.

    This registry provides routing and integration metadata discovery only.
    It does not own module business authority, persistence, security
    authority, tenant authority, or Core module identity.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, PublishedIntegration] = {}
        self._module_contracts: Dict[str, ModuleIntegrationContract] = {}

    def register_module_contract(
        self,
        integration_contract: ModuleIntegrationContract,
    ) -> None:
        module_code = integration_contract.module_code.strip().lower()

        if module_code in self._module_contracts:
            raise ValueError(
                f"Module integration contract already registered: {module_code}"
            )

        self._module_contracts[module_code] = integration_contract

    def get_module_contract(
        self,
        module_code: str,
    ) -> ModuleIntegrationContract:
        module_code = (module_code or "").strip().lower()

        try:
            return self._module_contracts[module_code]
        except KeyError:
            raise ValueError(
                f"Module integration contract not registered: {module_code}"
            ) from None

    def has_module_contract(self, module_code: str) -> bool:
        module_code = (module_code or "").strip().lower()
        return module_code in self._module_contracts

    def register(
        self,
        module_code: str,
        contract: str,
        handler: IntegrationHandler,
        integration_contract: Optional[ModuleIntegrationContract] = None,
    ) -> None:
        module_code = (module_code or "").strip().lower()
        contract = (contract or "").strip()

        if not module_code:
            raise ValueError("Publishing module code cannot be empty")

        if not contract:
            raise ValueError("Integration contract cannot be empty")

        if contract in self._handlers:
            raise ValueError(
                f"Integration contract already registered: {contract}"
            )

        if integration_contract is not None:
            if integration_contract.module_code != module_code:
                raise ValueError(
                    "Integration contract module code must match "
                    "the publishing module."
                )

            if not integration_contract.provides_contract(contract):
                raise ValueError(
                    "Integration contract metadata must declare "
                    "the published contract."
                )

        self._handlers[contract] = PublishedIntegration(
            module_code=module_code,
            contract=contract,
            handler=handler,
            integration_contract=integration_contract,
        )

    def get(self, contract: str) -> IntegrationHandler:
        try:
            return self._handlers[contract].handler
        except KeyError:
            raise ValueError(
                f"Integration contract not registered: {contract}"
            ) from None

    def get_publication(self, contract: str) -> PublishedIntegration:
        try:
            return self._handlers[contract]
        except KeyError:
            raise ValueError(
                f"Integration contract not registered: {contract}"
            ) from None

    def get_integration_contract(
        self,
        contract: str,
    ) -> ModuleIntegrationContract:
        publication = self.get_publication(contract)

        if publication.integration_contract is None:
            raise ValueError(
                f"Integration contract metadata not registered: {contract}"
            )

        return publication.integration_contract

    def has(self, contract: str) -> bool:
        return contract in self._handlers

    def owned_by(self, contract: str, module_code: str) -> bool:
        publication = self._handlers.get(contract)

        if publication is None:
            return False

        return publication.module_code == module_code.strip().lower()

    def list(self) -> Dict[str, PublishedIntegration]:
        return dict(self._handlers)

    def clear(self) -> None:
        self._handlers.clear()
        self._module_contracts.clear()
