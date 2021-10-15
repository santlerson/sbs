from setuptools import setup

setup(
    name='sbs',
    version='1.2.3',
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


)
