from newspaper import Article

url = "https://news.google.com/rss/articles/CBMioAFBVV95cUxOVUNKbHU3UTl6cElYd0VzUHNqd1N6T0FRNnphX19yVDNuMzZqRkZHS0hDal9Ba3BqbzQ3OE9HVFBtTUF6dzd5b2FWcEJUMlM4bDNUMHpydFNFMUhraWpBTTF1eVFQTW8xU1lfYy1KVDg4eFh3NmhKdWJ2SE1zbnFyT21uLVZZNTUyNzA0cGE2M19KVXo2RGctZTRSWER6S3ow?oc=5"

print(f"Testing URL: {url}")
article = Article(url)
article.download()
article.parse()
print(f"Title: {article.title}")
print(f"Text Length: {len(article.text)}")
print(f"Meta Description: {article.meta_description}")
print(f"Text Snippet: {article.text[:100]}")
