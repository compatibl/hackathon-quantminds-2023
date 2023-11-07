#!/bin/bash

cd ..

# Format using isort
echo "Format using isort"
isort hackathon --sp=.isort.cfg
isort tests --sp=.isort.cfg

# Format using black
echo ""
echo "Format using black"
black -q hackathon --config=pyproject.toml
black -q tests --config=pyproject.toml

# Change back to the original directory
cd -
