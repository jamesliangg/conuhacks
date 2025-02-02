# Add this as the first line after imports
import streamlit as st
st.set_page_config(page_title="Have I Met You Before?", page_icon="📸")
from datetime import datetime
import json
import os
from PIL import Image
import math
import plotly.express as px
import pandas as pd

# Initialize session states
if 'people' not in st.session_state:
    if os.path.exists('people_data.json'):
        with open('people_data.json', 'r') as f:
            st.session_state.people = json.load(f)
    else:
        st.session_state.people = []

if 'show_modal' not in st.session_state:
    st.session_state.show_modal = False
    st.session_state.current_person_idx = None

if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

if 'button_states' not in st.session_state:
    st.session_state.button_states = {}

if 'events' not in st.session_state:
    if os.path.exists('events_data.json'):
        with open('events_data.json', 'r') as f:
            st.session_state.events = json.load(f)
    else:
        st.session_state.events = []

# Dictionary of state abbreviations
COUNTRIES = {
    'United States': 'USA',
    'Canada': 'CAN',
    'Mexico': 'MEX',
    'United Kingdom': 'GBR'
}

# For US states, we'll keep them as regions
US_STATES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

def crop_center_square(image):
    width, height = image.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    return image.crop((left, top, right, bottom))

def save_image(image_file, person_name):
    if not os.path.exists('images'):
        os.makedirs('images')
    
    image_path = f"images/{person_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    img = Image.open(image_file)
    img = crop_center_square(img)
    img = img.resize((300, 300))
    img.save(image_path)
    return image_path

def save_people_data():
    with open('people_data.json', 'w') as f:
        json.dump(st.session_state.people, f)

def delete_image(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)

def show_person_modal(idx):
    st.session_state.show_modal = True
    st.session_state.current_person_idx = idx

def close_modal():
    st.session_state.show_modal = False
    st.session_state.current_person_idx = None

def get_photo_timestamp(photo_path):
    """Extract timestamp from photo filename"""
    try:
        # Extract the timestamp part from the filename (assumes format: name_YYYYMMDD_HHMMSS.jpg)
        timestamp_str = photo_path.split('_')[-1].split('.')[0]
        return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    except:
        return datetime.min

def set_button_clicked():
    st.session_state.button_clicked = True

def handle_photo_nav(person_name, direction):
    current_idx = st.session_state[f"current_photo_{person_name}"]
    if direction == "prev" and current_idx > 0:
        st.session_state[f"current_photo_{person_name}"] = current_idx - 1
    elif direction == "next":
        st.session_state[f"current_photo_{person_name}"] = current_idx + 1

def handle_photo_delete(person, current_idx):
    delete_image(person['photos'][current_idx])
    person['photos'].pop(current_idx)
    st.session_state[f"current_photo_{person['name']}"] = min(
        current_idx,
        len(person['photos']) - 1
    ) if person['photos'] else 0
    save_people_data()

def handle_date_delete(person, date):
    person['dates'].remove(date)
    save_people_data()

def handle_date_add(person, new_date):
    date_str = new_date.strftime("%Y-%m-%d")
    if date_str not in person['dates']:
        person['dates'].append(date_str)
        person['dates'].sort()
        save_people_data()

def save_events_data():
    with open('events_data.json', 'w') as f:
        json.dump(st.session_state.events, f)

