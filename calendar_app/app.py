import streamlit as st
# Must be the first Streamlit command
st.set_page_config(layout="wide", page_title="Calendar App")

import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import os
import json

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Database path
DB_PATH = '/Users/1112911/Desktop/MCP_TEST/calendar_app/calendar.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize SQLite database
def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Create events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                all_day BOOLEAN DEFAULT 0,
                color TEXT
            )
        ''')
        
        # Create participants table
        c.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        ''')
        
        # Enable foreign key support
        c.execute('PRAGMA foreign_keys = ON')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()

# Function to add event and participants
def add_event(title, description, start_date, end_date, participants, all_day=False, color="#3788d8"):
    if not title:
        st.error("Event title is required!")
        return False
    if not participants:
        st.error("At least one participant is required!")
        return False
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Convert datetime objects to string
        start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert event
        c.execute('''
            INSERT INTO events (title, description, start_date, end_date, all_day, color)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, start_str, end_str, all_day, color))
        
        event_id = c.lastrowid
        
        # Insert participants
        for participant in participants:
            if participant.strip():  # Only add non-empty participants
                c.execute('INSERT INTO participants (event_id, name) VALUES (?, ?)',
                         (event_id, participant.strip()))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error adding event: {e}")
        return False
    finally:
        conn.close()

# Function to update event
def update_event(event_id, title, description, start_date, end_date, participants, all_day=False, color="#3788d8"):
    if not title:
        st.error("Event title is required!")
        return False
    if not participants:
        st.error("At least one participant is required!")
        return False
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Convert datetime objects to string
        start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update event
        c.execute('''
            UPDATE events 
            SET title=?, description=?, start_date=?, end_date=?, all_day=?, color=?
            WHERE id=?
        ''', (title, description, start_str, end_str, all_day, color, event_id))
        
        # Delete existing participants
        c.execute('DELETE FROM participants WHERE event_id=?', (event_id,))
        
        # Insert new participants
        for participant in participants:
            if participant.strip():
                c.execute('INSERT INTO participants (event_id, name) VALUES (?, ?)',
                         (event_id, participant.strip()))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error updating event: {e}")
        return False
    finally:
        conn.close()

# Function to delete event
def delete_event(event_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM events WHERE id=?', (event_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error deleting event: {e}")
        return False
    finally:
        conn.close()

# Function to get event details
def get_event(event_id):
    try:
        conn = get_db_connection()
        # Get event details
        event_df = pd.read_sql_query("SELECT * FROM events WHERE id=?", conn, params=(event_id,))
        if event_df.empty:
            return None
        
        # Get participants
        participants_df = pd.read_sql_query(
            "SELECT name FROM participants WHERE event_id=?", 
            conn, 
            params=(event_id,)
        )
        
        event_data = event_df.iloc[0].to_dict()
        event_data['participants'] = participants_df['name'].tolist()
        
        # Convert string dates to datetime
        event_data['start_date'] = datetime.strptime(event_data['start_date'], '%Y-%m-%d %H:%M:%S')
        event_data['end_date'] = datetime.strptime(event_data['end_date'], '%Y-%m-%d %H:%M:%S')
        
        return event_data
    except sqlite3.Error as e:
        st.error(f"Error fetching event: {e}")
        return None
    finally:
        conn.close()

# Function to get all events
def get_events():
    try:
        conn = get_db_connection()
        events_df = pd.read_sql_query("""
            SELECT e.*, GROUP_CONCAT(p.name, ', ') as participants
            FROM events e
            LEFT JOIN participants p ON e.id = p.event_id
            GROUP BY e.id
        """, conn)
        
        # Convert events to FullCalendar format
        calendar_events = []
        for _, event in events_df.iterrows():
            participants = event['participants'] if pd.notna(event['participants']) else ''
            calendar_events.append({
                'id': str(event['id']),
                'title': f"{event['title']} ({participants})",
                'start': event['start_date'],
                'end': event['end_date'],
                'allDay': bool(event['all_day']),
                'backgroundColor': event['color'],
                'description': f"{event['description']}\n\nParticipants: {participants}"
            })
        return calendar_events
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        st.error(f"Error fetching events: {e}")
        return []
    finally:
        conn.close()

# Initialize the database
init_db()

# Streamlit app
st.markdown("""
<style>
    .stApp {
        font-size: 20px;
    }
    .css-10trblm {
        font-size: 40px !important;
    }
    .stButton > button {
        font-size: 20px;
    }
    .st-emotion-cache-16idsys p {
        font-size: 20px;
    }
    .fc {
        font-size: 16px !important;
    }
    .fc-toolbar-title {
        font-size: 24px !important;
    }
    .fc-button {
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📅 일정 관리")

# Initialize session state
if 'selected_event_id' not in st.session_state:
    st.session_state.selected_event_id = None

# Main layout with columns - adjusted ratio for larger calendar
col_calendar, col_details = st.columns([4, 1])

with col_calendar:
    # Calendar configuration
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "editable": False,
        "height": 850,
        "aspectRatio": 2.0,
        "events": get_events(),
        "eventClick": {
            "js": """
            function(info) {
                setSelectedEvent(info.event.id);
            }
            """
        },
        "eventDisplay": "block",
        "displayEventTime": True,
        "displayEventEnd": True,
        "locale": 'ko',
        "buttonText": {
            "today": "오늘",
            "month": "월간",
            "week": "주간",
            "day": "일간"
        }
    }

    # Display calendar
    calendar = calendar(events=get_events(), options=calendar_options, key="calendar")
    
    # Handle calendar event selection
    if calendar:
        try:
            event_id = calendar.get("eventClick", {}).get("event", {}).get("id")
            if event_id:
                st.session_state.selected_event_id = int(event_id)
                st.rerun()
        except (ValueError, AttributeError) as e:
            st.error(f"오류가 발생했습니다: {e}")

with col_details:
    if st.session_state.selected_event_id:
        event_data = get_event(st.session_state.selected_event_id)
        if event_data:
            # Event details display
            st.markdown(f"### 🗓️ {event_data['title']}")
            
            # Time information
            start_time = event_data['start_date']
            end_time = event_data['end_date']
            st.write(f"**⏰ 시간:**")
            st.write(f"시작: {start_time.strftime('%Y년 %m월 %d일 %H:%M')}")
            st.write(f"종료: {end_time.strftime('%Y년 %m월 %d일 %H:%M')}")
            
            if event_data['description']:
                st.write("**📝 설명:**")
                st.write(event_data['description'])
            
            st.write("**👥 참석자:**")
            for participant in event_data['participants']:
                st.write(f"- {participant}")

            # Quick action buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 삭제", type="primary", key="quick_delete"):
                    if delete_event(st.session_state.selected_event_id):
                        st.success("일정이 삭제되었습니다!")
                        st.session_state.selected_event_id = None
                        st.rerun()
            
            with col2:
                if st.button("✏️ 수정", type="primary", key="quick_edit"):
                    st.session_state.show_edit_form = True

            # Edit form
            if 'show_edit_form' not in st.session_state:
                st.session_state.show_edit_form = False

            if st.session_state.show_edit_form:
                st.markdown("---")
                with st.form(key="edit_form"):
                    st.subheader("일정 수정")
                    new_title = st.text_input("제목", value=event_data['title'])
                    new_description = st.text_area("설명", value=event_data['description'])
                    
                    st.write("**참석자**")
                    num_participants = st.number_input("참석자 수", 
                                                     min_value=1, 
                                                     value=len(event_data['participants']))
                    
                    new_participants = []
                    for i in range(num_participants):
                        default_value = event_data['participants'][i] if i < len(event_data['participants']) else ""
                        participant = st.text_input(f"참석자 {i+1}", value=default_value)
                        new_participants.append(participant)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_start_date = st.date_input("시작 날짜", value=start_time.date())
                        new_start_time = st.time_input("시작 시간", value=start_time.time())
                    with col2:
                        new_end_date = st.date_input("종료 날짜", value=end_time.date())
                        new_end_time = st.time_input("종료 시간", value=end_time.time())
                    
                    new_all_day = st.checkbox("종일", value=event_data['all_day'])
                    new_color = st.color_picker("일정 색상", value=event_data['color'])
                    
                    col1, col2 = st.columns(2)
                    submit = st.form_submit_button("💾 저장")
                    
                    if submit:
                        new_start = datetime.combine(new_start_date, new_start_time)
                        new_end = datetime.combine(new_end_date, new_end_time)
                        
                        if new_end < new_start:
                            st.error("종료 시간은 시작 시간 이후여야 합니다!")
                        else:
                            if update_event(st.session_state.selected_event_id, 
                                          new_title, new_description, new_start, new_end, 
                                          new_participants, new_all_day, new_color):
                                st.success("수정되었습니다!")
                                st.session_state.show_edit_form = False
                                st.rerun()
                
                if st.button("❌ 취소"):
                    st.session_state.show_edit_form = False
                    st.rerun()
    else:
        st.info("👆 일정을 클릭하면 상세 정보를 볼 수 있습니다")

# Sidebar with tabs for adding and deleting events
with st.sidebar:
    tab1, tab2 = st.tabs(["➕ 일정 추가", "🗑️ 일정 삭제"])
    
    # Add Event Tab
    with tab1:
        st.header("새 일정 추가")
        
        title = st.text_input("일정 제목", key="new_title")
        description = st.text_area("설명", key="new_description")
        
        st.subheader("참석자")
        num_participants = st.number_input("참석자 수", 
                                         min_value=1, value=1, 
                                         key="new_num_participants")
        
        participants = []
        for i in range(num_participants):
            participant = st.text_input(f"참석자 {i+1}", 
                                      key=f"new_participant_{i}")
            participants.append(participant)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작 날짜", key="new_start_date")
            start_time = st.time_input("시작 시간", key="new_start_time")
        with col2:
            end_date = st.date_input("종료 날짜", key="new_end_date")
            end_time = st.time_input("종료 시간", key="new_end_time")
        
        all_day = st.checkbox("종일", key="new_all_day")
        color = st.color_picker("일정 색상", value="#3788d8", key="new_color")
        
        if st.button("일정 추가", type="primary"):
            start = datetime.combine(start_date, start_time)
            end = datetime.combine(end_date, end_time)
            
            if end < start:
                st.error("종료 시간은 시작 시간 이후여야 합니다!")
            else:
                if add_event(title, description, start, end, participants, all_day, color):
                    st.success("일정이 추가되었습니다!")
                    st.rerun()
    
    # Delete Event Tab
    with tab2:
        st.header("일정 삭제")
        
        # Get all events for deletion
        try:
            conn = get_db_connection()
            events_df = pd.read_sql_query("""
                SELECT e.id, e.title, e.start_date, e.end_date, GROUP_CONCAT(p.name, ', ') as participants
                FROM events e
                LEFT JOIN participants p ON e.id = p.event_id
                GROUP BY e.id
                ORDER BY e.start_date DESC
            """, conn)
            
            if not events_df.empty:
                st.write("삭제할 일정을 선택하세요:")
                
                for _, event in events_df.iterrows():
                    start_time = datetime.strptime(event['start_date'], '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(event['end_date'], '%Y-%m-%d %H:%M:%S')
                    
                    # Create an expander for each event
                    with st.expander(f"📅 {event['title']} ({start_time.strftime('%Y년 %m월 %d일 %H:%M')})"):
                        st.write(f"**시간:** {start_time.strftime('%Y년 %m월 %d일 %H:%M')} - {end_time.strftime('%Y년 %m월 %d일 %H:%M')}")
                        if pd.notna(event['participants']):
                            st.write(f"**참석자:** {event['participants']}")
                        
                        if st.button("이 일정 삭제", key=f"delete_{event['id']}", type="primary"):
                            if delete_event(event['id']):
                                st.success(f"일정 '{event['title']}'이(가) 삭제되었습니다!")
                                st.rerun()
            else:
                st.info("삭제할 일정이 없습니다.")
                
        except sqlite3.Error as e:
            st.error(f"일정을 불러오는 중 오류가 발생했습니다: {e}")
        finally:
            conn.close() 