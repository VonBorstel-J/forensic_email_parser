# setup.py

from setuptools import setup, find_packages

setup(
    name='forensic_email_parser',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # keep using requirements.txt
    ],
    include_package_data=True,
    description='Automated Email Parsing and Data Integration System for Forensic Engineering.',
    author='JVB',
    author_email='',
    url='',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