# Modal dialog
if st.session_state.show_modal:
    person = st.session_state.people[st.session_state.current_person_idx]
    
    with st.container():
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✕", key="close_modal"):
                close_modal()
        with col2:
            st.subheader(person['name'])
        
        # Create two columns for image and details
        img_col, details_col = st.columns([1, 1])
        
        with img_col:
            # Initialize current photo index in session state if not exists
            if f"current_photo_{person['name']}" not in st.session_state:
                st.session_state[f"current_photo_{person['name']}"] = 0
            
            # Migrate old format to new format
            if 'photo' in person and 'photos' not in person:
                person['photos'] = [person['photo']]
                del person['photo']
                save_people_data()
            elif 'photos' not in person:
                person['photos'] = []
                save_people_data()
            
            if person['photos']:
                current_idx = st.session_state[f"current_photo_{person['name']}"]
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if current_idx > 0:
                        st.button("←", 
                                 key=f"prev_{person['name']}_{current_idx}",
                                 on_click=handle_photo_nav,
                                 args=(person['name'], "prev"))
                
                with col2:
                    st.write(f"Photo {current_idx + 1} of {len(person['photos'])}")
                
                with col3:
                    if current_idx < len(person['photos']) - 1:
                        st.button("→", 
                                 key=f"next_{person['name']}_{current_idx}",
                                 on_click=handle_photo_nav,
                                 args=(person['name'], "next"))
                
                # Display current photo
                if os.path.exists(person['photos'][current_idx]):
                    st.image(person['photos'][current_idx], use_container_width=True)
                    st.button("Delete Current Photo",
                             key=f"delete_photo_{person['name']}_{current_idx}",
                             on_click=handle_photo_delete,
                             args=(person, current_idx))
            
            # Add new photo
            new_photo = st.file_uploader("Add new photo", type=['jpg', 'jpeg', 'png'])
            if new_photo:
                # Create a unique key for this upload
                upload_key = f"uploaded_{person['name']}_{new_photo.name}"
                
                # Check if this photo was already uploaded
                if upload_key not in st.session_state:
                    new_path = save_image(new_photo, person['name'])
                    person['photos'].append(new_path)
                    save_people_data()
                    # Mark this photo as uploaded
                    st.session_state[upload_key] = True
        
        with details_col:
            # Edit fields
            new_name = st.text_input("Name", person['name'])
            
            # Location fields
            new_country = st.selectbox("Country", 
                                     options=list(COUNTRIES.keys()), 
                                     index=list(COUNTRIES.keys()).index(person.get('country', 'United States')))
            
            if new_country == "United States":
                new_state = st.selectbox("State", 
                                       options=list(US_STATES.keys()),
                                       index=list(US_STATES.keys()).index(person.get('state', 'New York')))
            else:
                new_state = None
            
            # Show and edit meetings
            st.write("**Meetings:**")
            meetings_to_remove = []
            for i, meeting in enumerate(person['meetings']):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"- {meeting['date']}")
                with col2:
                    st.write(meeting['location'])
                with col3:
                    if st.button("🗑", key=f"delete_meeting_{person['name']}_{i}"):
                        meetings_to_remove.append(meeting)
            
            # Remove selected meetings
            for meeting in meetings_to_remove:
                person['meetings'].remove(meeting)
            
            # Add new meeting
            new_date = st.date_input("Add new date")
            new_location = st.text_input("Location")
            if st.button("Add Meeting", key=f"add_meeting_{person['name']}_modal"):
                date_str = new_date.strftime("%Y-%m-%d")
                if not any(m['date'] == date_str for m in person['meetings']):
                    person['meetings'].append({
                        "date": date_str,
                        "location": new_location
                    })
                    person['meetings'].sort(key=lambda x: x['date'])
                    save_people_data()
                    st.success("Meeting added!")
            
            # Save changes
            if (new_name != person['name'] or 
                new_country != person.get('country') or
                new_state != person.get('state')):
                
                person.update({
                    "name": new_name,
                    "country": new_country,
                    "state": new_state if new_country == "United States" else None
                })
                save_people_data()
                st.success("Changes saved!")
            
            # Delete person
            if st.button("Delete Person", type="primary"):
                for photo in person['photos']:
                    delete_image(photo)
                st.session_state.people.pop(st.session_state.current_person_idx)
                save_people_data()
                close_modal()

# App title
st.title("MLH Coaches You've Met")

