from setuptools import setup, find_packages

setup(
    name="cfddns",
    version="0.1",
    packages=['cfddns'],
    entry_points={
        'console_scripts': ["cfddns = cfddns:main"],
    },
    install_requires=["cloudflare", "pyyaml"],
)
