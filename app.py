import streamlit as st
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
                
                # Ensure current_idx is within bounds
                if current_idx >= len(person['photos']):
                    current_idx = len(person['photos']) - 1
                    st.session_state[f"current_photo_{person['name']}"] = current_idx
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if current_idx > 0:
                        if st.button("←"):
                            st.session_state[f"current_photo_{person['name']}"] -= 1
                            st.rerun()
                
                with col2:
                    st.write(f"Photo {current_idx + 1} of {len(person['photos'])}")
                
                with col3:
                    if current_idx < len(person['photos']) - 1:
                        if st.button("→"):
                            st.session_state[f"current_photo_{person['name']}"] += 1
                            st.rerun()
                
                # Display current photo
                if os.path.exists(person['photos'][current_idx]):
                    st.image(person['photos'][current_idx], use_container_width=True)
                    if st.button("Delete Current Photo"):
                        delete_image(person['photos'][current_idx])
                        person['photos'].pop(current_idx)
                        # Reset index if needed after deletion
                        st.session_state[f"current_photo_{person['name']}"] = min(
                            current_idx,
                            len(person['photos']) - 1
                        ) if person['photos'] else 0
                        save_people_data()
                        st.rerun()
            
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
                    st.rerun()
        
        with details_col:
            # Edit fields
            new_name = st.text_input("Name", person['name'])
            new_location = st.text_input("Met at", person['location_met'])
            
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
            
            new_city = st.text_input("City/Town", person.get('city', ''))
            
            # Show and edit dates
            st.write("**Meeting dates:**")
            dates_to_remove = []
            for i, date in enumerate(person['dates']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {date}")
                with col2:
                    if st.button("🗑", key=f"delete_{person['name']}_{date}_{i}"):
                        dates_to_remove.append(date)
            
            # Remove selected dates
            for date in dates_to_remove:
                person['dates'].remove(date)
            
            # Add new date
            new_date = st.date_input("Add new date")
            if st.button("Add Date", key=f"add_date_{person['name']}_modal"):
                date_str = new_date.strftime("%Y-%m-%d")
                if date_str not in person['dates']:
                    person['dates'].append(date_str)
                    person['dates'].sort()
            
            # Save changes
            if (new_name != person['name'] or 
                new_location != person['location_met'] or 
                new_country != person.get('country') or
                new_state != person.get('state') or
                new_city != person.get('city') or
                dates_to_remove):
                
                person.update({
                    "name": new_name,
                    "location_met": new_location,
                    "country": new_country,
                    "state": new_state if new_country == "United States" else None,
                    "city": new_city
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
                st.rerun()

# App title
st.title("People Logger")

# Sidebar for adding new people
with st.sidebar:
    st.header("Add New Meeting")
    with st.form("add_person"):
        name = st.text_input("Name")
        
        # Check if person already exists
        existing_person = None
        for p in st.session_state.people:
            if p['name'].lower() == name.lower():
                existing_person = p
                break
        
        photo = st.file_uploader("Photo", type=['jpg', 'jpeg', 'png'])
        location_met = st.text_input("Location Met")
        
        # Only show origin fields for new people
        if not existing_person:
            country = st.selectbox("Country", options=list(COUNTRIES.keys()))
            
            # Show state selection only for US
            if country == "United States":
                state = st.selectbox("State", options=list(US_STATES.keys()))
            else:
                state = None
                
            city = st.text_input("City/Town")
        else:
            country = existing_person['country']
            state = existing_person.get('state')
            city = existing_person['city']
            st.write(f"Adding new meeting for existing person: {name}")
        
        date_met = st.date_input("Date Met")
        
        submitted = st.form_submit_button("Add Meeting")
        
        if submitted and name and photo and location_met and date_met:
            image_path = save_image(photo, name)
            
            if existing_person:
                # Add to existing person
                existing_person['photos'].append(image_path)
                existing_person['dates'].append(date_met.strftime("%Y-%m-%d"))
                existing_person['dates'].sort()
                st.success("Meeting added successfully!")
            else:
                # Create new person
                person = {
                    "name": name,
                    "photos": [image_path],
                    "location_met": location_met,
                    "country": country,
                    "state": state if country == "United States" else None,
                    "city": city,
                    "dates": [date_met.strftime("%Y-%m-%d")]
                }
                st.session_state.people.append(person)
                st.success("Person added successfully!")
            
            save_people_data()
            st.rerun()

# Main content - Display people grid
st.header("People You've Met")

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
                        # Add last seen date
                        if person['dates']:
                            last_seen = max(person['dates'])
                            st.caption(f"Last seen: {last_seen}")
                        if st.button("View Details", key=f"person_{idx}"):
                            show_person_modal(idx)

# Add this at the bottom of the file, after the grid display
st.header("Where People Are From")

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
        title_text='People Met by Country',
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