import streamlit as st
from datetime import datetime
import json
import os
from PIL import Image
import math

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
            new_origin = st.text_input("From", person['origin'])
            
            # Show and edit dates
            st.write("**Meeting dates:**")
            dates_to_remove = []
            for date in person['dates']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {date}")
                with col2:
                    if st.button("🗑", key=f"delete_{date}"):
                        dates_to_remove.append(date)
            
            # Remove selected dates
            for date in dates_to_remove:
                person['dates'].remove(date)
            
            # Add new date
            new_date = st.date_input("Add new date")
            if st.button("Add Date"):
                date_str = new_date.strftime("%Y-%m-%d")
                if date_str not in person['dates']:
                    person['dates'].append(date_str)
                    person['dates'].sort()
            
            # Save changes
            if (new_name != person['name'] or 
                new_location != person['location_met'] or 
                new_origin != person['origin'] or 
                dates_to_remove):
                
                person.update({
                    "name": new_name,
                    "location_met": new_location,
                    "origin": new_origin
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
        
        # Only show "Where they're from" for new people
        if not existing_person:
            origin = st.text_input("Where they're from")
        else:
            origin = existing_person['origin']
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
                    "origin": origin,
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