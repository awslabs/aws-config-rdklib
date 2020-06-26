#    Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#
#        http://aws.amazon.com/apache2.0/
#
#    or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import fnmatch
import rdklib
from rdklib import MY_VERSION
from setuptools import find_namespace_packages, setup
from setuptools.command.build_py import build_py as build_py_orig


def readme():
    with open('README.rst') as f:
        return f.read()

excluded = ['*internal.py', '*_test.py']


class build_py(build_py_orig):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        print(modules)
        return [
            (pkg, mod, file)
            for (pkg, mod, file) in modules
            if not any(fnmatch.fnmatchcase(file, pat=pattern) for pattern in excluded)
        ]

setup(name='rdklib',
      version=MY_VERSION,
      description='Rule Development Kit Library for AWS Config',
      long_description=readme(),
      url='https://github.com/awslabs/aws-config-rdklib/',
      author='Michael Borchert',
      author_email='mborch@amazon.com',
      license='Apache License Version 2.0',
      packages=find_namespace_packages(),
      cmdclass={'build_py': build_py},
      install_requires=[
          'rdk',
          'boto3',
          'botocore'
      ],
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
      ],
      zip_safe=False,
      include_package_data=True)
