"""setup.py"""

from setuptools import setup, find_packages

# Parse the version from the fiona module.
with open('rio_glui/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue

# Runtime requirements.
inst_reqs = ["tornado", "rio-tiler==1.0a5", "click"]

extra_reqs = {
    'test': ['mock', 'pytest', 'pytest-cov', 'codecov']}


setup(name='rio-glui',
      version=version,
      description=u"Demo rasterio / Mapbox GL JS demo app",
      long_description="""""",
      classifiers=[],
      keywords='',
      author=u"Damon Burgett",
      author_email='damon@mapbox.com',
      url='https://github.com/mapbox/rio-glui',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=inst_reqs,
      extras_require=extra_reqs,
      entry_points="""
      [rasterio.rio_plugins]
      glui=rio_glui.scripts.cli:glui
      """
      )
