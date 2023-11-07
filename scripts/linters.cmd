@echo off

pushd ..

echo.
echo Validate using flake8
flake8 hackathon --config=.flake8
flake8 tests --config=.flake8

popd
