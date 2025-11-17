import reflex as rx
from app.models import Article
import datetime
import requests
from bs4 import BeautifulSoup
import logging
from sqlalchemy import text, select, update, bindparam, func
from app.utils.summarizer import summarize_text_lsa
from app.utils.text_cleaner import clean_text
from app.utils.rate_limiter import is_rate_limited
from app.utils.url_validator import is_safe_url
import asyncio
import re


class ArticleState(rx.State):
    articles: list[Article] = []
    error_message: str = ""
    is_loading: bool = True
    is_submitting: bool = False
    is_processing_queue: bool = False
    current_article: Article | None = None
    is_loading_article: bool = False
    search_query: str = ""
    status_filter: str = "all"
    sort_by: str = "date_desc"
    view_mode: str = "grid"
    show_delete_modal: bool = False
    article_to_delete: Article | None = None
    is_deleting: bool = False
    article_retrying_id: int | None = None

    @rx.var
    def filtered_and_sorted_articles(self) -> list[Article]:
        articles = self.articles
        if self.status_filter != "all":
            articles = [art for art in articles if art["status"] == self.status_filter]
        if self.search_query:
            query = self.search_query.lower()
            articles = [
                art
                for art in articles
                if query in art["title"].lower() or query in art["url"].lower()
            ]
        if self.sort_by == "date_asc":
            articles.sort(key=lambda art: art["created_at"])
        elif self.sort_by == "status":
            articles.sort(key=lambda art: art["status"])
        else:
            articles.sort(key=lambda art: art["created_at"], reverse=True)
        return articles

    @rx.event
    def on_load(self) -> rx.event.EventSpec:
        self.is_loading = True
        with rx.session() as session:
            session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS article (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                );
                """)
            )
            session.commit()
        return [ArticleState.load_articles, ArticleState.poll_for_updates]

    @rx.event
    def load_articles(self):
        try:
            with rx.session() as session:
                result = session.execute(
                    text("SELECT * FROM article ORDER BY created_at DESC")
                ).all()
                self.articles = [
                    Article(
                        id=row[0],
                        url=row[1],
                        title=row[2],
                        status=row[3],
                        content=row[4],
                        summary=row[5],
                        created_at=row[6],
                        error_message=row[7],
                    )
                    for row in result
                ]
        finally:
            self.is_loading = False

    @rx.event
    def add_article(self, form_data: dict):
        self.error_message = ""
        self.is_submitting = True
        yield
        url = form_data.get("url", "").strip()
        if not url:
            self.error_message = "URL is required."
            self.is_submitting = False
            yield rx.toast.error("Please enter a URL.")
            return
        if len(url) > 2048:
            self.error_message = "URL is too long (max 2048 characters)."
            self.is_submitting = False
            yield rx.toast.error(self.error_message)
            return
        client_ip = self.router.session.client_ip
        if is_rate_limited(client_ip):
            self.error_message = "Rate limit exceeded. Please try again in an hour."
            self.is_submitting = False
            yield rx.toast.error(self.error_message)
            return
        validation_error = is_safe_url(url)
        if validation_error:
            self.error_message = validation_error
            self.is_submitting = False
            yield rx.toast.error(validation_error)
            return
        try:
            headers = {
                "User-Agent": "Read-it-Later-Summarizer/1.0",
                "Accept": "text/html, text/plain",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            }
            with requests.get(
                url, headers=headers, timeout=15, stream=True, allow_redirects=False
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if not any((ct in content_type for ct in ["text/html", "text/plain"])):
                    self.error_message = "Unsupported content type. Only HTML and plain text are supported."
                    yield rx.toast.error(self.error_message)
                    self.is_submitting = False
                    return
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > 5 * 1024 * 1024:
                    self.error_message = "Content is too large (max 5MB)."
                    yield rx.toast.error(self.error_message)
                    self.is_submitting = False
                    return
                content_chunks = []
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    total_size += len(chunk)
                    if total_size > 5 * 1024 * 1024:
                        self.error_message = "Content is too large (max 5MB)."
                        yield rx.toast.error(self.error_message)
                        self.is_submitting = False
                        return
                    content_chunks.append(chunk)
                full_content = b"".join(content_chunks)
            soup = BeautifulSoup(full_content, "html.parser")
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"]
            else:
                title = soup.title.string if soup.title else ""
            content = clean_text(soup.get_text(separator=" ", strip=True))
            if len(content) < 100:
                self.error_message = "Content could not be properly extracted or is too short after cleaning."
                yield rx.toast.error(self.error_message)
                self.is_submitting = False
                return
            non_alphanumeric_count = len(re.findall("[^A-Za-z0-9\\s]", content))
            if non_alphanumeric_count / len(content) > 0.5:
                self.error_message = "The extracted content appears to be mostly special characters or is garbled."
                yield rx.toast.error(self.error_message)
                self.is_submitting = False
                return
            title = clean_text(title)
            if not title:
                title = " ".join(content.split()[:10])
            title = title[:100]
            with rx.session() as session:
                new_article = text(
                    "INSERT INTO article (url, title, status, content, created_at) VALUES (:url, :title, :status, :content, :created_at) RETURNING id"
                )
                result = session.execute(
                    new_article,
                    params={
                        "url": url,
                        "title": title,
                        "status": "pending",
                        "content": content,
                        "created_at": datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                    },
                ).scalar_one()
                session.commit()
            yield ArticleState.load_articles()
            yield ArticleState.process_article_queue()
            yield rx.toast.success(f"Article '{title[:30]}...' added successfully!")
        except requests.exceptions.Timeout as e:
            logging.exception(f"Timeout while fetching URL: {url}: {e}")
            self.error_message = (
                "The request timed out. The website might be slow or offline."
            )
            yield rx.toast.error(self.error_message)
        except requests.exceptions.HTTPError as e:
            logging.exception(f"HTTP error for URL {url}: {e}")
            status_code = e.response.status_code if e.response else "Unknown"
            if status_code == 403:
                self.error_message = "Access to the article was denied by the server."
            elif status_code == 404:
                self.error_message = "The requested article could not be found."
            else:
                self.error_message = (
                    "Failed to fetch the article due to a server error."
                )
            yield rx.toast.error(self.error_message)
        except requests.exceptions.RequestException as e:
            logging.exception(f"Error fetching URL {url}: {e}")
            self.error_message = f"Failed to fetch the article. Please check the URL and your connection."
            yield rx.toast.error(self.error_message)
        except Exception as e:
            logging.exception(f"An unexpected error occurred while adding article: {e}")
            self.error_message = "An unexpected error occurred. Please try again later."
            yield rx.toast.error(self.error_message)
        finally:
            self.is_submitting = False

    @rx.event(background=True)
    async def process_article_queue(self):
        async with self:
            if self.is_processing_queue:
                return
            self.is_processing_queue = True
        try:
            while True:
                article_to_process = None
                with rx.session() as session:
                    result = session.execute(
                        text(
                            "SELECT * FROM article WHERE status = 'pending' ORDER BY created_at LIMIT 1"
                        )
                    ).first()
                    if result:
                        article_to_process = Article(
                            id=result[0],
                            url=result[1],
                            title=result[2],
                            status=result[3],
                            content=result[4],
                            summary=result[5],
                            created_at=result[6],
                            error_message=result[7],
                        )
                        session.execute(
                            text(
                                "UPDATE article SET status = 'processing' WHERE id = :id"
                            ),
                            params={"id": article_to_process["id"]},
                        )
                        session.commit()
                async with self:
                    if article_to_process:
                        for i, art in enumerate(self.articles):
                            if art["id"] == article_to_process["id"]:
                                self.articles[i]["status"] = "processing"
                                break
                    else:
                        break
                yield
                if not article_to_process:
                    break
                try:
                    summary = summarize_text_lsa(article_to_process["content"])
                    if not summary:
                        raise ValueError("Summarization returned empty result.")
                    with rx.session() as session:
                        session.execute(
                            text(
                                "UPDATE article SET status = 'completed', summary = :summary WHERE id = :id"
                            ),
                            params={"id": article_to_process["id"], "summary": summary},
                        )
                        session.commit()
                    async with self:
                        for i, art in enumerate(self.articles):
                            if art["id"] == article_to_process["id"]:
                                self.articles[i]["status"] = "completed"
                                self.articles[i]["summary"] = summary
                                break
                except Exception as e:
                    logging.exception(
                        f"Failed to summarize article {article_to_process['id']}: {e}"
                    )
                    error_msg = f"Summarization failed: {str(e)[:100]}"
                    with rx.session() as session:
                        session.execute(
                            text(
                                "UPDATE article SET status = 'failed', error_message = :error_message WHERE id = :id"
                            ),
                            params={
                                "id": article_to_process["id"],
                                "error_message": error_msg,
                            },
                        )
                        session.commit()
                    async with self:
                        for i, art in enumerate(self.articles):
                            if art["id"] == article_to_process["id"]:
                                self.articles[i]["status"] = "failed"
                                self.articles[i]["error_message"] = error_msg
                                break
                yield
        finally:
            async with self:
                self.is_processing_queue = False

    @rx.event
    def load_article_detail(self):
        article_id_str = self.router.page.params.get("article_id")
        if not article_id_str:
            self.is_loading_article = False
            return rx.redirect("/")
        try:
            article_id = int(article_id_str)
        except (ValueError, TypeError) as e:
            logging.exception(f"Invalid article_id: {article_id_str}. Error: {e}")
            self.is_loading_article = False
            return rx.redirect("/404")
        self.is_loading_article = True
        try:
            with rx.session() as session:
                result = session.execute(
                    text("SELECT * FROM article WHERE id = :id"),
                    params={"id": article_id},
                ).first()
                if result:
                    self.current_article = Article(
                        id=result[0],
                        url=result[1],
                        title=result[2],
                        status=result[3],
                        content=result[4],
                        summary=result[5],
                        created_at=result[6],
                        error_message=result[7],
                    )
                else:
                    self.current_article = None
                    return rx.redirect("/404")
        finally:
            self.is_loading_article = False

    @rx.event
    def set_search_query(self, query: str):
        self.search_query = query

    @rx.event
    def set_status_filter(self, status: str):
        self.status_filter = status

    @rx.event
    def set_sort_by(self, sort_option: str):
        self.sort_by = sort_option

    @rx.event
    def toggle_view_mode(self):
        self.view_mode = "list" if self.view_mode == "grid" else "grid"

    @rx.event
    def open_delete_modal(self, article: Article):
        self.show_delete_modal = True
        self.article_to_delete = article

    @rx.event
    def close_delete_modal(self):
        self.show_delete_modal = False
        self.article_to_delete = None
        self.is_deleting = False

    @rx.event
    def confirm_delete(self):
        self.is_deleting = True
        yield
        if self.article_to_delete is None:
            self.is_deleting = False
            yield rx.toast.error("No article selected for deletion.")
            return
        try:
            article_id = self.article_to_delete["id"]
            with rx.session() as session:
                session.execute(
                    text("DELETE FROM article WHERE id = :id"),
                    params={"id": article_id},
                )
                session.commit()
            self.articles = [art for art in self.articles if art["id"] != article_id]
            yield rx.toast.success("Article deleted successfully.")
        except Exception as e:
            logging.exception(f"Error deleting article: {e}")
            yield rx.toast.error("Failed to delete article.")
        finally:
            yield ArticleState.close_delete_modal

    @rx.event
    def retry_article(self, article_id: int):
        self.article_retrying_id = article_id
        yield
        try:
            with rx.session() as session:
                session.execute(
                    text(
                        "UPDATE article SET status = 'pending', error_message = NULL WHERE id = :id"
                    ),
                    params={"id": article_id},
                )
                session.commit()
            for i, art in enumerate(self.articles):
                if art["id"] == article_id:
                    self.articles[i]["status"] = "pending"
                    self.articles[i]["error_message"] = None
                    break
            yield rx.toast.info("Retrying article summarization...")
            yield ArticleState.process_article_queue
        except Exception as e:
            logging.exception(f"Error retrying article: {e}")
            yield rx.toast.error("Failed to retry article.")
        finally:
            self.article_retrying_id = None

    @rx.event(background=True)
    async def poll_for_updates(self):
        while True:
            await asyncio.sleep(5)
            processing_ids = []
            async with self:
                if self.is_loading:
                    continue
                processing_ids = [
                    art["id"]
                    for art in self.articles
                    if art["status"] in ["processing", "pending"]
                ]
            if not processing_ids:
                continue
            updated_articles_map = {}
            needs_ui_update = False
            with rx.session() as session:
                placeholders = ",".join(["?" for _ in processing_ids])
                query = text(f"SELECT * FROM article WHERE id IN ({placeholders})")
                result = session.execute(query, processing_ids).all()
                for row in result:
                    updated_articles_map[row[0]] = Article(
                        id=row[0],
                        url=row[1],
                        title=row[2],
                        status=row[3],
                        content=row[4],
                        summary=row[5],
                        created_at=row[6],
                        error_message=row[7],
                    )
            async with self:
                for i, art in enumerate(self.articles):
                    if art["id"] in updated_articles_map:
                        updated_art = updated_articles_map[art["id"]]
                        if art["status"] != updated_art["status"]:
                            self.articles[i] = updated_art
                            needs_ui_update = True
                if (
                    self.current_article
                    and self.current_article["id"] in updated_articles_map
                ):
                    updated_art = updated_articles_map[self.current_article["id"]]
                    if self.current_article["status"] != updated_art["status"]:
                        self.current_article = updated_art
                        needs_ui_update = True
            if needs_ui_update:
                yield