import socket
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Ожидает доступности PostgreSQL перед запуском миграций."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=60)
        parser.add_argument("--interval", type=float, default=2.0)

    def handle(self, *args, **options):
        timeout = options["timeout"]
        interval = options["interval"]
        deadline = time.monotonic() + timeout

        connection = connections["default"]
        host = connection.settings_dict.get("HOST") or "localhost"
        port = int(connection.settings_dict.get("PORT") or 5432)

        self.stdout.write(f"Waiting for database {host}:{port} ...")

        last_error = None
        while time.monotonic() < deadline:
            try:
                socket.getaddrinfo(host, port)
                connection.ensure_connection()
            except (socket.gaierror, OperationalError) as exc:
                last_error = exc
                self.stdout.write(
                    self.style.WARNING(f"Database is unavailable: {exc}. Retrying...")
                )
                time.sleep(interval)
                continue

            self.stdout.write(self.style.SUCCESS("Database is available."))
            return

        raise CommandError(f"Database did not become available in {timeout}s: {last_error}")