# Sidebar for adding new people
with st.sidebar:
    st.header("Add New Meeting")
    with st.form("add_person"):
        name = st.text_input("Name")
        
        # Check if person already exists
        existing_person = None
        if name:  # Only check if name is entered
            for p in st.session_state.people:
                if p['name'].lower() == name.lower():
                    existing_person = p
                    break
        
        photo = st.file_uploader("Photo", type=['jpg', 'jpeg', 'png'])
        location_met = st.text_input("Location Met")
        
        # Always show all fields, but pre-fill if person exists
        country = st.selectbox(
            "Country",
            options=list(COUNTRIES.keys()),
            index=list(COUNTRIES.keys()).index(existing_person['country']) if existing_person else 0
        )
        
        # Show state selection only for US
        if country == "United States":
            state = st.selectbox(
                "State",
                options=list(US_STATES.keys()),
                index=list(US_STATES.keys()).index(existing_person.get('state', 'New York')) if existing_person else 0
            )
        else:
            state = None
        
        if existing_person:
            st.write(f"Adding new meeting for existing person: {name}")
        
        date_met = st.date_input("Date Met")
        
        submitted = st.form_submit_button("Add Meeting")
        
        if submitted and name and photo and location_met and date_met:
            image_path = save_image(photo, name)
            
            if existing_person:
                # Add to existing person
                existing_person['photos'].append(image_path)
                # Store date with location
                existing_person['meetings'].append({
                    "date": date_met.strftime("%Y-%m-%d"),
                    "location": location_met
                })
                # Sort meetings by date
                existing_person['meetings'].sort(key=lambda x: x['date'])
                st.success("Meeting added successfully!")
            else:
                # Create new person
                person = {
                    "name": name,
                    "photos": [image_path],
                    "country": country,
                    "state": state if country == "United States" else None,
                    "meetings": [{
                        "date": date_met.strftime("%Y-%m-%d"),
                        "location": location_met
                    }]
                }
                st.session_state.people.append(person)
                st.success("Person added successfully!")
            
            save_people_data()
            
            # Clear the form by removing the uploaded file from session state
            if 'add_person' in st.session_state:
                del st.session_state.add_person
            

# Main content - Display people grid
# st.header("People You've Met")

# Create grid layout
COLS = 3
rows = math.ceil(len(st.session_state.people) / COLS)

for row in range(rows):
    cols = st.columns(COLS, gap="small")
    for col in range(COLS):
        idx = row * COLS + col
        if idx < len(st.session_state.people):
            person = st.session_state.people[idx]
            with cols[col]:
                # Handle both old and new format
                photos = person.get('photos', [person.get('photo')]) if 'photos' in person or 'photo' in person else []
                if photos and photos[0] is not None:
                    # Sort photos by timestamp and get the most recent one
                    valid_photos = [p for p in photos if p and os.path.exists(p)]
                    if valid_photos:
                        most_recent_photo = max(valid_photos, key=get_photo_timestamp)
                        st.image(most_recent_photo, 
                                caption=person['name'], 
                                use_container_width=True)
                        # Add last seen date and location
                        if person.get('meetings'):
                            last_meeting = person['meetings'][-1]
                            st.caption(f"Last seen: {last_meeting['date']}")
                            st.caption(f"At: {last_meeting['location']}")
                        st.button("View Details",
                                 key=f"view_{idx}",
                                 on_click=show_person_modal,
                                 args=(idx,))

# Add this at the bottom of the file, after the grid display
st.header("Where Coaches Are From")

# Create DataFrame for the map
people_by_location = {}
for person in st.session_state.people:
    country = person.get('country', 'Unknown')
    if country not in people_by_location:
        people_by_location[country] = []
    people_by_location[country].append(person['name'])

map_data = []
for country, names in people_by_location.items():
    location = {
        'country': country,
        'country_code': COUNTRIES.get(country, ''),
        'people': ', '.join(names),
        'count': len(names)
    }
    map_data.append(location)
    
    # Add US states if country is United States
    if country == 'United States':
        us_people_by_state = {}
        for person in [p for p in st.session_state.people if p.get('country') == 'United States']:
            state = person.get('state')
            if state:
                if state not in us_people_by_state:
                    us_people_by_state[state] = []
                us_people_by_state[state].append(person['name'])
        
        for state, state_names in us_people_by_state.items():
            map_data.append({
                'country': 'United States',
                'country_code': 'USA',
                'state': state,
                'state_code': US_STATES[state],
                'people': ', '.join(state_names),
                'count': len(state_names)
            })

