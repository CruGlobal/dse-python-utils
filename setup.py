from setuptools import setup, find_packages

setup(
    name="dse_utils",
    version="0.1",
    packages=find_packages(),
    description="A package of useful functions developed by Cru Data Science and Engineering team.",
    author="Tony Guan",
    author_email="tony.guan@cru.org",
    url="https://github.com/CruGlobal/dse-python-utils",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    install_requires=[
        "numpy",
        "pandas",
        "requests",
    ],
)
