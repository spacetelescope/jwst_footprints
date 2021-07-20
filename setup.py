from setuptools import setup, find_packages


setup(
    name='jwst_footprints',
    version='2.5.0',
    author='Leonardo Ubeda',
    author_email='lubeda@stsci.edu',
    description='The JWST NIRSpec Observation Visualization Tool is a Python application that provides a simultaneous view of both NIRSpec and NIRCam fields of view on a given sky position, for assistance in planning NIRCam pre-imaging for NIRSpec.',
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
        'pillow',
        'pyds9'
    ],

    packages=find_packages(),
    package_data={
        '': [
            'data/*',
        ]
    },
    entry_points={
        'gui_scripts': [
            'jwst_footprints=jwst_footprints.gui.footprints:main',
        ],
    },
)
