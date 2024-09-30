# setup.py

from setuptools import setup, find_packages

setup(
    name='forensic_email_parser',
    version='0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        # You can list your dependencies here or continue using requirements.txt
    ],
)
