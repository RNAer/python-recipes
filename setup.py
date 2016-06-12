from setuptools import setup

setup(
    name='recipes',
    author='Zech Xu',
    description='useful python recipes',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['numpy', 'pandas'],
    extras_require={'test': ["nose", "pep8", "flake8"],
                    'coverage': ["coverage"],
                    'doc': ["Sphinx"]})
