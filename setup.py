"""
Setup script for Vedika Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vedika-sdk",
    version="3.0.10",
    author="Vedika Intelligence",
    author_email="support@vedika.io",
    description="The only B2B astrology API with AI-powered chatbot queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vedika-io/vedika-sdk-python",
    project_urls={
        "Bug Tracker": "https://github.com/vedika-io/vedika-sdk-python/issues",
        "Documentation": "https://vedika.io/docs.html",
        "Source Code": "https://github.com/vedika-io/vedika-sdk-python",
        "Homepage": "https://vedika.io",
    },
    packages=find_packages(),
    # PEP 561: ships vedika/py.typed so type checkers (mypy, pyright) treat the
    # installed package as typed instead of falling back to Any everywhere.
    # Previously missing from BOTH setup.py and MANIFEST.in, so even a source
    # dist silently dropped the marker. package_data (not just MANIFEST.in) is
    # required so `pip install` picks it up for wheel builds, not just sdist.
    package_data={"vedika": ["py.typed"]},
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.33.0,<3",
        "urllib3>=2.7.0,<3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="astrology, vedic, api, AI, chatbot, horoscope, birth chart, compatibility, numerology, tarot, chinese astrology, iching, crystals, human design, feng shui, matrimony, spiritual",
)
