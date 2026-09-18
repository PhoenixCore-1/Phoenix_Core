from typing import Dict, List

from phoenix_framework.contracts import NavigationContract


class NavigationRegistry:
    """
    Runtime registry for Platform UI navigation contributions.

    Navigation metadata does not replace Core authorization.
    """

    def __init__(self) -> None:
        self._items: Dict[str, NavigationContract] = {}

    def register(self, item: NavigationContract) -> None:
        if item.key in self._items:
            raise ValueError(f"Navigation already registered: {item.key}")

        self._items[item.key] = item

    def get(self, key: str) -> NavigationContract:
        try:
            return self._items[key]
        except KeyError:
            raise ValueError(f"Navigation not registered: {key}") from None

    def has(self, key: str) -> bool:
        return key in self._items

    def list(self) -> List[NavigationContract]:
        return sorted(
            self._items.values(),
            key=lambda item: (item.order, item.key),
        )

    def clear(self) -> None:
        self._items.clear()
