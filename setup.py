from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qualcli",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for managing AppWright test jobs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/qualcli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "sqlalchemy>=1.4.0",
        "psycopg2-binary>=2.9.0",
        "redis>=4.0.0",
        "celery>=5.2.0",
        "click>=8.0.0",
        "rich>=10.0.0",
        "python-dotenv>=0.19.0",
        "requests>=2.31.0",
        "httpx>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "qgjob=cli.main:cli",
        ],
    },
) 