pushd %~dp0
python setup.py bdist_wheel
python -m pip install dist\eventloop-0.0.1-py3-none-any.whl --ignore-installed
popd