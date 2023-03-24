#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import io
from setuptools import setup, find_packages

with io.open("README.rst", encoding="utf-8") as readme_file, io.open(
    "HISTORY.rst", encoding="utf-8"
) as history_file:
    long_description = readme_file.read() + "\n\n" + history_file.read()

install_requires = ["click>=8.1.3", "requests", "ruamel.yaml", "demjson3"]

setup_requires = [
    "pytest-runner",
    # TODO(sorn): put setup requirements (distutils extensions, etc.) here
]

tests_requires = [
    "pytest",
    # TODO: put package test requirements here
]

setup(
    name="pyclashsub",
    version="0.2.0",
    description="A python clash subscriber script",
    long_description=long_description,
    author="Hong-She Liang",
    author_email="sorn@taorules.com",
    url="https://github.com/sorn/pyclashsub",
    packages=find_packages(),
    entry_points={"console_scripts": ["pyclashsub=pyclashsub.__main__:main"]},
    include_package_data=True,
    install_requires=install_requires,
    license="Apache Software License",
    zip_safe=False,
    keywords="pyclashsub",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    test_suite="tests",
    tests_require=tests_requires,
    setup_requires=setup_requires,
)
