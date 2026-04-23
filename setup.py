import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='bseindia',
    packages=setuptools.find_packages(),
    version='1.1',
    include_package_data=True,
    description='library to get BSE India data',
    long_description=long_description,
    long_description_content_type="text/markdown", author='RuchiTanmay',
    author_email='ruchitanmay@gmail.com',
    url='https://github.com/RuchiTanmay/bseindia',
    install_requires=['requests', 'pandas', 'xlrd', 'numpy', 'bs4', 'lxml'],
    keywords=['bseindia', 'bse', 'sensex', 'bselib', 'trading', 'stock markets', 'bse data', 'bse_data'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
