from setuptools import setup

setup(
    name='sbs',
    version='0.2.7',
    packages=['sbs'],
    url='https://github.com/santlerson/sbs',
    license='GNU GENERAL PUBLIC LICENSE',
    author='santlerson',
    author_email='shmooseyantlerson@gmail.com',
    description='A python tool for creating secure and encrypted backups',
    entry_points={
        'console_scripts': ['sbs=sbs.sbs:main'],
    },
    package_data={"sbs": ["credentials.json"]},
    include_package_data=True,
    install_requires=
"""
click>=8.0.3
tqdm>=4.62.3
httplib2>=0.20.1
google-auth-httplib2
google-auth-oauthlib
google-api-python-client
pycryptodomex
""".splitlines()

)
