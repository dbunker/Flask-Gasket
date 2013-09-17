"""
Flask-Gasket
-------------

Flask plugin for building REST APIs with Riak.
"""
from setuptools import setup


setup(
    name='Flask-Gasket',
    version='0.4',
    url='http://github.com/dbunker/flask-gasket/',
    license='BSD',
    author='David Bunker',
    author_email='dbunker@fizbizfiz.biz',
    description='Flask plugin for building REST APIs with Riak.',
    long_description=__doc__,
    packages=['flask_gasket'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'riak'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)