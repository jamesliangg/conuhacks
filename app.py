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
            if os.path.exists(person['photo']):
                st.image(person['photo'], use_container_width=True)
                if st.button("Delete Photo"):
                    delete_image(person['photo'])
                    person['photo'] = None
                    save_people_data()
                    st.rerun()
            
            new_photo = st.file_uploader("Update photo", type=['jpg', 'jpeg', 'png'])
            if new_photo:
                delete_image(person['photo'])
                person['photo'] = save_image(new_photo, person['name'])
                save_people_data()
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
                if person['photo']:
                    delete_image(person['photo'])
                st.session_state.people.pop(st.session_state.current_person_idx)
                save_people_data()
                close_modal()
                st.rerun()

# App title
st.title("People Logger")

# Sidebar for adding new people
with st.sidebar:
    st.header("Add New Person")
    with st.form("add_person"):
        name = st.text_input("Name")
        photo = st.file_uploader("Photo", type=['jpg', 'jpeg', 'png'])
        location_met = st.text_input("Location Met")
        origin = st.text_input("Where they're from")
        date_met = st.date_input("Date Met")
        
        submitted = st.form_submit_button("Add Person")
        
        if submitted and name and photo and location_met and origin and date_met:
            image_path = save_image(photo, name)
            
            person = {
                "name": name,
                "photo": image_path,
                "location_met": location_met,
                "origin": origin,
                "dates": [date_met.strftime("%Y-%m-%d")]
            }
            
            st.session_state.people.append(person)
            save_people_data()
            st.success("Person added successfully!")
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
                if os.path.exists(person['photo']):
                    # Display image
                    st.image(person['photo'], 
                            caption=person['name'], 
                            use_container_width=True)
                    # Add clickable button over the image
                    if st.button("View Details", key=f"person_{idx}"):
                        show_person_modal(idx)