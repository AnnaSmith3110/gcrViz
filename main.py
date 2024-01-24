import streamlit as st
import json
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import altair as alt
import numpy as np
from datetime import datetime
import random
from streamlit_tags import st_tags
import pytz
from collections import defaultdict


#----SCORE CARDS----
st.markdown(
            """
        <style>
        div[data-testid="stHorizontalBlock"] {
        width: 60vw;
        }
        div[data-testid="metric-container"] {
        padding:10px;
        border-radius: 3px;
        min-height: 20vh;
        width: 185px;
        background: linear-gradient(to top, rgba(243, 184, 6, 0.3), rgba(243, 184, 6, 0));
        }
        div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
        overflow-wrap: break-word;
        white-space: break-spaces;
        color: black;
        }
        div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div p {
        font-size: 1rem !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
#----SCORE CARD DELTA---
st.markdown(
    """
    <style>
    [data-testid="stMetricDelta"] {
        margin-top: -20px;
        font-weight: 600;
        font-size: 1.2rem;
    }
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#-----SIDEBAR BG------
st.markdown(
    """
    <style>
        [data-testid=stSidebar] {
        background-color: #F3B806;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#----SCORE CARD STYLES---
#rgb(0 104 201)
st.markdown(
    """
<style>

div[data-testid="metric-container"], div[data-testid="stMetric"] {
    border: 1.5px solid #F3B806;
    background: linear-gradient(to bottom, #F3B806, rgba(243, 184, 6, 0));

    padding: 10px;
    border-radius: 3px;
    height: 150px;
}
p {
color: red;
}
div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div p {
    font-size: 1rem !important;
    color: white; 
    font-weight: 600;
    # st-emotion-cache-q8sbsg e1nzilvr5
}
[data-testid="stMetricValue"] {
    height: 100px;
}
div[data-testid="stMetricValue"] > div {
    background-color: ;
    margin-bottom: -10px;
    padding: 10px;
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True,
)

#-----RADIO BTN COLOR-----
st.markdown (
    """
    <style>
    [data-testid="stMarkdownContainer"]>p, [data-testid="stMarkdownContainer"] {
       color: black;
        font-weight: 600;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#--------LOAD AND MERGE JSON DATA---------
# Load course data from the course JSON file
with open(r'.\GCRdata\finalCourses.json', 'r', encoding='utf-8') as course_file:
    course_data = json.load(course_file)

# Create a dictionary to map course IDs to course names
course_id_to_name = {course['id']: course['name'] for course in course_data}
# Create a dictionary to map course names to course IDs
course_name_to_id = {course['name']: course['id'] for course in course_data}

# Load submission data from the submission JSON file
with open(r'.\GCRdata\finalsubs.json', 'r', encoding='utf-8') as submission_file:
    submission_data = json.load(submission_file)
# Replace course IDs with course names in the submission data
for submission in submission_data:
    submission['courseId'] = course_id_to_name.get(submission['courseId'], submission['courseId'])
# Load coures coursework ie:detailed assignment info data
with open(r'.\GCRdata\finalcourseworks.json', 'r', encoding='utf-8') as courseWork_file:
     submission_metadata = json.load(courseWork_file)


#---------------GENERAL OVERVIEW FUNCTIONS-------------------------
def subStatusOverview():
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
    #st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # ------PIE CHART------
    # Create a DataFrame for the pie chart data
    pie_data = pd.DataFrame({
        'Status': ['Turned In', 'Created', 'Returned'],
        'Count': [turned_in, created, returned]
    })
    # Create a pie chart using Plotly
    fig = px.pie(pie_data, values='Count', names='Status', title='Submission Status Overview')
    st.plotly_chart(fig)


# ------TIMELINE CHART------
def subTimeline():
    #LATEST
    submission_dates = [submission.get("creationTime", "") for submission in submission_data]
    submission_dates = [date for date in submission_dates if date]  # Remove empty strings
    submission_dates = pd.to_datetime(submission_dates, errors='coerce')
    
    # Remove NaT (Not-a-Time) values
    submission_dates = submission_dates.dropna()
    
    # Create a DataFrame with submission dates
    timeline_data = pd.DataFrame({"Date": submission_dates})
    
    # Group submission counts by date
    submission_counts = timeline_data.resample("D", on="Date").size().fillna(0)
    
    # Apply Gaussian smoothing
    smoothed_counts = submission_counts.rolling(7, center=True, min_periods=1).mean()
    timeline_data = pd.DataFrame({"Date": submission_counts.index, "Submission Count": smoothed_counts.values})

    fig = px.line(timeline_data, x="Date", y="Submission Count",title="Submission Timeline")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Submission Count")
    
    # Display the timeline chart
    st.plotly_chart(fig)



# helper Function to convert a UTC datetime to IST
def convert_to_ist(utc_datetime_str):
    try:
        utc_datetime = datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_datetime = utc_datetime.replace(tzinfo=pytz.UTC)  # Add UTC timezone info
        ist_timezone = pytz.timezone("Asia/Kolkata")  # IST timezone
        ist_datetime = utc_datetime.astimezone(ist_timezone)
        return ist_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "Invalid Date/Time"  # Handle invalid datetime strings
    

# ------SUBMISSIONS BY TIME OF DAY CHART------
def subTimeOfDay():     
    # Add labels and title
    st.subheader("Submission Times Throughout the Day")             
    st.write("**24 Hr Format**", unsafe_allow_html=True) 
    # Extract submission times and create a DataFrame
    submission_times = []
    for metadata in submission_metadata:
        update_time_str = metadata.get("updateTime")
        if update_time_str:
            # Convert to IST
            ist_time = convert_to_ist(update_time_str)
            submission_times.append(ist_time)

    # Create a DataFrame with the submission times in IST
    df = pd.DataFrame({"Submission Times (IST)": submission_times})

    # Extract the hour of submission
    df["Hour of Submission"] = pd.to_datetime(df["Submission Times (IST)"]).dt.hour

    # Group by the hour and count the submissions
    hourly_submission_counts = df["Hour of Submission"].value_counts().sort_index()

    # Create a Streamlit bar chart
    st.bar_chart(hourly_submission_counts)

    st.markdown("---")  # Add a separator


def avgAssignmentsWeek():
    # Initialize variables for start and end dates
    start_date = None
    end_date = None

    # Iterate through the submission_metadata to find start and end dates
    for assignment in submission_metadata:
        creation_time_str = assignment.get("creationTime")
        if creation_time_str:
            creation_time = datetime.strptime(creation_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            if start_date is None or creation_time < start_date:
                start_date = creation_time
            if end_date is None or creation_time > end_date:
                    end_date = creation_time
    # Calculate the total number of assignments
    total_assignments = len(submission_metadata)

    # Calculate the total number of weeks
    total_weeks = (end_date - start_date).days / 7

    # Calculate the average assignments per week
    average_assignments_per_week = round(total_assignments / total_weeks)
    return average_assignments_per_week



# -----------SCORE CARD FNS----------
def     scorecards():
    # Assuming you have the relevant data loaded into submission_data
    col1, col2, col3, col4 = st.columns(4)
    total_submissions = len(submission_data)
    total_on_time = sum(1 for submission in submission_data if not submission.get("late", False))
    total_late_missing = total_submissions - total_on_time
    # Calculate percentages
    percent_on_time = round((total_on_time / total_submissions) * 100)
    percent_late_missing = round((total_late_missing / total_submissions) * 100)
    
    # Total Submissions Metric
    with col1:
        st.metric("Total Submissions", total_submissions, delta="#", delta_color="off")
    # % Turned in on Time Metrics
    with col2:
        ans = avgAssignmentsWeek()
        st.metric("Avg Assignments/Week", ans, delta="#", delta_color="off")
        
    # % Late/Missing Submissions Metric
    with col3:
        if percent_on_time > 80:
            st.metric("On Time Submissions", f"{percent_on_time}%", delta="+")
        else:
            st.metric("On Time Submissions", f"{percent_on_time}%", delta="-")
        
    # Average Grade Metric
    with col4:
        if percent_late_missing < 25:
            st.metric("Late Submissions", f"{percent_late_missing}%", delta="-", delta_color="inverse")
        else:
            st.metric("Late Submissions", f"{percent_late_missing}%", delta="+", delta_color="inverse")
        
    st.divider()
        

#---------------COURSE SPECIFIC FUNCTIONS-------------------------
#--course wise table---
def courseSubBar():
# Create a dictionary to store the assignment counts per course
    course_assignment_counts = {}

    for submission in submission_data:
        course_name = submission["courseId"]

        if course_name in course_assignment_counts:
            course_assignment_counts[course_name] += 1
        else:
            course_assignment_counts[course_name] = 1

    # Create a list of dictionaries to create the DataFrame
    data = [{"Course Name": course, "Count": count}
            for course, count in course_assignment_counts.items()]

    # Create a DataFrame from the data
    course_df = pd.DataFrame(data)

    # Create a bar chart using Plotly
    fig = px.bar(course_df, x="Course Name", y="Count", title="Total Assignments per Course")
    st.plotly_chart(fig)


def courseOntimeLate():
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


# Helper function to check if an assignment is missing
def is_assignment_missing(submission):
    return submission.get("late", False) == True and submission["state"] == "CREATED"
   
   
# ------LATE COURSES DROPDOWN------
# Function to display missing assignments
def lateCourseDropdown():
    st.write("\n")
    st.subheader("Missing & Late Assignments")
    # Create a sidebar to select a course
    selected_course_name = st.selectbox("Select a Course", ["All Courses"] + list(course_name_to_id.keys()))
   
    table_data = []
    courses_with_assignments = [] #stores only courses with assignments assoc (due to max limit of 15 in API call)
    # Loop through the submissions in submission_data
    for submission in submission_data:
        course_name = submission["courseId"]
        # DIFFERENTIATE BETWEEN LATE AND MISSING ASSIGNMENTS 
        if submission.get("state") == "CREATED":               
            if submission.get("late"):
                assignment_status = "Missing"
            else:
                assignment_status = "Assigned"
        elif submission.get("state") == "TURNED_IN" and submission.get("late"):
                assignment_status = "Turned in Late"
        else:
            assignment_status = "error"


        if submission.get("late", False) and (selected_course_name == "All Courses" or course_name == selected_course_name):
            # Find the corresponding assignment details in submission_metadata
            assignment_details = None
            for metadata in submission_metadata:
                if metadata["id"] == submission["courseWorkId"]:
                    assignment_details = metadata
                    break

            if assignment_details:
                # Get the assignment title, course name, and link
                assignment_title = assignment_details.get("title", "N/A")
                course_id = assignment_details.get("courseId", "N/A")
                course_name = course_id_to_name.get(course_id, "N/A")
                assignment_description = assignment_details.get("description", "N/A")
                link = submission.get("alternateLink", "N/A")
                due_date = assignment_details.get("dueDate", {})
                due_date_str = f"{due_date.get('year', 'N/A')}-{due_date.get('month', 'N/A')}-{due_date.get('day', 'N/A')}"


                 # Add assignment details to the table_data list as a dictionary
                table_data.append({
                    "Course": course_name,
                    "Assignment Title": assignment_title,
                    "Status": assignment_status,
                    "Due Date": due_date_str,
                    "Description": assignment_description,
                    "Link": link
                })


    # # Create a DataFrame from the table_data list
    df = pd.DataFrame(table_data)
    # # Render the course names as tags with dynamically assigned random colors
    st.data_editor(df, hide_index=True)


# ------LATE COURSES TABLE------
def courseSubTable():
    # Create a dictionary to store course statistics
    course_statistics = {}

    # Calculate course statistics
    for submission in submission_data:
        course_id = submission.get("courseId")
        if course_id not in course_statistics:
            course_statistics[course_id] = {
                "Total Assignments": 0,
                "Late Assignments": 0,
                "On-Time Assignments": 0,
            }

        total_assignments = course_statistics[course_id]["Total Assignments"]
        late_assignments = course_statistics[course_id]["Late Assignments"]
        
        total_assignments += 1
        if submission.get("late", False):
            late_assignments += 1

        course_statistics[course_id]["Total Assignments"] = total_assignments
        course_statistics[course_id]["Late Assignments"] = late_assignments
        course_statistics[course_id]["On-Time Assignments"] = total_assignments - late_assignments

    # Create a DataFrame from course statistics
    course_stats_df = pd.DataFrame(course_statistics).T
    course_stats_df.index.name = "Course ID"
     # Calculate late and on-time percentages
    course_stats_df["Late %"] = (course_stats_df["Late Assignments"] / course_stats_df["Total Assignments"]) * 100
    course_stats_df["On-Time %"] = 100 - course_stats_df["Late %"]
    # Remove the "Late Assignments" and "On-Time Assignments" columns
    course_stats_df.drop(columns=["Late Assignments", "On-Time Assignments"], inplace=True)
    
    # Rearrange columns: "On-Time %" before "Late %"
    course_stats_df = course_stats_df[["Total Assignments", "On-Time %", "Late %"]]

    # Rename columns for st.data_editor
    course_stats_df.columns = ["Total Assignments", "On-Time %", "Late %"]

    st.data_editor(
        course_stats_df,
        column_config={
            "Late %": st.column_config.ProgressColumn(
                "Late %",
                format="%.2f%%",
                min_value=0,
                max_value=100,
            ),
            "On-Time %": st.column_config.ProgressColumn(
                "On-Time %",
                format="%.2f%%",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=False,  # Set to True if you want to hide the index column
    )
                

#--------------------------------------MAIN--------------------------------------------
# Define the function for the general overview page
def general_overview():
    st.title("General Overview")
    #--scorecards---
    scorecards()
    #---sub timeline---
    subTimeline()
    #--sub time of day---
    subTimeOfDay()
    #---sub overview: table+pie chart---
    subStatusOverview()


# Define the function for the course-specific information page
def course_specific_info():
    st.title("Course-Specific Information")
    #--course wise submissions bar chart
    courseSubBar()
    #--course wise on time vs missing bar chart
    courseOntimeLate()
    #--course wise table of submission status
    courseSubTable()
    #--show missing assignments by course dropdown
    lateCourseDropdown()
        

    
    
#-----------------------SIDEBAR SELECT PAGE----------------------------------
# Create a sidebar radio button to choose the page
selected_page = st.sidebar.radio("Select a page", ["General Overview", "Course-Specific Info"])
# Conditionally render the selected page
if selected_page == "General Overview":
    general_overview()
elif selected_page == "Course-Specific Info":
    course_specific_info()