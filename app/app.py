import reflex as rx
from app.states.article_state import ArticleState
from app.components.article_card import article_card
from app.components.empty_state import empty_state
from app.components.delete_modal import delete_modal


def url_submission_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.input(
                placeholder="Enter article URL...",
                name="url",
                type="url",
                required=True,
                class_name="flex-grow bg-gray-800/50 text-white placeholder-gray-500 px-4 py-3 rounded-l-lg border-2 border-transparent focus:border-purple-500 focus:ring-0 transition-colors duration-300 w-full",
            ),
            rx.el.button(
                rx.cond(
                    ArticleState.is_submitting,
                    rx.el.div(
                        rx.icon("loader-circle", class_name="h-5 w-5 animate-spin"),
                        "Adding...",
                    ),
                    rx.el.div(rx.icon("plus", class_name="h-5 w-5"), "Add Article"),
                ),
                type="submit",
                disabled=ArticleState.is_submitting,
                class_name="flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-3 rounded-r-lg transition-all duration-300 ease-in-out whitespace-nowrap w-[150px] disabled:bg-purple-800 disabled:cursor-not-allowed",
            ),
            class_name="flex w-full max-w-2xl mx-auto shadow-lg rounded-lg",
        ),
        rx.cond(
            ArticleState.error_message != "",
            rx.el.div(
                rx.icon("flag_triangle_right", class_name="h-5 w-5 mr-2"),
                ArticleState.error_message,
                class_name="flex items-center mt-4 text-sm text-red-400 bg-red-400/10 p-3 rounded-lg w-full max-w-2xl mx-auto",
            ),
            None,
        ),
        on_submit=ArticleState.add_article,
        reset_on_submit=True,
        class_name="w-full mb-12",
    )


def filter_controls() -> rx.Component:
    status_filters = ["all", "pending", "processing", "completed", "failed"]
    return rx.el.div(
        rx.el.div(
            rx.foreach(
                status_filters,
                lambda status: rx.el.button(
                    status.capitalize(),
                    on_click=lambda: ArticleState.set_status_filter(status),
                    class_name=rx.cond(
                        ArticleState.status_filter == status,
                        "px-4 py-2 text-sm font-semibold rounded-full bg-purple-600 text-white transition-all",
                        "px-4 py-2 text-sm font-semibold rounded-full bg-gray-800 text-gray-300 hover:bg-gray-700 transition-all",
                    ),
                ),
            ),
            class_name="flex items-center gap-2 flex-wrap",
        ),
        class_name="mb-6",
    )


def search_and_sort_controls() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search", class_name="h-5 w-5 text-gray-400"),
            rx.el.input(
                placeholder="Search articles...",
                on_change=ArticleState.set_search_query,
                debounce_timeout=300,
                class_name="w-full bg-transparent text-white placeholder-gray-500 focus:ring-0 border-none pl-2",
                default_value=ArticleState.search_query,
            ),
            rx.cond(
                ArticleState.search_query != "",
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    on_click=lambda: ArticleState.set_search_query(""),
                    class_name="text-gray-500 hover:text-white",
                ),
                None,
            ),
            class_name="flex items-center bg-gray-800/50 rounded-lg px-4 py-2.5 w-full max-w-sm",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Sort by Date (Newest)", value="date_desc"),
                rx.el.option("Sort by Date (Oldest)", value="date_asc"),
                rx.el.option("Sort by Status", value="status"),
                on_change=ArticleState.set_sort_by,
                value=ArticleState.sort_by,
                class_name="bg-gray-800/50 text-white rounded-lg pl-3 pr-8 py-2.5 border-transparent focus:border-purple-500 focus:ring-purple-500 text-sm",
                custom_attrs={"aria-label": "Sort articles"},
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("layout-grid", class_name="h-5 w-5"),
                    on_click=ArticleState.toggle_view_mode,
                    class_name=rx.cond(
                        ArticleState.view_mode == "grid",
                        "p-2.5 rounded-lg bg-purple-600 text-white",
                        "p-2.5 rounded-lg bg-gray-800/50 text-gray-400 hover:bg-gray-700",
                    ),
                ),
                rx.el.button(
                    rx.icon("list", class_name="h-5 w-5"),
                    on_click=ArticleState.toggle_view_mode,
                    class_name=rx.cond(
                        ArticleState.view_mode == "list",
                        "p-2.5 rounded-lg bg-purple-600 text-white",
                        "p-2.5 rounded-lg bg-gray-800/50 text-gray-400 hover:bg-gray-700",
                    ),
                ),
                class_name="flex items-center gap-1 bg-gray-800/50 rounded-lg p-1",
            ),
            class_name="flex items-center gap-4",
        ),
        class_name="flex flex-col md:flex-row justify-between items-center gap-4 mb-8",
    )


