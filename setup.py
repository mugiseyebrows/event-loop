from setuptools import setup, find_packages

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    packages = find_packages(),
    name = 'eventloop',
    version='0.0.13',
    author="Stanislav Doronin",
    author_email="mugisbrows@gmail.com",
    url='https://github.com/mugiseyebrows/event-loop',
    description='Abstraction layer for filesystem events',
    long_description = long_description
)