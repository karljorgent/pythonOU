## Nõuded
- Python 3.8
- pip
- virtualenv

## Paigaldamine

git clone https://github.com/karljorgent/pythonOU.git
cd pythonOU

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python init_db.py

flask run

Rakendus on nüüd kättesaadav aadressil `http://localhost:5000`