import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt

from optimizer import FacultyOptimizer


def main():
    st.title("Faculty Course Assignment Optimizer")

    st.sidebar.header("Configuration")
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])
    max_credits_per_trimester = st.sidebar.number_input("Max Credits per Trimester", min_value=1, value=6)
    min_total_credits = st.sidebar.number_input("Min Total Credits", min_value=1, value=10)
    max_total_credits = st.sidebar.number_input("Max Total Credits", min_value=1, value=16)

    if uploaded_file:
        optimizer = FacultyOptimizer(uploaded_file, max_credits_per_trimester, min_total_credits, max_total_credits)
        optimizer.solve()
        total_happiness, assignment_details, faculty_credits, faculty_trimester_credits, not_assigned_courses = optimizer.get_results()

        # Use tabs for better navigation
        tabs = st.tabs(["Summary", "Assignments", "Credits", "Not Assigned"])

        # Summary Tab
        with tabs[0]:
            st.header("Summary")
            st.metric(label="Total Happiness Score", value=total_happiness)
            st.metric(label="Total Faculty Members", value=len(optimizer.faculty_members))
            st.metric(label="Total Courses", value=len(optimizer.courses))

        # Assignments Tab
        with tabs[1]:
            st.header("Faculty Course Assignments")

            # Create a DataFrame with essential information
            assignments_df = pd.DataFrame(assignment_details, columns=["Faculty", "Course", "Happiness", "Credits", "Trimester"])

            # Display a simplified view initially
            st.dataframe(assignments_df[["Faculty", "Course", "Credits"]])

            # Use expanders for detailed view
            st.subheader("Detailed View")
            for faculty, group in assignments_df.groupby("Faculty"):
                with st.expander(f"{faculty}"):
                    st.write(group[["Course", "Happiness", "Credits", "Trimester"]])

        # Credits Tab
        with tabs[2]:
            st.header("Faculty Credits Summary")
            credits_summary = []
            for faculty, total_credits in faculty_credits.items():
                trimester_credits_str = ", ".join([f"T{t}: {c}" for t, c in faculty_trimester_credits[faculty].items()])
                credits_summary.append([faculty, total_credits, trimester_credits_str])

            credits_df = pd.DataFrame(credits_summary, columns=["Faculty", "Total Credits", "Credits per Trimester"])
            st.dataframe(credits_df)

            # Plot credits distribution
            st.subheader("Credits Distribution")
            faculty_names = list(faculty_credits.keys())
            total_credits_values = list(faculty_credits.values())
            fig, ax = plt.subplots()
            ax.bar(faculty_names, total_credits_values)
            ax.set_xlabel("Faculty")
            ax.set_ylabel("Total Credits")
            ax.set_title("Total Credits per Faculty")
            plt.xticks(rotation=90)
            st.pyplot(fig)

        # Not Assigned Tab
        with tabs[3]:
            st.header("Courses Not Assigned")
            if not_assigned_courses:
                for course in not_assigned_courses:
                    st.write(f"- {course}")
            else:
                st.write("All courses have been assigned.")

if __name__ == "__main__":
    main()