

from ...models import UserDraftScorePoint
from django.core.management.base import BaseCommand, CommandParser
from datetime import datetime

format = "%Y-%m-%d"

class Command(BaseCommand):
  help = "Purge scorepoints."
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("before", type=str)

  def handle(self, *args, **options):
    before_datestring = options["before"]
    before = datetime.strptime(before_datestring, format)

    UserDraftScorePoint.objects.filter(time__lt=before).delete()
  