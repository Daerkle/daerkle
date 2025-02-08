from setuptools import setup, find_packages

setup(
    name="pivot-plotter-pro",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit>=1.31.0",
        "yfinance>=0.2.36",
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "plotly>=5.18.0",
    ],
)