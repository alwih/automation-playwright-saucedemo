# The password is the same for every user
PASSWORD = "secret_sauce"

# All usernames listed on the SauceDemo login page
ACCEPTED_USERS = [
    "standard_user",
    "locked_out_user",
    "problem_user",
    "performance_glitch_user",
    "error_user",
    "visual_user",
]

# Every accepted user except locked_out_user can log in
LOGIN_USERS = [user for user in ACCEPTED_USERS if user != "locked_out_user"]

# Users whose cart buttons are broken on purpose
BROKEN_CART_USERS = ["problem_user", "error_user"]
