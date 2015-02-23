from pathlib import Path
import re
from setuptools import setup, find_packages

def find_version(*path_parts):
    with Path(*path_parts).open(encoding='utf8') as f:
        version_match = re.search(
            r"^__version__ = ['\"]([^'\"]*)['\"]",
            f.read(), re.M
        )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")

setup(
    name='furk-tool',
    version=find_version('furk.py'),

    license='MIT',
    description='Auto tools for furk.net',

    author='Liang Bo Wang',
    author_email='ccwang002@gmail.com',

    url='https://github.com/ccwang002/furk_tool',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords=['furk'],

    install_requires=['docopt', 'requests', 'pyquery'],

    packages=find_packages(
        exclude=[
            'contrib', 'docs', 'examples', 'deps',
            '*.tests', '*.tests.*', 'tests.*', 'tests',
        ]
    ),

    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'furk = furk:console_main',
        ]
    },
)
