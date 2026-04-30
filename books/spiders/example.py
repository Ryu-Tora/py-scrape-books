import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()

    def closed(self, reason):
        self.driver.quit()

    def parse(self, response):
        books = response.css("article.product_pod")

        for book in books:
            relative_url = book.css("h3 a::attr(href)").get()
            url = response.urljoin(relative_url)

            yield scrapy.Request(url, callback=self.parse_book)

        next_page = response.css(".next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_book(self, response):
        self.driver.get(response.url)

        title = self.driver.find_element(By.TAG_NAME, "h1").text
        price = self.driver.find_element(By.CLASS_NAME, "price_color").text

        stock = self.driver.find_element(By.CLASS_NAME, "availability").text

        description = ""
        try:
            description = self.driver.find_element(By.ID, "product_description").find_element(
                By.XPATH, "following-sibling::p"
            ).text
        except:
            pass

        category = self.driver.find_elements(By.CSS_SELECTOR, "ul.breadcrumb li a")[-1].text

        table = self.driver.find_elements(By.CSS_SELECTOR, "table.table-striped tr")

        data = {}
        for row in table:
            key = row.find_element(By.TAG_NAME, "th").text
            value = row.find_element(By.TAG_NAME, "td").text
            data[key] = value

        yield {
            "title": title,
            "price": float(price.replace("£", "")),
            "amount_in_stock": stock,
            "rating": response.css("p.star-rating::attr(class)").get().split()[-1],
            "category": category,
            "description": description,
            "upc": data.get("UPC"),
        }
