"""Deterministic, offline-safe order & refund tools for the RefundOps ADK Agent.

All functions use explicit Python type hints, structured dictionary outputs,
and an in-memory resettable state store (`reset_mock_db()`) so ADK evaluations
(`adk eval` and `AgentEvaluator.evaluate(num_runs=2)`) are 100% repeatable.
"""

from __future__ import annotations

import copy
from typing import Any

RETURN_WINDOW_DAYS = 30

_INITIAL_CUSTOMERS: dict[str, dict[str, str]] = {
    "CUST-101": {
        "name": "Ayu Pratama",
        "pin_last4": "4821",
        "tier": "GOLD",
    },
    "CUST-202": {
        "name": "Budi Santoso",
        "pin_last4": "9910",
        "tier": "STANDARD",
    },
}

_INITIAL_ORDERS: dict[str, dict[str, Any]] = {
    "ORD-9001": {
        "order_id": "ORD-9001",
        "customer_id": "CUST-101",
        "item_name": "Pixel Buds Pro 2",
        "amount_usd": 199.00,
        "days_since_delivery": 12,
        "category": "ELECTRONICS",
        "is_final_sale": False,
        "refund_status": "NONE",
    },
    "ORD-9002": {
        "order_id": "ORD-9002",
        "customer_id": "CUST-101",
        "item_name": "Mechanical Keycap Set",
        "amount_usd": 89.00,
        "days_since_delivery": 45,
        "category": "ACCESSORIES",
        "is_final_sale": False,
        "refund_status": "NONE",
    },
    "ORD-9003": {
        "order_id": "ORD-9003",
        "customer_id": "CUST-202",
        "item_name": "Digital Gift Card $50",
        "amount_usd": 50.00,
        "days_since_delivery": 3,
        "category": "GIFT_CARD",
        "is_final_sale": True,
        "refund_status": "NONE",
    },
}

_CUSTOMERS_DB: dict[str, dict[str, str]] = copy.deepcopy(_INITIAL_CUSTOMERS)
_ORDERS_DB: dict[str, dict[str, Any]] = copy.deepcopy(_INITIAL_ORDERS)
_VERIFIED_CUSTOMERS: set[str] = set()


def reset_mock_db() -> None:
    """Reset in-memory customer, order, and verification state before each eval run."""
    global _CUSTOMERS_DB, _ORDERS_DB, _VERIFIED_CUSTOMERS
    _CUSTOMERS_DB = copy.deepcopy(_INITIAL_CUSTOMERS)
    _ORDERS_DB = copy.deepcopy(_INITIAL_ORDERS)
    _VERIFIED_CUSTOMERS = set()


def verify_customer_identity(customer_id: str, pin_last4: str) -> dict[str, Any]:
    """Verify a customer's identity using their customer ID and 4-digit security PIN.

    PRECONDITION: Must be called FIRST before disclosing order details or issuing
    any refund. Never guess or fabricate `pin_last4` if the user has not provided it.

    Args:
        customer_id: Customer identifier such as 'CUST-101'.
        pin_last4: Exact 4-digit security PIN provided by the customer (e.g., '4821').

    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - verified: True if the PIN matches the customer record, False otherwise
        - customer_id: Normalized customer ID
        - message: Human-readable verification status
    """
    normalized_id = customer_id.strip().upper()
    customer = _CUSTOMERS_DB.get(normalized_id)
    if not customer:
        return {
            "status": "error",
            "verified": False,
            "customer_id": normalized_id,
            "message": f"Customer '{normalized_id}' was not found.",
        }

    if customer["pin_last4"] != pin_last4.strip():
        return {
            "status": "error",
            "verified": False,
            "customer_id": normalized_id,
            "message": "Security PIN verification failed. Cannot proceed with account actions.",
        }

    _VERIFIED_CUSTOMERS.add(normalized_id)
    return {
        "status": "success",
        "verified": True,
        "customer_id": normalized_id,
        "customer_name": customer["name"],
        "message": f"Identity verified for {customer['name']} ({normalized_id}).",
    }


def get_order_details(order_id: str) -> dict[str, Any]:
    """Retrieve order metadata including item name, purchase amount, and delivery age.

    PRECONDITION: Call after `verify_customer_identity` succeeds, and before calling
    `check_return_eligibility` or `issue_refund`.

    Args:
        order_id: Order identifier such as 'ORD-9001'.

    Returns:
        Dictionary with order fields (`order_id`, `customer_id`, `item_name`,
        `amount_usd`, `days_since_delivery`, `is_final_sale`, `refund_status`).
    """
    normalized_order = order_id.strip().upper()
    order = _ORDERS_DB.get(normalized_order)
    if not order:
        return {
            "status": "error",
            "order_id": normalized_order,
            "message": f"Order '{normalized_order}' does not exist.",
        }

    return {
        "status": "success",
        **copy.deepcopy(order),
    }


