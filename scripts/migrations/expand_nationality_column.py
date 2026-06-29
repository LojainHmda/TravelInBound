"""One-off: widen inbound_request.nationality for mixed-nationality labels (PostgreSQL). SQLite ignores length."""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    url = (db.engine.url.drivername or "").lower()
    if "postgresql" not in url and "postgres" not in url:
        print("Not PostgreSQL — no ALTER needed (SQLite stores TEXT). Model String(500) is enough.")
    else:
        try:
            with db.engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE inbound_request ALTER COLUMN nationality TYPE VARCHAR(500)"
                    )
                )
                conn.commit()
            print("OK: inbound_request.nationality widened to VARCHAR(500)")
        except Exception as e:
            print(f"Error (column may already be widened): {e}")
