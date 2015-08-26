#!/usr/bin/python3

from setuptools import setup, find_packages

setup(
    name="cabot_tools",
    version="1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "requests",
    ],
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "cabot-monitor-instance = cabot_tools.main:main",
        ],
    },
)
