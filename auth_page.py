# Log in Page

import flet as ft
from database.users import get_all_users, verify_user, create_user

class AuthPage:
    def __init__(self, page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success # Callback to open main app

    def show_profile_selection(self):
        self.page.controls.clear()
        self.page.vertical_alignment = "center"
        self.page.horizontal_alignment = "center"

        # Fetch active users from PostgreSQL
        users = get_all_users()

        profiles_row = ft.Row(wrap=True, alignment="center", spacing=30)

        # 1. Generate an Avatar Circle for each existing user
        for user in users:
            profile_card = ft.Column(
                [
                    ft.Container(
                        width=100, height=100,
                        shape=ft.BoxShape.CIRCLE,
                        gradient=ft.LinearGradient(["#4F46E5", "#06B6D4"]), # Premium look
                        alignment=ft.alignment.center,
                        ink=True,
                        on_click=lambda e, u=user["username"]: self.show_login_prompt(u),
                        content=ft.Icon(ft.icons.PERSON, size=50, color="white"),
                        shadow=ft.BoxShadow(blur_radius=10, color="#00000020")
                    ),
                    ft.Text(user["username"], size=16, weight="bold")
                ],
                horizontal_alignment="center"
            )
            profiles_row.controls.append(profile_card)

        # 2. Add the "+" Circle for New User Registration
        add_profile_card = ft.Column(
            [
                ft.Container(
                    width=100, height=100,
                    shape=ft.BoxShape.CIRCLE,
                    bgcolor="#E5E7EB",
                    border=ft.border.all(2, "grey300"),
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=lambda e: self.show_signup_page(),
                    content=ft.Icon(ft.icons.ADD, size=40, color="grey600")
                ),
                ft.Text("Add Profile", size=16, color="grey600")
            ],
            horizontal_alignment="center"
        )
        profiles_row.controls.append(add_profile_card)

        # Render Main Layout
        self.page.add(
            ft.Text("Who is learning Georgian today?", size=32, weight="bold"),
            ft.Container(height=30),
            profiles_row
        )
        self.page.update()

    # --- PROMPT PASSWORD FOR SELECTED PROFILE ---
    def show_login_prompt(self, username):
        self.page.controls.clear()

        password_field = ft.TextField(label="Enter Password", password=True, can_reveal_password=True, width=280)
        error_text = ft.Text("", color="red")

        def handle_login(e):
            user = verify_user(username, password_field.value)
            if user:
                self.on_login_success(user) # Login successful, pass user details up
            else:
                error_text.value = "❌ Incorrect password!"
                self.page.update()

        self.page.add(
            ft.Icon(ft.icons.LOCK_PERSON_ROUNDED, size=70, color="blue"),
            ft.Text(f"Welcome back, {username}!", size=24, weight="bold"),
            ft.Container(height=15),
            password_field,
            error_text,
            ft.Container(height=15),
            ft.ElevatedButton("Unlock Profile", on_click=handle_login, width=280, bgcolor="blue", color="white"),
            ft.TextButton("Back to Profiles", on_click=lambda e: self.show_profile_selection())
        )
        self.page.update()

    # --- SIGN UP FORM ---
    def show_signup_page(self):
        self.page.controls.clear()

        username_field = ft.TextField(label="Username", width=280)
        email_field = ft.TextField(label="Email Address", width=280)
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=280)
        error_text = ft.Text("", color="red")

        def handle_signup(e):
            if not username_field.value or not email_field.value or not password_field.value:
                error_text.value = "❌ All fields are required!"
                self.page.update()
                return
            
            try:
                create_user(username_field.value, email_field.value, password_field.value)
                # Auto-login right after registering successfully
                user = verify_user(username_field.value, password_field.value)
                self.on_login_success(user)
            except Exception as ex:
                error_text.value = f"❌ Error: Username or Email might be taken!"
                self.page.update()

        self.page.add(
            ft.Icon(ft.icons.PERSON_ADD_ROUNDED, size=70, color="green"),
            ft.Text("Create Learning Profile", size=24, weight="bold"),
            ft.Container(height=15),
            username_field,
            email_field,
            password_field,
            error_text,
            ft.Container(height=15),
            ft.ElevatedButton("Create Profile", on_click=handle_signup, width=280, bgcolor="green", color="white"),
            ft.TextButton("Cancel", on_click=lambda e: self.show_profile_selection())
        )
        self.page.update()