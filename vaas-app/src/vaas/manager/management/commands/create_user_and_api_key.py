from django.core.management.base import BaseCommand
from tastypie.compat import User
from tastypie.models import ApiKey


class Command(BaseCommand):
    args = '<username email password api_key>'
    help = 'Creates superuser with specified username, email, password and (optional) api_key'

    def handle(self, *args, **options):
        if len(args) < 3:
            print('Exactly three/four arguments required: %s' % self.args)
        else:
            if len(args) == 3:
                username, email, password = args
                user = User.objects.create_superuser(username, email, password)
                tastypie_api_key = ApiKey.objects.create(user=user)
                tastypie_api_key.save()
            else:
                username, email, password, api_key = args
                user = User.objects.create_superuser(username, email, password)
                tastypie_api_key = ApiKey.objects.create(user=user)
                tastypie_api_key.key = api_key
                tastypie_api_key.save()
