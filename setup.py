from setuptools import setup

setup(
    name='normino',
    version='0.1',
    py_modules=['normino'],
    install_requires=[
        'colorama',
    ],
    entry_points={
        'console_scripts': [
            'normino=normino:main',
        ],
    },
)