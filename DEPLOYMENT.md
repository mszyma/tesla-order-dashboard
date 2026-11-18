# Deployment notes (Railway)

The step-by-step guide is in `README.md` (section "Deploy to Railway"). This file only collects extra details.

## Environment variables

- `DASHBOARD_PASSWORD` (required): password for HTTP Basic Auth (user `admin`, or set `DASHBOARD_USER`). The dashboard shows VIN, address and financing; without a password it refuses all requests that do not come directly from localhost, so a Railway deployment returns 503.
- `SECRET_KEY`: random string for Flask sessions (random per start if unset).
- `TESLA_TOKENS_JSON`: content of your `tesla_tokens.json` (one line). Never put tokens in the repo.
- `PORT`: set by Railway.

## Notes

- Health check: `/health`.
- Data is cached for 1 hour; the browser auto-refreshes every 30 minutes. Tesla may rate-limit frequent requests.
- `/health` is the only route without authentication.

## Troubleshooting

1. "No order data available": press Refresh in the dashboard (needs valid tokens), or run `python3 tesla_order_status.py` locally first.
2. "No Tesla tokens found": set `TESLA_TOKENS_JSON` (Railway) or run `python3 tesla_order_status.py` (local).
3. Authentication errors: the refresh token may have expired. Log in again with `python3 tesla_order_status.py` and update `TESLA_TOKENS_JSON`.
4. App not starting: check Railway logs; `requirements.txt`, `Procfile` and `railway.toml` must be committed.
5. Health check failing: confirm the service listens on `$PORT` (the Procfile does this).
