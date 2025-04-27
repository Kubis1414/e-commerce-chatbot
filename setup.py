from setuptools import setup, find_packages

setup(
    name="e-commerce-chatbot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "promptflow",
        "langchain",
        "pydantic",
    ]
)