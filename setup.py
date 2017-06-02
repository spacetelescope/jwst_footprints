from setuptools import setup, find_packages


setup(
    name='jwst_footprints',
    version='1.2.0',
    author='Leonardo Lubeda',
    author_email='lubeda@stsci.edu',
    description='TODO',
    url='https://github.com/spacetelescope/jwst_footprints',
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'astropy',
        'matplotlib',
        'numpy',
        'scipy',
        'pillow'
    ],

    packages=find_packages(),
    package_data={
        '': [
            'data/*',
        ]
    },
    entry_points={
        'console_scripts': [
            'jwst_footprints=jwst_footprints.launch_footprints:main',
        ],
    },
)
