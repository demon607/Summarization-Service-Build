import reflex as rx
from app.states.article_state import ArticleState


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="mx-auto h-16 w-16 text-gray-600"),
        rx.el.h3(
            "No Articles Found", class_name="mt-4 text-lg font-semibold text-gray-200"
        ),
        rx.cond(
            (ArticleState.search_query != "") | (ArticleState.status_filter != "all"),
            rx.el.p(
                "Try adjusting your search or filters to find what you're looking for.",
                class_name="mt-2 text-sm text-gray-400",
            ),
            rx.el.p(
                "Add a URL to get started and see your articles here.",
                class_name="mt-2 text-sm text-gray-400",
            ),
        ),
        class_name="flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-gray-700 rounded-2xl bg-[#1a1a2e]/40",
    )