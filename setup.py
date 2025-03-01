from setuptools import setup, find_packages

setup(
    name="cbatool",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "plotly",
        "openpyxl",  # For Excel file handling
    ],
    entry_points={
        'console_scripts': [
            'cbatool=cbatool.__main__:main',
        ],
    },
    author="Thomas Downs",
    description="Cable Burial Analysis Tool",
    python_requires=">=3.7",
)