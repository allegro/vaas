# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import json

import os
import environ

from typing import Optional
from vaas.configuration.loader import YamlConfigLoader


env = environ.Env()


def serialize(value: any) -> str:
    if type(value) in (dict, list, tuple):
        return json.dumps(value)
    return str(value)


config_loader = YamlConfigLoader(["/configuration"])
if config_loader.determine_config_file("config.yaml"):
    # Here we create environments variables from configuration repository and ensure that we have uppercase naming
    os.environ.update(
        {
            k.upper(): serialize(v)
            for k, v in config_loader.get_config_tree("config.yaml").items()
        }
    )

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
current_dir = os.path.abspath(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", default="notproductionsecret")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)
TEMPLATE_DEBUG = env.bool("TEMPLATE_DEBUG", default=False)

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = env.json("ALLOWED_HOSTS", default=[])

MESSAGE_STORAGE = env.str(
    "MESSAGE_STORAGE", default="django.contrib.messages.storage.session.SessionStorage"
)

# Application definition
INSTALLED_APPS = (
    "vaas.adminext",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "tastypie",
    "vaas.manager",
    "vaas.cluster",
    "vaas.router",
    "vaas.monitor",
    "vaas.account",
    "vaas.purger",
    "taggit",
    "django_ace",
    "simple_history",
)

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "log_request_id.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "vaas.manager.middleware.VclRefreshMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

# Plugins definition
INSTALLED_PLUGINS = tuple(env.json("INSTALLED_PLUGINS", default=[]))
INSTALLED_APPS = INSTALLED_PLUGINS + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + env.json("MIDDLEWARE_PLUGINS", default=[])

SOCIAL_AUTH_LOGIN_REDIRECT_URL = env.str(
    "SOCIAL_AUTH_LOGIN_REDIRECT_URL", default="/admin/"
)

SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)

ROOT_URLCONF = env.str("ROOT_URLCONF", default="vaas.urls")

WSGI_APPLICATION = env.str("WSGI_APPLICATION", default="vaas.external.wsgi.application")

SIGNALS = env.str("SIGNALS", default="on")

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = env.str("STATIC_URL", default="/static/")
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

