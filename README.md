# metagameplay_server

## Run
```bash
git clone git@github.com:StarNuik/shop_server.git
cd ./shop_server

python -m venv ./.venv
source ./.venv/bin/activate
pip install -r requirements.txt

docker compose up -d # Run Jaeger

python -m server
python -m client [-h] COMMAND
```

## Usage example
```bash
alias client "python -m client"
client login my_username
client user_info
client shop_items
client buy free_snack
client buy kitten
client user_info
client owned_items
client sell kitten
client logout
client login my_username
client user_info
client owned_items
```