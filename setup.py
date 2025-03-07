from setuptools import setup, find_packages

setup(
    name="e-commerce-chatbot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "promptflow"
    ]
)