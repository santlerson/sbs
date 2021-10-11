import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sbs-santlerson",
    version="1.1.8",
    author="Shmoosey Antlerson",
    author_email="shmooseyantlerson@gmail.com",
    description="A tool for creating secure and encrypted backups on Google Drive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/santlerson/sbs",
    project_urls={
        "Bug Tracker": "https://github.com/santlerson/sbs/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "sbs"},
    packages=setuptools.find_packages(where="sbs"),
    python_requires=">=3.6",
    entry_points={
        'console_scripts': ['sbs=sbs.sbs:main'],
    }
)
