from setuptools import setup

setup(
    name='battle',
    version='0.1',
    description='battle environment for Starcraft II',
    keywords='battle environment for StarCraft II',
    packages=[
        'battle',
        'battle.arena_sc2',
    ],

    install_requires=[
        'pysc2',
    ],
)