DATABASES = env.json(
    "DATABASES",
    default={
        "default": {
            "ENGINE": "vaas.db",
            "NAME": "vaas",
            "USER": "root",
            "PASSWORD": "password",
            "HOST": "mysql",
        }
    },
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": env.str("CONSOLE_LOG_FORMATTER", default="verbose"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": False,
            "level": "ERROR",
        },
        "vaas": {
            "handlers": ["console"],
            "propagate": False,
            "level": "DEBUG",
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

VAAS_LOADER_PARTIAL_RELOAD = env.bool("VAAS_LOADER_PARTIAL_RELOAD", default=False)
VAAS_LOADER_MAX_WORKERS = env.int("VAAS_LOADER_MAX_WORKERS", default=30)
VAAS_RENDERER_MAX_WORKERS = env.int("VAAS_RENDERER_MAX_WORKERS", default=30)
VAAS_GATHER_STATUSES_MAX_WORKERS = env.int(
    "VAAS_GATHER_STATUSES_MAX_WORKERS", default=50
)
VAAS_GATHER_STATUSES_CONNECT_TIMEOUT = env.float(
    "VAAS_GATHER_STATUSES_CONNECT_TIMEOUT", default=0.1
)

REFRESH_TRIGGERS_CLASS = tuple(
    env.json(
        "REFRESH_TRIGGERS_CLASS",
        default=(
            "Probe",
            "Backend",
            "Director",
            "VarnishServer",
            "VclTemplate",
            "VclTemplateBlock",
            "TimeProfile",
            "VclVariable",
            "Route",
            "Redirect",
        ),
    )
)

CELERY_TASK_RESULT_EXPIRES = env.int("CELERY_TASK_RESULT_EXPIRES", default=600)
CELERY_TASK_SERIALIZER = env.str("CELERY_TASK_SERIALIZER", default="json")
CELERY_RESULT_SERIALIZER = env.str("CELERY_RESULT_SERIALIZER", default="json")
CELERY_IGNORE_RESULT = env.bool("CELERY_IGNORE_RESULT", default=False)
CELERY_TASK_PUBLISH_RETRY = env.bool("CELERY_TASK_PUBLISH_RETRY", default=True)
CELERY_BEAT_MAX_LOOP_INTERVAL = env.int("CELERY_BEAT_MAX_LOOP_INTERVAL", default=300)

# 5min we will wait for kill task
CELERY_TASK_SOFT_TIME_LIMIT_SECONDS = env.int(
    "CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", default=300
)

CELERY_TASK_REJECT_ON_WORKER_LOST = env.bool(
    "CELERY_TASK_REJECT_ON_WORKER_LOST", default=False
)

CELERY_ROUTES = {
    "vaas.router.report.fetch_urls_async": {"queue": "routes_test_queue"},
    "vaas.cluster.cluster.connect_command": {"queue": "routes_test_queue"},
    "vaas.monitor.tasks.refresh_backend_statuses": {"queue": "cron_queue"},
    "vaas.*": {"queue": "worker_queue"},
}

BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS = env.int(
    "BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS", default=120
)

VARNISH_COMMAND_TIMEOUT = env.int("VARNISH_COMMAND_TIMEOUT", default=5)
VARNISH_VCL_INLINE_COMMAND_TIMEOUT = env.int(
    "VARNISH_VCL_INLINE_COMMAND_TIMEOUT", default=60
)

# UWSGI CONTEXT SWITCH (UGREEN)
ENABLE_UWSGI_SWITCH_CONTEXT = env.bool("ENABLE_UWSGI_SWITCH_CONTEXT", default=False)

VCL_TEMPLATE_COMMENT_REGEX = env.str("VCL_TEMPLATE_COMMENT_REGEX", default=None)
VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE = env.str(
    "VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE", default=None
)

DEFAULT_VCL_VARIABLES = env.json(
    "DEFAULT_VCL_VARIABLES",
    default={
        "MESH_IP": "127.0.0.1",
        "MESH_PORT": "31001",
        "MESH_TIMEOUT_CONTROL_HEADER": "x-service-mesh-timeout",
    },
)

PURGER_HTTP_CLIENT_TIMEOUT = env.int("PURGER_HTTP_CLIENT_TIMEOUT", default=10)
PURGER_MAX_HTTP_WORKERS = env.int("PURGER_MAX_HTTP_WORKERS", default=100)

# VALIDATION_HEADER
VALIDATION_HEADER = env.str("VALIDATION_HEADER", default="x-validation")

FETCHER_HTTP_CLIENT_TIMEOUT = env.int("FETCHER_HTTP_CLIENT_TIMEOUT", default=10)
FETCHER_MAX_HTTP_WORKERS = env.int("FETCHER_MAX_HTTP_WORKERS", default=100)

# ENABLE RUN TEST BUTTON
ROUTE_TESTS_ENABLED = env.bool("ROUTE_TESTS_ENABLED", default=True)

# STATSD ENV
STATSD_ENABLE = env.bool("STATSD_ENABLE", default=False)
STATSD_HOST = env.str("STATSD_HOST", default="localhost")
STATSD_PORT = env.int("STATSD_PORT", default=8125)
STATSD_PREFIX = env.str("STATSD_PREFIX", default="example.statsd.path")

# PROMETHEUS PUSH_GATEWAY
PROMETHEUS_ENABLE = env.bool("PROMETHEUS_ENABLE", default=False)
if PROMETHEUS_ENABLE:
    INSTALLED_APPS = INSTALLED_APPS + ("django_prometheus",)
    MIDDLEWARE.insert(0, "django_prometheus.middleware.PrometheusBeforeMiddleware")
    MIDDLEWARE.append("django_prometheus.middleware.PrometheusAfterMiddleware")

PROMETHEUS_EXPORTER_PATH = env.str("PROMETHEUS_EXPORTER_PATH", default="metrics")
PROMETHEUS_GATEWAY_HOST = env.str("PROMETHEUS_GATEWAY_HOST", default="localhost")
PROMETHEUS_GATEWAY_PORT = env.int("PROMETHEUS_GATEWAY_PORT", default=9091)
PROMETHEUS_GATEWAY_JOB = env.str("PROMETHEUS_GATEWAY_JOB", default="vaas")
# Please in env definition stick to the proscription: name=value,second=value
# It will transfer to: {name: value, second: value}.
PROMETHEUS_GATEWAY_LABELS = env.dict("PROMETHEUS_GATEWAY_LABELS", default={})

# We also allow push metric via victoriametrics agent.
# https://docs.victoriametrics.com/#how-to-import-data-in-prometheus-exposition-format
VICTORIAMETRICS_SUPPORT = env.bool("VICTORIAMETRICS_SUPPORT", default=False)
VICTORIAMETRICS_PATH = env.str(
    "VICTORIAMETRICS_PATH", default="/api/v1/import/prometheus"
)

# HEADER FOR PERMIT ACCESS TO /vaas/ ENDPOINT
ALLOW_METRICS_HEADER = env.bool("ALLOW_METRICS_HEADER", default="x-allow-metric-header")

CLUSTER_IN_SYNC_ENABLED = env.bool("CLUSTER_IN_SYNC_ENABLED", default=False)
CLUSTER_IN_SYNC_HIDDEN = env.bool("CLUSTER_IN_SYNC_HIDDEN", default=False)
MESH_X_ORIGINAL_HOST = env.str("MESH_X_ORIGINAL_HOST", default="x-original-host")
SERVICE_TAG_HEADER = env.str("SERVICE_TAG_HEADER", default="x-service-tag")

# If file exists in specified path /vaas_status endpoint will return HTTP 503 code
VAAS_STATUS_CODE_503_TRIGGER_FILE = env.str(
    "VAAS_STATUS_CODE_503_TRIGGER_FILE", default="/etc/vaas_status_503"
)


# CELERY
def generate_redis_url(
    hostname: str, port: int, db_number: int, password: Optional[str] = None
) -> str:
    if password:
        return f"redis://:{password}@{hostname}:{port}/{db_number}"
    return f"redis://{hostname}:{port}/{db_number}"


REDIS_HOSTNAME = env.str("REDIS_HOSTNAME", default="redis")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
BROKER_DB_NUMBER = env.int("BROKER_DB_NUMBER", default=0)
CELERY_RESULT_DB_NUMBER = env.int("CELERY_RESULT_DB_NUMBER", default=1)
REDIS_PASSWORD = env.str("REDIS_PASSWORD", default=None)
REDIS_BACKEND_HEALTH_CHECK_INTERVAL_SEC = env.int(
    "REDIS_BACKEND_HEALTH_CHECK_INTERVAL_SEC", default=60
)
REDIS_SOCKET_KEEPALIVE = env.int("REDIS_SOCKET_KEEPALIVE", default=True)
REDIS_RETRY_ON_TIMEOUT = env.int("REDIS_RETRY_ON_TIMEOUT", default=True)
REDIS_SOCKET_CONNECT_TIMEOUT = env.int("REDIS_SOCKET_CONNECT_TIMEOUT", default=5)
REDIS_SOCKET_TIMEOUT = env.int("REDIS_SOCKET_TIMEOUT", default=120)

BROKER_URL = generate_redis_url(
    hostname=REDIS_HOSTNAME,
    port=REDIS_PORT,
    db_number=BROKER_DB_NUMBER,
    password=REDIS_PASSWORD,
)
CELERY_RESULT_BACKEND = generate_redis_url(
    hostname=REDIS_HOSTNAME,
    port=REDIS_PORT,
    db_number=CELERY_RESULT_DB_NUMBER,
    password=REDIS_PASSWORD,
)


ROUTES_LEFT_CONDITIONS = {}
for condition in env.json(
    "ROUTES_LEFT_CONDITIONS",
    default=[
        {"name": "req.url", "value": "URL"},
        {"name": "req.http.Host", "value": "Domain"},
        {"name": "req.http.X-Example", "value": "X-Example"},
    ],
):
    ROUTES_LEFT_CONDITIONS[condition["name"]] = condition["value"]

ROUTES_CANARY_HEADER = env.str("ROUTES_CANARY_HEADER", default="x-canary-random")
if ROUTES_CANARY_HEADER:
    ROUTES_LEFT_CONDITIONS[f"std.real(req.http.{ROUTES_CANARY_HEADER},0)"] = "Canary"

DOMAIN_MAPPER = {}
for entry in env.json(
    "DOMAIN_MAPPER",
    default=[
        {"name": "example.com", "value": "example.com"},
        {"name": "example.pl", "value": "example.{{ PLACEHOLDER }}.pl"},
    ],
):
    DOMAIN_MAPPER[entry["name"]] = entry["value"]
REDIRECT_CUSTOM_HEADER = env.str("REDIRECT_CUSTOM_HEADER", default="x-internal-network")
REDIRECT_CUSTOM_HEADER_LABEL = env.str(
    "REDIRECT_CUSTOM_HEADER_LABEL",
    default="Require {} header".format(REDIRECT_CUSTOM_HEADER),
)


DEFAULT_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title)
    "site_title": None,
    # Title on the login screen (19 chars max) (will default to current_admin_site.site_header)
    "site_header": None,
    # Title on the brand (19 chars max) (will default to current_admin_site.site_header)
    "site_brand": None,
    # Relative path to logo for your site, used for brand on top left (must be present in static files)
    "site_logo": "vendor/adminlte/img/AdminLTELogo.png",
    # Relative path to logo for your site, used for login logo (must be present in static files. Defaults to site_logo)
    "login_logo": None,
    # Logo to use for login form in dark themes (must be present in static files. Defaults to login_logo)
    "login_logo_dark": None,
    # CSS classes that are applied to the logo
    "site_logo_classes": "img-circle",
    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,
    # Welcome text on the login screen
    "welcome_sign": "Welcome",
    # Copyright on the footer
    "copyright": "",
    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": None,
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the nav bar
    "topmenu_links": [],
    #############
    # User Menu #
    #############
    # Additional links to include in the user menu on the top right ('app' url type is not allowed)
    "usermenu_links": [],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],
    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],
    # List of apps to base side menu ordering off of
    "order_with_respect_to": [],
    # Custom links to append to side menu app groups, keyed on lower case app label
    # or makes a new group if the given app label doesnt exist in installed apps
    "custom_links": {},
    # Custom icons for side menu apps/models See the link below
    # https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,
    # 5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,
    # 5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Activate Bootstrap modal
    "related_modal_active": False,
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,
    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {},
    # Add a language dropdown into the admin
    "language_chooser": False,
}

