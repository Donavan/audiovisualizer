from setuptools import setup, find_packages

setup(
    name="audiovisualizer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "numpy",
        "pillow",
        "moviepy",
        "librosa",
    ],
    python_requires=">=3.8",
)