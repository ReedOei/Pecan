from setuptools import setup, find_packages

setup(
    name="Pecan",
    version="0.1",
    packages=find_packages(),
    scripts=['pecan.py'],
    install_requires=['argparse', 'lark-parser', 'colorama']
)

