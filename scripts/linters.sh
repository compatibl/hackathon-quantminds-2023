#!/bin/bash

cd ..

# Validate using flake8
echo ""
echo "Validate using flake8"
flake8 hackathon --config=.flake8
flake8 tests --config=.flake8

# Change back to the original directory
cd -
