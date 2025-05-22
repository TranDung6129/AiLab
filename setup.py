from setuptools import setup, find_packages

setup(
    name="BaseRealTimeDisplacement",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.0.0',
        'numpy>=1.21.0',
        'scipy>=1.7.0',
        'matplotlib>=3.4.0',
        'pyserial>=3.5',
        'pytest>=7.0.0',
    ],
) 