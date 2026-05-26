class ScopeViolation(Exception):
    pass


def check_target(target: str, allowed: list[str]) -> None:
    if target not in allowed:
        raise ScopeViolation(f"Target '{target}' is not in allowed scope: {allowed}")
