# Calendar App

A Streamlit-based calendar application that uses FullCalendar for event management and SQLite for data storage.

## Features

- Interactive calendar with month, week, and day views
- Add events with title, description, start/end times
- All-day event support
- Custom event colors
- SQLite database for persistent storage

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Usage

1. The calendar will be displayed in the main area
2. Use the sidebar to add new events:
   - Enter event title and description
   - Select start and end dates/times
   - Choose if it's an all-day event
   - Pick a custom color for the event
3. Click "Add Event" to save the event
4. Events will appear on the calendar immediately

## Database

The application uses SQLite for data storage. The database file will be created automatically in the `data` directory when you first run the application. 