def loading_skeleton() -> rx.Component:
    return rx.cond(
        ArticleState.view_mode == "grid",
        rx.el.div(
            rx.foreach(
                [1, 2, 3, 4, 5, 6],
                lambda i: rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            class_name="h-5 w-20 bg-gray-700/50 rounded-full animate-pulse"
                        ),
                        class_name="flex justify-between items-center mb-4",
                    ),
                    rx.el.div(
                        class_name="h-6 w-3/4 bg-gray-700/50 rounded-md animate-pulse mb-2"
                    ),
                    rx.el.div(
                        class_name="h-4 w-1/2 bg-gray-700/50 rounded-md animate-pulse"
                    ),
                    class_name="p-6 bg-gray-800/20 rounded-xl",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
        ),
        rx.el.div(
            rx.foreach(
                [1, 2, 3, 4, 5, 6],
                lambda i: rx.el.div(
                    rx.el.div(
                        class_name="h-6 flex-grow bg-gray-700/50 rounded-md animate-pulse"
                    ),
                    rx.el.div(
                        class_name="h-6 w-24 bg-gray-700/50 rounded-full animate-pulse"
                    ),
                    rx.el.div(
                        class_name="h-6 w-28 bg-gray-700/50 rounded-md animate-pulse"
                    ),
                    class_name="flex items-center gap-4 p-4 bg-gray-800/20 rounded-xl",
                ),
            ),
            class_name="flex flex-col gap-4",
        ),
    )


def article_list() -> rx.Component:
    return rx.cond(
        ArticleState.filtered_and_sorted_articles.length() > 0,
        rx.cond(
            ArticleState.view_mode == "grid",
            rx.el.div(
                rx.foreach(
                    ArticleState.filtered_and_sorted_articles,
                    lambda article: article_card(article, key=article["id"]),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
            ),
            rx.el.div(
                rx.foreach(
                    ArticleState.filtered_and_sorted_articles,
                    lambda article: article_card(article, key=article["id"]),
                ),
                class_name="flex flex-col gap-4",
            ),
        ),
        empty_state(),
    )


def index() -> rx.Component:
    return rx.el.main(
        delete_modal(),
        rx.el.div(
            rx.el.header(
                rx.el.div(
                    rx.el.h1(
                        "Read-it-Later",
                        class_name="text-4xl md:text-5xl font-extrabold text-white",
                    ),
                    rx.el.p(
                        "Your personal article summarizer.",
                        class_name="text-lg text-gray-400 mt-2",
                    ),
                    class_name="text-center relative pb-8",
                ),
                url_submission_form(),
                class_name="py-12 px-4 sm:px-6 lg:px-8",
            ),
            rx.el.div(
                search_and_sort_controls(),
                filter_controls(),
                rx.cond(ArticleState.is_loading, loading_skeleton(), article_list()),
                class_name="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8",
            ),
            class_name="min-h-screen w-full",
        ),
        class_name="font-['Inter'] bg-[#1a1a2e] text-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
            rel="stylesheet",
        ),
    ],
)
from app.pages.article_detail import article_detail_page

app.add_page(index, on_load=ArticleState.on_load, route="/")
app.add_page(
    article_detail_page,
    route="/article/[article_id]",
    on_load=ArticleState.load_article_detail,
)