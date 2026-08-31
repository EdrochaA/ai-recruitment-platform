"""Remove closed and archived job offers and their associated data."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from gridfs import GridFS
from pymongo import MongoClient
from pymongo.database import Database


LOGGER = logging.getLogger("cleanup-inactive-job-offers")
BACKEND_DIR = Path(__file__).resolve().parents[1]
INACTIVE_STATUSES = ("closed", "archived")


@dataclass(frozen=True)
class OfferSummary:
    id: Any
    title: str
    status: str


@dataclass
class CleanupPlan:
    offers: list[OfferSummary]
    application_ids: list[Any]
    gridfs_file_ids: list[ObjectId]
    shared_storage_keys: list[str]
    invalid_storage_keys: list[str]
    missing_storage_keys: list[str]

    def fingerprint(self) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
        return (
            frozenset(str(offer.id) for offer in self.offers),
            frozenset(str(application_id) for application_id in self.application_ids),
            frozenset(str(file_id) for file_id in self.gridfs_file_ids),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete closed and archived job offers, their applications, "
            "and GridFS CVs that would become orphaned."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the cleanup summary without prompting or deleting data.",
    )
    return parser.parse_args()


def load_database_settings() -> tuple[str, str]:
    load_dotenv(BACKEND_DIR / ".env")

    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise RuntimeError("MONGODB_URL is not configured")

    database_name = os.getenv("MONGODB_DATABASE", "ai-recruitment-platform")
    return mongodb_url, database_name


def build_cleanup_plan(db: Database, fs: GridFS) -> CleanupPlan:
    offers_collection = db.get_collection("job_offers")
    applications_collection = db.get_collection("job_applications")

    offer_documents = list(
        offers_collection.find(
            {"status": {"$in": list(INACTIVE_STATUSES)}},
            {"title": 1, "status": 1},
        ).sort([("title", 1), ("_id", 1)])
    )
    offers = [
        OfferSummary(
            id=document["_id"],
            title=str(document.get("title") or "(sin titulo)"),
            status=str(document.get("status") or "unknown"),
        )
        for document in offer_documents
    ]
    offer_id_strings = [str(offer.id) for offer in offers]

    applications = list(
        applications_collection.find(
            {"job_offer_id": {"$in": offer_id_strings}},
            {"cv_storage_key": 1},
        )
    )
    application_ids = [application["_id"] for application in applications]

    storage_keys = sorted(
        {
            str(application["cv_storage_key"]).strip()
            for application in applications
            if application.get("cv_storage_key")
        }
    )

    gridfs_file_ids: list[ObjectId] = []
    shared_storage_keys: list[str] = []
    invalid_storage_keys: list[str] = []
    missing_storage_keys: list[str] = []

    for storage_key in storage_keys:
        try:
            file_id = ObjectId(storage_key)
        except (InvalidId, TypeError):
            invalid_storage_keys.append(storage_key)
            continue

        retained_reference = applications_collection.find_one(
            {
                "_id": {"$nin": application_ids},
                "cv_storage_key": {"$in": [storage_key, file_id]},
            },
            {"_id": 1},
        )
        if retained_reference:
            shared_storage_keys.append(storage_key)
        elif fs.exists(file_id):
            gridfs_file_ids.append(file_id)
        else:
            missing_storage_keys.append(storage_key)

    return CleanupPlan(
        offers=offers,
        application_ids=application_ids,
        gridfs_file_ids=gridfs_file_ids,
        shared_storage_keys=shared_storage_keys,
        invalid_storage_keys=invalid_storage_keys,
        missing_storage_keys=missing_storage_keys,
    )


def print_summary(plan: CleanupPlan, database_name: str, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "REAL"
    print("=" * 72)
    print(f"LIMPIEZA DE OFERTAS INACTIVAS - MODO {mode}")
    print(f"Base de datos: {database_name}")
    print(f"Estados incluidos: {', '.join(INACTIVE_STATUSES)}")
    print("=" * 72)
    print(f"Ofertas que se borrarian: {len(plan.offers)}")
    for offer in plan.offers:
        print(f"  - [{offer.status}] {offer.title} (id={offer.id})")

    print(f"Candidaturas asociadas que se borrarian: {len(plan.application_ids)}")
    print(f"Archivos GridFS huerfanos que se borrarian: {len(plan.gridfs_file_ids)}")

    if plan.shared_storage_keys:
        print(
            "Archivos GridFS conservados por tener otras referencias: "
            f"{len(plan.shared_storage_keys)}"
        )
        for storage_key in plan.shared_storage_keys:
            print(f"  - storage_key={storage_key}")

    if plan.invalid_storage_keys:
        print(
            "Claves de almacenamiento invalidas que se omitiran: "
            f"{len(plan.invalid_storage_keys)}"
        )
        for storage_key in plan.invalid_storage_keys:
            print(f"  - storage_key={storage_key}")

    if plan.missing_storage_keys:
        print(
            "Claves sin archivo existente en GridFS: "
            f"{len(plan.missing_storage_keys)}"
        )
        for storage_key in plan.missing_storage_keys:
            print(f"  - storage_key={storage_key}")

    print("=" * 72)


def execute_cleanup(db: Database, fs: GridFS, plan: CleanupPlan) -> None:
    applications_collection = db.get_collection("job_applications")
    offers_collection = db.get_collection("job_offers")
    offer_id_strings = [str(offer.id) for offer in plan.offers]

    for file_id in plan.gridfs_file_ids:
        LOGGER.info("Deleting GridFS file id=%s", file_id)
        fs.delete(file_id)
        LOGGER.info("Deleted GridFS file id=%s", file_id)

    for application_id in plan.application_ids:
        LOGGER.info("Deleting job application id=%s", application_id)
        result = applications_collection.delete_one(
            {
                "_id": application_id,
                "job_offer_id": {"$in": offer_id_strings},
            }
        )
        if result.deleted_count != 1:
            raise RuntimeError(
                f"Expected to delete job application {application_id}, but it was not deleted"
            )
        LOGGER.info("Deleted job application id=%s", application_id)

    for offer in plan.offers:
        LOGGER.info(
            "Deleting job offer id=%s title=%r status=%s",
            offer.id,
            offer.title,
            offer.status,
        )
        result = offers_collection.delete_one(
            {
                "_id": offer.id,
                "status": {"$in": list(INACTIVE_STATUSES)},
            }
        )
        if result.deleted_count != 1:
            raise RuntimeError(
                f"Expected to delete job offer {offer.id}, but it was not deleted"
            )
        LOGGER.info("Deleted job offer id=%s title=%r", offer.id, offer.title)


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    client: MongoClient | None = None
    try:
        mongodb_url, database_name = load_database_settings()
        LOGGER.info("Connecting to MongoDB database=%s", database_name)
        client = MongoClient(mongodb_url)
        client.admin.command("ping")
        db = client[database_name]
        fs = GridFS(db)
        LOGGER.info("Connected to MongoDB database=%s", database_name)

        plan = build_cleanup_plan(db, fs)
        print_summary(plan, database_name, args.dry_run)

        if args.dry_run:
            LOGGER.info("Dry run completed. No data was deleted.")
            return 0

        if not plan.offers:
            LOGGER.info("No closed or archived job offers found. Nothing to delete.")
            return 0

        confirmation = input(
            "Escribe SI para borrar permanentemente estos datos: "
        ).strip()
        if confirmation != "SI":
            LOGGER.info("Cleanup cancelled. No data was deleted.")
            return 0

        refreshed_plan = build_cleanup_plan(db, fs)
        if refreshed_plan.fingerprint() != plan.fingerprint():
            LOGGER.error(
                "The cleanup target changed after the summary was generated. "
                "No data was deleted; run the script again."
            )
            print_summary(refreshed_plan, database_name, dry_run=False)
            return 2

        execute_cleanup(db, fs, refreshed_plan)
        LOGGER.info(
            "Cleanup completed: offers=%d applications=%d gridfs_files=%d",
            len(refreshed_plan.offers),
            len(refreshed_plan.application_ids),
            len(refreshed_plan.gridfs_file_ids),
        )
        return 0
    except KeyboardInterrupt:
        LOGGER.warning("Cleanup interrupted. Review the logs before retrying.")
        return 130
    except Exception:
        LOGGER.exception("Cleanup failed")
        return 1
    finally:
        if client is not None:
            client.close()
            LOGGER.info("MongoDB connection closed")


if __name__ == "__main__":
    sys.exit(main())