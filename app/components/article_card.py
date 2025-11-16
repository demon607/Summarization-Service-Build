import reflex as rx
from app.models import Article
import reflex as rx
from app.models import Article
from app.states.article_state import ArticleState


def status_badge(status: str) -> rx.Component:
    return rx.el.div(
        status.capitalize(),
        class_name=rx.match(
            status,
            (
                "pending",
                "w-fit px-3 py-1 text-xs font-semibold rounded-full border bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
            ),
            (
                "processing",
                "w-fit px-3 py-1 text-xs font-semibold rounded-full border bg-blue-400/10 text-blue-400 border-blue-400/20",
            ),
            (
                "completed",
                "w-fit px-3 py-1 text-xs font-semibold rounded-full border bg-green-400/10 text-green-400 border-green-400/20",
            ),
            (
                "failed",
                "w-fit px-3 py-1 text-xs font-semibold rounded-full border bg-red-400/10 text-red-400 border-red-400/20",
            ),
            "w-fit px-3 py-1 text-xs font-semibold rounded-full border bg-gray-400/10 text-gray-400 border-gray-400/20",
        ),
    )


def card_actions(article: Article) -> rx.Component:
    return rx.el.div(
        rx.cond(
            article["status"] == "failed",
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                on_click=lambda: ArticleState.retry_article(article["id"]),
                class_name="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-md transition-colors",
                disabled=ArticleState.article_retrying_id == article["id"],
            ),
            None,
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-4 w-4"),
            on_click=lambda: ArticleState.open_delete_modal(article),
            class_name="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-colors",
        ),
        class_name="flex items-center gap-2",
    )


def article_card_grid(article: Article, **props) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            status_badge(article["status"]),
            card_actions(article),
            class_name="flex justify-between items-center mb-4",
        ),
        rx.el.a(
            rx.el.h3(
                article["title"],
                class_name="text-lg font-bold text-gray-100 mb-2 truncate group-hover:text-purple-400 transition-colors",
            ),
            rx.el.p(article["url"], class_name="text-sm text-purple-400 truncate"),
            href=f"/article/{article['id']}",
            class_name="block",
        ),
        class_name="p-6 bg-[#1a1a2e]/50 border border-purple-900/30 rounded-xl shadow-lg hover:shadow-purple-500/10 hover:-translate-y-1 transition-all duration-300 ease-in-out group",
        **props,
    )


def article_card_list(article: Article, **props) -> rx.Component:
    return rx.el.div(
        rx.el.a(
            rx.el.div(
                rx.el.h3(
                    article["title"],
                    class_name="text-md font-bold text-gray-100 truncate group-hover:text-purple-400 transition-colors",
                ),
                rx.el.p(article["url"], class_name="text-sm text-purple-400 truncate"),
                class_name="flex-1 block truncate mr-4",
            ),
            href=f"/article/{article['id']}",
        ),
        status_badge(article["status"]),
        rx.el.p(
            rx.el.time(
                article["created_at"].to_string(),
                datetime=article["created_at"].to_string(),
                class_name="text-gray-400 text-xs font-mono",
            ),
            class_name="text-gray-400 text-xs w-36 text-right shrink-0",
        ),
        card_actions(article),
        class_name="flex items-center w-full gap-4 p-4 bg-[#1a1a2e]/50 border border-purple-900/30 rounded-xl shadow-sm hover:bg-gray-800/50 hover:border-purple-700/50 transition-all duration-300 ease-in-out group",
        **props,
    )


def article_card(article: Article, **props) -> rx.Component:
    return rx.cond(
        ArticleState.view_mode == "grid",
        article_card_grid(article, **props),
        article_card_list(article, **props),
    )