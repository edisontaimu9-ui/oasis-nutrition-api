"""
Management command: python manage.py seed_sources
Loads all SEED_SOURCES into the database.
"""

from django.core.management.base import BaseCommand
from articles.models import Source
from crawler.registry import SEED_SOURCES


class Command(BaseCommand):
    help = "Seed the database with default clinical nutrition news sources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing sources before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            count = Source.objects.count()
            Source.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing sources"))

        created = 0
        updated = 0

        for data in SEED_SOURCES:
            obj, was_created = Source.objects.update_or_create(
                name=data["name"],
                defaults={
                    "url":         data.get("url", ""),
                    "feed_url":    data.get("feed_url"),
                    "region":      data.get("region", "global"),
                    "source_type": data.get("source_type", "rss"),
                    "description": data.get("description", ""),
                    "logo_url":    data.get("logo_url"),
                    "is_active":   True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(f"  ✓ Created: {obj.name} [{obj.region}]")
            else:
                updated += 1
                self.stdout.write(f"  ~ Updated: {obj.name} [{obj.region}]")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {created} created, {updated} updated | "
                f"Total sources: {Source.objects.count()}"
            )
        )
        self.stdout.write(
            "\nNext step: python manage.py crawl_now"
        )
