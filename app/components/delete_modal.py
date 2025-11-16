import reflex as rx
from app.states.article_state import ArticleState


def delete_modal() -> rx.Component:
    return rx.el.div(
        rx.cond(
            ArticleState.show_delete_modal,
            rx.el.div(
                rx.el.div(
                    class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40",
                    on_click=ArticleState.close_delete_modal,
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "triangle-alert", class_name="h-6 w-6 text-red-400"
                                ),
                                class_name="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-900/50",
                            ),
                            rx.el.div(
                                rx.el.h3(
                                    "Delete Article",
                                    class_name="text-lg font-semibold leading-6 text-white text-center",
                                ),
                                rx.el.div(
                                    rx.el.p(
                                        "Are you sure you want to delete this article? This action cannot be undone.",
                                        class_name="text-sm text-gray-400 text-center",
                                    ),
                                    class_name="mt-2",
                                ),
                                class_name="mt-3 text-center sm:mt-5",
                            ),
                        ),
                        rx.el.div(
                            rx.el.button(
                                "Cancel",
                                on_click=ArticleState.close_delete_modal,
                                disabled=ArticleState.is_deleting,
                                class_name="w-full justify-center rounded-md bg-gray-700 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 transition-colors disabled:opacity-50",
                            ),
                            rx.el.button(
                                rx.cond(
                                    ArticleState.is_deleting,
                                    rx.el.div(
                                        rx.icon(
                                            "loader-circle",
                                            class_name="animate-spin h-5 w-5 mr-2",
                                        ),
                                        "Deleting...",
                                    ),
                                    "Delete",
                                ),
                                on_click=ArticleState.confirm_delete,
                                disabled=ArticleState.is_deleting,
                                class_name="w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed",
                            ),
                            class_name="mt-5 sm:mt-6 grid grid-cols-2 gap-3",
                        ),
                        class_name="p-6",
                    ),
                    class_name="relative transform overflow-hidden rounded-lg bg-[#161625] border border-purple-900/30 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center p-4",
            ),
        ),
        class_name="relative z-50",
    )