if map_data:
    df = pd.DataFrame(map_data)
    
    # Create world map
    fig = px.choropleth(
        df,
        locations='country_code',
        locationmode='ISO-3',
        color='count',
        scope='world',
        hover_data=['people'],
        color_continuous_scale='Viridis',
        labels={'count': 'Number of People', 'people': 'Names'}
    )
    
    # Customize the map view to focus on our countries of interest
    fig.update_layout(
        title_text='Coaches Met by Country',
        geo=dict(
            scope='world',
            projection_type='equirectangular',
            visible=True,
            center=dict(lat=45, lon=-100),  # Center roughly between North America and UK
            lonaxis_range=[-130, 0],  # Longitude range to show
            lataxis_range=[15, 75],   # Latitude range to show
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # If there are US people, show US state map
    us_data = df[df['country_code'] == 'USA'].copy()
    if not us_data.empty and 'state_code' in us_data.columns:
        st.subheader("United States Breakdown")
        fig_us = px.choropleth(
            us_data,
            locations='state_code',
            locationmode='USA-states',
            color='count',
            scope='usa',
            hover_data=['people'],
            color_continuous_scale='Viridis',
            labels={'count': 'Number of People', 'people': 'Names'}
        )
        
        fig_us.update_layout(
            title_text='People Met by State (US)',
            geo_scope='usa',
        )
        
        st.plotly_chart(fig_us, use_container_width=True)
else:
    st.info("Add people to see them on the map!")

# Box Cutters Gallery section
st.header("Hackathon Box Cutters")

# Add event form
with st.expander("Add New Event"):
    event_name = st.text_input("Event Name")
    event_date = st.date_input("Event Date")
    event_photos = st.file_uploader(
        "Upload Photos", 
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    if st.button("Add Event") and event_name and event_date and event_photos:
        # Create event directory if it doesn't exist
        event_dir = "event_images"
        if not os.path.exists(event_dir):
            os.makedirs(event_dir)
        
        # Save photos and get their paths
        photo_paths = []
        for photo in event_photos:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_path = f"{event_dir}/{event_name}_{timestamp}.jpg"
            
            # Process and save the image
            img = Image.open(photo)
            img = crop_center_square(img)
            img = img.resize((300, 300))
            img.save(photo_path)
            photo_paths.append(photo_path)
        
        # Create event entry
        event = {
            "name": event_name,
            "date": event_date.strftime("%Y-%m-%d"),
            "photos": photo_paths
        }
        
        st.session_state.events.append(event)
        save_events_data()
        st.success("Event added successfully!")
        st.rerun()

# Display events in a grid
if st.session_state.events:
    # Sort events by date (most recent first)
    sorted_events = sorted(
        st.session_state.events,
        key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'),
        reverse=True
    )
    
    # Calculate grid layout
    COLS = 3
    all_photos = []
    
    # Prepare all photos with their event info
    for event in sorted_events:
        for photo_path in event['photos']:
            if os.path.exists(photo_path):
                all_photos.append({
                    'path': photo_path,
                    'event_name': event['name'],
                    'date': event['date'],
                    'event': event  # Keep reference to full event
                })
    
    # Create grid layout
    rows = math.ceil(len(all_photos) / COLS)
    
    for row in range(rows):
        cols = st.columns(COLS, gap="small")
        for col in range(COLS):
            idx = row * COLS + col
            if idx < len(all_photos):
                photo_info = all_photos[idx]
                with cols[col]:
                    st.image(photo_info['path'], use_container_width=True)
                    st.caption(f"{photo_info['event_name']}")
                    st.caption(f"{photo_info['date']}")
                    
                    # Add delete button for each event
                    if st.button("Delete Event", key=f"delete_event_{photo_info['event_name']}_{idx}"):
                        event = photo_info['event']
                        # Delete all photos
                        for path in event['photos']:
                            if os.path.exists(path):
                                os.remove(path)
                        # Remove event from list
                        st.session_state.events.remove(event)
                        save_events_data()
                        st.rerun()
else:
    st.info("No events added yet. Add your first event above!")