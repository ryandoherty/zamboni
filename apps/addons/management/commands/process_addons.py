from optparse import make_option

from django.core.management.base import BaseCommand

from addons.models import Addon
from amo.utils import chunked
from devhub.tasks import convert_purified, flag_binary, get_preview_sizes


tasks = {
    'flag_binary': {'method': flag_binary, 'qs': []},
    'get_preview_sizes': {'method': get_preview_sizes, 'qs': []},
    'convert_purified': {'method': convert_purified, 'qs': []}
}


class Command(BaseCommand):
    """
    A generic command to run a task on addons.
    Add tasks to the tasks dictionary, providing a list of Q objects if you'd
    like to filter the list down.
    """
    option_list = BaseCommand.option_list + (
        make_option('--task', action='store', type='string',
                    dest='task', help='Run task on the addons.'),
    )

    def handle(self, *args, **options):
        task = tasks.get(options.get('task'))
        if not task:
            raise ValueError('Unknown task: %s' % ', '.join(tasks.keys()))
        pks = (Addon.objects.filter(*task['qs'])
                            .values_list('pk', flat=True)
                            .order_by('id'))
        for chunk in chunked(pks, 100):
            task['method'].delay(chunk)
