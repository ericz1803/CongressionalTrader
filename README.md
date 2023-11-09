# CongressionalTrader
Trading Algorithm Based on Congressional Trading Data

Inspired by: https://www.quiverquant.com/congresstrading/

This project automatically deploys to AWS Lambda using serverless and github actions.

## Installation
To run locally, first install dependencies:
```bash
pip install -r requirements.txt
```

Then, set get the Alpaca API key from the dashboard and set them as environment variables:
```bash
export ALPACA_API_KEY=<YOUR_API_KEY>
export ALPACA_API_SECRET=<YOUR_SECRET_KEY>
```

Finally, run the script:
```bash
python main.py
```