#######################################
# Currently available UI tweaks       #
# Use the UI builder to generate this #
#######################################

DEFAULT_UI_TWEAKS = {
    # Small text on the top navbar
    "navbar_small_text": False,
    # Small text on the footer
    "footer_small_text": False,
    # Small text everywhere
    "body_small_text": False,
    # Small text on the brand/logo
    "brand_small_text": False,
    # brand/logo background colour
    "brand_colour": False,
    # Link colour
    "accent": "accent-primary",
    # topmenu colour
    "navbar": "navbar-white navbar-light",
    # topmenu border
    "no_navbar_border": False,
    # Make the top navbar sticky, keeping it in view as you scroll
    "navbar_fixed": False,
    # Whether to constrain the page to a box (leaving big margins at the side)
    "layout_boxed": False,
    # Make the footer sticky, keeping it in view all the time
    "footer_fixed": False,
    # Make the sidebar sticky, keeping it in view as you scroll
    "sidebar_fixed": False,
    # sidemenu colour
    "sidebar": "sidebar-dark-primary",
    # sidemenu small text
    "sidebar_nav_small_text": False,
    # Disable expanding on hover of collapsed sidebar
    "sidebar_disable_expand": False,
    # Indent child menu items on sidebar
    "sidebar_nav_child_indent": False,
    # Use a compact sidebar
    "sidebar_nav_compact_style": False,
    # Use the AdminLTE2 style sidebar
    "sidebar_nav_legacy_style": False,
    # Use a flat style sidebar
    "sidebar_nav_flat_style": False,
    # Bootstrap theme to use (default, or from bootswatch, see THEMES below)
    "theme": "default",
    # Theme to use instead if the user has opted for dark mode (e.g darkly/cyborg/slate/solar/superhero)
    "dark_mode_theme": None,
    # The classes/styles to use with buttons
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

THEMES = {
    # light themes
    "default": "vendor/bootswatch/default/bootstrap.min.css",
    "cerulean": "vendor/bootswatch/cerulean/bootstrap.min.css",
    "cosmo": "vendor/bootswatch/cosmo/bootstrap.min.css",
    "flatly": "vendor/bootswatch/flatly/bootstrap.min.css",
    "journal": "vendor/bootswatch/journal/bootstrap.min.css",
    "litera": "vendor/bootswatch/litera/bootstrap.min.css",
    "lumen": "vendor/bootswatch/lumen/bootstrap.min.css",
    "lux": "vendor/bootswatch/lux/bootstrap.min.css",
    "materia": "vendor/bootswatch/materia/bootstrap.min.css",
    "morph": "vendor/bootswatch/morph/bootstrap.min.css",
    "minty": "vendor/bootswatch/minty/bootstrap.min.css",
    "pulse": "vendor/bootswatch/pulse/bootstrap.min.css",
    "sandstone": "vendor/bootswatch/sandstone/bootstrap.min.css",
    "simplex": "vendor/bootswatch/simplex/bootstrap.min.css",
    "sketchy": "vendor/bootswatch/sketchy/bootstrap.min.css",
    "spacelab": "vendor/bootswatch/spacelab/bootstrap.min.css",
    "united": "vendor/bootswatch/united/bootstrap.min.css",
    "yeti": "vendor/bootswatch/yeti/bootstrap.min.css",
    "quartz": "vendor/bootswatch/quartz/bootstrap.min.css",
    "zephyr": "vendor/bootswatch/zephyr/bootstrap.min.css",
    # dark themes
    "darkly": "vendor/bootswatch/darkly/bootstrap.min.css",
    "cyborg": "vendor/bootswatch/cyborg/bootstrap.min.css",
    "slate": "vendor/bootswatch/slate/bootstrap.min.css",
    "solar": "vendor/bootswatch/solar/bootstrap.min.css",
    "superhero": "vendor/bootswatch/superhero/bootstrap.min.css",
    "vapor": "vendor/bootswatch/vapor/bootstrap.min.css",
}

DARK_THEMES = ("darkly", "cyborg", "slate", "solar", "superhero")

CHANGEFORM_TEMPLATES = {
    "single": "jazzmin/includes/single.html",
    "carousel": "jazzmin/includes/carousel.html",
    "collapsible": "jazzmin/includes/collapsible.html",
    "horizontal_tabs": "jazzmin/includes/horizontal_tabs.html",
    "vertical_tabs": "jazzmin/includes/vertical_tabs.html",
}
