from botasaurus.request import request, Request
from botasaurus.soupify import soupify

@request(
    output=None  # Esto evita que se guarde el resultado
)
def scrape_heading_task(request: Request, data):
    # Navigate to the Link
    response = request.get(data["link"])

    # Create a BeautifulSoup object    
    soup = soupify(response)
    
    # Obtener el título de la página
    product_name = soup.find('title').get_text().strip()
    
    # Obtener el precio usando las clases específicas mostradas en la imagen
    price_element = soup.find('span', {'class': ['a-price', 'aok-align-center'], 'data-a-size': 'xl'})
    if price_element:
        price_text = price_element.find('span', {'class': 'a-offscreen'})
        price = price_text.get_text().strip() if price_text else "No disponible"
    else:
        price = "No disponible"
    
    # Obtener la política de devoluciones - buscando primero el enlace y luego el span dentro
    return_policy_link = soup.find('a', {'class': 'a-link-normal a-popover-trigger a-declarative'})
    return_policy_text = return_policy_link.find('span').get_text().strip() if return_policy_link else "No disponible"

    # Return the data
    return {
        "product_name": product_name,
        "price": price,
        "return_policy": return_policy_text,
        "link": data["link"]
    }
     