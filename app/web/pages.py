from nicegui import ui


@ui.page("/")
def index() -> None:
    with ui.column().classes("w-full max-w-2xl mx-auto p-8 gap-4"):
        ui.label("Bookmarks").classes("text-3xl font-bold")
        ui.label("A personal bookmarks manager.").classes("text-gray-600")

        with ui.row().classes("gap-2 mt-4"):
            ui.button(
                "Swagger UI",
                on_click=lambda: ui.navigate.to("/api/docs", new_tab=True),
            )
            ui.button(
                "ReDoc",
                on_click=lambda: ui.navigate.to("/api/redoc", new_tab=True),
            ).props("outline")
            ui.button(
                "OpenAPI spec",
                on_click=lambda: ui.navigate.to("/api/openapi.json", new_tab=True),
            ).props("outline")
