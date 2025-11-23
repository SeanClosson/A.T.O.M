import wikipediaapi

class WikipediaSearcher:
    def __init__(self, language='en', user_agent='my-custom-ai-agent/1.0'):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=user_agent,
            language=language
        )

    def search_summary(self, query, max_chars=500):
        page = self.wiki.page(query)

        if page.exists():
            summary = page.summary
            return summary[:max_chars] + "..." if len(summary) > max_chars else summary
        else:
            return f"Sorry, no page found for '{query}'."

    def search_full_page(self, query):
        page = self.wiki.page(query)
        return page.text if page.exists() else f"Sorry, no page found for '{query}'."
