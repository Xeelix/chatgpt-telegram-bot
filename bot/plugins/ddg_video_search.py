import os
import random
from itertools import islice
from typing import Dict

from duckduckgo_search import DDGS

from .plugin import Plugin


class DDGVideoSearchPlugin(Plugin):
    """
    A plugin to search images and GIFs for a given query, using DuckDuckGo
    """

    def __init__(self):
        self.safesearch = os.getenv('DUCKDUCKGO_SAFESEARCH', 'moderate')

    def get_source_name(self) -> str:
        return "DuckDuckGo Videos"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "search_videos",
            "description": "Search video for a given query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The query to search for"},
                    "region": {
                        "type": "string",
                        "enum": ['xa-ar', 'xa-en', 'ar-es', 'au-en', 'at-de', 'be-fr', 'be-nl', 'br-pt', 'bg-bg',
                                 'ca-en', 'ca-fr', 'ct-ca', 'cl-es', 'cn-zh', 'co-es', 'hr-hr', 'cz-cs', 'dk-da',
                                 'ee-et', 'fi-fi', 'fr-fr', 'de-de', 'gr-el', 'hk-tzh', 'hu-hu', 'in-en', 'id-id',
                                 'id-en', 'ie-en', 'il-he', 'it-it', 'jp-jp', 'kr-kr', 'lv-lv', 'lt-lt', 'xl-es',
                                 'my-ms', 'my-en', 'mx-es', 'nl-nl', 'nz-en', 'no-no', 'pe-es', 'ph-en', 'ph-tl',
                                 'pl-pl', 'pt-pt', 'ro-ro', 'ru-ru', 'sg-en', 'sk-sk', 'sl-sl', 'za-en', 'es-es',
                                 'se-sv', 'ch-de', 'ch-fr', 'ch-it', 'tw-tzh', 'th-th', 'tr-tr', 'ua-uk', 'uk-en',
                                 'us-en', 'ue-es', 've-es', 'vn-vi', 'wt-wt'],
                        "description": "The region to use for the search. Infer this from the language used for the"
                                       "query. Default to `wt-wt` if not specified",
                    }
                },
                "required": ["query", "region"],
            },
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        with DDGS() as ddgs:
            image_type = kwargs.get('type', 'photo')
            ddgs_images_gen = ddgs.videos(
                kwargs['query'],
                region=kwargs.get('region', 'wt-wt'),
                safesearch='off'
            )
            results = list(islice(ddgs_images_gen, 2))
            if not results or len(results) == 0:
                return {"result": "No results found"}

            # Shuffle the results to avoid always returning the same image
            random.shuffle(results)

            def to_metadata(result: Dict) -> Dict[str, str]:
                return {
                    # "snippet": result["body"],
                    "description": result["description"],
                    "link": result["content"],
                }

            return {"result": [to_metadata(result) for result in results]}


if __name__ == "__main__":
    # plugin = DDGVideoSearchPlugin()
    # plugin.execute("search_videos", query="cat", type="photo", region="wt-wt")
    print(1)
