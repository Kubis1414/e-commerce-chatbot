import streamlit as st

def product_carousel(products):
    """
    Zobrazí mřížku s doporučenými produkty.
    - Karty mají konzistentní výšku obrázkové části.
    - Popis je omezen na max_desc_length znaků s tooltipem pro plný text.
    - Celá karta je klikatelná (pokud produkt má URL).

    Args:
        products (list): Seznam slovníků produktů k zobrazení.
                        Každý slovník by měl obsahovat klíče:
                        'name', 'url', 'image_url', 'description', 'price'.
                        'image_url' bude použita pro zobrazení, nebo placeholder, pokud chybí.
    """
    if not products:
        st.write("Žádné doporučené produkty k zobrazení.")
        return

    st.markdown("""
    <style>
    /* --- Carousel Container (Used for both Mobile and Desktop) --- */
    .product-carousel-container {
        display: block; /* Visible by default */
        overflow-x: auto; /* Horizontal scrolling */
        white-space: nowrap; /* Prevent wrapping */
        padding: 10px 0 10px 8px; /* Add left padding, keep top/bottom */
        padding-right: 30px; /* Add right padding to make the next item peek */
        clip-path: inset(0 0 0 0); /* Clip content to padding box */
        -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
        scrollbar-width: none; /* Hide scrollbar (Firefox) */
        margin: 0 -10px; /* Compensate for Streamlit padding */
    }
    .product-carousel-container::-webkit-scrollbar {
        display: none; /* Hide scrollbar (Chrome/Safari) */
    }

    /* --- Carousel Item Styling (Common) --- */
    .carousel-item {
        display: inline-block; /* Items side-by-side */
        width: 250px; /* Fixed width for carousel items */
        padding: 0 8px; /* Spacing between items */
        vertical-align: top;
        white-space: normal; /* Allow text wrapping inside the item */
    }

    /* --- Product Card Container (Common Styling) --- */
    .product-card-container {
        height: 100%; /* Základ pro vyplnění výšky sloupce */
        display: flex; /* Použít flexbox pro vnitřní uspořádání */
        flex-direction: column; /* Prvky uvnitř budou pod sebou */
        border: 1px solid #eee; /* Tenký šedý rámeček */
        border-radius: 8px; /* Zaoblené rohy */
        margin-bottom: 15px; /* Mezera pod kartou */
        overflow: hidden; /* Ořízne obsah podle border-radius */
        background-color: #fff; /* Bílé pozadí karty */
    }

    /* --- Odkaz obalující celou kartu (pokud existuje URL) --- */
    a.product-card-link, div.product-card-link { /* Styly platí pro <a> i fallback <div> */
        display: flex; /* Vnitřní layout pomocí flexbox */
        flex-direction: column; /* Prvky pod sebou (obrázek, detaily) */
        flex-grow: 1; /* Odkaz/div zabere všechnu dostupnou výšku v kontejneru */
        text-decoration: none; /* Bez podtržení */
        color: inherit; /* Dědit barvu textu (černá/šedá) */
        padding: 10px; /* Vnitřní odsazení karty */
        transition: box-shadow 0.2s ease-in-out; /* Plynulý přechod pro hover efekt */
    }

    /* --- Hover efekt pro odkaz --- */
    a.product-card-link:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.1); /* Mírný stín při najetí myší */
        color: inherit; /* Zachovat barvu textu */
        text-decoration: none; /* Žádné podtržení */
    }

    /* --- Kontejner pro obrázek (Common) --- */
    /* Keep desktop height for consistency, or adjust if needed */
    .product-image-container {
        height: 200px; 
        display: flex;
        align-items: center; /* Vertikální centrování obrázku */
        justify-content: center; /* Horizontální centrování obrázku */
        overflow: hidden;
        margin-bottom: 15px; /* Mezera mezi obrázkem a textem */
    }
    
    /* --- Media Queries Removed - Styles below apply to all sizes --- */

    /* --- Samotný obrázek (Common) --- */
    .product-image {
        max-height: 100%;
        max-width: 100%;
        object-fit: contain; /* Zachovat poměr stran, vejít se celý */
        border-radius: 4px; /* Lehké zaoblení rohů obrázku */
    }

    /* --- Kontejner pro textovou část (název, popis, cena) --- */
    .product-details {
        flex-grow: 1; /* Textová část zabere zbytek místa pod obrázkem */
        display: flex;
        flex-direction: column;
    }
    .product-details h5 { /* Styl pro název produktu */
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 1em; /* Velikost písma názvu */
        font-weight: 600; /* Mírně tučnější název */
        color: #31333F;
        /* Omezení na 2 řádky s tečkami (vyžaduje Webkit prohlížeče) */
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3; /* Výška řádku pro lepší čitelnost při zalomení */
        min-height: 2.6em; /* Rezervuje místo pro 2 řádky */

    }
    .product-details small { /* Styl pro popis */
        font-size: 0.85em;
        color: #6c757d; /* Tmavě šedá barva popisu */
        line-height: 1.4;
        margin-bottom: 10px;
        /* Omezení na 3 řádky s tečkami (pro popis) */
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        min-height: 4.2em; /* Rezervuje místo pro 3 řádky */

    }


    /* --- Kontejner pro cenu (aby byla dole) --- */
    .product-price {
        margin-top: auto; /* Posune cenu na spodek kontejneru s detaily */
        padding-top: 10px; /* Malá mezera nad cenou */
        font-size: 1.1em;
        font-weight: bold;
        color: #31333F;
        text-align: right; /* Zarovnání ceny doprava */
    }

    </style>
    """, unsafe_allow_html=True)

    # --- 2. Generate HTML for the Carousel ---
    carousel_html = '<div class="product-carousel-container">' # Use the unified class name

    for product in products:
        # --- Get product data ---
        name = product.get('name', 'Neznámý produkt')
        url = product.get('url')
        image_url = product.get('image_url')
        if not image_url or not str(image_url).strip():
            image_url = "https://placehold.co/400x300?text=Obrázek+není+k+dispozici"

        full_description = product.get("description", "")
        price = product.get("price")

        # --- Truncate description ---
        max_desc_length = 70 # Zvýšíme limit pro popis na 3 řádky
        ellipsis = "..."
        display_description = full_description # Výchozí hodnota
        tooltip_text = None # Tooltip jen pokud zkracujeme

        # Check if description is None or empty before checking length
        if full_description and len(full_description) > max_desc_length:
            chars_to_keep = max_desc_length - len(ellipsis)
            if chars_to_keep > 0:
                display_description = full_description[:chars_to_keep] + ellipsis
                tooltip_text = full_description # Plný text do tooltipu
                # Pokud limit < délka elipsy, zobrazíme jen prvních max_desc_length znaků
            else:
                display_description = full_description[:max_desc_length]
                tooltip_text = full_description

        # --- Format price ---
        if price is not None:
            try:
                price_float = float(price)
                formatted_price = f"{price_float:,.0f} Kč".replace(",", " ")
            except (ValueError, TypeError):
                formatted_price = "Cena neuvedena"
        else:
            formatted_price = "Cena neuvedena"

        # --- Build HTML for a single card ---
        link_start = f'<a href="{url}" target="_blank" class="product-card-link" title="Zobrazit detail produktu: {name}">' if url else '<div class="product-card-link">'
        link_end = '</a>' if url else '</div>'

        card_html = f"""
            <div class="product-card-container">
                {link_start}
                    <div class="product-image-container">
                        <img src="{image_url}" class="product-image" alt="{name}" loading="lazy">
                    </div>
                    <div class="product-details">
                        <h5>{name}</h5>
                        <small {'title="'+tooltip_text+'"' if tooltip_text else ''}>{display_description if display_description else ' '}</small>
                        <div class="product-price">
                            {formatted_price}
                        </div>
                    </div>
                {link_end}
            </div>
        """

        # --- Add card to Carousel HTML string ---
        carousel_html += f'<div class="carousel-item">{card_html}</div>'

    carousel_html += '</div>'  # Close product-carousel-container

    # --- 3. Render the Carousel HTML structure ---
    st.markdown(carousel_html, unsafe_allow_html=True)
