from requests import get
from bs4 import BeautifulSoup
import csv
from os import path
from os import getcwd


def getPrice(prices, headers, url, i):
    url = url.strip()
    page = get(url, headers=headers)

    soup = BeautifulSoup(page.content, 'html.parser')

    jimms = 'https://www.jimms.'
    jimms_dict = {
        "id": "productinfo",
        "itemprop": "name",
        "itemprop1": "price",
        "class1": "filteritem selectitem activechild"
    }

    multitronic = 'https://www.multitronic.'
    multitronic_dict = {
        "id": "product_wrapper",
        "class": "header_box_trans",
        "id1": "vat",
        "class1": "level1 active"
    }

    gigantti = 'https://www.gigantti.'
    p = '0'
    n = 'N/A'
    price = ''
    price_valid_until = '-'
    category = ''
    name = ''

    if url[:len(jimms)] == 'https://www.jimms.':
        name, p, selected = getAttrs(soup, jimms_dict)
        price = int(p.get_text()[:-3])
        category = selected.find(attrs={"class": "treefilter-item"}).get_text()

    elif url[:len(multitronic)] == 'https://www.multitronic.':
        name, p, s = getAttrs(soup, multitronic_dict)
        price = int(p.get_text()[:-5])
        selected = s.find(attrs={"class": "active"})
        category = selected.find('a', class_="nLink").get_text()

    elif url[:len(gigantti)] == 'https://www.gigantti.':
        n = soup.find(attrs={"class": "product-detail-page"})
        na = n.find("meta", itemprop="name")
        name = na["content"]
        p = n.find("meta", itemprop="price")
        price = int(p["content"])
        valid_date = n.find("meta", itemprop="priceValidUntil")
        price_valid_until = valid_date["content"]
        category = '-'

    discount = 0
    if p and n:
        if i > len(prices):
            prices.append(price)
            print('New item added! Check the new price-list')

        if (prices[i] - price) > 10:
            discount = prices[i] - price
        elif (prices[i] - price) != 0:
            print('The price of ' + name + ' is higher than before! :( '
                    'old: ' + str(prices[i]) + ' new: ' + str(price))
            prices[i] = price
    return name, price, discount, category, price_valid_until


def getAttrs(soup, contents):
    keys = list(contents.keys())
    base = soup.find(attrs={keys[0]: contents[keys[0]]})
    if base:
        name_help = base.find(attrs={keys[1]: contents[keys[1]]})
        if (keys[1] == "meta"):
            name = name_help["content"]
        else:
            name = name_help.get_text()
        price_help = base.find(attrs={keys[2][:-1]: contents[keys[2]]})
        category = soup.find(attrs={keys[3][:-1]: contents[keys[3]]})
    else:
        name = "not found"
        price_help = "0.0000000"
        category = "not found"
    return name, price_help, category
    


def getUrls():
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/80.0.3987.162 Safari/537.36'}
    urls = open("urls.csv", "r")
    items = {'title': 'price'}
    discounts = {'title': 'discount'}
    categories = {'title': 'category'}
    names = ['title']
    dates = {'title': 'valid until'}
    cats = {'types': 'price'}
    i = 0
    sum_of_prices = 0
    discount_sum = 0
    url_list = []
    prices = []

    for row in urls:
        url, price = row.split(',')
        url_list.append(url)
        prices.append(int(price.strip()))

    for row in url_list:
        name, price, discount, category, date = getPrice(prices, headers, row, i)
        items[name] = price
        discounts[name] = discount
        categories[name] = category
        dates[name] = date
        if category not in cats:
            if category != '-':
                sum_of_prices += price
            cats[category] = price
        else:
            if price < cats[category] and category != '-':
                sum_of_prices -= cats[category]
                sum_of_prices += price
                cats[category] = price
        discount_sum += discount

        if discount != 0:
            print(name + ' has a discount of {0}€!!!'.format(discount))
        names.append(name)
        i += 1

    total = 'Lowest total'
    names.append(total)
    sum_of_prices = sum_of_prices
    items[total] = sum_of_prices
    if discount_sum == 0:
        print('No discounts this time...')
    discounts[total] = discount_sum
    categories[total] = '.'
    urls.close()
    makeCsv(items, names, discounts, categories, dates, 'result.csv')
    return


def makeCsv(items, fieldnames, discounts, categories, dates, file_name):
    file_path = path.join(getcwd(), file_name)

    csv_file = open(file=file_path, mode="w+", encoding="utf-8", newline='')
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerow(categories)
    writer.writerow(items)
    writer.writerow(discounts)
    writer.writerow(dates)

    csv_file.close()


def main():
    getUrls()
    print('Success!')


main()
