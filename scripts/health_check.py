"""Checks that the SMTP sender credential still authenticates. Run on a
low-frequency schedule (see .github/workflows/health-check.yml) to catch
credential rot before a real send fails. Exits non-zero on failure and
relies on GitHub Actions' own failed-workflow notification to report it
-- deliberately not sending an email itself, since a broken credential
can't reliably email you that it's broken."""

import os
import smtplib
import sys

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def main() -> int:
    sender_email = os.environ["SENDER_EMAIL"]
    app_password = os.environ["SMTP_APP_PASSWORD"]

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(sender_email, app_password)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    print("OK: SMTP login succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
