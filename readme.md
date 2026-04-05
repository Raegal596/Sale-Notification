# Sale-Notification

A Python application that periodically scrapes listing websites (Craigslist, Kijiji, Facebook Marketplace, eBay) for specific items matching a search query in a specified region. It sends real-time SMS notifications via Twilio whenever new listings are found.

## Features

- **Multi-Platform Scraping**: Supports scraping Craigslist, Kijiji, Facebook Marketplace, and eBay.
- **Automated Scanning**: Includes a built-in scheduler (using `schedule`) that runs the scrapers periodically (every 30 minutes).
- **Duplicate Prevention**: Maintains a history of seen listings locally (`seen_listings.json`) to prevent sending duplicate notifications.
- **SMS Notifications**: Integrates with Twilio to send bulk text message alerts of all newly discovered listings.

## Dependencies

The project relies on external libraries for scraping and sending notifications.
Install the required dependencies using:

```bash
pip install -r requirements.txt
```

*(Note: Ensure you have `beautifulsoup4`, `requests`, `schedule`, `twilio`, and `python-dotenv` installed, along with any other required scraping dependencies like `playwright` if used.)*

## Configuration

### 1. Environment Variables (`.env`)
You must provide your Twilio credentials in a `.env` file at the root of the project:

```env
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
```

### 2. Search Settings (`config.json`)
Create or edit `config.json` to configure the target search parameters:

```json
{
    "SEARCH_QUERY": "Herman Miller Aeron",
    "REGION": "Edmonton",
    "TO_PHONE_NUMBER": "+18777804236"
}
```

- `SEARCH_QUERY`: The item you are searching for.
- `REGION`: The general region/city you'd like to target (currently used to approximate specific site locations).
- `TO_PHONE_NUMBER`: The destination mobile number (must include country code, e.g., `+1`) to receive SMS alerts.

## Usage

You can run the application in two modes:

### Periodic Scheduler Mode (Default)
Runs a scrape immediately, and then continues running indefinitely on a 30-minute interval.

```bash
python main.py
```

### Run-Once Mode
Performs a single scrape, sends notifications for new finds, and then exits.

```bash
python main.py --run-once
```

## How It Works

1. `main.py` coordinates reading configuration and schedules interval runs.
2. The scrapers (in the `scrapers/` folder) search their respective platforms for the query in the region.
3. The results are compared against `seen_listings.json` to filter out listings that have already been processed.
4. Any novel items found are compiled and passed to `notifier.py`, which formats them and dispatches an SMS via Twilio.
5. `seen_listings.json` is updated to remember the newly discovered items.
