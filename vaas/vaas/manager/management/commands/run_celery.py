import os
import sys
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from subprocess import Popen
from threading import Thread
from time import sleep

from django.core.management.base import BaseCommand


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """Provides '/status/ping' endpoint meant for health checks. Rejects all
    methods except GET.
    """

    def _send_response(self, status_code, headers, msg):
        self.send_response(status_code)
        for header in headers:
            self.send_header(*header)
        self.end_headers()
        self.wfile.write(msg.encode(encoding='utf_8'))

    def _not_found_or_not_allowed(self):
        if self.path.rstrip('/') != '/status/ping':
            status_code = 404
            message = "Not Found\n"
        else:
            status_code = 405
            message = "Method Not Allowed\n"
        headers = [('Content-Type', 'text/plain')]
        self._send_response(status_code, headers, message)

    def do_GET(self):
        headers = [('Content-Type', 'text/plain')]
        if self.path.rstrip('/') == '/status/ping':
            self._send_response(200, headers, "OK\n")
        else:
            self._send_response(404, headers, "Not Found\n")

    def do_POST(self):
        self._not_found_or_not_allowed()

    def do_PUT(self):
        self._not_found_or_not_allowed()


class Command(BaseCommand):
    help = ('Wrapper around "run_celery" management command adding a HTTP '
            'endpoint "/status/ping" for health checks, which may be useful '
            'when Celery is run on environments like Mesos or Kubernetes')

    def add_arguments(self, parser):
        parser.add_argument(
            '--health-check-port',
            action='store',
            dest='health-check-port',
            default=8000,
            type=int,
            help='HTTP port number where server is listening',
        )
        parser.add_argument(
            '--project',
            action='store',
            dest='project',
            default='config',
            type=str,
            help='The project name with Celery will start',
        )
        parser.add_argument(
            '--type',
            action='store',
            choices=['worker', 'scheduler'],
            dest='type',
            default='worker',
            type=str,
            help='The project name with Celery will start',
        )
        parser.add_argument(
            '--workdir',
            action='store',
            dest='workdir',
            default='/home/app/hiena',
            type=str,
            help='Number of thread for celery worker',
        )
        parser.add_argument(
            '--loglevel',
            action='store',
            dest='loglevel',
            default='DEBUG',
            type=str,
            help='Loglevel for celery [DEBUG, INFO, WARNING]',
        )
        parser.add_argument(
            '--concurrency',
            action='store',
            dest='concurrency',
            default=1,
            type=int,
            help='Number of thread for celery worker',
        )
        parser.add_argument(
            '--queue',
            nargs="+",
            action='store',
            dest='queue',
            type=str,
            help='Specify queues names to inclusively process them on this worker',
        )
        parser.add_argument(
            '--thread-timeout',
            action='store',
            dest='thread-timeout',
            default=30.,
            type=float,
            help='Timeout parameter for thread termination',
        )

    def handle(self, *args, **options):
        def create_new_server():
            address = ('', port)  # first element here is for hostname
            handler = HTTPServer(address, HTTPRequestHandler)
            thread = Thread(target=handler.serve_forever,
                            name="HTTP server")
            return thread, handler

        def graceful_shutdown(reason=None):
            if reason is not None:
                print(f"{reason} Shutting down...")
            else:
                print("Shutting down...")
            if subp.poll() is None:
                subp.terminate()
                sleep(3)
                if subp.poll() is None:
                    subp.kill()
            server_handler.shutdown()
            server_thread.join(timeout=options['thread-timeout'])
            sys.exit()

        def signal_handler(signum, stack):
            reason = f"Received signal {signum}."
            graceful_shutdown(reason)

        signal.signal(signal.SIGTERM, signal_handler)
        self.stdout.write('Starting wrapper around "celery"...')
        port = options['health-check-port']
        server_thread, server_handler = create_new_server()
        server_thread.start()
        self.stdout.write(f'HTTP server is listening on port {port}.')
        cmd = ['/usr/local/bin/celery']
        cmd.append(f"--workdir={options['workdir']}")
        cmd.append(f"--app={options['project']}")
        if options['type'] == 'scheduler':
            cmd.append('beat')
            cmd.append('--scheduler=django_celery_beat.schedulers:DatabaseScheduler')
        else:
            cmd.append('worker')
            cmd.append(f"--concurrency={options['concurrency']}")
        cmd.append(f"--loglevel={options['loglevel']}")
        if options['queue']:
            cmd.append(f"--queues={','.join(options['queue'])}")
        env = dict(os.environ)
        self.stdout.write(f'Starting Celery... {cmd}')
        try:
            subp = Popen(cmd, env=env, stdout=sys.stdout, stderr=sys.stdout)
            while True:
                subp_status = subp.poll()
                if subp_status is None:  # Celery is still alive
                    if not server_thread.is_alive():
                        server_thread.join(timeout=options['thread-timeout'])
                        server_thread, server_handler = create_new_server()
                        self.stdout.write('Restarting HTTP server...')
                        server_thread.start()
                    sleep(0.5)
                else:
                    reason = "Celery subprocess is dead."
                    graceful_shutdown(reason)
        except KeyboardInterrupt:
            graceful_shutdown()
