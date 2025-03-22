from setuptools import setup, find_packages

setup(
    name="screen-time-tracker",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "pandas>=1.5.0",
        "matplotlib>=3.5.0",
        "click>=8.0.0",
    ],
    entry_points={
        'console_scripts': [
            'screen-time-tracker=screen_time_tracker.main:cli',
        ],
    },
)
