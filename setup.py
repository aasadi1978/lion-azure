from setuptools import setup
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return False

setup(
    distclass=BinaryDistribution,
    options={
        'bdist_wheel': {
            'dist_name': 'lion-latest',
            'python_tag': 'py3',
            'plat_name': 'none-any'
        }
    }
)