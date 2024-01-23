import streamlit as st
import json
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

#--------LOAD AND MERGE JSON DATA---------
# Load course data from the course JSON file
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalCourses.json', 'r') as course_file:
    course_data = json.load(course_file)
# Create a dictionary to map course IDs to course names
course_id_to_name = {course['id']: course['name'] for course in course_data}
# Load submission data from the submission JSON file
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalsubs.json', 'r') as submission_file:
    submission_data = json.load(submission_file)
# Replace course IDs with course names in the submission data
for submission in submission_data:
    submission['courseId'] = course_id_to_name.get(submission['courseId'], submission['courseId'])
# Load coures coursework ie:detailed assignment info data
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalcourseworks.json', 'r') as courseWork_file:
     submission_metadata = json.load(courseWork_file)


#-------APP-------------
st.title("Submission Status Overview")
# Calculate and display the submission status overview
total_submissions = len(submission_data)
turned_in = sum(1 for submission in submission_data if submission["state"] == "TURNED_IN")
created = sum(1 for submission in submission_data if submission["state"] == "CREATED")
returned = sum(1 for submission in submission_data if submission["state"] == "RETURNED")


# ------TABLE-------
overview_data = {
    "Total Submissions": [total_submissions],
    "Turned In": [turned_in],
    "Created": [created],
    "Returned": [returned]
}
df = pd.DataFrame(overview_data)
# Display the table
st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)


# ------PIE CHART------
# Create a DataFrame for the pie chart data
pie_data = pd.DataFrame({
    'Status': ['Turned In', 'Created', 'Returned'],
    'Count': [turned_in, created, returned]
})
# Create a pie chart using Plotly
fig = px.pie(pie_data, values='Count', names='Status', title='Submission Status Overview')
st.plotly_chart(fig)


# ------COURSE WISE TABLE------
# Create a DataFrame to store course-wise submission status
course_submission_data = []

for submission in submission_data:
    course_name = submission["courseId"]
    state = submission["state"]

    # Check if a course entry already exists
    existing_entry = next((entry for entry in course_submission_data if entry["Course Name"] == course_name and entry["Status"] == state), None)

    if existing_entry:
        # Update the existing entry
        existing_entry["Count"] += 1
    else:
        # Create a new entry for the course and status combination
        course_entry = {"Course Name": course_name, "Status": state, "Count": 1}
        course_submission_data.append(course_entry)

# Create a DataFrame from the course submission data
course_df = pd.DataFrame(course_submission_data)

# Create a grouped bar chart using Plotly
fig = px.bar(course_df, x="Course Name", y="Count", color="Status", barmode="group", title="Course-wise Submission Status")
st.plotly_chart(fig)


# ------TIMELINE CHART------
submission_dates = [submission["creationTime"] for submission in submission_data]
submission_dates = pd.to_datetime(submission_dates)
# Create a DataFrame with submission dates
timeline_data = pd.DataFrame({"Date": submission_dates})
# Group submission counts by date
submission_counts = timeline_data.resample("D", on="Date").size().fillna(0)
# Apply Gaussian smoothing
smoothed_counts = submission_counts.rolling(7, center=True, min_periods=1).mean()
timeline_data = pd.DataFrame({"Date": submission_counts.index, "Submission Count": smoothed_counts.values})
fig = px.line(timeline_data, x="Date", y="Submission Count", title="Submission Timeline")
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Submission Count")
# Display the timeline chart
st.plotly_chart(fig)

# ------LATE SUBMISSIONS BAR CHART------
# Create a DataFrame to store on-time and late submission counts for each course
course_submission_data = []
for submission in submission_data:
    course_name = submission["courseId"]
    state = submission["state"]

    # Determine if the submission is late based on the presence of the "late" key
    is_late = "late" in submission and submission["late"] is True

    # Check if a course entry already exists
    existing_entry = next((entry for entry in course_submission_data if entry["Course Name"] == course_name), None)

    if existing_entry:
        # Update the existing entry
        if is_late:
            existing_entry["Late Count"] += 1
        else:
            existing_entry["On Time Count"] += 1
    else:
        # Create a new entry for the course
        course_entry = {"Course Name": course_name, "Late Count": 0, "On Time Count": 0}
        if is_late:
            course_entry["Late Count"] = 1
        else:
            course_entry["On Time Count"] = 1
        course_submission_data.append(course_entry)

# Create a DataFrame from the course submission data
course_df = pd.DataFrame(course_submission_data)

# Create a grouped bar chart using Plotly
fig = px.bar(
    course_df,
    x="Course Name",
    y=["Late Count", "On Time Count"],
    title="Course-wise Late vs On Time Submissions",
    labels={"value": "Count"},
)
fig.update_layout(barmode="group")
st.plotly_chart(fig)


#------DROPDOWN FOR LATE ASSIGNMENTS BY COURSE------------
# Create a dictionary to map course IDs to course names
course_id_to_name = {course['id']: course['name'] for course in course_data}
# Create a dropdown to select a course
selected_course = st.selectbox('Select a course:', list(course_id_to_name.values()))
# Get the current date (you may need to import datetime)
current_date = datetime.now()
