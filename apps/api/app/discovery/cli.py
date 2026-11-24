import argparse
import asyncio
import json

from app.db.session import SessionLocal

from app.discovery.orchestrator import (
    DiscoveryOrchestrator,
)

from app.discovery.registry import list_adapters

from app.discovery.source_registration import (
    register_source,
)

from app.services.discovery import DiscoveryService


async def execute(args):

    if args.list_sources:

        print("AVAILABLE ADAPTERS:")

        for source in list_adapters():
            print(f" - {source}")

        return 0

    if args.register_sources:

        with SessionLocal() as db:

            for identifier in list_adapters():

                source = register_source(
                    db,
                    identifier,
                )

                print(
                    f"{source.source_identifier}: "
                    f"enabled={source.enabled}"
                )

            db.commit()

        return 0

    if args.approve_source:

        with SessionLocal() as db:

            source = register_source(
                db,
                args.approve_source,
                access_approved=True,
                access_notes=args.access_notes,
            )

            db.commit()

            print(
                f"Approved: "
                f"{source.source_identifier}"
            )

        return 0

    if args.dry_run:

        summary = await DiscoveryOrchestrator().run(
            sources=(
                [args.source]
                if args.source
                else None
            ),
            limit=args.limit,
        )

        print(
            summary.model_dump_json(indent=2)
        )

        return 1 if summary.failed_sources else 0

    if args.persist:

        with SessionLocal() as db:

            service = DiscoveryService(db)

            try:

                result = await service.run_source(
                    args.source,
                    args.limit,
                )

            except ValueError as error:

                print(str(error))

                return 1

            print(
                json.dumps(
                    result,
                    indent=2,
                )
            )

            return (
                0
                if result["status"] == "completed"
                else 1
            )

    return 1


def main():

    parser = argparse.ArgumentParser(
        description="HackRadar AI Discovery Engine"
    )

    parser.add_argument(
        "--source",
        choices=list_adapters(),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )

    modes = parser.add_mutually_exclusive_group(
        required=True
    )

    modes.add_argument(
        "--list-sources",
        action="store_true",
    )

    modes.add_argument(
        "--register-sources",
        action="store_true",
    )

    modes.add_argument(
        "--dry-run",
        action="store_true",
    )

    modes.add_argument(
        "--persist",
        action="store_true",
    )

    modes.add_argument(
        "--approve-source",
        choices=list_adapters(),
    )

    parser.add_argument(
        "--access-notes",
        type=str,
    )

    args = parser.parse_args()

    if args.limit < 1:
        parser.error(
            "--limit must be positive."
        )

    if args.persist and not args.source:
        parser.error(
            "--persist requires --source."
        )

    if (
        args.approve_source
        and not (
            args.access_notes
            and args.access_notes.strip()
        )
    ):
        parser.error(
            "Source approval requires "
            "--access-notes."
        )

    raise SystemExit(
        asyncio.run(execute(args))
    )


if __name__ == "__main__":
    main()