from setuptools import setup, find_packages

setup(
    name="hexarch-guardrails",
    version="0.4.0",
    description="Lightweight policy-driven API protection and guardrails library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Noir Stack",
    author_email="hira@noirstack.com",
    maintainer="Hira",
    url="https://www.noirstack.com/",
    project_urls={
        "Repository": "https://github.com/no1rstack/hexarch-guardrails",
        "Documentation": "https://github.com/no1rstack/hexarch-guardrails#readme",
    },
    license="MIT",
    license_files=["LICENSE"],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.21.0",
        "click>=8.1.0",
        "pydantic>=2.0",
        "tabulate>=0.9.0",
        "colorama>=0.4.6",
        "sqlalchemy>=2.0.0",
        "alembic>=1.13.0",
        "psycopg2-binary>=2.9.0",
    ],
    extras_require={
        "cli": [
            "click>=8.1.0",
            "pydantic>=2.0",
            "tabulate>=0.9.0",
            "colorama>=0.4.6",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "hexarch-ctl=hexarch_cli:cli",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
