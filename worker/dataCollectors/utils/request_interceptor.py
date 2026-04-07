from abc import abstractmethod
from playwright.async_api import async_playwright


class ReqeustInterceptor:
    def __init__(self):
        self.base_url = ''
        self.collected_data = []

    async def fetch_xhr_data(self):

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Set up response handler
            page.on("response", self._handle_response)

            # Navigate and wait for network to be idle
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            # Close browser
            await browser.close()

        # Format the collected data
        return await self.format_data(self.collected_data)

    async def _handle_response(self, response):

        if response.request.resource_type == "xhr":
            try:
                response_url = response.url

                if response.ok:

                    try:
                        data = await response.json()
                    except:
                        data = await response.text()

                    self.collected_data.append({
                        "url": response_url,
                        "data": data
                    })
            except Exception as e:
                print(f"Error processing response: {e}")

    @abstractmethod
    async def format_data(self, raw_data):
        pass
