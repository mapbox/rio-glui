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
inst_reqs = ["tornado", "rio-tiler>=1.0b1", "click", "rio-color"]

extra_reqs = {
    'test': ['mock', 'pytest', 'pytest-cov']}


setup(name='rio-glui',
      version=version,
      description=u"Inspect CloudOptimized Geotiff using Mapbox GL JS",
      long_description="""""",
      classifiers=[
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scientific/Engineering :: GIS'],
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
