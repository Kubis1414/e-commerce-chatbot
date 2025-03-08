import streamlit as st

def product_carousel(products):
    """
    Zobrazí carousel s doporučenými produkty.
    
    Args:
        products (list): Seznam produktů k zobrazení, každý produkt obsahuje name, description, price, image_url a url
    """
    if not products:
        return
        
    # Použijeme columns pro vytvoření mřížky produktů
    cols = st.columns(min(len(products), 3))  # Maximálně 3 produkty na řádek
    
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            with st.container():
                # Obrázek produktu
                st.image(product.get("image_url", "https://placehold.co/400"), 
                        caption=product.get("name", ""),
                        use_container_width=True)
                
                # Název produktu jako odkaz
                st.markdown(f"[{product.get('name', '')}]({product.get('url', '')})")
                
                # Popis produktu
                st.write(product.get("description", ""))
                
                # Cena produktu
                st.write(f"**{product.get('price', 0):,.2f} Kč**") 