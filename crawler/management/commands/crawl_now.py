"""
Management command: python manage.py crawl_now [--source-id N]
Manually triggers a crawl from the terminal.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Manually trigger a news crawl for all sources or a specific source"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-id",
            type=int,
            default=None,
            help="Crawl a specific source by ID (default: all active sources)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all active sources and their IDs",
        )

    def handle(self, *args, **options):
        from articles.models import Source

        if options["list"]:
            sources = Source.objects.filter(is_active=True).order_by("region", "name")
            self.stdout.write(f"\n{'ID':<5} {'Region':<10} {'Name'}")
            self.stdout.write("-" * 50)
            for s in sources:
                self.stdout.write(f"{s.id:<5} {s.region:<10} {s.name}")
            return

        source_id = options["source_id"]

        if source_id:
            self.stdout.write(f"Crawling source ID {source_id}...")
            from crawler.scheduler import crawl_single_source
            log = crawl_single_source(source_id, triggered_by="management_command")
            if log:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Done — {log.articles_new} new / {log.articles_found} found"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR("Source not found or inactive"))
        else:
            self.stdout.write("Crawling all active sources...")
            from crawler.scheduler import crawl_all_sources
            crawl_all_sources(triggered_by="management_command")
            self.stdout.write(self.style.SUCCESS("Full crawl complete — check logs"))
