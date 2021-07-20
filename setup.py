from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="timeseries_generator",
    description="Library for generating time series data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    # TODO: Once we use apis to import public data, the `package_data` is no longer required.
    package_data={
        "timeseries_generator": ["resources/public_data/*.csv"]
    },
    version="0.1.0",
    url='https://github.com/Nike-Inc/ts-generator',
    author='Zhe Sun, Jaap Langemeijer',
    author_email='zhe.sun@nike.com',
    install_requires=[
        "pandas==1.2.0",
        "workalendar==15.0.1",
        "matplotlib==3.3.3"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    license='Apache License, v2.0',
    python_requires='>=3.6',
)
