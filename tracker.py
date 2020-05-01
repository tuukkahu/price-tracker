from requests import get
from bs4 import BeautifulSoup
import csv
from os import path
from os import getcwd
from tempfile import NamedTemporaryFile
import shutil


# Get the data that we want from an url
def getData(old_price, headers, url):
    url = url.strip()
    page = get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    jimms = 'https://www.jimms.'
    jimms_dict = {
        "id": "productinfo",
        "itemprop": "name",
        "itemprop1": "price",
        "class1": "filteritem selectitem activechild",
        "class2": "treefilter-item"
    }

    multitronic = 'https://www.multitronic.'
    multitronic_dict = {
        "id": "product_wrapper",
        "class": "header_box_trans",
        "id1": "vat",
        "class1": "level1 active",
        "class2": "active"
    }

    gigantti = 'https://www.gigantti.'
    p = '0'
    n = 'N/A'
    price = ''
    category = ''
    name = ''

    if url[:len(jimms)] == 'https://www.jimms.':
        name, price, category = getAttrs(soup, jimms_dict)
        if type(price) != str and type (category) != str:
            price = int(price.get_text()[:-3])
            category = category.get_text()
        else:
            print("An item can't be found. Check the csv-file!")

    elif url[:len(multitronic)] == 'https://www.multitronic.':
        name, price, category = getAttrs(soup, multitronic_dict)
        if type(price) != str and type (category) != str:
            price = int(price.get_text()[:-5])
            category = category.find('a', class_="nLink").get_text()
        else:
            print("An item can't be found. Check the csv-file!")

    elif url[:len(gigantti)] == 'https://www.gigantti.':
        n = soup.find(attrs={"class": "product-detail-page"})
        na = n.find("meta", itemprop="name")
        name = na["content"]
        p = n.find("meta", itemprop="price")
        price = int(p["content"])
        category = '-'

    discount = 0
    # check if the product has a discount
    if (old_price - price) > 0:
        discount = old_price - price
    elif (old_price - price) < 0:
        print('The price of ' + name + ' is higher than before! :( '
                    'old: ' + str(old_price) + ' new: ' + str(price))

    return name, price, discount, category


# get elements from the website to simplify the process
def getAttrs(soup, contents):
    keys = list(contents.keys())
    base = soup.find(attrs={keys[0]: contents[keys[0]]})
    if base:
        name_help = base.find(attrs={keys[1]: contents[keys[1]]})
        name = name_help.get_text()
        price_help = base.find(attrs={keys[2][:-1]: contents[keys[2]]})
        selected = soup.find(attrs={keys[3][:-1]: contents[keys[3]]})
        category = selected.find(attrs={keys[4][:-1]: contents[keys[4]]})
    else:
        name = "not found"
        price_help = 0.0000000
        category = "not found"
    return name, price_help, category
    


def scrapeUrls():
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/81.0.4044.122 Safari/537.36'}
    urls = open("urls.csv", "r")
    items = {'title': 'price'}
    discounts = {'title': 'discount'}
    categories = {'title': 'category'}
    names = ['title']
    # this dict contains the lowest price of each category
    category_lowest = {'types': 'price'}
    url_dict = {'title': 'url'}
    lowest_seen = {'title': 'lowest price seen'}
    sum_of_prices = 0
    discount_sum = 0
    new_lowest = []

    for row in urls:
        url, old_price, lowest_price = row.split(',')
        old_price = int(old_price.strip())
        lowest_price = int(lowest_price.strip())

        name, price, discount, category = getData(old_price, headers, row)
        items[name] = price
        discounts[name] = discount
        categories[name] = category
        url_dict[name] = url.strip()
        if category not in category_lowest:
            if category != '-':
                sum_of_prices += price
            category_lowest[category] = price
        else:
            if price < category_lowest[category] and category != '-':
                sum_of_prices -= category_lowest[category]
                sum_of_prices += price
                category_lowest[category] = price
        discount_sum += discount

        if discount != 0 and name != "not found":
            print(name + ' ({0}€) has a discount of {1}€! The lowest price seen is {2}€.'.format(price, discount, lowest_price))
        names.append(name)

        if price < lowest_price:
            new_lowest.append(price)
            lowest_seen[name] = price
        else:
            new_lowest.append(lowest_price)
            lowest_seen[name] = lowest_price
    urls.close()

    total = 'Lowest total'
    names.append(total)
    items[total] = sum_of_prices

    if discount_sum == 0:
        print('No discounts this time...')
    discounts[total] = discount_sum
    categories[total] = ' '
    lowest_seen[total] = sum_of_prices
    url_dict[total] = ' '
    makeCsv(items, names, discounts, categories, url_dict, lowest_seen, 'result.csv')

    tempfile = NamedTemporaryFile(mode='w', delete=False, newline='')
    with open("urls.csv", 'r') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter=',', quotechar='"')
        writer = csv.writer(tempfile, delimiter=',', quotechar='"')
        i = 0
        for row in reader: 
            row[2] = new_lowest[i]
            i += 1
            writer.writerow(row)

    shutil.move(tempfile.name, "urls.csv")

    return


def makeCsv(items, fieldnames, discounts, categories, urls, lowest_prices, file_name):
    file_path = path.join(getcwd(), file_name)

    csv_file = open(file=file_path, mode="w+", encoding="utf-8", newline='')
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerow(categories)
    writer.writerow(items)
    writer.writerow(discounts)
    writer.writerow(urls)
    writer.writerow(lowest_prices)

    csv_file.close()


def main():
    scrapeUrls()
    print('Success! Results can be found in result.csv in the project folder :)')


main()
