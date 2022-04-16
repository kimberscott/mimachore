# mimachore
Simplified minimax chore allocation implementation with input from Google Sheets

## To use

1. Clone this repo
2. Set up Google auth as described by gspread [for end users](https://docs.gspread.org/en/latest/oauth2.html#for-end-users-using-oauth-client-id)
3. Create a Google Sheet with at least a 'Weights' tab. It should have the following columns:
   * Chore
   * [NAMES] - one column per name of family member to allocate chores to. In this column should be (unnormalized) weights per chore.
   * Assigned to (contains a value in NAMES if the chore is assigned to a particular person, otherwise empty)
   * Fixed weight (contains weights for any chores that are assigned to someone; can be blank otherwise. Individual weights for fixed chores are ignored in favor of the fixed weights.)
4. Edit the list of NAMES and the Google sheet ID in `mimasheet.py`
5. Install the requirements (e.g. `pip install -r requirements.txt`)
6. Run `mimasheet.py` to find the 100 best chore allocations and write them back to a new tab in the Google sheet.

