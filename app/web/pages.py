
from nicegui import ui


@ui.page("/")
def index() -> None:
    with ui.column().classes("w-full max-w-2xl mx-auto p-8 gap-4"):
        ui.label("Bookmarks").classes("text-3xl font-bold")
        ui.label("A personal bookmarks manager.").classes("text-gray-600")

        with ui.row().classes("gap-2"):
            ui.button("API docs", on_click=lambda: ui.navigate.to("/api/docs", new_tab=True))
            ui.button("Health", on_click=lambda: ui.navigate.to("/api/health", new_tab=True))
