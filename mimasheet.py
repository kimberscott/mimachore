import gspread
import pandas as pd
import numpy as np

# Assumptions: The spreadsheet named here has a tab named 'Weights' with columns 'Chore', [each of the NAMES],
# 'Assigned to' (which contains only empty cells and values in NAMES), and 'Fixed weight' (which represents a weight
# out of 100 that should be assumed for a fixed chore; can be blank for other chores).
# The columns with NAMES have unnormalized weights for the
# corresponding chores. Individual weights for fixed chores are ignored in favor of the fixed weights.
SPREADSHEET_ID = "1dMaMGtyNROZz_LkZceEja-EcdrzmW-7QvmzNQcmREEM"
NAMES = ["Kim", "Cody"]  # Names expected as columns + used in 'Assigned to' column
DISPLAY_TOP_K = 100  # How many of the top allocations to write to the Google Sheet

# Get weights from GSheet. This requires setting up authentication for end users as described at
# https://docs.gspread.org/en/latest/oauth2.html
print("Loading weights from GSheet")
gc = gspread.oauth()
sh = gc.open_by_key(SPREADSHEET_ID)
weights = pd.DataFrame(sh.worksheet("Weights").get_all_records())

# Note total fixed weights per person (out of 100), and ensure all assignments are valid
print("Getting effort for fixed chores per person")
fixed_sums_per_person = [
    weights.loc[weights["Assigned to"] == name]["Fixed weight"].sum() for name in NAMES
]
acceptable_assigned_to_vals = NAMES + [""]
if not all(weights["Assigned to"].isin(acceptable_assigned_to_vals)):
    raise ValueError(
        f"Invalid value in 'Assigned to' column of weights worksheet: should all be in {acceptable_assigned_to_vals}"
    )

# Normalize *non-fixed* weights per person, taking into account weights of fixed chores
print("Normalizing weights per person")
chore_is_fixed = weights["Assigned to"] != ""
total_fixed_weights = sum(fixed_sums_per_person)
for name in NAMES:
    weights[name].loc[~chore_is_fixed] = weights[name].loc[~chore_is_fixed] / (sum(weights[name].loc[~chore_is_fixed])) * (100 - total_fixed_weights)
    weights[name].loc[chore_is_fixed] = weights["Fixed weight"].loc[chore_is_fixed]
    assert 99.99 < weights[name].sum() < 100.01

# Brute-force minimax allocation.
print("Constructing possibilities for all chore allocations")
n_chores = len(weights)
options_per_chore = [
    np.arange(len(NAMES)) if assignee == "" else np.array([NAMES.index(assignee)]) for assignee in weights["Assigned to"]
]
allocations = np.array(np.meshgrid(*options_per_chore)).T.reshape(-1, n_chores)
assert allocations.shape == (len(NAMES) ** (len(weights) - sum(chore_is_fixed)), n_chores)

# How much does each person work in each allocation?
print(f"Comparing {allocations.shape[0]} allocations")
sums_per_person = [
    np.matmul(allocations == ind, np.array(weights[name])) for ind, name in enumerate(NAMES)
]
max_sum = np.maximum.reduce(sums_per_person)

# What are the indices of the best allocations?
top_k_ind = np.argpartition(max_sum, DISPLAY_TOP_K)[0:DISPLAY_TOP_K]  # Get the top k values, any order
top_k_ind = top_k_ind[np.argsort(max_sum[top_k_ind])]  # Then order them within that set

# Get the corresponding best allocations and put in a dataframe for viewing
print("Preparing display of best allocations")
best_allocations = pd.DataFrame(allocations[top_k_ind,:], columns=weights['Chore']).applymap(lambda x: NAMES[x])
for ind, name in enumerate(NAMES):
    best_allocations[name] = sums_per_person[ind][top_k_ind]
best_allocations['max'] = max_sum[top_k_ind]

best_allocations = best_allocations.T
best_allocations.reset_index(inplace=True)
best_allocations = best_allocations.rename(columns = {'index':'Chore'})

# Write back to the Google sheet to display
print("Writing back to Google sheet")
try:
    worksheet = sh.add_worksheet(title="Best allocations", rows=DISPLAY_TOP_K+1, cols=n_chores+1)
except:
    worksheet = sh.worksheet("Best allocations")
    worksheet.clear()

worksheet.update(best_allocations.values.tolist())

print("Best allocation found:")
print(best_allocations[['Chore', 0]])