def check_return_eligibility(order_id: str) -> dict[str, Any]:
    """Evaluate deterministic return policy eligibility for a specific order.

    POLICY RULES:
    1. Orders marked `is_final_sale == True` (such as digital gift cards) are non-refundable.
    2. Orders delivered more than 30 days ago (`days_since_delivery > 30`) are outside
       the return window and ineligible for refunds.
    3. Already refunded orders (`refund_status == 'REFUNDED'`) cannot be refunded twice.

    PRECONDITION: Must be called BEFORE `issue_refund`.

    Args:
        order_id: Order identifier such as 'ORD-9001'.

    Returns:
        Dictionary containing `status`, `order_id`, `eligible` (bool),
        `policy_code`, `refundable_amount_usd`, and `reason`.
    """
    normalized_order = order_id.strip().upper()
    order = _ORDERS_DB.get(normalized_order)
    if not order:
        return {
            "status": "error",
            "order_id": normalized_order,
            "eligible": False,
            "policy_code": "ORDER_NOT_FOUND",
            "refundable_amount_usd": 0.0,
            "reason": f"Order '{normalized_order}' was not found.",
        }

    if order["refund_status"] == "REFUNDED":
        return {
            "status": "success",
            "order_id": normalized_order,
            "eligible": False,
            "policy_code": "ALREADY_REFUNDED",
            "refundable_amount_usd": 0.0,
            "reason": f"Order {normalized_order} has already been refunded.",
        }

    if order["is_final_sale"]:
        return {
            "status": "success",
            "order_id": normalized_order,
            "eligible": False,
            "policy_code": "FINAL_SALE_EXCLUDED",
            "refundable_amount_usd": 0.0,
            "reason": (
                f"Order {normalized_order} ({order['item_name']}) is a final-sale item "
                "and is non-refundable under policy FINAL_SALE_EXCLUDED."
            ),
        }

    if order["days_since_delivery"] > RETURN_WINDOW_DAYS:
        return {
            "status": "success",
            "order_id": normalized_order,
            "eligible": False,
            "policy_code": "RETURN_WINDOW_EXPIRED",
            "refundable_amount_usd": 0.0,
            "reason": (
                f"Order {normalized_order} was delivered {order['days_since_delivery']} days ago, "
                f"which exceeds the {RETURN_WINDOW_DAYS}-day return window."
            ),
        }

    return {
        "status": "success",
        "order_id": normalized_order,
        "eligible": True,
        "policy_code": "WITHIN_30_DAY_WINDOW",
        "refundable_amount_usd": order["amount_usd"],
        "reason": (
            f"Order {normalized_order} was delivered {order['days_since_delivery']} days ago "
            f"(within the {RETURN_WINDOW_DAYS}-day return window)."
        ),
    }


def issue_refund(order_id: str, reason: str) -> dict[str, Any]:
    """Execute a financial refund for an eligible order of a verified customer.

    CRITICAL PRECONDITIONS:
    1. `verify_customer_identity` MUST have succeeded (`verified == True`) for the
       order's `customer_id` in this session.
    2. `check_return_eligibility(order_id)` MUST have returned `eligible == True`.
    Never call this tool if eligibility is False or identity is unverified.

    Args:
        order_id: Order identifier such as 'ORD-9001'.
        reason: Short customer-stated reason for the refund (e.g., 'defective_audio').

    Returns:
        Dictionary containing `status`, `order_id`, `refund_id`, `refunded_amount_usd`,
        and `message`.
    """
    normalized_order = order_id.strip().upper()
    order = _ORDERS_DB.get(normalized_order)
    if not order:
        return {
            "status": "error",
            "order_id": normalized_order,
            "message": f"Cannot refund unknown order '{normalized_order}'.",
        }

    if order["customer_id"] not in _VERIFIED_CUSTOMERS:
        return {
            "status": "error",
            "order_id": normalized_order,
            "policy_violation": "UNVERIFIED_IDENTITY",
            "message": (
                f"Refund blocked: customer '{order['customer_id']}' identity has not been "
                "verified with a valid 4-digit PIN."
            ),
        }

    eligibility = check_return_eligibility(normalized_order)
    if not eligibility["eligible"]:
        return {
            "status": "error",
            "order_id": normalized_order,
            "policy_violation": eligibility["policy_code"],
            "message": f"Refund blocked: {eligibility['reason']}",
        }

    order["refund_status"] = "REFUNDED"
    refund_id = f"RFND-{normalized_order.split('-')[-1]}"
    return {
        "status": "success",
        "order_id": normalized_order,
        "refund_id": refund_id,
        "refunded_amount_usd": order["amount_usd"],
        "reason_recorded": reason.strip(),
        "message": (
            f"Refund {refund_id} of ${order['amount_usd']:.2f} issued for "
            f"{normalized_order} ({order['item_name']})."
        ),
    }
