from setuptools import setup, find_packages
import sys

if sys.version_info[:2] < (3, 6):
    raise RuntimeError("Python Version >= 3.6 required.")

__version__ = '0.5'

setup(
    name='dragpy',
    version=f'{__version__}',

    author='sco1',
    author_email='sco1.git@gmail.com',
    url='https://github.com/sco1/dragpy',

    packages=find_packages(),
    install_requires=["matplotlib"]    
)