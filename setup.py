from setuptools import setup, find_packages

setup(
    name="encrypted_file_migrator",
    version="1.3.0",
    packages=find_packages(),
    install_requires=[
        "wcmatch==10.1"
    ],
    entry_points={
        "console_scripts": [
            "encrypted_file_migrator=encrypted_file_migrator.main:main",
        ],
    },
)
