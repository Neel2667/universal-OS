"""Small dependency-free semantic-version helpers for the v1 prototype."""

from __future__ import annotations

import re
from typing import Tuple

from .errors import ContractError

_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def parse_version(value: str) -> Tuple[int, int, int]:
    """Parse the deliberately narrow v1 X.Y.Z version syntax."""
    match = _VERSION.fullmatch(value)
    if not match:
        raise ContractError(f"invalid semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def is_in_range(version: str, expression: str) -> bool:
    """Return whether `version` meets a whitespace-separated >=, >, <=, <, = range.

    The narrow grammar is intentional for an auditable first contract. Examples:
    `>=0.1.0 <0.2.0` and `=1.2.3`.
    """
    candidate = parse_version(version)
    terms = expression.split()
    if not terms:
        raise ContractError("empty bootstrap version range")

    for term in terms:
        match = re.fullmatch(r"(>=|<=|>|<|=)([0-9]+\.[0-9]+\.[0-9]+)", term)
        if not match:
            raise ContractError(f"invalid version range term: {term!r}")
        operator, raw_bound = match.groups()
        bound = parse_version(raw_bound)
        if operator == ">=" and not candidate >= bound:
            return False
        if operator == ">" and not candidate > bound:
            return False
        if operator == "<=" and not candidate <= bound:
            return False
        if operator == "<" and not candidate < bound:
            return False
        if operator == "=" and not candidate == bound:
            return False
    return True
