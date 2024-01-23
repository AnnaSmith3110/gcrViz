# import streamlit as st
# import json
# import pandas as pd
# import matplotlib.pyplot as plt
# import plotly.express as px

# # Load and parse your JSON data (replace this with your actual data loading code)
# with open(r'C:\Users\HP\Desktop\assignments\SEM 5\SEM 5 Project\gcr\finalsubs.json', 'r') as file:
#     data = json.load(file)

# # Create a Streamlit app
# st.title("Submission Status Overview")

# # Calculate and display the submission status overview
# total_submissions = len(data)
# turned_in = sum(1 for submission in data if submission["state"] == "TURNED_IN")
# created = sum(1 for submission in data if submission["state"] == "CREATED")
# returned = sum(1 for submission in data if submission["state"] == "RETURNED")

# #------TABLE-------
# overview_data = {
#     "Total Submissions": [total_submissions],
#     "Turned In": [turned_in],
#     "Created": [created],
#     "Returned": [returned]
# }
# df = pd.DataFrame(overview_data)
# # Display the table
# st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)


# ##------PIE CHART#------
# # Create a DataFrame for the pie chart data
# pie_data = pd.DataFrame({
#     'Status': ['Turned In', 'Created', 'Returned'],
#     'Count': [turned_in, created, returned]
# })
# # Create a pie chart using Plotly
# fig = px.pie(pie_data, values='Count', names='Status', title='Submission Status Overview')
# st.plotly_chart(fig)


# #------COURSE WISE TABLE------
# # Create a DataFrame to store course-wise submission status
# course_submission_data = []

# for submission in data:
#     course_id = submission["courseId"]
#     state = submission["state"]
    
#     # Check if a course entry already exists
#     existing_entry = next((entry for entry in course_submission_data if entry["Course ID"] == course_id), None)
    
#     if existing_entry:
#         # Update the existing entry
#         if state in existing_entry:
#             existing_entry[state] += 1
#     else:
#         # Create a new entry for the course
#         course_entry = {"Course ID": course_id, "Turned In": 0, "Created": 0, "Returned": 0}
#         if state in course_entry:
#             course_entry[state] += 1
#         course_submission_data.append(course_entry)

# # Create a DataFrame from the course submission data
# course_df = pd.DataFrame(course_submission_data)

# # Create a bar plot using Streamlit
# st.bar_chart(course_df.set_index("Course ID")[["Turned In", "Created", "Returned"]])

# # Display a table
# st.table(course_df)