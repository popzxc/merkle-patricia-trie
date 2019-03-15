import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="eth_mpt",
    version="0.1.0",
    author="Igor Aleksanov",
    author_email="popzxc@yandex.com",
    description="A simlpe Merkle Patricia Trie implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/popzxc/merkle-patricia-trie",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
    ],
)
