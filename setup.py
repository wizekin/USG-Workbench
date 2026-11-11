"""Setuptools configuration including the archived v0.7.0 Mention model package."""
from setuptools import find_namespace_packages, setup

packages = [
    name for name in find_namespace_packages(
        include=["tools", "tools.*", "interoperability", "interoperability.*",
                 "specifications", "rules", "benchmarks", "examples", "release", "resources", "resources.*"]
    )
    if all(part.isidentifier() for part in name.split("."))
]
packages.append("usg_discourse_v07")

setup(
    packages=packages,
    package_dir={
        "usg_discourse_v07": "implementations/python-kernel/v0.7.0/usg_discourse_v07",
    },
)
