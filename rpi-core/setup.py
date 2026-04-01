from setuptools import setup, find_packages

setup(
    name="rpicore",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo>=4.0",
        "python-dotenv>=1.0",
    ],
)
