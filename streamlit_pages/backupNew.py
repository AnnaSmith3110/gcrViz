import streamlit as st
import json
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

#-----------------------STYLES-----------------------------
#----SCORE CARDS----
st.markdown(
            """
        <style>
        div[data-testid="metric-container"] {
        border: 1px solid lightgrey;
        padding:10px;
        border-radius: 3px;
        min-height: 20vh;
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
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



#--------LOAD AND MERGE JSON DATA---------
# Load course data from the course JSON file
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalCourses.json', 'r', encoding='utf-8') as course_file:
    course_data = json.load(course_file)

# Create a dictionary to map course IDs to course names
course_id_to_name = {course['id']: course['name'] for course in course_data}
# Create a dictionary to map course names to course IDs
course_name_to_id = {course['name']: course['id'] for course in course_data}

# Load submission data from the submission JSON file
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalsubs.json', 'r', encoding='utf-8') as submission_file:
    submission_data = json.load(submission_file)
# Replace course IDs with course names in the submission data
for submission in submission_data:
    submission['courseId'] = course_id_to_name.get(submission['courseId'], submission['courseId'])
# Load coures coursework ie:detailed assignment info data
with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalcourseworks.json', 'r', encoding='utf-8') as courseWork_file:
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


def subTimeline():
    # ------TIMELINE CHART------
    # submission_dates = [submission["creationTime"] for submission in submission_data]
    # submission_dates = pd.to_datetime(submission_dates)
    # # Create a DataFrame with submission dates
    # timeline_data = pd.DataFrame({"Date": submission_dates})
    # # Group submission counts by date
    # submission_counts = timeline_data.resample("D", on="Date").size().fillna(0)
    # # Apply Gaussian smoothing
    # smoothed_counts = submission_counts.rolling(7, center=True, min_periods=1).mean()
    # timeline_data = pd.DataFrame({"Date": submission_counts.index, "Submission Count": smoothed_counts.values})
    # fig = px.line(timeline_data, x="Date", y="Submission Count", title="Submission Timeline")
    # fig.update_xaxes(title_text="Date")
    # fig.update_yaxes(title_text="Submission Count")
    # # Display the timeline chart
    # st.plotly_chart(fig)
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
    
    fig = px.line(timeline_data, x="Date", y="Submission Count", title="Submission Timeline")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Submission Count")
    
    # Display the timeline chart
    st.plotly_chart(fig)

# Helper fumction calc avg grade
def calculate_average_grade():
    # total_grade = 0
    # num_submissions_with_grades = 0

    # for submission in submission_data:
    #     if "assignedGrade" in submission:
    #         assigned_grade = submission["assignedGrade"]
    #         try:
    #             # Try to parse the grade as a float
    #             assigned_grade = float(assigned_grade)
    #             total_grade += assigned_grade
    #             num_submissions_with_grades += 1
    #         except ValueError:
    #             # Handle cases where assignedGrade is not a valid float
    #             pass

    # if num_submissions_with_grades > 0:
    #     average_grade = round((total_grade / num_submissions_with_grades)*100)
    #     return total_grade
    # else:
    #     return None  # Return None if no valid grades are found
    total_weighted_score = 0
    total_max_points = 0

    for submission in submission_data:
        course_name = submission["courseId"]  # Get the course name
        assignment_id = submission["courseWorkId"]
        
        # Look up the course ID based on the course name
        course_id = course_name_to_id.get(course_name, None)
        # st.write(course_id)
        # st.warning(assignment_id) 
        #if course_id is not None and assignment_id in submission_metadata:
        
        if course_id is not None and assignment_id is not None in submission_metadata:
            
            max_points = submission_metadata[assignment_id].get("maxPoints")
            assigned_grade = submission.get("assignedGrade")

            if max_points is not None and assigned_grade is not None:
                try:
                    max_points = float(max_points)
                    assigned_grade = float(assigned_grade)
                    weighted_score = (assigned_grade / max_points) * 100  # Convert to percentage
                    total_weighted_score += weighted_score
                    total_max_points += max_points
                except ValueError:
                    # Handle cases where maxPoints or assignedGrade is not a valid float
                    pass

    if total_max_points > 0:
        average_grade = (total_weighted_score / total_max_points)  # Calculate the weighted average
        return round(average_grade, 2)
    else:
        return None  # Handle the case when there are no valid grades


    

def scorecards():
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
        if percent_on_time > 80:
            st.metric("Turned in on Time", f"{percent_on_time}%", delta="+")
        else:
            st.metric("Turned in on Time", f"{percent_on_time}%", delta="-")
    # % Late/Missing Submissions Metric
    with col3:
        if percent_late_missing < 25:
            st.metric("Late Submissions", f"{percent_late_missing}%", delta="-", delta_color="inverse")
        else:
            st.metric("Late Submissions", f"{percent_late_missing}%", delta="+", delta_color="inverse")
    # Average Grade Metric
    with col4:
        # Calculate the average grade here (replace None with your calculation)
        average_grade = calculate_average_grade()
        if average_grade is not None:
            st.metric("Average Grade", f"{average_grade}%", "Your Average Grade")
        else:
            st.metric("Average Grade", "N/A", "Your Average Grade")
    st.divider()
        

#---------------COURSE SPECIFIC FUNCTIONS-------------------------
#--course wise table---
def courseSubBar():
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


# Function to display missing assignments
def lateCourseDropdown():
    # st.write("\n")
    # st.subheader("Missing & Late Assignments")
    # # Create a sidebar to select a course
    # selected_course = st.selectbox("Select a Course", ["All Courses"] + list(course_id_to_name.values()))

    # # Loop through the submissions in submission_data
    # for submission in submission_data:
    #     if submission.get("late", False) and (selected_course == "All Courses" or submission["courseId"] == selected_course):
    #         # Find the corresponding assignment details in submission_metadata
    #         assignment_details = None
    #         for metadata in submission_metadata:
    #             if metadata["id"] == submission["courseWorkId"]:
    #                 assignment_details = metadata
    #                 break

    #         if assignment_details:
    #             # Get the assignment title, course name, and link
    #             assignment_title = assignment_details.get("title", "N/A")
    #             course_name = course_id_to_name.get(assignment_details.get("courseId"), "N/A")
    #             link = submission.get("alternateLink", "N/A")

    #             # Display assignment details
    #             st.markdown(f'**Course**: ***{course_name}***')
    #             st.markdown(f'**Assignment Titwle**: {assignment_title}')
    #             st.markdown(f'**Description:** {assignment_details.get("description", "N/A")}')
    #             due_date = assignment_details.get("dueDate", {})
    #             due_date_str = f"{due_date.get('year', 'N/A')}-{due_date.get('month', 'N/A')}-{due_date.get('day', 'N/A')}"
    #             st.markdown(f'**Due Date:** {due_date_str}')
    #             st.markdown(f'**Link:** [{assignment_title} Assignment]({link})')
    #             st.divider()
    st.write("\n")
    st.subheader("Missing & Late Assignments")
    # Create a sidebar to select a course
    selected_course_name = st.selectbox("Select a Course", ["All Courses"] + list(course_name_to_id.keys()))

    # Loop through the submissions in submission_data
    for submission in submission_data:
        course_name = submission["courseId"]
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
                link = submission.get("alternateLink", "N/A")

                # Display assignment details
                st.markdown(f'**Course**: ***{course_name}***')
                st.markdown(f'**Assignment Title**: {assignment_title}')
                st.markdown(f'**Description:** {assignment_details.get("description", "N/A")}')
                due_date = assignment_details.get("dueDate", {})
                due_date_str = f"{due_date.get('year', 'N/A')}-{due_date.get('month', 'N/A')}-{due_date.get('day', 'N/A')}"
                st.markdown(f'**Due Date:** {due_date_str}')
                st.markdown(f'**Link:** [{assignment_title} Assignment]({link})')
                st.divider()
                


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

    # Display course statistics
    st.subheader("Course Submissions States")

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


    # Display the DataFrame with progress bars using st.data_editor
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
    #---sub overview: table+pie chart---
    subStatusOverview()
    #---sub timeline---
    subTimeline()

    


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