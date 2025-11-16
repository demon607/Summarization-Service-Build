import reflex as rx
from app.states.article_state import ArticleState
from app.components.article_card import status_badge


def detail_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="h-8 w-1/4 bg-gray-700 rounded-md animate-pulse"),
        rx.el.div(class_name="h-4 w-1/2 bg-gray-700 rounded-md animate-pulse mt-4"),
        rx.el.div(class_name="h-4 w-1/3 bg-gray-700 rounded-md animate-pulse mt-2"),
        rx.el.div(
            rx.el.div(class_name="h-6 w-32 bg-gray-700 rounded-md animate-pulse"),
            rx.el.div(
                class_name="h-24 w-full bg-gray-800 rounded-lg animate-pulse mt-4"
            ),
            class_name="mt-8",
        ),
        rx.el.div(
            rx.el.div(class_name="h-6 w-48 bg-gray-700 rounded-md animate-pulse"),
            rx.el.div(
                class_name="h-64 w-full bg-gray-800 rounded-lg animate-pulse mt-4"
            ),
            class_name="mt-8",
        ),
        class_name="w-full max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8",
    )


def summary_section(article: rx.Var[dict]) -> rx.Component:
    return rx.el.div(
        rx.el.h2("Summary", class_name="text-2xl font-bold text-white mb-4"),
        rx.cond(
            (article["status"] == "completed") & (article["summary"] != None),
            rx.el.div(
                rx.el.p(article["summary"], class_name="text-gray-300 leading-relaxed"),
                rx.el.button(
                    rx.icon("copy", class_name="h-4 w-4 mr-2"),
                    "Copy Summary",
                    on_click=rx.set_clipboard(article["summary"]),
                    class_name="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 focus:ring-offset-gray-900 transition-all",
                ),
                class_name="p-6 bg-gray-800/50 rounded-lg border border-purple-900/30",
            ),
            rx.cond(
                article["status"] == "failed",
                rx.el.div(
                    rx.icon(
                        "flag_triangle_right", class_name="h-5 w-5 mr-3 text-red-400"
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Summarization Failed",
                            class_name="font-semibold text-red-300",
                        ),
                        rx.el.p(
                            article["error_message"],
                            class_name="text-sm text-red-400 mt-1",
                        ),
                    ),
                    class_name="flex items-center p-4 bg-red-900/20 rounded-lg border border-red-500/30",
                ),
                rx.el.div(
                    rx.icon(
                        "loader-circle",
                        class_name="h-5 w-5 mr-3 animate-spin text-blue-400",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Processing...", class_name="font-semibold text-blue-300"
                        ),
                        rx.el.p(
                            "The article is being summarized. This may take a moment.",
                            class_name="text-sm text-blue-400 mt-1",
                        ),
                    ),
                    class_name="flex items-center p-4 bg-blue-900/20 rounded-lg border border-blue-500/30",
                ),
            ),
        ),
        class_name="mt-8",
    )


def article_content_section(article: rx.Var[dict]) -> rx.Component:
    return rx.el.div(
        rx.el.h2("Full Content", class_name="text-2xl font-bold text-white mb-4"),
        rx.el.div(
            rx.el.p(
                article["content"],
                class_name="text-gray-400 whitespace-pre-wrap leading-relaxed",
            ),
            class_name="p-6 bg-gray-800/50 rounded-lg max-h-96 overflow-y-auto border border-purple-900/30",
        ),
        class_name="mt-8",
    )


def article_detail_view() -> rx.Component:
    return rx.cond(
        ArticleState.is_loading_article,
        detail_skeleton(),
        rx.cond(
            ArticleState.current_article,
            rx.el.div(
                rx.el.a(
                    rx.icon("arrow-left", class_name="h-4 w-4 mr-2"),
                    "Back to Articles",
                    href="/",
                    class_name="inline-flex items-center text-purple-400 hover:text-purple-300 font-semibold mb-8 transition-colors",
                ),
                rx.el.div(
                    rx.el.div(status_badge(ArticleState.current_article["status"])),
                    rx.el.h1(
                        ArticleState.current_article["title"],
                        class_name="text-3xl md:text-4xl font-extrabold text-white mt-4",
                    ),
                    rx.el.a(
                        ArticleState.current_article["url"],
                        href=ArticleState.current_article["url"],
                        target="_blank",
                        class_name="text-purple-400 hover:underline break-all mt-2 block",
                    ),
                ),
                summary_section(ArticleState.current_article),
                article_content_section(ArticleState.current_article),
            ),
            rx.el.div("Article not found.", class_name="text-center text-gray-400"),
        ),
    )


def article_detail_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            article_detail_view(),
            class_name="min-h-screen w-full max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8",
        ),
        class_name="font-['Inter'] bg-[#1a1a2e] text-white",
    )