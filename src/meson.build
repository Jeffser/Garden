pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'garden'
gnome = import('gnome')

gnome.compile_resources('garden',
  'garden.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'garden.in',
  output: 'garden',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

garden_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

custom_widgets = [
  'custom_widgets/shimeji_widget.py'
]

install_data(garden_sources, install_dir: moduledir)
install_data(custom_widgets, install_dir: moduledir / 'custom_widgets')