import random

from optimizer import FacultyOptimizer


def run_monte_carlo_simulation(optimizer: FacultyOptimizer, num_simulations=1000):
    best_allocation = None
    best_happiness = float("-inf")

    for _ in range(num_simulations):
        # Random allocation
        allocation = {}
        for i, course in enumerate(optimizer.courses):
            faculty = random.choice(optimizer.faculty_members)
            allocation[(i, optimizer.faculty_members.index(faculty))] = 1

        # Calculate happiness for this allocation
        happiness = sum(
            optimizer.happiness_index[i][j] * allocation.get((i, j), 0)
            for i in range(len(optimizer.courses))
            for j in range(len(optimizer.faculty_members))
        )

        # If this allocation is better, keep it
        if happiness > best_happiness:
            best_happiness = happiness
            best_allocation = allocation

    return best_allocation, best_happiness