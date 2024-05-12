from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='normino',
    version='0.1',
    py_modules=['normino'],
    install_requires=[
        'colorama',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'normino=normino:main',
        ],
    },
)
