# How To Install and Use Python on Atlas

## login to the atlas head node
your username / password are from UA Credentials -- See ELMO
```sh
ssh atlas.snap.uaf.edu
```

## download and install python3
### download python
```sh
mkdir ~/src
mkdir ~/.localpython
cd ~/src
wget https://www.python.org/ftp/python/2.7.14/Python-2.7.14.tar.xz
```

### unzip 
```sh
tar xvfJ Python-2.7.14.tar.xz
```

### python2 installation / configuration
```sh
cd ~/src/Python-2.7.14
make clean
./configure --prefix=/home/UA/malindgren/.localpython
make
make install
```

### Python2 requires virtualenv for the next steps, Install it.
cd ~/src
# wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.1.0.tar.gz --no-check-certificate
wget https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-15.1.0.tar.gz#md5=44e19f4134906fe2d75124427dc9b716
tar -zxvf virtualenv-15.1.0.tar.gz
cd virtualenv-15.1.0/
~/.localpython/bin/python2.7 setup.py install


## use the installation
### make a virtual environment where we will install some packages
```sh
~/.localpython/bin/virtualenv venv --python=~/.localpython/bin/python2.7
source ~/venv/bin/activate
```

### install some packages (optional)
```sh
pip install --upgrade pip
pip install numpy
pip install 'ipython[all]'
pip install scipy rasterio fiona pandas geopandas scikit-image scikit-learn shapely netCDF4 xarray
```

