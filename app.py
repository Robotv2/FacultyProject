import os

import altair as alt
import pandas as pd
import streamlit as st

import optimizer
from optimizer import solve_from_path

# Streamlit app title with custom styling
st.markdown("""
    <style>
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
    }
    .header {
        font-size: 24px;
        color: #555;
    }
    .success {
        color: green;
    }
    .warning {
        color: orange;
    }
    </style>
    <div class="title">Interactive Course Allocation Dashboard</div>
    """, unsafe_allow_html=True)


def main():
    # Ensure the uploads directory exists
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # File upload widget in the sidebar
    st.sidebar.header("Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx", "xls"])

    # Interactive filters
    st.sidebar.header("Filters")
    trimester_limit = st.sidebar.slider("Trimester Credit Limit", 1, 10, 6)
    annual_min_limit = st.sidebar.slider("Annual Min Credit Limit", 5, 20, 10)
    annual_max_limit = st.sidebar.slider("Annual Max Credit Limit", 10, 30, 16)

    if uploaded_file is not None:
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Check if the file exists
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
        else:
            # Solve the optimization problem with interactive limits
            result: optimizer.OptimizerResult = solve_from_path(file_path, trimester_limit, annual_min_limit,
                                                                annual_max_limit)

            if result is None:
                st.markdown('<div class="header">No optimal solution found.</div>', unsafe_allow_html=True)
                return

            # Display general summary
            st.markdown('<div class="header">General Summary</div>', unsafe_allow_html=True)
            st.write(f"Total Happiness Index: {result.happiness_index}")
            st.write("Total Credits per Faculty:")
            st.json(result.faculty_credits)

            if result.unassigned_courses:
                st.markdown('<div class="warning">Unassigned Courses:</div>', unsafe_allow_html=True)
                st.write(result.unassigned_courses)
            else:
                st.markdown('<div class="success">All courses have been assigned.</div>', unsafe_allow_html=True)

            # Display course assignments
            st.markdown('<div class="header">Course Assignments</div>', unsafe_allow_html=True)
            assignments_df = result.to_df()
            st.dataframe(assignments_df.style.map(lambda val: 'background-color: darkgreen' if val == 1 else 'background-color: red'))

            # Display specific summary for each faculty
            st.markdown('<div class="header">Faculty Specific Summary</div>', unsafe_allow_html=True)
            for faculty_id, credits in result.faculty_credits.items():
                with st.expander(f"Faculty {faculty_id}"):
                    st.write(f"Total Credits: {credits}")
                    faculty_courses = [course for course, f_id in result.course_assignments.items() if f_id == faculty_id]
                    st.write("Assigned Courses:")
                    st.write(faculty_courses)

                    # Visualize faculty workload
                    chart_data = pd.DataFrame({
                        'Course': faculty_courses,
                        'Credits': [
                            result.faculty_credits[result.course_assignments[course]] for course in faculty_courses]
                    })

                    chart = alt.Chart(chart_data).mark_bar().encode(
                        x='Course',
                        y='Credits',
                        color=alt.value('steelblue')
                    ).properties(
                        title=f"Faculty {faculty_id} Workload"
                    )

                    st.altair_chart(chart, use_container_width=True)


main()
