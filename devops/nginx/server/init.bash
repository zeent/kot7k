# Init directory
cd /opt
sudo mkdir kot7k
sudo chown joan:joan kot7k

# Test it
ls -ld /opt/kot7k

# Clone kot7k repository
git clone git@github.com:zeent/kot7k.git

# And install
cd /opt/kot7k
/usr/local/bin/python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

cd /opt/kot7k/api
python -m pip install -r requirements.txt



9Zxoy_p3cZxoy_p3cmJjQB9tmJjQB9t9