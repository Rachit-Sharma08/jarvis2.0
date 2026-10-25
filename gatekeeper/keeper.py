"""Gatekeeper ka dimag. Yahi ek jagah hai jahan faisla milta hai.

Rasta: kill switch -> rate limit -> rules -> (ASK par UI ka Allow/Deny) -> audit.
Sunday aur Prabh dono ke liye bilkul same — `mode` sirf log me likha jaata hai.
"""

from gatekeeper import audit, nocards, rules
from gatekeeper.approvals import Registry
from gatekeeper.limiter import Limiter

import config

ALLOW, ASK, DENY = "allow", "ask", "deny"

LIMITER = Limiter()
APPROVALS = Registry()


def tools_on() -> bool:
    return LIMITER.enabled


def set_tools(on: bool) -> bool:
    """UI ka TOOLS OFF / ON toggle."""
    if not on:
        APPROVALS.cancel()
    return LIMITER.set_enabled(on)


def cancel_all() -> tuple:
    """STOP dabane par pending card + chalta hua command dono ruke."""
    return APPROVALS.cancel()


def review(tool: str, args: dict, mode: str) -> tuple:
    """-> (faisla, payload). payload: None | Pending | reason (str)"""
    blocked_by = LIMITER.check()
    if blocked_by:
        audit.log_action(mode, tool, args, DENY, blocked_by)
        return DENY, blocked_by

    risk, reason = rules.decide(tool, args)

    if risk == config.BLOCKED:
        audit.log_action(mode, tool, args, DENY, reason)
        return DENY, reason

    # BLOCKED budget nahi khata - warna injection loop apni hi limit kha jaata.
    LIMITER.record()

    if risk == config.ASK:
        if config.NO_CARDS:
            verdict, reason = nocards.resolve_ask(tool, args)
            if verdict == nocards.ALLOW:
                audit.log_action(mode, tool, args, ALLOW, "no-cards: auto allow")
                return ALLOW, None
            audit.log_action(mode, tool, args, DENY, f"no-cards: {reason}")
            return DENY, reason
        if APPROVALS.busy():
            message = "pehle wala Allow/Deny card abhi pending hai"
            audit.log_action(mode, tool, args, DENY, message)
            return DENY, message
        pending = APPROVALS.open(tool, args)
        audit.log_action(mode, tool, args, ASK, f"card {pending.id} bheja")
        return ASK, pending

    audit.log_action(mode, tool, args, ALLOW, reason)
    return ALLOW, None


def wait(pending, mode: str) -> tuple:
    """Card ka jawab ya 60 second timeout (deny). -> (allowed, reason)"""
    allowed, reason = APPROVALS.wait(pending)
    audit.log_action(mode, pending.tool, pending.args, ALLOW if allowed else DENY, reason)
    return allowed, reason
