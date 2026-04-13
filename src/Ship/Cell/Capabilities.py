"""Проверка capability и attenuation для L2 Cell Engine.

Сравнивает требуемые ``Capability`` с выданным списком; дочерняя ячейка может
получить только подмножество возможностей родителя.
"""

from __future__ import annotations

from src.Ship.Core.Types import Capability


def check_capability(required: Capability, granted: list[Capability]) -> bool:
    """Check if required capability is satisfied by any granted capability."""
    for cap in granted:
        if cap.resource == required.resource and cap.action == required.action:
            # Check constraints: all required constraints must be present in granted
            if all(
                required.constraints.get(k) == cap.constraints.get(k)
                for k in required.constraints
            ):
                return True
    return False


def attenuate(parent_caps: list[Capability], child_request: list[Capability]) -> list[Capability]:
    """Attenuate: child can only get subset of parent capabilities."""
    result = []
    for req in child_request:
        if check_capability(req, parent_caps):
            result.append(req)
    return result


def check_all_capabilities(required: list[Capability], granted: list[Capability]) -> bool:
    """Check if ALL required capabilities are satisfied."""
    return all(check_capability(r, granted) for r in required)
