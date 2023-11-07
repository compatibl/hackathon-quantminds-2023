@echo off

pushd ..

echo.
echo Format using isort
isort hackathon --sp=.isort.cfg
isort tests --sp=.isort.cfg

echo.
echo Format using black
black -q hackathon --config=pyproject.toml
black -q tests --config=pyproject.toml

popd
