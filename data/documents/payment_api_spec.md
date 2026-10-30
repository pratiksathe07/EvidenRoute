# Payment API & Gateway Specification (v2.4)

## Overview
The EvidenRoute Payment Gateway provides unified payment processing for credit cards, ACH, and digital wallets.

## Authentication
All requests must pass an `Authorization: Bearer <API_KEY>` header.

## Endpoint: Process Charge
- **Method:** `POST /v1/payments/charge`
- **Headers:** `Idempotency-Key: <UUID>`
- **Payload:**
  ```json
  {
    "amount": 4900,
    "currency": "usd",
    "customer_id": "cust_98124",
    "payment_method": "pm_card_visa"
  }
  ```

## Common Failure Modes & Error Codes
- `ERR_PAYMENT_GATEWAY_TIMEOUT (504)`: Upstream bank processor did not respond within 5000ms.
- `ERR_DB_CONNECTION_EXHAUSTION (500)`: Payment ledger database pool saturated after rolling deployment.
- `ERR_INVALID_IDEMPOTENCY_KEY (400)`: Duplicate or expired idempotency token.

## Deployment Notes (Release 2026.10-rc2)
During the recent 2026.10 deployment, connection pool timeouts were observed due to aggressive keep-alive settings on the reverse proxy. Ensure `MAX_DB_POOL_SIZE` is at least 50.
