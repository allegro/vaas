from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tastypie.models import ApiKey


class Command(BaseCommand):
    help = 'Creates superuser with specified username, email, password and (optional) api_key'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('email')
        parser.add_argument('password')
        parser.add_argument('api_key', nargs='?')

    def handle(self, *args, **options):
        if len(args) == 3:
            username = options['username']
            email = options['email']
            password = options['password']
            user = User.objects.create_superuser(username, email, password)
            tastypie_api_key = ApiKey.objects.create(user=user)
            tastypie_api_key.save()
        else:
            username = options['username']
            email = options['email']
            password = options['password']
            api_key = options['api_key']
            user = User.objects.create_superuser(username, email, password)
            tastypie_api_key = ApiKey.objects.create(user=user)
            tastypie_api_key.key = api_key
            tastypie_api_key.save()
