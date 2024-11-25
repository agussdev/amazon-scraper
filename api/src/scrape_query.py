from botasaurus.request import request, Request
from botasaurus.soupify import soupify

@request
def scrape_query(request: Request, data):
    # Construir la URL con el número de página
    page = data.get("page", 1)
    base_url = f"https://www.amazon.es/s?k={data['keyword']}"
    if page > 1:
        url = f"{base_url}&page={page}"
    else:
        url = base_url
        
    response = request.get(url)
    soup = soupify(response)
    
    # Encontrar todos los productos en la página de resultados
    products = soup.find_all('div', {'data-component-type': 's-search-result'})
    
    results = []
    for product in products:
        # Extraer título
        title_element = product.find('h2', {'class': 'a-size-mini'})
        title = title_element.get_text().strip() if title_element else "No disponible"
        
        # Extraer precio
        price_element = product.find('span', {'class': 'a-price'})
        price = price_element.find('span', {'class': 'a-offscreen'}).get_text().strip() if price_element else "No disponible"
        
        # Extraer enlace del producto
        link_element = product.find('a', {'class': 'a-link-normal s-no-outline'})
        link = "https://www.amazon.es" + link_element['href'] if link_element else "No disponible"
        
        results.append({
            "title": title,
            "price": price,
            "link": link
        })
    
    return results
     