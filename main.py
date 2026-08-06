from nicegui import app as nicegui_app
from nicegui import ui
from app.api.main import create_api
from app.web import pages  

nicegui_app.mount("/api", create_api())


def main() -> None:
    ui.run(title="Bookmarks", port=8080, reload=False, show=False)


if __name__ in ("__main__", "__mp_main__"):
    main()
