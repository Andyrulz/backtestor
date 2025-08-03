# Zerodha Kite Trading System

A minimal, well-tested trading system for Zerodha Kite API with a user-friendly interface.

## Features

- Clean UI for accessing Kite API endpoints
- Order placement and management
- Historical data (candlestick) retrieval
- Comprehensive test coverage
- Modular architecture

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Kite credentials:

   ```
   KITE_API_KEY=your_api_key
   KITE_ACCESS_TOKEN=your_access_token
   ```

3. Run the application:
   ```bash
   streamlit run src/app.py
   ```

## Project Structure

```
src/
├── kite/
│   ├── __init__.py
│   ├── client.py       # Kite API wrapper
│   └── models.py       # Data models
├── ui/
│   ├── __init__.py
│   └── components.py   # UI components
├── app.py              # Main Streamlit app
└── config.py           # Configuration

tests/
├── __init__.py
├── test_kite_client.py
└── test_ui_components.py
```

## Development

Run tests:

```bash
pytest
```

Format code:

```bash
black src/ tests/
```

Lint code:

```bash
flake8 src/ tests/
```
