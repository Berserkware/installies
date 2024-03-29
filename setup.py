from setuptools import setup
try:
    from installies import __version__
except ImportError:
    __version__ = "0.1.0"
    
setup(
    name='installies',
    version=__version__,
    packages=[
        'installies', 
        'installies.database',
        'installies.static',
        'installies.templates',
        'installies.lib',
        'installies.models',
        'installies.groups',
        'installies.validators',
        'installies.forms',
        'installies.blueprints.api',
        'installies.blueprints.app_library',
        'installies.blueprints.app_manager',
        'installies.blueprints.auth',
        'installies.blueprints.admin',
        ],
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'peewee',
        'flask',
        'bleach',
        'bcrypt',
        'pymysql',
    ],
)
