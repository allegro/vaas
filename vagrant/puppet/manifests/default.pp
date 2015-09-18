node default {

  class { 'grub2': cmdline_linux => 'apparmor=0 cgroup_enable=memory swapaccount=1'; } ->
  class { 'containers': } ->
  class { 'vaas_service': }

  package { ['vim', 'python', 'python-dev', 'python-pip', 'python-setupdocs', 'python-virtualenv', 'curl', 'sqlite3', 'screen']:
    ensure => latest
  }
  package { ['libsasl2-dev', 'libldap2-dev', 'libssl-dev' ]:
    ensure => installed
  }
}

class vaas_service {

  exec {
    'fix.python.easyinstall':
      command => 'curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python',
      user    => 'root',
      creates => '/usr/local/bin/easy_install',
      path    => '/usr/bin:/usr/sbin',
      require => [Package['curl'], Package['python-pip']];
    'fix.python.pip.freeze':
      command => 'pip install setuptools==7.0',
      user    => 'root',
      unless  => 'pip freeze',
      path    => '/usr/bin',
      require => Package['python-pip'];
  } ->
  package {
    'django':
      ensure   => '1.6.4',
      provider => pip;
    'django-admin-bootstrapped':
      ensure   => '1.6.4',
      provider => pip;
    'python-varnish':
      ensure   => '0.2.1',
      provider => pip;
    'jinja2':
      ensure   => '2.7.2',
      provider => pip;
    'django-nose':
      ensure   => '1.2',
      provider => pip;
    'coverage':
      ensure   => '3.7.1',
      provider => pip;
    'mock':
      ensure   => '1.0.1',
      provider => pip;
    'enum34':
      ensure   => '1.0',
      provider => pip;
    'PyYAML':
      ensure   => '3.11',
      provider => pip;
    'django-auth-ldap':
      ensure   => '1.2.0',
      provider => pip;
    'python-ldap':
      ensure   => '2.4.15',
      provider => pip;
    'lck.django':
      ensure   => '0.8.10',
      provider => pip;
    'django-tastypie':
      ensure   => '0.11.1',
      provider => pip;
    'nose-exclude':
      ensure   => '0.2.0',
      provider => pip;
    'futures':
      ensure   => '2.1.6',
      provider => pip;
    'django-log-request-id':
      ensure   => '1.0.0',
      provider => pip;
    'pep8':
      ensure   => '1.5.7',
      provider => pip;
    'django-simple-history':
      ensure   => '1.5.3',
      provider => pip;
    'factory-boy':
      ensure   => '2.5.2',
      provider => pip;
    'django-secure':
      ensure   => '1.0.1',
      provider => pip;
  } ->
  file {
    '/home/vagrant/vaas/vaas-app/src/vaas/resources/data.yaml':
      ensure  => 'present',
      source  => 'puppet:///files/data.yaml';
    '/home/vagrant/vaas/vaas-app/src/vaas/resources/db_config.yml':
      ensure  => present,
      source  => 'puppet:///files/db_config.yml';
    '/home/vagrant/vaas/vaas-app/src/vaas/settings/__init__.py':
      ensure  => present,
      source  => 'puppet:///files/init_local_settings.py';
  } ->
  exec { 'create_vaas_db':
    command => 'python /home/vagrant/vaas/vaas-app/src/manage.py syncdb --noinput',
    user    => 'vagrant',
    path    => '/usr/bin:/usr/sbin',
  } ->
  exec { 'populate_vaas_db':
    command => 'python /home/vagrant/vaas/vaas-app/src/manage.py loaddata /home/vagrant/vaas/vaas-app/src/vaas/resources/data.yaml',
    user    => 'vagrant',
    path    => '/usr/bin:/usr/sbin',
  } ->
  exec { 'collect_static_files':
    command => 'echo yes | python /home/vagrant/vaas/vaas-app/src/manage.py collectstatic',
    user    => 'vagrant',
    path    => '/bin:/usr/bin:/usr/sbin'
  } ->
  exec { 'start_vaas':
    command => 'nohup python /home/vagrant/vaas/vaas-app/src/manage.py runserver 0.0.0.0:3030 &',
    user    => 'vagrant',
    path    => '/usr/bin:/usr/sbin',
    unless  => '/usr/bin/pgrep python'
  }

  cron { 'refresh_backend_statuses':
    ensure  => 'present',
    command => '/usr/bin/python /home/vagrant/vaas/vaas-app/src/manage.py backend_statuses',
    user    => 'vagrant',
  }
}

class containers {

  include docker

  file {
    ['/srv/www', '/srv/www/first', '/srv/www/second']:
      ensure => 'directory';
    'first':
      ensure => 'file',
      path   => '/srv/www/first/index.html',
      content => '<h2>Welcome to the first service</h2>';
    'second':
      ensure => 'file',
      path   => '/srv/www/second/index.html',
      content => '<h2>Welcome to the second service</h2>';
  }
  docker::run { 'varnish-3':
    image        => 'allegro/vaas-varnish-3',
    memory_limit => '104857600b',
    use_name     => 'true',
    ports        => ['192.168.200.10:80:6081', '192.168.200.10:6082:6082'];
  } ->
  docker::run { 'varnish-4':
    image        => 'allegro/vaas-varnish-4',
    memory_limit => '104857600b',
    use_name     => 'true',
    ports        => ['192.168.200.11:80:6081', '192.168.200.11:6082:6082'];
  } ->
  docker::image { 'jpetazzo/nsenter': } ->
  exec { 'instal-nsenter':
    unless  => '/bin/ls /usr/local/bin/nsenter',
    command => '/usr/bin/docker run --rm -v /usr/local/bin:/target jpetazzo/nsenter';
  }
  $backends = [ '0', '1', '2', '3', '4', '5']
  each($backends) |$backend| {
    docker::run { "nginx-${backend}":
      image        => 'allegro/vaas-nginx',
      volumes      => ['/srv/www/first:/usr/share/nginx/html/first', '/srv/www/second:/usr/share/nginx/html/second'],
      ports        => "192.168.200.1${backend}:808${backend}:80",
      use_name     => 'true',
      memory_limit => '26214400b',
      require      => Docker::Run['varnish-4'];
    }
  }
}
