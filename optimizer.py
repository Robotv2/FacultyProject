import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

from models import Faculty, Course


def solve_from_path(file_path: str, trimester_limit=6, annual_min=10, annual_max=16):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please use CSV or Excel.")

    courses = []
    faculty_members = []
    faculty_preferences = {}

    faculty_ids = [col for col in df.columns if col.startswith('Faculty_')]

    for faculty_id in faculty_ids:
        faculty_preferences[faculty_id] = {}
        faculty_members.append(Faculty(faculty_id, faculty_preferences[faculty_id]))

    for index, row in df.iterrows():
        course_id = row['Course']
        credits = int(row['Credits'])
        courses.append(Course(course_id, credits))

        for faculty_id in faculty_ids:
            faculty_preferences[faculty_id][course_id] = int(row[faculty_id])

    optimizer = CourseAllocationOptimizer(
        courses,
        faculty_members,
        trimester_limit=trimester_limit,
        annual_min=annual_min,
        annual_max=annual_max
    )
    result = optimizer.solve()
    return result


class CourseAllocationOptimizer:
    def __init__(self, courses, faculty_members, trimester_limit=6, annual_min=10, annual_max=16):
        self.courses = courses
        self.faculty_members = faculty_members
        self.trimester_limit = trimester_limit
        self.annual_min = annual_min
        self.annual_max = annual_max

        self.model = LpProblem("Course_Allocation", LpMaximize)
        self.x = self.create_decision_variables()
        self.setup_problem()

    def create_decision_variables(self):
        """Create binary decision variables for the optimization problem."""
        return {(c.id, f.id): LpVariable(f"x_{c.id}_{f.id}", cat="Binary") for c in self.courses for f in
                self.faculty_members}

    def setup_problem(self):
        """Set up the optimization problem with objective and constraints."""
        self.add_objective_function()
        self.add_constraints()

    def add_objective_function(self):
        """Add the objective function to maximize the happiness index."""
        self.model += lpSum(
            self.faculty_members[f_idx].preferences[c.id] * self.x[c.id, self.faculty_members[f_idx].id]
            for f_idx in range(len(self.faculty_members))
            for c in self.courses
        ), "Total_Happiness_Index"

    def add_constraints(self):
        """Add constraints to the optimization problem."""
        self.add_course_assignment_constraints()
        self.add_faculty_workload_constraints()

    def add_course_assignment_constraints(self):
        """Each course must be assigned to one faculty member."""
        for c in self.courses:
            self.model += lpSum(self.x[c.id, f.id] for f in self.faculty_members) == 1

    def add_faculty_workload_constraints(self):
        """Faculty workload constraints for trimester and annual limits."""
        trimesters = [self.courses[:6], self.courses[6:12], self.courses[12:]]

        for f in self.faculty_members:
            for trimester in trimesters:
                self.model += lpSum(c.credits * self.x[c.id, f.id] for c in trimester) <= self.trimester_limit
            self.model += lpSum(c.credits * self.x[c.id, f.id] for c in self.courses) <= self.annual_max
            self.model += lpSum(c.credits * self.x[c.id, f.id] for c in self.courses) >= self.annual_min

    def solve(self):
        """Solve the optimization problem."""
        status = self.model.solve(PULP_CBC_CMD(msg=False))
        if status != 1:  # 1 indicates an optimal solution is found
            print("No optimal solution found.")
        else:
            return self.create_optimizer_result()

    def create_optimizer_result(self):
        """Create an OptimizerResult object with the results of the optimization."""
        course_assignments = {}
        faculty_credits = {f.id: 0 for f in self.faculty_members}
        unassigned_courses = []

        for c in self.courses:
            assigned = False
            for f in self.faculty_members:
                if self.x[c.id, f.id].value() == 1:
                    course_assignments[c.id] = f.id
                    faculty_credits[f.id] += c.credits
                    assigned = True
            if not assigned:
                unassigned_courses.append(c.id)

        happiness_index = self.model.objective.value()
        return OptimizerResult(course_assignments, faculty_credits, happiness_index, unassigned_courses)


class OptimizerResult:
    def __init__(self, course_assignments, faculty_credits, happiness_index, unassigned_courses):
        """
        :param course_assignments: A dictionary mapping course IDs to faculty member IDs.
        :param faculty_credits: A dictionary mapping faculty member IDs to their total credits.
        :param happiness_index: The total happiness index achieved by the optimization.
        :param unassigned_courses: A list of course IDs that were not assigned to any faculty member.
        """
        self.course_assignments = course_assignments
        self.faculty_credits = faculty_credits
        self.happiness_index = happiness_index
        self.unassigned_courses = unassigned_courses

    def to_df(self):
        all_faculty_ids = list(self.faculty_credits.keys())
        assignment_matrix = {
            course_id: [int(faculty_id == self.course_assignments.get(course_id)) for faculty_id in all_faculty_ids] for
            course_id in self.course_assignments}
        assignments_df = pd.DataFrame.from_dict(assignment_matrix, orient='index', columns=[f"Faculty {f_id}" for f_id in all_faculty_ids])
        assignments_df.index.name = 'Class'
        return assignments_df

    def display_stats(self):
        print("Total Credits per Faculty:")
        for faculty_id, credits in self.faculty_credits.items():
            print(f"Faculty {faculty_id}: {credits} credits")

        print(f"Total Happiness Index: {self.happiness_index}")

        if self.unassigned_courses:
            print("Unassigned Courses:")
            for course_id in self.unassigned_courses:
                print(f"Course {course_id} is unassigned")
        else:
            print("All courses have been assigned.")
