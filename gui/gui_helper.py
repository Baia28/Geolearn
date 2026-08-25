import flet as ft

def create_review_badge(target: dict) -> ft.Control | None:
    if target and target.get("is_review_item"):
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.AUTORENEW, color=ft.Colors.ORANGE_700, size=16),  # Changed AUTO_RENEW -> AUTORENEW
                ft.Text("Review Item", color=ft.Colors.ORANGE_700, weight=ft.FontWeight.BOLD, size=13)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
        )
    return None