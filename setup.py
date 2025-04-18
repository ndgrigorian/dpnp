import importlib.machinery as imm
import os

from skbuild import setup

import versioneer

"""
Get the project version
"""
thefile_path = os.path.abspath(os.path.dirname(__file__))
version_mod = imm.SourceFileLoader(
    "version", os.path.join(thefile_path, "dpnp", "_version.py")
).load_module()
__version__ = version_mod.get_versions()["version"]

"""
Set project auxiliary data like readme and licence files
"""
with open("README.md") as f:
    __readme_file__ = f.read()


def _get_cmdclass():
    return versioneer.get_cmdclass()


CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Programming Language :: C++
Programming Language :: Cython
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Programming Language :: Python :: 3.11
Programming Language :: Python :: 3.12
Programming Language :: Python :: 3.13
Programming Language :: Python :: Implementation :: CPython
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX :: Linux
Operating System :: POSIX
Operating System :: Unix
"""


setup(
    name="dpnp",
    version=__version__,
    cmdclass=_get_cmdclass(),
    description="Data Parallel Extension for NumPy",
    long_description=__readme_file__,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    classifiers=[_f for _f in CLASSIFIERS.split("\n") if _f],
    keywords="sycl numpy python3 intel mkl oneapi gpu dpcpp",
    platforms=["Linux", "Windows"],
    author="Intel Corporation",
    url="https://github.com/IntelPython/dpnp",
    packages=[
        "dpnp",
        "dpnp.dpnp_algo",
        "dpnp.dpnp_utils",
        "dpnp.fft",
        "dpnp.linalg",
        "dpnp.random",
    ],
    package_data={
        "dpnp": [
            "backend/include/*.hpp",
            "libdpnp_backend_c.so",
            "dpnp_backend_c.lib",
            "dpnp_backend_c.dll",
            "tests/*.*",
            "tests/testing/*.py",
            "tests/third_party/cupy/*.py",
            "tests/third_party/cupy/*/*.py",
        ]
    },
    include_package_data=False,
    python_requires=">=3.9,<3.14",
    install_requires=["dpctl >= 0.20.0dev0", "numpy"],
)
