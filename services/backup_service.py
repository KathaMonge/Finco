import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config import DB_PATH, USER_DATA_DIR
from core.database import get_session
from core.models import Account, Category, Transaction


class BackupService:
    def export_db(self, destination: Path) -> Path:
        """Copy the SQLite database file to destination."""
        destination = Path(destination)
        if destination.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = destination / f"finco_backup_{timestamp}.db"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(DB_PATH), str(destination))
        return destination

    def import_db(self, backup_path: Path) -> None:
        """Restore a SQLite database from backup file."""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        shutil.copy2(str(backup_path), str(DB_PATH))

    def export_json(self, destination: Path) -> Path:
        """Export all data as JSON (human-readable backup)."""
        destination = Path(destination)
        if destination.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = destination / f"finco_export_{timestamp}.json"

        data = {"exported_at": datetime.now().isoformat()}
        with get_session() as session:
            data["accounts"] = [
                {
                    "id": a.id,
                    "name": a.name,
                    "type": a.type,
                    "balance": str(a.balance),
                    "icon": a.icon,
                    "created_at": a.created_at.isoformat(),
                }
                for a in session.query(Account).all()
            ]
            data["categories"] = [
                {
                    "id": c.id,
                    "name": c.name,
                    "icon": c.icon,
                    "color": c.color,
                    "monthly_budget": str(c.monthly_budget) if c.monthly_budget else None,
                    "is_system": c.is_system,
                }
                for c in session.query(Category).all()
            ]
            data["transactions"] = [
                {
                    "id": t.id,
                    "account_id": t.account_id,
                    "category_id": t.category_id,
                    "amount": str(t.amount),
                    "currency": t.currency,
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "type": t.type,
                    "receipt_image": t.receipt_image,
                    "ocr_confidence": t.ocr_confidence,
                    "created_at": t.created_at.isoformat(),
                    "deleted_at": t.deleted_at.isoformat() if t.deleted_at else None,
                }
                for t in session.query(Transaction).all()
            ]

        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return destination

    def export_csv(self, destination: Path) -> Path:
        """Export active transactions to CSV format."""
        import csv
        destination = Path(destination)
        if destination.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = destination / f"finco_transactions_{timestamp}.csv"

        destination.parent.mkdir(parents=True, exist_ok=True)
        with get_session() as session:
            txs = (
                session.query(Transaction)
                .filter(Transaction.deleted_at.is_(None))
                .order_by(Transaction.date.desc())
                .all()
            )
            with open(destination, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Fecha", "Tipo", "Monto", "Moneda",
                    "Descripción", "Categoría", "Cuenta"
                ])
                for t in txs:
                    cat_name = t.category.name if t.category else ""
                    acc_name = t.account.name if t.account else ""
                    writer.writerow([
                        t.id, t.date.isoformat(), t.type, str(t.amount),
                        t.currency, t.description, cat_name, acc_name
                    ])
        return destination


backup_service = BackupService()
