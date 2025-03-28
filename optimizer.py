import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus


class FacultyOptimizer:
    def __init__(self, data_file, max_credits_per_trimester, min_total_credits, max_total_credits):
        self.data = pd.read_excel(data_file)
        self.courses = self.data['Course Code'].tolist()
        self.faculty_members = [col for col in self.data.columns if col.startswith('Faculty ')]
        self.happiness_index = self.data[self.faculty_members].values
        self.min_groups = self.data['Min Nb Groups'].tolist()
        self.max_groups = self.data['Max Nb Groups'].tolist()
        self.credits = self.data['Credits'].tolist()
        self.trimesters = self.data['Trimester'].tolist()

        self.max_credits_per_trimester = max_credits_per_trimester
        self.min_total_credits = min_total_credits
        self.max_total_credits = max_total_credits

        self.model = LpProblem("Faculty_Course_Assignment", LpMaximize)
        self.x = {(i, j): LpVariable(name=f"x_{i}_{j}", cat='Binary') for i in range(len(self.courses)) for j in range(len(self.faculty_members))}
        self.model += lpSum(self.happiness_index[i][j] * self.x[i, j] for i in range(len(self.courses)) for j in range(len(self.faculty_members)))
        self._add_constraints()

    def _add_constraints(self):
        for i in range(len(self.courses)):
            self.model += lpSum(self.x[i, j] for j in range(len(self.faculty_members))) >= self.min_groups[i]
            self.model += lpSum(self.x[i, j] for j in range(len(self.faculty_members))) <= self.max_groups[i]

        for j in range(len(self.faculty_members)):
            self.model += lpSum(self.x[i, j] for i in range(len(self.courses))) >= 1

        for j in range(len(self.faculty_members)):
            for t in set(self.trimesters):
                self.model += lpSum(self.x[i, j] * self.credits[i] for i in range(len(self.courses)) if self.trimesters[i] == t) <= self.max_credits_per_trimester

        for j in range(len(self.faculty_members)):
            self.model += lpSum(self.x[i, j] * self.credits[i] for i in range(len(self.courses))) >= self.min_total_credits
            self.model += lpSum(self.x[i, j] * self.credits[i] for i in range(len(self.courses))) <= self.max_total_credits

    def solve(self):
        self.model.solve()
        self.solution_status = LpStatus[self.model.status]
        self.assignment = {(i, j): self.x[i, j].varValue for i in range(len(self.courses)) for j in range(len(self.faculty_members)) if self.x[i, j].varValue == 1}

    def get_results(self):
        total_happiness = 0
        assigned_courses = set()
        faculty_credits = {faculty: 0 for faculty in self.faculty_members}
        faculty_trimester_credits = {faculty: {t: 0 for t in set(self.trimesters)} for faculty in self.faculty_members}
        assignment_details = []

        for (i, j), value in self.assignment.items():
            faculty_name = self.faculty_members[j]
            course_code = self.courses[i]
            happiness = self.happiness_index[i][j]
            credits = self.credits[i]
            trimester = self.trimesters[i]

            total_happiness += happiness
            assigned_courses.add(course_code)
            faculty_credits[faculty_name] += credits
            faculty_trimester_credits[faculty_name][trimester] += credits
            assignment_details.append((faculty_name, course_code, happiness, credits, trimester))

        not_assigned_courses = [course for course in self.courses if course not in assigned_courses]

        return total_happiness, assignment_details, faculty_credits, faculty_trimester_credits, not_assigned_courses, self.solution_status
